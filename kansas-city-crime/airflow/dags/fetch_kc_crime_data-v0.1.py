from airflow.models import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.python import PythonOperator
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.hooks.postgres_hook import PostgresHook
from airflow.operators.postgres_operator import PostgresOperator

from datetime import datetime
import os
import requests
import pandas as pd
#from sodapy import Socrata
import json 

default_args = {
    'start_date': datetime(2021,4,10)
}

app_config = {
    'endpoint': 'resource/w795-ffu6.json',
    'url': 'https://data.kcmo.org'
}

def fetch_crime_window(ti):
    select_old = """
        with crime as (
            select
                json_array_elements_text(info)::json as e
            from
                crime_2021_raw),
            xform as (
            select to_timestamp(e->>'report_date', 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone as report_date
            from crime)
            select max(to_char(report_date, 'YYYY-MM-DD"T"HH24:MI:ss.ms')) from xform;
        """
    select = """select max(to_char(window_end, 'YYYY-MM-DD"T"HH24:MI:ss.ms')) from public.crime_2021_raw;"""
    pg_hook = PostgresHook(postgres_conn_id='pg_kcmo_opendata')
    connection = pg_hook.get_conn()
    cursor = connection.cursor()
    cursor.execute(select)
    min_window_date = cursor.fetchone()[0]
    print(min_window_date)
    ti.xcom_push(key='min_window', value=min_window_date)
    # date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    max_window_date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    # %Y-%m-%dT%-H:%M:%S.%f
    # 2021-04-18T17%:00:10.955
    print(max_window_date)
    ti.xcom_push(key='max_window', value=max_window_date)

def download_latest_crime_data(ti):
    max_window = ti.xcom_pull(key='max_window', task_ids='fetch_crime_window')
    min_window = ti.xcom_pull(key='min_window', task_ids='fetch_crime_window')
    
    #TODO - generate current date in correct date format (2021-04-03T12:00:00)
    #TODO - fetch last run date, probably from postgres
    #querystring = {}
    print("Min Window: {}".format(min_window))
    print("Max Window: {}".format(max_window))
    filter_str = "report_date BETWEEN '{}' and '{}'".format(min_window, max_window)
    querystring = {"$where":filter_str}
    print(querystring)
    payload = ""
    url = "https://data.kcmo.org/resource/w795-ffu6.json"
    response = requests.request("GET", url, data=payload, params=querystring)

    if response.status_code == 200 :

        #Get JSON data
        json_data = response.json()
        file_name = str(datetime.now().date()) + '.json'
        tot_name = os.path.join(os.path.dirname(__file__), 'data', file_name)
        print("Output file: {}".format(tot_name))

        with open(tot_name, 'w') as outputfile:
            json.dump(json_data, outputfile)
    else:
        print("Error in API call")

def load_data_raw(ti):
    max_window = ti.xcom_pull(key='max_window', task_ids='fetch_crime_window')
    min_window = ti.xcom_pull(key='min_window', task_ids='fetch_crime_window')
    pg_hook = PostgresHook(postgres_conn_id='pg_kcmo_opendata')

    file_name = str(datetime.now().date()) + '.json'
    tot_name = os.path.join(os.path.dirname(__file__), 'data', file_name)
    print("Output file: {}".format(tot_name))

    with open(tot_name, 'r') as inputfile:
        this_json_doc = json.load(inputfile)
    print(type(this_json_doc))
    print(type(json.dumps(this_json_doc)))
    #window_start = '2021-01-01T12:00:00'
    #window_end = '2021-04-01T12:00:00'
    row = (json.dumps(this_json_doc),min_window, max_window,)

    insert_cmd = """
        INSERT INTO public.crime_2021_raw(info, window_start, window_end) VALUES (%s, to_timestamp(%s, 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone, 
        to_timestamp(%s, 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone)
            ;"""

    pg_hook.run(insert_cmd, parameters=row)

def load_data():
    pg_hook = PostgresHook(postgres_conn_id='pg_kcmo_opendata')

    file_name = str(datetime.now().date()) + '.json'
    tot_name = os.path.join(os.path.dirname(__file__), 'data', file_name)

    with open(tot_name, 'r') as inputfile:
        this_doc = json.load(inputfile)
        
        for doc in this_doc:                
            # transform json to the correct data types in db
            report_no = str(doc['report_no'])
            report_date = datetime.strptime(doc['report_date'], '%Y-%m-%dT%H:%M:%S.%f')
            report_time = str(doc['report_time'])
            #from_date1 = str(doc['from_date'])
            from_date   = datetime.strptime(doc['from_date']  , '%Y-%m-%dT%H:%M:%S.%f')
            from_time = str(doc['from_time'])
            to_time = str(doc['to_time'])
            offense = str(doc['offense']) if 'offense' in doc else ''
            ibrs = str(doc['ibrs']) if 'ibrs' in doc else ''
            description = str(doc['description']) if 'description' in doc else ''
            beat = str(doc['beat']) if 'beat' in doc else ''
            address = str(doc['address']) if 'address' in doc else ''
            city = str(doc['city']) if 'city' in doc else ''
            zip_code  = str(doc['zip_code']) if 'zip_code' in doc else ''
            rep_dist = str(doc['rep_dist']) if 'rep_dist' in doc else ''
            area  = str(doc['area']) if 'area' in doc else ''
            dvflag = str(doc['dvflag']) if 'dvflag' in doc else ''
            involvement = str(doc['involvement']) if 'involvement' in doc else ''
            race  = str(doc['race']) if 'race' in doc else ''
            sex  = str(doc['sex']) if 'sex' in doc else ''
            age = int(doc['age']) if 'age' in doc else ''
            firearmused_flag = str(doc['firearmused_flag']) if 'firearmused_flag' in doc else ''
            address_coord = str(doc['location']['coordinates']) if 'location' in doc else ''

            # slow by slow, row by row insert
            #TODO convert to bulk inset
            row = (report_no, report_date, report_time, from_date, from_time, to_time, offense, ibrs, description, beat, address, city, zip_code, rep_dist, area, dvflag, involvement, race, sex, age, firearmused_flag, address_coord)

            #TODO adjust ON CONFLICT DO NOTHING to upsert
            insert_cmd = """
                INSERT INTO public.crime_2021(
                report_no, report_date, report_time, from_date, from_time, to_time, offense, ibrs, description, beat, address, city, zip_code, rep_dist, area, dvflag, involvement, race, sex, age, firearmused_flag, address_coord)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ON CONSTRAINT crime_2021_pkey 
                DO UPDATE SET 
                    report_date = EXCLUDED.report_date,
                    report_time = EXCLUDED.report_time,
                    from_date = EXCLUDED.from_date,
                    from_time = EXCLUDED.from_time,
                    to_time = EXCLUDED.to_time,
                    offense = EXCLUDED.offense,
                    ibrs = EXCLUDED.ibrs,
                    description = EXCLUDED.description,
                    beat = EXCLUDED.beat,
                    address = EXCLUDED.address,
                    city = EXCLUDED.city,
                    zip_code = EXCLUDED.zip_code,
                    rep_dist = EXCLUDED.rep_dist,
                    area = EXCLUDED.area,
                    dvflag = EXCLUDED.dvflag,
                    involvement = EXCLUDED.involvement,
                    race = EXCLUDED.race,
                    sex = EXCLUDED.sex,
                    age = EXCLUDED.age,
                    firearmused_flag = EXCLUDED.firearmused_flag,
                    address_coord = EXCLUDED.address_coord,
                    row_upd_date = now()
                ;"""

            pg_hook.run(insert_cmd, parameters=row)

# https://data.kcmo.org/resource/d4px-6rwg.json
with DAG('fetch_kc_crime_data-v0.1', schedule_interval='@daily',
        default_args=default_args,
        catchup=False) as dag:

    check_endpoint_availability =  HttpSensor(
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

    #load_data