FROM apache/spark:3.5.3-python3

USER root

# Create cache directory with proper permissions
RUN mkdir -p /home/spark/.ivy2/cache && \
    chown -R spark:spark /home/spark/.ivy2

WORKDIR /opt/spark-apps

COPY iss_streaming_job.py .

# Pre-download the required packages to avoid runtime downloads
RUN /opt/spark/bin/spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,mysql:mysql-connector-java:8.0.33 \
    --dry-run \
    iss_streaming_job.py || true

USER 185