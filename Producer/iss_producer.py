import os
import json
import time
import math
import logging
import requests
from confluent_kafka import Producer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "iss-topic")
API_URL = "http://api.open-notify.org/iss-now.json"

POLL_INTERVAL = 1

logging.basicConfig(
    level=logging.INFO,
    format="[PRODUCER] %(asctime)s %(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)


def ensure_topic():
    """Create topic if missing."""
    try:
        admin = AdminClient({'bootstrap.servers': KAFKA_BOOTSTRAP})
        topic_metadata = admin.list_topics(timeout=5)
        
        if TOPIC not in topic_metadata.topics:
            new_topic = NewTopic(TOPIC, num_partitions=1, replication_factor=1)
            fs = admin.create_topics([new_topic])
            
            for topic, f in fs.items():
                try:
                    f.result()
                    log.info("Topic created: %s", topic)
                except Exception as e:
                    log.warning("Topic creation issue: %s", e)
        else:
            log.info("Topic already exists: %s", TOPIC)
    except Exception as e:
        log.warning("Topic check failed: %s", e)


def delivery_callback(err, msg):
    """Callback for message delivery reports."""
    if err:
        log.error('Message delivery failed: %s', err)
    

def producer_client():
    config = {
        'bootstrap.servers': KAFKA_BOOTSTRAP,
        'client.id': 'iss-producer',
        'acks': 'all',
        'compression.type': 'gzip',
        'linger.ms': 10,
        'batch.size': 16384,
    }
    return Producer(config)


def fetch_real_iss():
    """Use API when available."""
    r = requests.get(API_URL, timeout=3)
    r.raise_for_status()
    js = r.json()
    return {
        "name": "iss",
        "id": 25544,
        "latitude": float(js["iss_position"]["latitude"]),
        "longitude": float(js["iss_position"]["longitude"]),
        "altitude": 408.0,
        "velocity": 27600.0,
        "timestamp": js["timestamp"],
        "visibility": "daylight",
    }


def synthetic(ts):
    """Realistic simulated ISS orbit with varying parameters."""
    # ISS orbital period: ~92 minutes
    period = 92 * 60
    frac = (ts % period) / period
    
    # Orbital inclination: 51.6 degrees
    lat = 51.6 * math.sin(2 * math.pi * frac)
    lon = ((frac * 360) - 180)
    
    # Altitude varies slightly (407-410 km)
    altitude = 408.0 + 1.5 * math.sin(4 * math.pi * frac)
    
    # Velocity varies with altitude (27580-27620 km/h)
    velocity = 27600.0 + 20.0 * math.cos(4 * math.pi * frac)
    
    # Calculate if ISS is in daylight or eclipse
    # Simple approximation based on longitude and time
    sun_angle = (ts % 86400) / 86400 * 360  # Sun position (0-360 degrees)
    iss_sun_diff = abs(lon - sun_angle)
    if iss_sun_diff > 180:
        iss_sun_diff = 360 - iss_sun_diff
    
    # ISS is in eclipse if it's on the dark side (roughly)
    if iss_sun_diff > 100:
        visibility = "eclipsed"
    else:
        visibility = "daylight"

    return {
        "name": "iss",
        "id": 25544,
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "altitude": round(altitude, 2),
        "velocity": round(velocity, 2),
        "timestamp": ts,
        "visibility": visibility,
    }


def main():
    log.info("Starting ISS Producer...")
    ensure_topic()
    
    # Wait for Kafka to be ready
    time.sleep(2)
    
    p = producer_client()
    count = 0
    consecutive_failures = 0

    while True:
        ts = int(time.time())
        try:
            data = fetch_real_iss()
            consecutive_failures = 0
            if count % 15 == 0:
                log.info("Using REAL API data")
        except Exception as e:
            consecutive_failures += 1
            if consecutive_failures == 1:
                log.info("API unavailable, using realistic simulation")
            data = synthetic(ts)

        try:
            # Produce message
            p.produce(
                TOPIC,
                key=str(data["id"]).encode('utf-8'),
                value=json.dumps(data).encode('utf-8'),
                callback=delivery_callback
            )
            
            # Poll to handle delivery callbacks
            p.poll(0)
            
            # Flush periodically
            if count % 3 == 0:
                p.flush(timeout=1)
                if count % 15 == 0:
                    log.info("Sent → lat=%.4f lon=%.4f alt=%.1f vel=%.0f vis=%s", 
                            data["latitude"], data["longitude"], 
                            data["altitude"], data["velocity"], data["visibility"])
            
            count += 1
        except BufferError:
            log.warning("Local producer queue full, waiting...")
            p.poll(1)
        except Exception as e:
            log.error("Kafka send failed: %s", e)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()