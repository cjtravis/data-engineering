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
@click.option('--route', help='Choices are: \'CHI\', \'KC\', or \'STL\'')
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
        self.geo_fields = ['position_lat', 'position_long'] 
        self.fields = ['distance', 'position_lat', 'position_long', 'speed', 'timestamp']
       
       # menu
        self.tacos =[
            {"Avenger": 4.00},
            {"Grave Digger": 5.50},
            {"Bigfoot": 6.50},
            {"Swamp Thing": 5.00},
            {"Bulldozer": 5.00},
            {"Maximum Destruction": 10.00},
            {"Snake Bite": 7.00}
        ]
        
        self.drinks =[
            {"Liter-a-Cola": 5},
            {"Water": 6}
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

        sub_total = sum([float(x) for x in list(drink_purchase.values())] + [float(x) for x in list(food_purchase.values())])
        sub_total = round(float(sub_total) * float(self.multiplier),2)
        total = round(float(sub_total) * float(sales_tax),2) + sub_total

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

            print(f'Event # {self.record_counter}')
            if self.record_counter % self.density == 0 and 'location' in json.loads(event_record):

                route_key = self.route + '-' + str(self.record_counter)
                self.route_producer.produce(topic=self.route_topic, value=json_pr, key=route_key)
                
                # should I stop?
                we_stop = True if abs(randrange(21) - randrange(21)) <= 2 else False
                
                if we_stop:
                    # generate a stop record
                    stop_record = self._generate_stop(json.loads(event_record)["location"])
                    self.stops_producer.poll(0)
                    self.stops_producer.produce(topic=self.stop_topic, value=stop_record, key=stop_record["stop_id"])
                    self.stop_counter +=1
                    print(f'  Stop # {self.stop_counter}')
                    print(f'{self.driver}\'s stopping to sell some food.')

                    # how many sales (between 1-10) should we generate on this stop?
                    number_of_sales = randint(1,10)
                    print(f'Number of sales: {number_of_sales}')
                    for x in range(1, number_of_sales):
                        print(f'    sale {x} of {number_of_sales}')
                        sale_record = self._generate_sale(stop_record["stop_id"])
                        
                        # generate a sales record
                        self.sales_producer.poll(0)
                        self.sales_producer.produce(topic=self.sale_topic, value=sale_record, key=sale_record["sale_id"])

                    self.sales_producer.flush()

                time.sleep(self.rate)

            self.record_counter +=1
            self.route_producer.flush()

    def run(self):
        self._execute()

if __name__ == '__main__':
    app()

