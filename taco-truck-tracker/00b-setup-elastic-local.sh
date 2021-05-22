# Index templates
curl --silent --show-error -XPUT -H 'Content-Type: application/json' \
    http://localhost:9200/_index_template/tacos_routes/ \
    -d'{
        "index_patterns": [ "routes" ],
        "template": {
            "mappings": {
                "properties": 
                    {
                    "Route.activity_ts": {
                    "type": "date"
                    },
                    "Route.location": {
                    "type": "geo_point"
                    }
                }
            }
        } }'

curl --silent --show-error -XPUT -H 'Content-Type: application/json' \
    http://localhost:9200/_index_template/tacos_stops/ \
    -d'{
        "index_patterns": [ "stops" ],
        "template": {
            "mappings": {
                "properties": 
                    {
                    "Stop.activity_ts": {
                    "type": "date"
                    },
                    "Stop.location": {
                    "type": "geo_point"
                    }
                }
            }
        } }'

curl --silent --show-error -XPUT -H 'Content-Type: application/json' \
    http://localhost:9200/_index_template/tacos_sales/ \
    -d'{
        "index_patterns": [ "sales" ],
        "template": {
            "mappings": {
                "properties": 
                    {
                    "activity_ts": {
                    "type": "date"
                    }
                }
            }
        } }'


# Index patterns
echo -e "\n\nCreating ES Index Patterns (tacos_routes/tacos_orders)"
## es index pattterns
curl -s -X POST http://localhost:5601/api/saved_objects/index-pattern/tacos_routes -H 'kbn-xsrf: true' \
-H 'Content-Type: application/json' \
-d '{ "attributes": {
    "title": "routes",
    "timeFieldName": "Route.activity_ts"
  }
}' | jq .
sleep 1.5

curl -s -X POST http://localhost:5601/api/saved_objects/index-pattern/tacos_stops -H 'kbn-xsrf: true' \
-H 'Content-Type: application/json' \
-d '{ "attributes": {
    "title": "stops",
    "timeFieldName": "Stop.activity_ts"
  }
}' | jq .

sleep 1.5

curl -s -X POST http://localhost:5601/api/saved_objects/index-pattern/tacos_sales -H 'kbn-xsrf: true' \
-H 'Content-Type: application/json' \
-d '{ "attributes": {
    "title": "sales",
    "timeFieldName": "activity_ts"
  }
}' | jq .
