from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "airflow",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="goodair_pipeline",
    default_args=default_args,
    description="Pipeline qualite air + meteo — Bronze/Silver/Gold",
    schedule="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl", "goodair", "datalake"],
) as dag:

    # ── BRONZE : collecte API → MinIO ──
    etl_aqicn = BashOperator(
        task_id="etl_aqicn",
        bash_command="python /opt/airflow/etl/etl_aqicn.py"
    )

    etl_openweather = BashOperator(
        task_id="etl_openweather",
        bash_command="python /opt/airflow/etl/etl_openweather.py"
    )

    # ── SILVER : nettoyage ──
    bronze_to_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command="python /opt/airflow/etl/bronze_to_silver.py"
    )

    # ── GOLD : agregation + dataset ML ──
    silver_to_gold = BashOperator(
        task_id="silver_to_gold",
        bash_command="python /opt/airflow/etl/silver_to_gold.py"
    )

    # ── QUALITE : controles + rapport + alerte ──
    data_quality = BashOperator(
        task_id="data_quality",
        bash_command="python /opt/airflow/etl/data_quality.py"
    )

    # ── Séquence ──
    etl_aqicn >> etl_openweather >> bronze_to_silver >> silver_to_gold >> data_quality