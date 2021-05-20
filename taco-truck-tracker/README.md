## Consume using Kafkacat
```bash
docker exec kafkacat kafkacat \
    -b broker:29092 \
    -C -o beginning -e -q \
    -t demo \
    -f 'Topic+Partition+Offset: %t+%p+%o\tKey: %k\tValue:%s\n'
```

Output:
```bash
Topic+Partition+Offset: demo+0+2579	Key: 	Value:{"MSG_TS": 1620934682, "event_key": "CHICAGO", "event_id": 2580, "distance": 42780.37, "position_lat": 499521554, "location": {"lat": 41.86941297724843, "lon": -87.6205862313509}, "position_long": -1045354312, "speed": 3.35, "event_ts_human": "2017-10-08 16:05:14", "event_ts_epoch": 1507496714}
Topic+Partition+Offset: demo+0+2580	Key: 	Value:{"MSG_TS": 1620934682, "event_key": "CHICAGO", "event_id": 2581, "distance": 42800.94, "position_lat": 499523765, "location": {"lat": 41.86959830112755, "lon": -87.62058313004673}, "position_long": -1045354275, "speed": 3.368, "event_ts_human": "2017-10-08 16:05:20", "event_ts_epoch": 1507496720}
Topic+Partition+Offset: demo+0+2581	Key: 	Value:{"MSG_TS": 1620934682, "event_key": "CHICAGO", "event_id": 2582, "distance": 42809.43, "position_lat": 499524680, "location": {"lat": 41.86967499554157, "lon": -87.62057818472385}, "position_long": -1045354216, "speed": 3.359, "event_ts_human": "2017-10-08 16:05:23", "event_ts_epoch": 1507496723}
```

**Prettier using `jq`**
```bash
docker exec kafkacat kafkacat \
    -b broker:29092 \
    -C -o beginning -e -q \
    -t demo \
    -f '%s'
```
Output:
```json
{
  "MSG_TS": 1620934682,
  "event_key": "CHICAGO",
  "event_id": 2581,
  "distance": 42800.94,
  "position_lat": 499523765,
  "location": {
    "lat": 41.86959830112755,
    "lon": -87.62058313004673
  },
  "position_long": -1045354275,
  "speed": 3.368,
  "event_ts_human": "2017-10-08 16:05:20",
  "event_ts_epoch": 1507496720
}
{
  "MSG_TS": 1620934682,
  "event_key": "CHICAGO",
  "event_id": 2582,
  "distance": 42809.43,
  "position_lat": 499524680,
  "location": {
    "lat": 41.86967499554157,
    "lon": -87.62057818472385
  },
  "position_long": -1045354216,
  "speed": 3.359,
  "event_ts_human": "2017-10-08 16:05:23",
  "event_ts_epoch": 1507496723
}
```

Paul, Scott, and Chad Tranport


##Setup
**Deploy Kafka Connector**
```bash
docker exec -it ksqldb ksql http://ksqldb:8088
```

**Method 1: Using ksqlDB**
```sql
CREATE SINK CONNECTOR SINK_ELASTIC_ROUTE_01 WITH (
  'connector.class'                     = 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
  'connection.url'                      = 'http://elasticsearch:9200',
  'key.converter'                       = 'org.apache.kafka.connect.storage.StringConverter',
  'type.name'                           = '_doc',
  'topics'                              = 'tacos_route',
  'key.ignore'                          = 'true',
  'schema.ignore'                       = 'true',
  'value.converter'                     = 'org.apache.kafka.connect.json.JsonConverter',
  'value.converter.schemas.enable'      = 'false'
);

CREATE SINK CONNECTOR SINK_ELASTIC_STOP_01 WITH (
  'connector.class'                     = 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
  'connection.url'                      = 'http://elasticsearch:9200',
  'key.converter'                       = 'org.apache.kafka.connect.storage.StringConverter',
  'type.name'                           = '_doc',
  'topics'                              = 'tacos_stops',
  'key.ignore'                          = 'true',
  'schema.ignore'                       = 'true',
  'value.converter'                     = 'org.apache.kafka.connect.json.JsonConverter',
  'value.converter.schemas.enable'      = 'false'
);

CREATE SINK CONNECTOR SINK_ELASTIC_ORDER_01 WITH (
  'connector.class'                     = 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
  'connection.url'                      = 'http://elasticsearch:9200',
  'key.converter'                       = 'org.apache.kafka.connect.storage.StringConverter',
  'type.name'                           = '_doc',
  'topics'                              = 'tacos_orders',
  'key.ignore'                          = 'true',
  'schema.ignore'                       = 'true',
  'value.converter'                     = 'org.apache.kafka.connect.json.JsonConverter',
  'value.converter.schemas.enable'      = 'false'
);

CREATE SINK CONNECTOR SINK_ELASTIC_ORDER_02 WITH (
  'connector.class'                     = 'io.confluent.connect.elasticsearch.ElasticsearchSinkConnector',
  'connection.url'                      = 'http://elasticsearch:9200',
  'key.converter'                       = 'org.apache.kafka.connect.storage.StringConverter',
  'type.name'                           = '_doc',
  'topics'                              = 'tacos_orders_payload',
  'key.ignore'                          = 'true',
  'schema.ignore'                       = 'true',
  'value.converter'                     = 'org.apache.kafka.connect.json.JsonConverter',
  'value.converter.schemas.enable'      = 'false'
);


CREATE SINK CONNECTOR SINK_POSTGRES_ORDER_01 WITH (
  'connector.class'                     = 'io.confluent.connect.jdbc.JdbcSinkConnector',
  'connection.url'                      = 'jdbc:postgresql://postgres:5432/demo',
  'connection.user'                     = 'master',
  'connection.password'                  = 'postgres',
  'key.converter'                       = 'org.apache.kafka.connect.storage.StringConverter',
  'topics'                              = 'tacos_orders',
  'key.ignore'                          = 'true',
  'value.converter'                     = 'org.apache.kafka.connect.json.JsonConverter',
  'auto.create'                         = 'true',
  'auto.evolve'                         = 'true',
  'pk.mode'                             = 'kafka',
  'table.name.format'                   = 'public.orders',
  'insert.mode'                         = 'upsert',
  'value.converter.schemas.enable'      = 'true'
);


show connectors;
```

**Method 2: Using curl & Kafka Connect Rest endpoint**
```bash
$ curl -i -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_ELASTIC_ROUTE_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"tacos_route",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable":"false"
    }'

$ curl -i -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_ELASTIC_ORDER_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"tacos_orders",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable":"false"
    }'


$ curl -i -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_POSTGRES_ORDER_01/config \
    -d '{
            "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
            "connection.url":"jdbc:postgresql://postgres:5432/demo",
            "connection.user":"master",
            "connection.password":"postgres",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "topics":"tacos_orders",
            "key.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "auto.create":"true",
            "auto.evolve":"true",
            "pk.mode":"kafka",
            "table.name.format":"public.orders",
            "insert.mode":"upsert",
            "value.converter.schemas.enable":"true"
    }'

HTTP/1.1 201 Created
Date: Sun, 16 May 2021 14:40:25 GMT
Location: http://192.168.99.107:8083/connectors/SINK_POSTGRES_ORDER_01
Content-Type: application/json
Content-Length: 615
Server: Jetty(9.4.33.v20201020)

{"name":"SINK_POSTGRES_ORDER_01","config":{"connector.class":"io.confluent.connect.jdbc.JdbcSinkConnector","connection.url":"jdbc:postgresql://postgres:5432/demo","connection.user":"master","connection.password":"postgres","key.converter":"org.apache.kafka.connect.storage.StringConverter","topics":"tacos_orders","key.ignore":"true","value.converter":"org.apache.kafka.connect.json.JsonConverter","auto.create":"true","auto.evolve":"true","pk.mode":"kafka","table.name.format":"public.orders","insert.mode":"upsert","value.converter.schemas.enable":"true","name":"SINK_POSTGRES_ORDER_01"},"tasks":[],"type":"sink"}%  

$ curl -s http://192.168.99.107:8083/connectors/SINK_POSTGRES_ORDER_01/status | jq .
{
  "name": "SINK_POSTGRES_ORDER_01",
  "connector": {
    "state": "RUNNING",
    "worker_id": "kafka-connect:8083"
  },
  "tasks": [
    {
      "id": 0,
      "state": "RUNNING",
      "worker_id": "kafka-connect:8083"
    }
  ],
  "type": "sink"
}
```
**Deploy ElasticSearch Index Pattern**
```bash
curl --silent --show-error -XPUT -H 'Content-Type: application/json' \
    http://192.168.99.107:9200/_index_template/tacos/ \
    -d'{
        "index_patterns": [ "tacos*" ],
        "template": {
            "mappings": {
                "properties": {
                    "MSG_TS": {
                    "type": "date"
                    },
                    "location": {
                    "type": "geo_point"
                    }
                }
            }
        } }'
```

**Verify**
```bash
curl -s -XGET http://localhost:9200/_index_template/route/ |  jq .
{
  "index_templates": [
    {
      "name": "route",
      "index_template": {
        "index_patterns": [
          "route*"
        ],
        "template": {
          "mappings": {
            "properties": {
              "MSG_TS": {
                "type": "date"
              },
              "location": {
                "type": "geo_point"
              }
            }
          }
        },
        "composed_of": []
      }
    }
  ]
}
```
**Delete Index Pattern**
```bash
curl -s -XDELETE http://192.168.99.107:9200/_index_template/order/ |  jq .
{
  "acknowledged": true
}
```

```bash
sudo apt-get install openjdk-8-jre openssh-server 
cd ~/Downloads && curl https://mirror.nodesdirect.com/apache/kafka/2.8.0/kafka_2.13-2.8.0.tgz -o kafka-2.8.0.tgz
mkdir ~/kafka && cd ~/kafka
tar -xvzf ~/Downloads/kafka-2.8.0.tgz --strip 1

```


## Interacting with Kafka
**List topics**
```bash
cd ~/kafka
bin/kafka-topics.sh --bootstrap-server=192.168.99.107:9092 --list
bin/kafka-topics.sh --bootstrap-server=192.168.99.107:9092 --delete --topic tacos_orders
bin/kafka-topics.sh --bootstrap-server=192.168.99.107:9092 --delete --topic tacos_routes

```


**Run the app**
```bash

python app.py --help
Usage: app.py [OPTIONS]

Options:
  --route TEXT    Choices are: 'CHI', 'KC', or 'LIB'
  --driver TEXT   The name of the driver performing the route
  --rate INTEGER  The rate at which to process the data
  --help          Show this message and exit.

python app.py --driver='Paul' --route='KC' --rate=6
python app.py --driver='Scott' --route='CHI' --rate=3
python app.py --driver='Chad' --route='LIB' --rate=1.5
python app.py --driver='Scott' --route='CHI' --rate=3 --density 7
```


## CLI Tricks
**List all running connectors**
```bash
# Source: https://rmoff.net/2018/12/03/kafka-connect-cli-tricks/
curl -s "http://192.168.99.107:8083/connectors"| \
jq '.[]'| \
xargs -I{connector_name} curl -s "http://192.168.99.107:8083/connectors/"{connector_name}"/status"| jq -c -M '[.name,.connector.state,.tasks[].state]|join(":|:")'| \
column -s : -t| \
sed 's/\"//g'| \
sort
```

```bash
# create index pattern in es
curl -X POST http://192.168.99.107:5601/api/saved_objects/index-pattern/index-pattern-id  -H 'kbn-xsrf: true' -H 'Content-Type: application/json' -d '\n{\n  "attributes": {\n    "title": "my-index-*"\n  }\n}'

curl -X POST http://192.168.99.107:5601/api/saved_objects/index-pattern/tacos_route -H 'kbn-xsrf: true' \
-H 'Content-Type: application/json' \
-d '{ "attributes": {
    "title": "tacos_route*",
    "timeFieldName": "MSG_TS"
  }
}'


curl -X POST http://192.168.99.107:5601/api/saved_objects/index-pattern/tacos_order -H 'kbn-xsrf: true' \
-H 'Content-Type: application/json' \
-d '{ "attributes": {
    "title": "tacos_order*",
    "timeFieldName": "MSG_TS"
  }
}'


```

"attributes": {
    "fieldAttrs": "{}",
    "title": "tacos_route*",
    "timeFieldName": "MSG_TS",
    "fields": "[]"
  }