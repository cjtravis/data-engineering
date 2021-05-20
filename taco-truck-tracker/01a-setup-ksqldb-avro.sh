curl -s -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_ELASTIC_ROUTES_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"routes",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"io.confluent.connect.avro.AvroConverter",
            "value.converter.schema.registry.url": "http://192.168.99.107:8081"
    }' | jq .


curl -s -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_ELASTIC_SALES_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"sales",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"io.confluent.connect.avro.AvroConverter",
            "value.converter.schema.registry.url": "http://192.168.99.107:8081"
    }' | jq .



curl -s -X PUT -H  "Content-Type:application/json" \
    http://192.168.99.107:8083/connectors/SINK_ELASTIC_STOPS_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"stops",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"io.confluent.connect.avro.AvroConverter",
            "value.converter.schema.registry.url": "http://192.168.99.107:8081"
    }' | jq .