from math import prod
import fitparse
import json
import os
import time
import click
import random
import uuid
from random import randrange, randint
from confluent_kafka import Producer, avro
from confluent_kafka.avro import AvroProducer

from multiprocessing import Process
from datetime import datetime, timedelta
from pprint import pprint

@click.command()
@click.option('--route', help='Choices are: \'CHI\', \'KC\', or \'LIB\'')
@click.option('--driver', help='The name of the driver performing the route')
@click.option('--rate', default=3, help='The rate at which to process the data')
@click.option('--density', default=3, help='Controls how dense/sparse the data is emitted')
@click.option('--multiplier', default=1.0, type=float, help='Cost buff/nerf multiplier to apply to base product price')
def app(route, driver, rate, density, multiplier):
    r1 = Route(route=route, driver=driver, rate=rate, density=density, multiplier=multiplier)
    r1.run()

class Route():

    def __init__(self, route='default', driver='cjtravis', rate=3, density=1, multiplier=1.0):
        self.route = route
        self.driver = driver
        self.rate = rate
        self.density = density
        self.multiplier = float(multiplier)
        self.kafka_config = {
            'bootstrap.servers': '0.0.0.0:9092',
            'on_delivery': self._delivery_report,
            'schema.registry.url': 'http://0.0.0.0:8081'
            }
        #self.default_key_schema = None
        self.default_key_schema = avro.loads('{"type": "string"}')
        self.route_value_schema = avro.load("schema/route.avsc")
        self.stop_value_schema = avro.load("schema/stop.avsc")
        self.sale_value_schema = avro.load("schema/sale.avsc")
        self.route_producer = AvroProducer(self.kafka_config, default_key_schema=self.default_key_schema, default_value_schema=self.route_value_schema)
        self.sales_producer = AvroProducer(self.kafka_config, default_key_schema=self.default_key_schema, default_value_schema=self.sale_value_schema)
        self.stops_producer = AvroProducer(self.kafka_config, default_key_schema=self.default_key_schema, default_value_schema=self.stop_value_schema)
        self.route_topic = 'routes' # 'route_' + str(self.route).lower()
        self.sale_topic = 'sales'
        self.stop_topic = 'stops'
        
        #self.route_key = route + date + CHI_20210519
        #self.sale_topic_es = 'sales_payload'
        self.geo_fields = ['position_lat', 'position_long'] 
        self.fields = ['distance', 'position_lat', 'position_long', 'speed', 'timestamp']
       
       # menu
        self.tacos =[
            {"chips and salsa": 2},
            {"fresco": 3.50},
            {"grilled steak": 4.50}
        ]
        
        self.drinks =[
            {"liter-a-cola": 5},
            {"water": 6}
        ]

    def _delivery_report(self, err, msg):
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            pass
            # suppress successes
            #print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    def _generate_stop(self, loc):
        return {
            "stop_id": str(uuid.uuid4()),
            "route_event_id": self.record_counter,
            "driver": self.driver, 
            "route": self.route,
            "location": loc,
            "stop_date": datetime.now().strftime("%b-%d-%Y %H:%M:%S"),
            "activity_ts": int(datetime.now().strftime("%s")) * 1000
            }

    def _generate_sale(self, stop_id):
        sales_tax = .07
        drink_purchase = random.choice(self.drinks)
        food_purchase = random.choice(self.tacos)

        #print(drink_purchase)
        #print(taco_purchase)
        sub_total = sum([float(x) for x in list(drink_purchase.values())] + [float(x) for x in list(food_purchase.values())])
        sub_total = round(float(sub_total) * float(self.multiplier),2)

        total = round(float(sub_total) * float(sales_tax),2) + sub_total
        # "items": [{
        #     **taco_purchase, 
        #     **drink_purchase}],
        message = {
            "schema": {
                "type": "struct", "optional": False, "version": 1, "fields": [
                { "field": "stop_id", "type": "string", "optional": True },
                { "field": "sale_id", "type": "string", "optional": True },
                { "field": "driver", "type": "string", "optional": True },
                { "field": "route", "type": "string", "optional": True },
                { "field": "event_id", "type": "int64", "optional": True },
                { "field": "sale_date", "type": "string", "optional": True },
                { "field": "sub_total", "type": "float", "optional": True },
                { "field": "total", "type": "float", "optional": True },
                { "field": "activity_ts", "type": "int64", "optional": True }
                ] },
            "payload": {
                "stop_id": stop_id,
                "sale_id": str(uuid.uuid4()),
                "driver": self.driver, 
                "route": self.route,
                "event_id": self.record_counter,
                "sale_date": datetime.now().strftime("%b-%d-%Y %H:%M:%S"),
                "sub_total":sub_total,
                "total": total,
                "activity_ts": int(datetime.now().strftime("%s")) * 1000
            }
        }

        return {
                "stop_id": stop_id,
                "sale_id": str(uuid.uuid4()),
                "driver": self.driver, 
                "route": self.route,
                "route_event_id": self.record_counter,
                "sale_date": datetime.now().strftime("%b-%d-%Y %H:%M:%S"),
                "sub_total":sub_total,
                "total": total,
                "activity_ts": int(datetime.now().strftime("%s")) * 1000
            }

    def _degrees(self, semi):
        return semi * 180.0 / (1<<31)

    def _parse_file(self, FIT_FILE):
        self.file = os.path.join('./data', FIT_FILE + '.fit')
        return fitparse.FitFile(self.file)

    def _event_record_builder(self, id, route_data):
        self.event = {}
        lat = None
        lon = None
        self.event['activity_ts'] = int(datetime.now().strftime("%s")) * 1000
        self.event['route'] = self.route
        self.event['route_event_id'] = id
        self.event['driver'] = self.driver

        for data in route_data:

            if data.name in self.fields:
                if data.name in self.geo_fields:
                    if not lat and data.name == "position_lat":
                        lat = self._degrees(data.value) 
                    if not lon and data.name == "position_long":
                        lon = self._degrees(data.value)
                if lat and lon:
                        #pass
                        #self.event['location'] = {"lat": lat, "lon": lon}
                        # "location": "41.12,-71.34"
                        self.event['location'] = str(lat) + "," + str(lon)
                if data.name == "timestamp":
                    self.event['event_ts_human'] = str(data.value)
                    self.event['event_ts_epoch'] = int(data.value.strftime('%s'))
                else:
                    self.event[data.name] = data.value

        return json.dumps(self.event)

    def _execute(self):
        # iterate FIT events
        self.raw_route_message = self._parse_file(self.route)

        self.record_counter = 1
        self.stop_counter = 0
        checkpoints = [0]
    
        for record in self.raw_route_message.get_messages("record"):
            self.route_producer.poll(0)
            event_record = self._event_record_builder(self.record_counter, record)
            json_pr = json.loads(event_record)
            json_pr['travel_distance_delta_meters'] = round(json_pr['distance'] - checkpoints.pop(),2)
            checkpoints.append(json_pr['distance'])
            #self.route_producer.produce(self.route_topic, json.dumps(json_pr).encode('utf-8'), callback=self._delivery_report)
            #print(f'\n\n{json_pr}')
            print(f'Event # {self.record_counter}')
            if self.record_counter % self.density == 0 and 'location' in json.loads(event_record):
                route_key = self.route + '-' + str(self.record_counter)
                self.route_producer.produce(topic=self.route_topic, value=json_pr, key=route_key)
                # should I stop?
                we_stop = True if abs(randrange(21) - randrange(21)) <= 2 else False
                # trigger stop event in kafka
                #print(type(json.loads(event_record)))
                #print(json.loads(event_record))
                
                ##self.stops_producer.flush()
                #print(stop_choice)
                if we_stop:
                    stop_record = self._generate_stop(json.loads(event_record)["location"])
                    self.stops_producer.poll(0)
                    self.stops_producer.produce(topic=self.stop_topic, value=stop_record, key=stop_record["stop_id"])
                    self.stop_counter +=1
                    print(f'  Stop # {self.stop_counter}')
                    print(f'{self.driver}\'s stopping to sell some food.')

                    # how many sales should we generate on this stop?
                    number_of_sales = randint(1,10)
                    print(f'Number of sales: {number_of_sales}')
                    for x in range(1, number_of_sales):
                        print(f'    sale {x} of {number_of_sales}')
                        #print(stop_record["stop_id"])
                        sale_record = self._generate_sale(stop_record["stop_id"])
                        # trigger sale event in kafka
                        self.sales_producer.poll(0)
                        self.sales_producer.produce(topic=self.sale_topic, value=sale_record, key=sale_record["sale_id"])
                        
                        #print(sale_record["payload"])
                        #time.sleep(1)
                    self.sales_producer.flush()
                    
                    #for x in range(1, number_of_sales):

                        # Cheat and send to Kafka for ES
                     #   print(sale["payload"])
                        #self.sales_producer_es.poll()
                        ##self.sales_producer_es.produce(self.sale_topic_es, json.dumps(sale_record["payload"]).encode('utf-8'))
                        ##self.sales_producer_es.flush()

                #self.route_producer.produce(self.route_topic, json.dumps(json_pr).encode('utf-8'), callback=self._delivery_report)
                
                time.sleep(self.rate)
            self.record_counter +=1

            self.route_producer.flush()

    def run(self):
        self._execute()
        #self._generate_sale()

if __name__ == '__main__':
    app()

