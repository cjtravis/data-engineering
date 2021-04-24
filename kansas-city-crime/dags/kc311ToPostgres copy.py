from airflow.models import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.python import PythonOperator
from airflow.operators.http_operator import SimpleHttpOperator
from datetime import datetime

import pandas as pd
from sodapy import Socrata
import json 
default_args = {
    'start_date': datetime(2021,4,10)
}
# https://data.kcmo.org/resource/d4px-6rwg.json
with DAG('kc311ToPostgres', schedule_interval='@daily',
        default_args=default_args,
        catchup=False) as dag:

    is_api_available =  HttpSensor(
        task_id='is_api_available',
        http_conn_id='http_data_kcmo_org',
        endpoint='/resource/d4px-6rwg.json'
    )

    fetch_311 = SimpleHttpOperator(
        task_id='fetch_311_data',
        http_conn_id='http_data_kcmo_org',
        endpoint='resource/d4px-6rwg.json',
        method='GET',
        response_filter=lambda response: json.loads(response.text),
        log_response=True
    )
 