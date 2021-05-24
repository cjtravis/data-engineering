curl -s -X PUT -H  "Content-Type:application/json" \
    http://localhost:8083/connectors/SINK_ELASTIC_ROUTES_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"routes",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"io.confluent.connect.avro.AvroConverter",
            "value.converter.schema.registry.url":"http://schema-registry:8081"
    }' | jq .


curl -s -X PUT -H  "Content-Type:application/json" \
    http://localhost:8083/connectors/SINK_ELASTIC_SALES_01/config \
    -d '{
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "connection.url":"http://elasticsearch:9200",
            "key.converter":"org.apache.kafka.connect.storage.StringConverter",
            "type.name":"_doc",
            "topics":"sales",
            "key.ignore":"true",
            "schema.ignore":"true",
            "value.converter":"io.confluent.connect.avro.AvroConverter",
            "value.converter.schema.registry.url":"http://schema-registry:8081"
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
            "value.converter":"io.confluent.connect.avro.AvroConverter",
            "value.converter.schema.registry.url":"http://schema-registry:8081"
    }' | jq .


curl -s -X PUT -H "Content-Type:application/json" \
    http://localhost:8083/connectors/SINK_JDBC_POSTGRES_SALES/config \
    -d '{
        "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
        "auto.create": "true",
        "auto.evolve": "true",
        "connection.url": "jdbc:postgresql://postgres:5432/monster_tacos",
        "connection.user": "postgres",
        "connection.password": "postgres",
        "delete.enabled": "true",
        "dialect.name": "PostgreSqlDatabaseDialect",
        "insert.mode": "upsert",
        "pk.fields": "sale_id",
        "pk.mode": "record_key",
        "topics": "sales",
        "table.name.format": "public.sales",
        "key.converter": "io.confluent.connect.avro.AvroConverter",
        "key.converter.schema.registry.url": "http://schema-registry:8081",
        "value.converter": "io.confluent.connect.avro.AvroConverter",
        "value.converter.schema.registry.url": "http://schema-registry:8081"
    }' | jq .

curl -s -X PUT -H "Content-Type:application/json" \
    http://localhost:8083/connectors/SINK_JDBC_POSTGRES_STOPS/config \
    -d '{
        "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
        "auto.create": "true",
        "auto.evolve": "true",
        "connection.url": "jdbc:postgresql://postgres:5432/monster_tacos",
        "connection.user": "postgres",
        "connection.password": "postgres",
        "delete.enabled": "true",
        "dialect.name": "PostgreSqlDatabaseDialect",
        "insert.mode": "upsert",
        "pk.fields": "stop_id",
        "pk.mode": "record_key",
        "topics": "stops",
        "table.name.format": "public.stops",
        "key.converter": "io.confluent.connect.avro.AvroConverter",
        "key.converter.schema.registry.url": "http://schema-registry:8081",
        "value.converter": "io.confluent.connect.avro.AvroConverter",
        "value.converter.schema.registry.url": "http://schema-registry:8081",
        "transforms"                    : "flatten",
        "transforms.flatten.type"       : "org.apache.kafka.connect.transforms.Flatten$Value",
        "transforms.flatten.delimiter"  : "_"
    }' | jq .

curl -s -X PUT -H "Content-Type:application/json" \
    http://localhost:8083/connectors/SINK_JDBC_POSTGRES_ROUTES/config \
    -d '{
        "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
        "auto.create": "true",
        "auto.evolve": "true",
        "connection.url": "jdbc:postgresql://postgres:5432/monster_tacos",
        "connection.user": "postgres",
        "connection.password": "postgres",
        "delete.enabled": "true",
        "dialect.name": "PostgreSqlDatabaseDialect",
        "insert.mode": "upsert",
        "pk.fields": "route_id",
        "pk.mode": "record_key",
        "topics": "routes",
        "table.name.format": "public.routes",
        "key.converter": "io.confluent.connect.avro.AvroConverter",
        "key.converter.schema.registry.url": "http://schema-registry:8081",
        "value.converter": "io.confluent.connect.avro.AvroConverter",
        "value.converter.schema.registry.url": "http://schema-registry:8081",
        "transforms"                    : "flatten",
        "transforms.flatten.type"       : "org.apache.kafka.connect.transforms.Flatten$Value",
        "transforms.flatten.delimiter"  : "_"
    }' | jq .