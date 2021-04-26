from airflow.models import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.python import PythonOperator
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.postgres_operator import PostgresOperator

from datetime import datetime
import os
import requests
import json

default_args = {
    'start_date': datetime(2021, 4, 10)
}

app_config = {
    'endpoint': 'resource/w795-ffu6.json',
    'url': 'https://data.kcmo.org'
}

def fetch_crime_window(ti):

    pg_hook = PostgresHook(postgres_conn_id='pg_kcmo_opendata')

    select_statement = """
        select 
            max(to_char(window_end, 'YYYY-MM-DD"T"HH24:MI:ss.ms')) 
          from kcmo.crime_2021_raw;
    """

    # establish PG connection, perform select
    connection = pg_hook.get_conn()
    cursor = connection.cursor()
    cursor.execute(select_statement)

    min_window_date = cursor.fetchone()[0]
    max_window_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]

    # set Airflow xcom variables
    ti.xcom_push(key='min_window', value=min_window_date)
    ti.xcom_push(key='max_window', value=max_window_date)


def download_latest_crime_data(ti):
    
    # get Airflow xcom variables
    max_window = ti.xcom_pull(key='max_window', task_ids='fetch_crime_window')
    min_window = ti.xcom_pull(key='min_window', task_ids='fetch_crime_window')

    filter_string = "report_date BETWEEN '{}' and '{}'".format(min_window, max_window)
    querystring = {"$where": filter_string}

    payload = ""
    url = "https://data.kcmo.org/resource/w795-ffu6.json"
    response = requests.request("GET", url, data=payload, params=querystring)

    json_data = response.json()
    print(f"Request URL: {response.request.url}\nRequest Body: {response.request.body}\nRequest Headers: {response.request.headers}")

    if response.json() and response.status_code == 200:

        file_name = str(datetime.now().date()) + '.json'
        tot_name = os.path.join(os.path.dirname(__file__), 'data', file_name)

        with open(tot_name, 'w') as outputfile:
            json.dump(json_data, outputfile)
    else:
        print(f"No data fetched or there was an error performing HTTP request (Response code: {str(resonse.status_code)}")


def load_data_raw(ti):
    # get xcom values
    max_window = ti.xcom_pull(key='max_window', task_ids='fetch_crime_window')
    min_window = ti.xcom_pull(key='min_window', task_ids='fetch_crime_window')

    pg_hook = PostgresHook(postgres_conn_id='pg_kcmo_opendata')

    file_name = str(datetime.now().date()) + '.json'
    tot_name = os.path.join(os.path.dirname(__file__), 'data', file_name)

    if os.path.isfile(tot_name):
        with open(tot_name, 'r') as inputfile:
            this_json_doc = json.load(inputfile)

        print(type(this_json_doc))
        print(type(json.dumps(this_json_doc)))

        row = (json.dumps(this_json_doc), min_window, max_window,)

        insert_statement = """
            INSERT INTO kcmo.crime_2021_raw(info, window_start, window_end) 
            VALUES (%s, to_timestamp(%s, 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone, 
            to_timestamp(%s, 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone);
            """

        # Only attempt insert if we retriev new data
        if os.path.getsize(tot_name) > 0:
            pg_hook.run(insert_statement, parameters=row)

            os.remove(tot_name)
        else:
            print("No file named {}".format(tot_name))
    else:
        print("No file named {}.  No data to load.".format(tot_name))

with DAG('fetch_kc_crime_data-v0.1', schedule_interval='@daily',
         default_args=default_args,
         catchup=False) as dag:

    check_endpoint_availability = HttpSensor(
        task_id='check_endpoint_availability',
        http_conn_id='http_data_kcmo_org',
        endpoint=app_config['endpoint']
    )

    download_latest_crime_data = PythonOperator(
        task_id='download_latest_crime_data',
        python_callable=download_latest_crime_data
    )

    load_data = PythonOperator(
        task_id='load_data_raw',
        python_callable=load_data_raw
    )

    fetch_crime_window = PythonOperator(
        task_id='fetch_crime_window',
        python_callable=fetch_crime_window
    )

    check_endpoint_availability >> fetch_crime_window >> download_latest_crime_data >> load_data

