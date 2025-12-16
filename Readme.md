# 🛰️ ISS Real-Time Orbital Tracker

![Python](https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python)
![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=apachekafka)
![Apache Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C?style=for-the-badge&logo=apachespark)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=apacheairflow)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql)

**A production-grade real-time data engineering pipeline that ingests, processes, stores, and visualizes live telemetry from the International Space Station.**

---

## 📸 Dashboard Preview

![ISS Real-Time Dashboard](Dashboard_demo.jpg)

*The interactive Streamlit dashboard featuring live global tracking, orbital path visualization, and real-time telemetry metrics.*

---

## 🧠 Architecture Diagram

![Project Architecture](ISS_project_architecture.png)

*End-to-end streaming architecture with Producer-Broker-Consumer pattern, enhanced by orchestration and monitoring.*

---

## 📖 Project Overview

This project demonstrates an **end-to-end streaming architecture** designed to mimic modern enterprise data platforms. It goes beyond simple scripts by implementing a robust, containerized system capable of handling continuous data streams with fault tolerance, scalability, and monitoring.

**Key Features:**
- **🚀 Real-time Ingestion:** Polls the public ISS API (http://api.open-notify.org/iss-now.json) for sub-second location updates.
- **⚡ Event Streaming:** Uses **Apache Kafka** to decouple producers from consumers and ensure reliable message delivery.
- **🔥 Stream Processing:** Utilizes **Spark Structured Streaming** for low-latency transformations and enrichments.
- **💾 Persistent Storage:** Sinks processed data into **MySQL** for historical querying and analysis.
- **📊 Interactive UI:** Visualizes the orbital path and ground track using **Streamlit** with **PyDeck** for immersive 3D globe rendering.
- **🤖 Orchestration & Monitoring:** Fully managed by **Apache Airflow** for scheduling, health checks, data quality alerts, and automated maintenance.
- **🛡️ Reliability:** Built-in retries, schema enforcement, and backpressure handling.

---

## 🧩 Tech Stack

| Domain          | Technology                  | Role                              |
|-----------------|-----------------------------|-----------------------------------|
| Ingestion       | Python, Requests            | Fetching API data                 |
| Messaging       | Apache Kafka                | Message broker & buffering        |
| Processing      | Spark Structured Streaming  | ETL & real-time transformations   |
| Storage         | MySQL                       | Relational data persistence       |
| Orchestration   | Apache Airflow              | Scheduling, monitoring & cleanup  |
| Visualization   | Streamlit, PyDeck           | Interactive front-end dashboard   |
| Infra           | Docker Compose              | Container management              |

---

## ⚙️ Engineering Phases

**Phase 1: Ingestion & Messaging**  
Component: `iss_producer.py`  
- Fetches live position data (latitude, longitude, timestamp).  
- Serializes payload to JSON and pushes to Kafka topic `iss_raw`.  
- Handles API rate limiting, connection retries, and graceful shutdowns.

**Phase 2: Stream Processing**  
Component: `iss_streaming_job.py` (Spark)  
- Consumes from `iss_raw`.  
- Enforces schema (Lat/Lon as Doubles, timestamp).  
- Generates derived metrics (velocity, visibility, local time at position).  
- Writes enriched data to MySQL via JDBC sink.

**Phase 3: Visualization**  
Component: `app.py` (Streamlit)  
- Queries MySQL for the last N records (e.g., last 100 positions).  
- Renders a 3D globe with live ground track path using PyDeck.  
- Displays real-time KPIs (altitude, velocity, current position).  
- Auto-refreshes for live movement.

**Phase 4: Reliability Engineering (Airflow)**  
DAGs:  
- `iss_monitoring` (Runs every 5 mins): Checks data freshness (alerts if >15s stale), monitors record growth.  
- `iss_restart`: Automated cleanup of logs and fail-safe container restarts.

---

## 🛠️ How to Run

### Prerequisites
- Docker & Docker Compose installed.
- 4GB+ RAM available for Docker (Spark/Kafka require resources).

### 1️⃣ Clone & Start
```bash
git clone https://github.com/NAYANJ7/iss-data-platform.git
cd iss-data-platform
docker compose up --build -d
```

### Service URLs

| Service      | URL                        | Description                  | Credentials (if any) |
|--------------|----------------------------|------------------------------|---------------------|
| Dashboard    | http://localhost:8501      | Live Tracking UI             | -                   |
| Airflow      | http://localhost:8082      | DAGs & Monitoring            | airflow / airflow   |
| MySQL        | localhost:3306             | Database access              | root / example      |

---

## 📂 Project Structure

```
iss-real-time-tracker/
├── airflow/                  # Airflow DAGs & configurations
├── config/                   # Global configuration files
├── dashboard/                # Streamlit Dashboard source code
├── db/                       # Database schema & initialization
├── kafka/                    # Kafka setup & config
├── producer/                 # Data ingestion (Producer) scripts
├── spark/                    # Spark processing jobs
├── webapp/                   # Web application components
├── docker-compose.yaml       # Main orchestration file
├── Dashboard_demo.jpg        # Dashboard screenshot
├── ISS_project_architecture.png  # Architecture diagram
├── testapi.py                # API endpoint testing script
├── troubleshoot.sh           # System troubleshooting utility
└── README.md                 # This documentation
```

---

## 🚀 Why This Project?

This is not just a script—it's a **complete system**. It showcases:
- Handling high-velocity streaming data.
- Ensuring reliability with monitoring and orchestration.
- Containerization for reproducibility ("It works on my machine" solved).
- Scalable design patterns used in real-world data platforms.

Perfect for: Data Engineering portfolios, learning event-driven architecture, mastering Kafka-Spark-Airflow integration, or exploring space data!

---

## 🔮 Future Enhancements

- [ ] **Grafana Integration:** Visualize Kafka consumer lag, Spark metrics, and pipeline throughput.
- [ ] **Cloud Deployment:** Migrate to AWS (MSK for Kafka, EMR for Spark, RDS for MySQL, ECS/EKS for orchestration).
- [ ] **Data Lake Layer:** Sink raw data to S3 in Parquet format for long-term storage and batch analytics.
- [ ] **Alerting System:** Integrate Slack/Email notifications via Airflow for anomalies (e.g., API downtime).
- [ ] **Multiple Sources:** Add crew info, ISS passes over specific locations, or astronaut data from additional APIs.
- [ ] **Machine Learning:** Predict orbital paths or detect anomalies using historical data.
- [ ] **Kubernetes Deployment:** Orchestrate with Helm charts for production scalability.
- [ ] **Security Enhancements:** Add authentication to dashboard and encrypt Kafka traffic.

---

👤 **Author**  
Nayan Jain  
Data Engineering | Streaming Systems | Real-time Pipelines  

[![GitHub](https://img.shields.io/badge/GitHub-NAYANJ7-181717?style=for-the-badge&logo=github)](https://github.com/NAYANJ7)  
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Nayan%20Jain-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/nayan-jain007)

⭐ If you found this helpful, please **star** the repository!
