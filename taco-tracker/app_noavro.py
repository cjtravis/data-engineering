from math import prod
import fitparse
import json
import os
import time
import click
import random
import uuid
from random import randrange, randint
from confluent_kafka import Producer
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
        self.kafka_config = {'bootstrap.servers': '192.168.99.107:9092'}
        self.route_producer = Producer(self.kafka_config)
        self.order_producer = Producer(self.kafka_config)
        self.order_producer_es = Producer(self.kafka_config)
        self.stop_producer = Producer(self.kafka_config)
        self.route_topic = 'tacos_routes' # 'route_' + str(self.route).lower()
        self.order_topic = 'tacos_orders'
        self.stop_topic = 'tacos_stops'
        self.order_topic_es = 'tacos_orders_payload'
        self.geo_fields = ['position_lat', 'position_long'] 
        self.fields = ['distance', 'position_lat', 'position_long', 'speed', 'timestamp']

            # Street tacos!
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
            #print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    def _generate_stop(self, loc):
        return {
            "stop_id": str(uuid.uuid4()),
            "event_id": self.record_counter,
            "driver": self.driver, 
            "route": self.route,
            "location": loc,
            "stop_date": datetime.now().strftime("%b-%d-%Y %H:%M:%S"),
            "MSG_TS": int(datetime.now().strftime("%s")) * 1000
            }

    def _create_order(self, stop_id):
        #stop_choice = True if abs(randrange(11) - randrange(11)) < 2 else False
        #print(stop_choice)
        sales_tax = .07
        drink_purchase = random.choice(self.drinks)
        food_purchase = random.choice(self.tacos)

        #print(drink_purchase)
        #print(taco_purchase)

        #print(drink_purchase.values()[0])
        sub_total = sum([float(x) for x in list(drink_purchase.values())] + [float(x) for x in list(food_purchase.values())])
        sub_total = round(float(sub_total) * float(self.multiplier),2)

        #print(sub_total)
        #print(type(float(sub_total[0])))
        #print(f'sub total: {str(sub_total[0])}')

        total = round(float(sub_total) * float(sales_tax),2) + sub_total
        # "items": [{
        #     **taco_purchase, 
        #     **drink_purchase}],
        message = {
            "schema": {
                "type": "struct", "optional": False, "version": 1, "fields": [
                { "field": "stop_id", "type": "string", "optional": True },
                { "field": "order_id", "type": "string", "optional": True },
                { "field": "driver", "type": "string", "optional": True },
                { "field": "route", "type": "string", "optional": True },
                { "field": "event_id", "type": "int64", "optional": True },
                { "field": "order_date", "type": "string", "optional": True },
                { "field": "sub_total", "type": "float", "optional": True },
                { "field": "total", "type": "float", "optional": True },
                { "field": "MSG_TS", "type": "int64", "optional": True }
                ] },
            "payload": {
                "stop_id": stop_id,
                "order_id": str(uuid.uuid4()),
                "driver": self.driver, 
                "route": self.route,
                "event_id": self.record_counter,
                "order_date": datetime.now().strftime("%b-%d-%Y %H:%M:%S"),
                "sub_total":sub_total,
                "total": total,
                "MSG_TS": int(datetime.now().strftime("%s")) * 1000
            }
        }

        return message

    def _degrees(self, semi):
        return semi * 180.0 / (1<<31)

    def _parse_file(self, FIT_FILE):
        self.file = os.path.join('/Users/cjtravis/git/cjtravis/data-engineering-pipelines/taco-tracker/data', FIT_FILE + '.fit')
        return fitparse.FitFile(self.file)

    def _record_builder(self, id, route_data):
        self.activity = {}
        lat = None
        lon = None
        self.activity['MSG_TS'] = int(datetime.now().strftime("%s")) * 1000
        self.activity['route'] = self.route
        self.activity['event_id'] = id
        self.activity['driver'] = self.driver

        for data in route_data:

            if data.name in self.fields:
                if data.name in self.geo_fields:
                    if not lat and data.name == "position_lat":
                        lat = self._degrees(data.value) 
                    if not lon and data.name == "position_long":
                        lon = self._degrees(data.value)
                if lat and lon:
                        self.activity['location'] = {"lat": lat, "lon": lon}
                if data.name == "timestamp":
                    #print(type(data.value))
                    #print(data.value.strftime('%s'))
                    self.activity['event_ts_human'] = str(data.value)
                    self.activity['event_ts_epoch'] = int(data.value.strftime('%s'))
                else:
                    self.activity[data.name] = data.value

        return json.dumps(self.activity)

    def _execute(self):
        # iterate these
        self.raw_route_message = self._parse_file(self.route)

        self.record_counter = 1
        self.stop_counter = 0
        checkpoints = [0]
    
        for record in self.raw_route_message.get_messages("record"):
            self.route_producer.poll(0)
            producer_record = self._record_builder(self.record_counter, record)
            json_pr = json.loads(producer_record)
            json_pr['travel_distance_delta_meters'] = round(json_pr['distance'] - checkpoints.pop(),2)
            checkpoints.append(json_pr['distance'])
            #self.route_producer.produce(self.route_topic, json.dumps(json_pr).encode('utf-8'), callback=self._delivery_report)
            #print(f'\n\n{json_pr}')
            print(f'Event # {self.record_counter}')
            if self.record_counter % self.density == 0 and 'location' in json.loads(producer_record):
                self.route_producer.produce(self.route_topic, json.dumps(json_pr).encode('utf-8'), callback=self._delivery_report)
                # should I stop?
                we_stop = True if abs(randrange(21) - randrange(21)) <= 2 else False
                # trigger stop event in kafka
                #print(type(json.loads(producer_record)))
                #print(json.loads(producer_record))
                
                ##self.stop_producer.flush()
                #print(stop_choice)
                if we_stop:
                    stop_record = self._generate_stop(json.loads(producer_record)["location"])
                    self.stop_producer.poll(0)
                    self.stop_producer.produce(self.stop_topic, json.dumps(stop_record).encode('utf-8'), callback=self._delivery_report)
                    self.stop_counter +=1
                    print(f'  Stop # {self.stop_counter}')
                    print(f'{self.driver}\'s stopping to sell some food.')

                    # how many orders should we generate on this stop?
                    number_of_orders = randint(1,10)
                    print(f'Number of orders: {number_of_orders}')
                    for x in range(1, number_of_orders):
                        print(f'    Order {x} of {number_of_orders}')
                        order = self._create_order(stop_record["stop_id"])
                        # trigger order event in kafka
                        #self.order_producer.poll(0)
                        self.order_producer.produce(self.order_topic, json.dumps(order).encode('utf-8'), callback=self._delivery_report)
                        ##self.order_producer.flush()
                        print(order["payload"])
                        #time.sleep(1)
                    
                    #for x in range(1, number_of_orders):

                        # Cheat and send to Kafka for ES
                     #   print(order["payload"])
                        #self.order_producer_es.poll()
                        self.order_producer_es.produce(self.order_topic_es, json.dumps(order["payload"]).encode('utf-8'))
                        self.order_producer_es.flush()

                #self.route_producer.produce(self.route_topic, json.dumps(json_pr).encode('utf-8'), callback=self._delivery_report)
                
                time.sleep(self.rate)
            self.record_counter +=1

            self.route_producer.flush()

    def run(self):
        self._execute()
        #self._create_order()

if __name__ == '__main__':
    app()

