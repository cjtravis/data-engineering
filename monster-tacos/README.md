
# Monster Tacos 🌮

Monster Tacos™️ is the (fictitious) revolutionary new food truck experience unlike any seen before.  Think of it like the neighborhood ice cream truck, except only for tacos and delivered by a monster truck.  

## Project Overview
Monster Tacos operates in three US cities: 
Kansas City, St. Louis, and Chicago.  

This project makes use of several open source technologies including Apache Kafka, Elasticsearch, and Postgres.  

The opereational data produced is simple: 
- one lat/lon tracking event along the predefined _route_ generated from an onboard device such as an [ELD](https://en.wikipedia.org/wiki/Electronic_logging_device)
- one event per _stop_ along the **route**
- one to many _sales_ transactions per **stop** along the **route**

A simple python application is responsible for producing these events to three topics in Apache Kafka: routes, stops, and sales.  The generated events are serialized using Avro and managed using the Confluent Schema Registry.  ksqlDB is used to deploy _Kafka Connect_ sink connectors to ElasticSearch and Postgres.  Finally, Kibana is used as a tool to aggregate and visualize the metrics received in real-time using the custom dashboard, [_Taco Tracker 2000_](http://localhost:5601/app/dashboards).

Afterall, who doesn't like tacos _and_ monster trucks?

## Screenshots

![](img/dashboard.png)

|||
|-|-|
|![](img/kc-zoom.png)| ![](img/stl-zoom.png)|


## Tech Stack

**Applications**
- [Confluent ksqlDB](https://ksqldb.io/)
- [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)

**Containerization**
- Docker
- docker-compose

**Data**
- Geolocation data extracted from Garmin FIT files<sup>[1](1)</sup>

**Languages**
- Python 3

**Serialization**
- Avro

**Storage**
- Elasticsearch
- Kafka
- Postgres

**Visualization**
- Kibana

> **<sup>1</sup>** The FIT data was produced on my personal Garmin device and is provided freely for the purposes of this project.


## Data Model
![](img/data-model.png)

## Run Locally
Clone the project
```bash
git clone git@github.com:cjtravis/data-engineering.git
```

Switch into project directory

```bash
cd data-engineering/monster-tacos
```
### Deployment
**Start up environment**
```bash
docker-compose up -d
```
> Note: If you notice any of the containers crashing, try increasing the amount of RAM allocated to the docker service.  I specifically had to do this in order to keep Elasticsearch up and running.

**Deploy Elasticsearch artifacts**
```bash
scripts/00-setup-elastic-local.sh
```

**Deploy Kafka Connect sink connectors**
```bash
scripts/01-setup-ksqldb-avro-local.sh
```
> Note: Depending on your system resources, it might take a few minutes for all of the services to start.  I recommend waiting 4-5 minutes before deploying ES / KC resources.

**Verify Connectors are running**
```bash
docker exec -it ksqldb ksql http://localhost:8088
```

```bash
OpenJDK 64-Bit Server VM warning: Option UseConcMarkSweepGC was deprecated in version 9.0 and will likely be removed in a future release.

                  ===========================================
                  =       _              _ ____  ____       =
                  =      | | _____  __ _| |  _ \| __ )      =
                  =      | |/ / __|/ _` | | | | |  _ \      =
                  =      |   <\__ \ (_| | | |_| | |_) |     =
                  =      |_|\_\___/\__, |_|____/|____/      =
                  =                   |_|                   =
                  =  Event Streaming Database purpose-built =
                  =        for stream processing apps       =
                  ===========================================

Copyright 2017-2020 Confluent Inc.

CLI v0.15.0, Server v0.15.0 located at http://localhost:8088
Server Status: RUNNING

Having trouble? Type 'help' (case-insensitive) for a rundown of how things work!

ksql> show connectors;

 Connector Name            | Type | Class                                                         | Status
--------------------------------------------------------------------------------------------------------------------------------
 SINK_ELASTIC_ROUTES_01    | SINK | io.confluent.connect.elasticsearch.ElasticsearchSinkConnector | RUNNING (1/1 tasks RUNNING)
 SINK_ELASTIC_STOPS_01     | SINK | io.confluent.connect.elasticsearch.ElasticsearchSinkConnector | RUNNING (1/1 tasks RUNNING)
 SINK_JDBC_POSTGRES_SALES  | SINK | io.confluent.connect.jdbc.JdbcSinkConnector                   | RUNNING (1/1 tasks RUNNING)
 SINK_JDBC_POSTGRES_ROUTES | SINK | io.confluent.connect.jdbc.JdbcSinkConnector                   | RUNNING (1/1 tasks RUNNING)
 SINK_JDBC_POSTGRES_STOPS  | SINK | io.confluent.connect.jdbc.JdbcSinkConnector                   | RUNNING (1/1 tasks RUNNING)
 SINK_ELASTIC_SALES_01     | SINK | io.confluent.connect.elasticsearch.ElasticsearchSinkConnector | RUNNING (1/1 tasks RUNNING)
--------------------------------------------------------------------------------------------------------------------------------
```


**Services**
|Service Name|Endpoint |
|----|---|
|Kibana|localhost:5601|
|Elasticseach|localhost:9200|
|Kafka| localhost:9092|
|Zookeeper |localhost:2181 |
|Schema Registry|localhost:8081|
|Kafka Connect|localhost:8083|
|ksqlDB|localhost:8088|
|Postgres| localhost:5432| 

**Create Python virtual environment**
```bash
pip3 install virtualenv

python3 -m venv ./venv/monster-tacos

source ./venv/monster-tacos/bin/activate

pip3 install -r requirements.txt
```

### Running the app 

The python application can be used to execute against a single route and produce data (routes, stops, and sales) to Kafka.  Alternatively, you may elect to execute `run.sh` which will start 3 isntances of `app.py` for 3 drivers against 3 distinct routes.


```bash
python3 app.py --help
Usage: app.py [OPTIONS]

Options:
  --route TEXT        Choices are: 'CHI', 'KC', or 'STL'
  --driver TEXT       The name of the driver performing the route
  --rate INTEGER      The rate at which to process the data
  --density INTEGER   Controls how dense/sparse the data is emitted
  --multiplier FLOAT  Cost buff/nerf multiplier to apply to base product price
  --help              Show this message and exit.
```

```bash
python3 app.py --driver='Scott' --route='CHI' --rate=3 --density 7 --multiplier 1.45 
```

### Consuming data from Kafka
While the application is running, fire up a session to ksqlDB.
```bash
docker exec -it ksqldb ksql http://localhost:8088
```

```bash
# Routes
ksql> print routes from beginning limit 3;
Key format: AVRO or HOPPING(KAFKA_STRING) or TUMBLING(KAFKA_STRING) or KAFKA_STRING
Value format: AVRO
rowtime: 2021/05/22 21:06:59.288 Z, key: CHI-7, value: {"activity_ts": 1621717616000, "route": "CHI", "route_event_id": 7, "driver": "Scott", "distance": 114.2, "position_lat": 499667611, "location": "41.881655333563685,-87.62093567289412", "location2": null, "position_long": -1045358481, "speed": 3.816, "event_ts_human": "2017-10-08 12:35:32", "event_ts_epoch": 1507484132, "travel_distance_delta_meters": 21.97}, partition: 0
rowtime: 2021/05/22 21:06:59.290 Z, key: STL-3, value: {"activity_ts": 1621717616000, "route": "STL", "route_event_id": 3, "driver": "Chad", "distance": 42.94, "position_lat": 459910064, "location": "38.549216240644455,-90.32879029400647", "location2": null, "position_long": -1077664445, "speed": 2.995, "event_ts_human": "2017-06-12 02:08:25", "event_ts_epoch": 1497251305, "travel_distance_delta_meters": 21.86}, partition: 0
rowtime: 2021/05/22 21:06:59.290 Z, key: KC-3, value: {"activity_ts": 1621717616000, "route": "KC", "route_event_id": 3, "driver": "Paul", "distance": 25.26, "position_lat": 466309388, "location": "39.08560138195753,-94.58164114505053", "location2": null, "position_long": -1128402932, "speed": 3.004, "event_ts_human": "2019-10-19 12:05:42", "event_ts_epoch": 1571504742, "travel_distance_delta_meters": 3.09}, partition: 0

# Stops
ksql> print stops from beginning limit 3;
Key format: AVRO or HOPPING(KAFKA_STRING) or TUMBLING(KAFKA_STRING) or KAFKA_STRING
Value format: AVRO
rowtime: 2021/05/22 21:06:59.448 Z, key: 142fcfe3-4329-47bc-8973-905b91d53ed5, value: {"stop_id": "142fcfe3-4329-47bc-8973-905b91d53ed5", "route_event_id": 7, "driver": "Scott", "route": "CHI", "location": "41.881655333563685,-87.62093567289412", "stop_date": "May-22-2021 16:06:59", "activity_ts": 1621717619000}, partition: 0
rowtime: 2021/05/22 21:07:05.398 Z, key: ca483a8c-3d47-4f83-9837-10f4c1955c92, value: {"stop_id": "ca483a8c-3d47-4f83-9837-10f4c1955c92", "route_event_id": 9, "driver": "Paul", "route": "KC", "location": "39.08650184981525,-94.58160225301981", "stop_date": "May-22-2021 16:07:05", "activity_ts": 1621717625000}, partition: 0
rowtime: 2021/05/22 21:07:09.017 Z, key: 94c43164-b44c-4754-8daf-5db6b802efed, value: {"stop_id": "94c43164-b44c-4754-8daf-5db6b802efed", "route_event_id": 12, "driver": "Paul", "route": "KC", "location": "39.08700912259519,-94.58160233683884", "stop_date": "May-22-2021 16:07:09", "activity_ts": 1621717629000}, partition: 0

# Sales
ksql> print sales from beginning limit 3;
Key format: AVRO or HOPPING(KAFKA_STRING) or TUMBLING(KAFKA_STRING) or KAFKA_STRING
Value format: AVRO
rowtime: 2021/05/22 21:06:59.525 Z, key: 0e235c51-c311-4d83-a5e6-bab4e25493cc, value: {"stop_id": "142fcfe3-4329-47bc-8973-905b91d53ed5", "sale_id": "0e235c51-c311-4d83-a5e6-bab4e25493cc", "driver": "Scott", "route": "CHI", "route_event_id": 7, "sale_date": "May-22-2021 16:06:59", "sub_total": 11.6, "total": 12.41, "activity_ts": 1621717619000}, partition: 0
rowtime: 2021/05/22 21:06:59.525 Z, key: 79366673-1a36-4407-b367-8648bda71fc3, value: {"stop_id": "142fcfe3-4329-47bc-8973-905b91d53ed5", "sale_id": "79366673-1a36-4407-b367-8648bda71fc3", "driver": "Scott", "route": "CHI", "route_event_id": 7, "sale_date": "May-22-2021 16:06:59", "sub_total": 15.22, "total": 16.29, "activity_ts": 1621717619000}, partition: 0
rowtime: 2021/05/22 21:06:59.526 Z, key: 32b6e88a-dbb0-41b0-b564-74a8cd5361a6, value: {"stop_id": "142fcfe3-4329-47bc-8973-905b91d53ed5", "sale_id": "32b6e88a-dbb0-41b0-b564-74a8cd5361a6", "driver": "Scott", "route": "CHI", "route_event_id": 7, "sale_date": "May-22-2021 16:06:59", "sub_total": 11.6, "total": 12.41, "activity_ts": 1621717619000}, partition: 0
```

### Viewing data in Postgres

The three topics are replicated to Postgres using the JDBC Sink Connector.  
|Kafka Topic|Postgres Table|
|--|--|
|routes|public.routes|
|sales|public.sales|
|stops|public.stops|


```bash
psql -h localhost -p 5432 -U postgres -d monster_tacos
```
The password is _postgres_


```bash
monster_tacos=# \dt
         List of relations
 Schema |  Name  | Type  |  Owner
--------+--------+-------+----------
 public | routes | table | postgres
 public | sales  | table | postgres
 public | stops  | table | postgres
(3 rows)

monster_tacos=# select route, driver, sum(total) as total_sales from public.sales group by 1,2 order by 3 desc;
 route | driver | total_sales
-------+--------+-------------
 CHI   | Scott  |   6588.3237
 STL   | Chad   |      156.01
 KC    | Paul   |      132.16
```

### Stopping the app
If running the app using the `run.sh` script, background processes will need to be killed in order to stop the application.  This is easy using the `scripts/killswitch.sh` script.

```bash
# run in a new terminal
scripts/killswitch.sh
```

## Teardown
```bash
# destroy docker network and containers created in this project.
docker-compose down
```

## Roadmap

- Integrate Kafka Streams API (Java) with a Rest API to demonstrate state store functionality

- Include specific order details in the `sales` event and update Avro schema to reflect accordingly.

- Provide more sample analytical queries in Postgres and additional charts in Kibana dashboard.

## References
The [docker-compose.yml](docker-compose.yml) was modified from its original version, provided by [Robin Moffatt](https://github.com/rmoff) of Confluent and may be [found here](https://github.com/confluentinc/demo-scene/blob/master/kafka-to-elasticsearch/docker-compose.yml).