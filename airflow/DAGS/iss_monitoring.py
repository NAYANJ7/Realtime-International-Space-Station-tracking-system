"""
ISS Pipeline Monitoring - WORKING VERSION
Place in: airflow/dags/iss_monitoring.py
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import mysql.connector
import time

default_args = {
    'owner': 'iss-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# ============================================
# DATABASE CONNECTION
# ============================================

def get_mysql_connection():
    """Get MySQL connection"""
    return mysql.connector.connect(
        host='mysql',
        port=3306,
        user='root',
        password='password',
        database='iss_db'
    )

# ============================================
# HEALTH CHECK FUNCTIONS
# ============================================

def check_mysql_health(**context):
    """Check if MySQL is healthy and has data"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SHOW TABLES LIKE 'iss_positions'")
        result = cursor.fetchone()
        
        if not result:
            print("❌ Table 'iss_positions' not found")
            cursor.close()
            conn.close()
            return False
        
        # Get record count and latest timestamp
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MAX(ts_unix) as latest_ts,
                UNIX_TIMESTAMP() - MAX(ts_unix) as data_age
            FROM iss_positions
        """)
        
        stats = cursor.fetchone()
        total_records = stats[0]
        latest_ts = stats[1]
        data_age = stats[2] if stats[2] else 999999
        
        print("=" * 60)
        print("MYSQL HEALTH CHECK")
        print("=" * 60)
        print(f"✅ Connection: Successful")
        print(f"📊 Total Records: {total_records:,}")
        print(f"⏰ Latest Data Age: {data_age:.1f} seconds")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
        # Push to XCom
        context['task_instance'].xcom_push(key='total_records', value=total_records)
        context['task_instance'].xcom_push(key='data_age', value=data_age)
        
        return True
        
    except Exception as e:
        print(f"❌ MySQL health check failed: {str(e)}")
        return False


def check_producer_active(**context):
    """Check if producer is actively creating data"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Check for records in last 60 seconds
        cursor.execute("""
            SELECT COUNT(*) FROM iss_positions 
            WHERE ts_unix > UNIX_TIMESTAMP() - 60
        """)
        
        recent_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        is_active = recent_count > 0
        
        print("=" * 60)
        print("PRODUCER STATUS CHECK")
        print("=" * 60)
        print(f"📈 Records (last 60s): {recent_count}")
        print(f"Status: {'✅ ACTIVE' if is_active else '❌ INACTIVE'}")
        print("=" * 60)
        
        context['task_instance'].xcom_push(key='producer_active', value=is_active)
        context['task_instance'].xcom_push(key='recent_records', value=recent_count)
        
        return True
        
    except Exception as e:
        print(f"❌ Producer check failed: {str(e)}")
        return False


def check_data_freshness(**context):
    """Check if data is fresh (< 15 seconds old)"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                MAX(ts_unix) as latest_ts,
                UNIX_TIMESTAMP() - MAX(ts_unix) as age_seconds
            FROM iss_positions
        """)
        
        result = cursor.fetchone()
        age_seconds = result[1] if result[1] else 999999
        
        cursor.close()
        conn.close()
        
        is_fresh = age_seconds < 15
        
        print("=" * 60)
        print("DATA FRESHNESS CHECK")
        print("=" * 60)
        print(f"⏰ Data Age: {age_seconds:.1f} seconds")
        print(f"Status: {'✅ FRESH' if is_fresh else '⚠️ STALE'}")
        print("=" * 60)
        
        context['task_instance'].xcom_push(key='data_fresh', value=is_fresh)
        context['task_instance'].xcom_push(key='age_seconds', value=age_seconds)
        
        return True
        
    except Exception as e:
        print(f"❌ Freshness check failed: {str(e)}")
        return False


def calculate_pipeline_metrics(**context):
    """Calculate pipeline performance metrics"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Get statistics for last hour
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                AVG(altitude_km) as avg_altitude,
                AVG(velocity_kmh) as avg_velocity,
                MIN(altitude_km) as min_altitude,
                MAX(altitude_km) as max_altitude,
                MIN(ts_unix) as oldest_ts,
                MAX(ts_unix) as newest_ts
            FROM iss_positions
            WHERE ts_unix > UNIX_TIMESTAMP() - 3600
        """)
        
        result = cursor.fetchone()
        
        if result and result[0] > 0:
            total_records = result[0]
            avg_altitude = result[1]
            avg_velocity = result[2]
            min_altitude = result[3]
            max_altitude = result[4]
            oldest_ts = result[5]
            newest_ts = result[6]
            
            duration_seconds = newest_ts - oldest_ts if newest_ts and oldest_ts else 1
            records_per_second = total_records / duration_seconds if duration_seconds > 0 else 0
            
            print("=" * 60)
            print("PIPELINE METRICS (Last Hour)")
            print("=" * 60)
            print(f"📊 Total Records: {total_records:,}")
            print(f"⚡ Records/Second: {records_per_second:.2f}")
            print(f"🚀 Avg Altitude: {avg_altitude:.2f} km")
            print(f"💨 Avg Velocity: {avg_velocity:.2f} km/h")
            print(f"📏 Altitude Range: {min_altitude:.2f} - {max_altitude:.2f} km")
            print(f"⏱️ Time Span: {duration_seconds:.0f} seconds")
            print("=" * 60)
            
            # Check if metrics are within expected ranges
            altitude_ok = 400 <= avg_altitude <= 420
            velocity_ok = 27000 <= avg_velocity <= 28500
            
            print(f"\n✅ Altitude Check: {'PASS' if altitude_ok else 'FAIL'}")
            print(f"✅ Velocity Check: {'PASS' if velocity_ok else 'FAIL'}")
            
            context['task_instance'].xcom_push(key='metrics', value={
                'total_records': total_records,
                'records_per_second': records_per_second,
                'avg_altitude': avg_altitude,
                'avg_velocity': avg_velocity
            })
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Metrics calculation failed: {str(e)}")
        return False


def cleanup_old_data(**context):
    """Remove data older than 24 hours"""
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # Count records to be deleted
        cursor.execute("""
            SELECT COUNT(*) FROM iss_positions 
            WHERE ts_unix < UNIX_TIMESTAMP() - 86400
        """)
        old_count = cursor.fetchone()[0]
        
        # Delete old records
        cursor.execute("""
            DELETE FROM iss_positions 
            WHERE ts_unix < UNIX_TIMESTAMP() - 86400
        """)
        
        deleted = cursor.rowcount
        conn.commit()
        
        print("=" * 60)
        print("DATA CLEANUP")
        print("=" * 60)
        print(f"🗑️ Records Deleted: {deleted:,}")
        print(f"✅ Cleanup Complete")
        print("=" * 60)
        
        cursor.close()
        conn.close()
        
        context['task_instance'].xcom_push(key='deleted_count', value=deleted)
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {str(e)}")
        return False


def generate_health_report(**context):
    """Generate comprehensive health report"""
    ti = context['task_instance']
    
    # Get all metrics from XCom
    total_records = ti.xcom_pull(task_ids='check_mysql', key='total_records') or 0
    data_age = ti.xcom_pull(task_ids='check_mysql', key='data_age') or 0
    producer_active = ti.xcom_pull(task_ids='check_producer', key='producer_active') or False
    recent_records = ti.xcom_pull(task_ids='check_producer', key='recent_records') or 0
    data_fresh = ti.xcom_pull(task_ids='check_freshness', key='data_fresh') or False
    age_seconds = ti.xcom_pull(task_ids='check_freshness', key='age_seconds') or 0
    metrics = ti.xcom_pull(task_ids='calculate_metrics', key='metrics') or {}
    deleted_count = ti.xcom_pull(task_ids='cleanup_data', key='deleted_count') or 0
    
    print("\n" + "=" * 70)
    print("ISS PIPELINE HEALTH REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print("\n📊 COMPONENT STATUS:")
    print(f"  MySQL Database:     {'✅ Healthy' if total_records > 0 else '❌ No Data'}")
    print(f"  Producer:           {'✅ Active' if producer_active else '❌ Inactive'}")
    print(f"  Data Freshness:     {'✅ Fresh' if data_fresh else '⚠️ Stale'}")
    
    print("\n📈 KEY METRICS:")
    print(f"  Total Records:      {total_records:,}")
    print(f"  Recent Records:     {recent_records} (last 60s)")
    print(f"  Data Age:           {age_seconds:.1f} seconds")
    print(f"  Records Cleaned:    {deleted_count:,}")
    
    if metrics:
        print(f"\n🚀 PERFORMANCE (Last Hour):")
        print(f"  Records/Second:     {metrics.get('records_per_second', 0):.2f}")
        print(f"  Avg Altitude:       {metrics.get('avg_altitude', 0):.2f} km")
        print(f"  Avg Velocity:       {metrics.get('avg_velocity', 0):.2f} km/h")
    
    print("\n" + "=" * 70)
    
    # Overall health status
    all_healthy = producer_active and data_fresh and total_records > 0
    
    if all_healthy:
        print("✅ OVERALL STATUS: ALL SYSTEMS OPERATIONAL")
    else:
        print("⚠️ OVERALL STATUS: ISSUES DETECTED")
    
    print("=" * 70 + "\n")
    
    return all_healthy


# ============================================
# DAG DEFINITION
# ============================================

with DAG(
    'iss_monitoring',
    default_args=default_args,
    description='Monitor ISS pipeline health and performance',
    schedule_interval=timedelta(minutes=5),
    catchup=False,
    tags=['iss', 'monitoring', 'production'],
) as dag:

    # Health checks
    mysql_check = PythonOperator(
        task_id='check_mysql',
        python_callable=check_mysql_health,
    )

    producer_check = PythonOperator(
        task_id='check_producer',
        python_callable=check_producer_active,
    )

    freshness_check = PythonOperator(
        task_id='check_freshness',
        python_callable=check_data_freshness,
    )

    # Metrics and cleanup
    metrics = PythonOperator(
        task_id='calculate_metrics',
        python_callable=calculate_pipeline_metrics,
    )

    cleanup = PythonOperator(
        task_id='cleanup_data',
        python_callable=cleanup_old_data,
    )

    # Final report
    report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_health_report,
    )

    # Task dependencies
    [mysql_check, producer_check, freshness_check] >> metrics >> cleanup >> report


# ============================================
# MANUAL RESTART DAG
# ============================================

with DAG(
    'iss_restart',
    default_args=default_args,
    description='Manually restart ISS pipeline components',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['iss', 'maintenance'],
) as restart_dag:

    restart_producer = BashOperator(
        task_id='restart_producer',
        bash_command='docker restart iss-data-platform-producer-1',
    )

    restart_spark = BashOperator(
        task_id='restart_spark',
        bash_command='docker restart iss-data-platform-spark-1',
    )

    wait_services = BashOperator(
        task_id='wait_for_services',
        bash_command='sleep 30 && echo "Services restarted, waiting for stabilization..."',
    )

    verify = PythonOperator(
        task_id='verify_restart',
        python_callable=check_producer_active,
    )

    [restart_producer, restart_spark] >> wait_services >> verify