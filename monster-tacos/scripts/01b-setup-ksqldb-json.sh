curl -s -X PUT -H  "Content-Type:application/json" \
    http://localhost:8083/connectors/SINK_ELASTIC_ROUTE_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"routes",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable":"false"
    }' | jq .


curl -s -X PUT -H  "Content-Type:application/json" \
    http://localhost:8083/connectors/SINK_ELASTIC_ORDER_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"orders",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable":"false"
    }' | jq .



curl -s -X PUT -H  "Content-Type:application/json" \
    http://localhost:8083/connectors/SINK_ELASTIC_STOPS_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"stops",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable":"false"
    }' | jq .
