# Kansas City Crime Dashboard 🚓
A project leveraging Docker, Apache Airflow, Postgres GIS, and Apache Superset to retrieve, store, and visualize Kansas City crime statistics.

Link to dataset:
- [Kansas City Crime Data - 2021](https://data.kcmo.org/Crime/KCPD-Crime-Data-2021/w795-ffu6)

Kansas City crime data is updated regularly and freely available from the KC Open Data [website](https://data.kcmo.org/).

Orchestration - Apache Airflow
Data Storage - Postgres on Docker
Visualization - Apache Superset
Python and SQL - Data movement and manipulation

## Environment Setup
### Postgres
This example relies on the `postgis/postgis` image of Postgres, which includes additional geospatial libraries not included with the standard `postgres/postgres` docker image.  Once downloaded, it should only take a few moments to have a running Postgres instance.

```bash
# Generate a `postgres.conf` file using the Postgres docker image
docker run -i --rm postgres cat /usr/share/postgresql/postgresql.conf.sample > ./postgres/postgres.conf

# Start Postgres
docker-compose up 
```

Once running, using a database client (DBeaver, VS Code + sqltools, PGAdmin, etc...), connect using:
```
- Host: localhost
- Port: 5400
- Username: docker
- Password: docker
```

### Apache Airflow
Instructions to download and setup Apache Airflow are detailed in my [Airflow Repository](https://www.github.com/cjtravis/airflow).

Additional python modules need to installed in order to satisfy communications with Postgres via Airflow.

```bash
# Activate python virtual environment if applicable first
source path/to/airflow/virtualenv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Configurations
HTTP:
```bash
http_data_kcmo_org
```

Postgres:
```bash
pg_kcmo_opendata
```

### Apache Superset
```bash
git clone https://github.com/apache/superset.git
cd superset-frontend
npm update
docker-compose build
docker-compose up
```


## Environment Teardown
## Postgres
```bash
docker-compose down
```