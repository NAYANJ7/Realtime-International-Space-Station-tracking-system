import os
from pyspark.sql import SparkSession, functions as F, types as T
import time

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "iss-topic")

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_DB = "iss_db"
MYSQL_TABLE = "iss_positions"
MYSQL_USER = "root"
MYSQL_PASS = "password"

JDBC = f"jdbc:mysql://{MYSQL_HOST}:3306/{MYSQL_DB}?serverTimezone=UTC"

# Wait for Kafka topic to be ready
print(f"Waiting for Kafka topic '{TOPIC}' to be available...")
time.sleep(10)

spark = (
    SparkSession.builder.appName("ISSFastStream")
    .config("spark.sql.shuffle.partitions", "2")
    .config("spark.streaming.backpressure.enabled", "true")
    .config("spark.sql.streaming.minBatchesToRetain", "2")
    .config("spark.streaming.kafka.maxRatePerPartition", "100")
    .config("spark.sql.adaptive.enabled", "true")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

schema = T.StructType([
    T.StructField("name", T.StringType()),
    T.StructField("id", T.LongType()),
    T.StructField("latitude", T.DoubleType()),
    T.StructField("longitude", T.DoubleType()),
    T.StructField("altitude", T.DoubleType()),
    T.StructField("velocity", T.DoubleType()),
    T.StructField("timestamp", T.LongType()),
    T.StructField("visibility", T.StringType()),
])

print(f"Connecting to Kafka at {BOOTSTRAP}, topic: {TOPIC}")

raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", BOOTSTRAP)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "earliest")  # Changed from latest to earliest
    .option("failOnDataLoss", "false")
    .option("kafka.session.timeout.ms", "30000")
    .option("kafka.request.timeout.ms", "40000")
    .load()
)

df = raw.select(
    F.from_json(F.col("value").cast("string"), schema).alias("d")
).select("d.*")

# Add required columns that dashboard expects
final = (
    df.withColumn("ts_unix", F.col("timestamp"))
      .withColumn("ts_utc", F.from_unixtime("timestamp"))
      .withColumn("record_id", F.concat(F.col("id"), F.lit("_"), F.col("timestamp")))
      .withColumn("altitude_km", F.col("altitude"))
      .withColumn("velocity_kmh", F.col("velocity"))
      .withColumn("ingested_at", F.current_timestamp())
      .select(
          "record_id", "id", "ts_unix", "ts_utc", 
          "latitude", "longitude", "altitude_km", "velocity_kmh",
          "visibility", "ingested_at"
      )
)

def write_batch(batch, batch_id):
    if batch.rdd.isEmpty():
        return
    
    try:
        batch.write.format("jdbc") \
            .option("url", JDBC) \
            .option("dbtable", MYSQL_TABLE) \
            .option("user", MYSQL_USER) \
            .option("password", MYSQL_PASS) \
            .option("driver", "com.mysql.cj.jdbc.Driver") \
            .option("batchsize", "500") \
            .option("isolationLevel", "READ_COMMITTED") \
            .mode("append") \
            .save()
        
        count = batch.count()
        print(f"✓ Batch {batch_id}: Inserted {count} rows")
    except Exception as e:
        print(f"✗ Batch {batch_id} failed: {e}")

print("Starting Spark Streaming job...")

(
    final.writeStream
    .foreachBatch(write_batch)
    .trigger(processingTime="2 seconds")
    .option("checkpointLocation", "/tmp/isschk")
    .outputMode("append")
    .start()
    .awaitTermination()
)