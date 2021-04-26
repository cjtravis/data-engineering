
# Kansas City Crime Dashboard 🚓

This project aims to make use of completely free and open source technologies to perform the orchestration, ingestion, storage, and execution found in a modern data pipeline.  The data is also freely available, courtesy of [Open Data KC](https://data.kcmo.org/). 


![](img/kansas-city-crime-dashboard.jpg)
## Tech Stack

**Orchestration:** Apache Airflow, Python

**Storage:** PostgreSQL (GIS)

**Visualization:** Apache Superset

**Container Service:** Docker

  
## Deployment   
### Postgres and Apache Airflow
```bash
docker-compose up 
```

After a couple of moments, both the webserver and scheduler components of Airflow should be running.  
Verify by running:

```bash
docker ps
CONTAINER ID   IMAGE                  COMMAND                  CREATED          STATUS                    PORTS                     NAMES
b4ade13b584b   apache/airflow:2.0.1   "/usr/bin/dumb-init …"   2 minutes ago    Up 2 minutes (healthy)    0.0.0.0:8080->8080/tcp    kansas-city-crime_airflow-webserver_1
34e79993f13e   apache/airflow:2.0.1   "/usr/bin/dumb-init …"   2 minutes ago    Up 2 minutes              8080/tcp                  kansas-city-crime_airflow-scheduler_1
c8b2de1f6032   postgis/postgis        "docker-entrypoint.s…"   20 minutes ago   Up 10 minutes (healthy)   0.0.0.0:54322->5432/tcp   kansas-city-crime_postgres_1
```
#### Troubleshooting
If you encounter this error in the docker output
```bash
airflow-init_1       | [2021-04-25 00:57:23,060] {providers_manager.py:299} WARNING - Exception when importing 'airflow.providers.microsoft.azure.hooks.wasb.WasbHook' from 'apache-airflow-providers-microsoft-azure' package: No module named 'azure.storage.blob'
```
Attach to the container and install the appropriate module using `pip`
```bash
$ docker exec -it kansas-city-crime_airflow-webserver_1 /bin/bash
```
```bash
airflow@b4ade13b584b:/opt/airflow$ pip uninstall --yes azure-storage && pip install -U azure-storage-blob apache-airflow-providers-microsoft-azure==1.1.0
airflow@b4ade13b584b:/opt/airflow$ exit
```

After installed, the error should no longer appear in the docker log output.

### Apache Superset
**Clone the repository**
```bash
git clone https://github.com/apache/superset.git
```

**MapBox API**
Add the following to the `docker/.env` file:
```bash
MAPBOX_API_KEY=pk.eyJ1IjoiY2p0cm...
```

**Patch the frontend**
```bash
cd superset-frontend
npm update
```

**Start the containers**
```bash
docker-compose build
docker-compose up
```

Note: Apache Superset may take some time before everything comes online.  Grab some coffee or tea while you wait.
  
## Workflow

### Running the Airflow DAG

In a web browser, open the [Apache Airflow web console](http://localhost:8080/home) and navigate to the [custom DAG](http://localhost:8080/tree?dag_id=fetch_kc_crime_data-v0.1).  The username and password will both be `airflow`.

By design, the DAG `fetch_kc_crime_data-v0.1` will execute automatically.  Assuming a succesful execution of the DAG, you should observe the following:

![](img/dag.png)

The structure of the pipeline is simple.  A single DAG in Apache Airflow will perform the following 4 steps:

  - Validate the HTTP endpoint where we will be fetching our data is available.
  - Identify the appropriate date window for which we will request data from the API
  - Perform the HTTP _GET_ request and store the resulting JSON on the local filesystem.
  - Insert the resulting _JSON_ payload in its raw (JSON) format into a Postgres table.

Once the data has been loaded into Postgres, we will be taking advantage of `JSON` functions in Postgres in order to extract and transfrom the data.  While there are other methods of parsing JSON and loading into a database, the decision to insert raw JSON into the database was deliberate so I could better familiarize myself with the technology.

### Querying Postgres

![](img/dbeaver.png)

#### Profiling All Crimes
Postgres may be accessed using a database client tool such as PGAdmin or DBeaver.  

**Connection Info**

|Host|User|Pass|Port|Database
|----|---|---|---|---|
|localhost|etl_user|etl_user|5432|pipelines


Using a common table expression (CTE), expand raw JSON using `json_array_elements_text()` function

```sql
with crime as (
    select json_array_elements_text(info)::json as e
    from crime_2021_raw
),
event as (
    select 
    e->>'report_no'::varchar as report_no
    ,to_timestamp(e->>'report_date', 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone as report_date
    ,e->>'report_time' as report_time
    ,to_timestamp(e->>'from_date', 'YYYY-MM-DD"T"HH24:MI:ss.ms')::timestamp without time zone as from_date
    ,e->>'from_time' as from_time
    ,e->>'to_time' as to_time
    ,e->>'offense' as offsense
    ,e->>'ibrs' as ibrs
    ,e->>'description' as description
    ,e->>'beat' as beat
    ,e->>'address' as address
    ,e->>'city' as city
    ,e->>'zip_code' as zip_code
    ,e->>'rep_dist' as rep_dist
    ,e->>'area' as area
    ,e->>'dvflag' as dvflag
    ,e->>'involvement' as involvement
    ,e->>'sex' as sex
    ,e->>'age' as age
    ,e->>'firearmused_flag' as firearmused_flag
    ,e->>'location' as location
    ,e as payload
    from crime
)
select * 
from event;
```

More profiling queries are available in [sql/data-profiling-queries.sql](sql/data-profiling-queries.sql)

### Dashboarding with Apache Superset
Navigate to [Apache Superset](http://localhost:8088/superset/welcome/) in your browser. 

> Note: Use `admin/admin` for username and password.

#### Create connection to Postgres database

Once in Superset, navigate to _Data > Databases_.

![](img/superset-create-database.png)

**Database Name**: Crime

**SQL Alchemy URI**: postgres://superset_user:superset_user@host.docker.internal:54322/pipelines

Click `Save`.

#### Import Dashboard

The dashboard export file is located in [superset/kansas-city-crime-dashboard-2021.json](superset/kansas-city-crime-dashboard-2021.json).

In Superset, navigate to _Settings_ > _Import Dashboards_


On the _Import Dashboard(s)_ dialogue, click `File` and navigate to [superset/kansas-city-crime-dashboard-2021.json](superset/kansas-city-crime-dashboard-2021.json).

On the `Database` dropdown, select `Crime`.

![](img/superset-select-file-database.png)

Click `Upload`.

The dashboard should now be available and ready for use under the _Dashboards_ menu.

## Teardown
### Superset
**Stopping Superset**
From the superset directory:
```bash
docker-compose stop
```
**Teardown Superset**
From the superset directory:
```bash
docker-compose down
```
### Airflow/Postgres
**Stopping Airflow and Postgres**
From the project repository:
```bash
docker-compose stop
```

**Teardown Airflow and Postgres**
From the project repository:
```bash
docker-compose down
# removes postgres data directory 
rm -rf ./postgres/data # warning, destructive operation
```
## References

- https://airflow.apache.org/docs/apache-airflow/2.0.1/docker-compose.yaml