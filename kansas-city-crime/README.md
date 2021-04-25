
# Kansas City Crime Dashboard 🚓

A project utilyzing Docker, Apache Airflow, Postgres GIS, and Apache Superset to retrieve, store, and visualize Kansas City crime statistics.

## Tech Stack

**Orchestration:** Apache Airflow, Python

**Storage:** PostgreSQL (GIS)

**Visualization:** Apache Superset

**Container Service:** Docker

  
## Demo



  - [Apache Airflow](http://localhost:8080/home)
  - [Apache Superset](#)
## Deployment 
### Postgres
Setting up Postgres is the first step of the deployment.  This will create the `kcmo` database and a `data_user`
postgres user that we will use to connect to the database.  See [sql/setup.sql](setup.sql)
for more details on the SQL.
```bash
# Generate a `postgres.conf` file using the Postgres docker image
docker run -i --rm postgres cat /usr/share/postgresql/postgresql.conf.sample > ./postgres/postgres.conf

# Start Postgres
docker-compose up -d postgres
```
    
### Apache Airflow
```bash
# Initialize airflow database 
# This will automatically exit upon successful completion
docker-compose up airfow initdb
```

```bash
docker-compose up -d
```

After a moment, both the Airflow webserver and scheduler components should be running.  
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
```bash
git clone https://github.com/apache/superset.git
cd superset-frontend
npm update
docker-compose build
docker-compose up
```

  
## Setup
### Airflow Connections
#### HTTP
Navigate to Admin > Connections > Add a New Record (blue plus sign icon)

* Conn Id: **http_data_kcmo_org**
* Conn Type: **HTTP**
* Host: **https://data.kcmo.org**

#### Postgres

Navigate to Admin > Connections > Add a New Record (blue plus sign icon)

* Conn Id: **pg_kcmo_opendata**
* Conn Type: **Postgres**
* Host: **postgres**
* Port: **5432**
* Schema: **kcmo**
* Login: **data_user**
* Password: **data_user**

## Workflow

### Running the Airflow DAG

In a browesr, open the [Apache Airflow web gui](http://localhost:8080/home) and navigate to the [custom DAG](http://localhost:8080/tree?dag_id=fetch_kc_crime_data-v0.1).  The username and password will both be `airflow`.

Click the slider icon to enable the DAG, and the job will automatically kick off.  Click on the `Graph View` tab and monitor progress.  Click on any task to view logs as desired.  After a few seconds, all tasks should complete successfully.  If failures occur, click the task to view the logs.  Be sure to follow the instructions in the `Setup` section.


The structure of the pipeline is simple.  A single DAG in Apache Airflow will perform the following 4 steps:

  - Validate the HTTP endpoint where we will be fetching our data is available.
  - Identify the appropriate date window for which we will request data from the API
  - Perform the HTTP _GET_ request and store the resulting JSON on the local filesystem.
  - Insert the resulting _JSON_ payload in its raw (JSON) format into a Postgres table.

![](img/dag.png)
Once the data has been loaded into Postgres, we will be taking advantage of `JSON` functions in Postgres in order to extract and transfrom the data.  While there are other methods of parsing JSON and loading into a database, the decision to insert raw JSON into the database was deliberate so I could better familiarize myself with the technology.

### Verifying Postgres Results

![](img/dbeaver.png)

#### Profiling All Crimes

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

More proifling queries are available in [sql/data-profiling-queries.sql](sql/data-profiling-queries.sql)