#!/bin/bash
echo -e "FANCY SETUP SCRIPT"
echo -e "Createing index template in ElasticSearch (MSG_TS/location)"
#elasticsearch patterns
# curl --silent --show-error -XPUT -H 'Content-Type: application/json' \
#     http://192.168.99.107:9200/_index_template/tacos/ \
#     -d'{
#         "index_patterns": [ "*orders_es" ],
#         "template": {
#             "mappings": {
#                 "properties": 
#                     {
                
#                     "payload": {
#                         "type": "nested",
#                         "properties": {
#                             "MSG_TS": { "type": "date" }
#                         }
#                     }
#                 }
#             }
#         } }'

curl --silent --show-error -XPUT -H 'Content-Type: application/json' \
    http://192.168.99.107:9200/_index_template/tacos/ \
    -d'{
        "index_patterns": [ "tacos_routes", "tacos_stops", "tacos_orders_payload" ],
        "template": {
            "mappings": {
                "properties": 
                    {
                    "MSG_TS": {
                    "type": "date"
                    },
                    "location": {
                    "type": "geo_point"
                    }
                }
            }
        } }'

sleep 2
echo -e "\n\nCreating Kafka Connect Sink Connectors (2 ES, 1 PG)"

# kafka connectors
curl -s -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_ELASTIC_ROUTE_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"tacos_routes",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable":"false"
    }' | jq .
sleep 1.5

curl -s -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_ELASTIC_ORDER_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"tacos_orders_payload",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable":"false"
    }' | jq .

sleep 1.5

curl -s -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_ELASTIC_STOPS_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"tacos_stops",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable":"false"
    }' | jq .

sleep 1.5

curl -s -X PUT -H  "Content-Type:application/json" \
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
    }' | jq .

# curl -s -X PUT -H  "Content-Type:application/json" \
#     http://192.168.99.107:8083/connectors/SINK_POSTGRES_ROUTE_01/config \
#     -d '{
#             "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
#             "connection.url":"jdbc:postgresql://postgres:5432/demo",
#             "connection.user":"master",
#             "connection.password":"postgres",
#             "key.converter":"org.apache.kafka.connect.storage.StringConverter",
#             "topics":"tacos_routes",
#             "key.ignore":"true",
#             "value.converter":"org.apache.kafka.connect.json.JsonConverter",
#             "auto.create":"true",
#             "auto.evolve":"true",
#             "pk.mode":"kafka",
#             "table.name.format":"public.routes",
#             "insert.mode":"upsert",
#             "value.converter.schemas.enable":"true"
#     }' | jq .

# curl -s -X PUT -H  "Content-Type:application/json" \
#     http://192.168.99.107:8083/connectors/SINK_POSTGRES_STOP_01/config \
#     -d '{
#             "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
#             "connection.url":"jdbc:postgresql://postgres:5432/demo",
#             "connection.user":"master",
#             "connection.password":"postgres",
#             "key.converter":"org.apache.kafka.connect.storage.StringConverter",
#             "topics":"tacos_stops",
#             "key.ignore":"true",
#             "value.converter":"org.apache.kafka.connect.json.JsonConverter",
#             "auto.create":"true",
#             "auto.evolve":"true",
#             "pk.mode":"kafka",
#             "table.name.format":"public.stops",
#             "insert.mode":"upsert",
#             "value.converter.schemas.enable":"true"
#     }' | jq .

sleep 1.5
echo -e "\n\nCreating ES Index Patterns (tacos_routes/tacos_orders)"
## es index pattterns
curl -s -X POST http://192.168.99.107:5601/api/saved_objects/index-pattern/tacos_routes -H 'kbn-xsrf: true' \
-H 'Content-Type: application/json' \
-d '{ "attributes": {
    "title": "tacos_routes*",
    "timeFieldName": "MSG_TS"
  }
}' | jq .
sleep 1.5

curl -s -X POST http://192.168.99.107:5601/api/saved_objects/index-pattern/tacos_stops -H 'kbn-xsrf: true' \
-H 'Content-Type: application/json' \
-d '{ "attributes": {
    "title": "tacos_stops*",
    "timeFieldName": "MSG_TS"
  }
}' | jq .

sleep 1.5

curl -s -X POST http://192.168.99.107:5601/api/saved_objects/index-pattern/tacos_orders -H 'kbn-xsrf: true' \
-H 'Content-Type: application/json' \
-d '{ "attributes": {
    "title": "tacos_orders*",
    "timeFieldName": "MSG_TS"
  }
}' | jq .

echo "\n\nSETUP COMPLETE"