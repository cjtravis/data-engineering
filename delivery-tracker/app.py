import fitparse
import json
import os
import time
import click
import random
from random import randrange
from confluent_kafka import Producer
from multiprocessing import Process
from datetime import datetime, timedelta
from pprint import pprint



def run_in_parallel(*fns):
    proc = []
    for fn in fns:
        p = Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()

@click.command()
@click.option('--route', help='Choices are: \'CHI\', \'KC\', or \'LIB\'')
@click.option('--driver', help='The name of the driver performing the route')
@click.option('--rate', default=3, help='The rate at which to process the data')
@click.option('--density', default=3, help='Controls how dense/sparse the data is emitted')
def app(route, driver, rate, density):
    r1 = Route(route=route, courier=driver, product=None, rate=rate, density=density)
    r1.run()

class Route():

    def __init__(self, route='default', courier='cjtravis', product=None, rate=3, density=1):
        self.route = route
        self.courier = courier
        self.product = product
        self.rate = rate
        self.density = density
        self.kafka_config = {'bootstrap.servers': 'localhost:9092'}
        self.route_producer = Producer(self.kafka_config)
        self.order_producer = Producer(self.kafka_config)
        self.route_topic = 'tacos_route' # 'route_' + str(self.route).lower()
        self.order_topic = 'tacos_orders'
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

    def _create_order(self):
        #stop_choice = True if abs(randrange(11) - randrange(11)) < 2 else False
        #print(stop_choice)
        sales_tax = .07
        drink_purchase = random.choice(self.drinks)
        taco_purchase = random.choice(self.tacos)

        print(drink_purchase)
        print(taco_purchase)

        #print(drink_purchase.values()[0])
        sub_total = sum([float(x) for x in list(drink_purchase.values())] + [float(x) for x in list(taco_purchase.values())])
        #print(sub_total)
        #print(type(float(sub_total[0])))
        #print(f'sub total: {str(sub_total[0])}')

        total = round(float(sub_total) * float(sales_tax),2) + sub_total

        order = {
            "driver": self.courier, 
            "route": self.route,
            "event_id": self.record_counter,
            "location": self.activity['location'],
            "order_date": datetime.now().strftime("%b-%d-%Y %H:%M:%S"),
            "items": [{
            **taco_purchase, 
            **drink_purchase}],
            "sub_total":sub_total,
            "total": total,
            "MSG_TS": int(datetime.now().strftime("%s")) * 1000}
        #print(order)
        return order

    def _degrees(self, semi):
        return semi * 180.0 / (1<<31)
    
    def _delivery_report(self, err, msg):
        """ Called once for each message produced to indicate delivery result.
            Triggered by poll() or flush(). """
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    def _parse_file(self, FIT_FILE):
        self.file = os.path.join('/home/cjtravis/git/cjtravis/data-engineering-pipelines/delivery-tracker/data', FIT_FILE + '.fit')
        return fitparse.FitFile(self.file)

    def _record_builder(self, id, route_data):
        self.activity = {}
        lat = None
        lon = None
        self.activity['MSG_TS'] = int(datetime.now().strftime("%s")) * 1000
        self.activity['route'] = self.route
        self.activity['event_id'] = id
        self.activity['courier'] = self.courier
        self.activity['product'] = self.product
        #activity['vehicle_id'] = 311

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
        checkpoints = [0]
    
        for record in self.raw_route_message.get_messages("record"):
            self.route_producer.poll(0)
            producer_record = self._record_builder(self.record_counter, record)
            json_pr = json.loads(producer_record)
            json_pr['travel_distance_delta_meters'] = round(json_pr['distance'] - checkpoints.pop(),2)
            checkpoints.append(json_pr['distance'])
            
            print(f'\n\n{json_pr}')

            if self.record_counter % self.density == 0:
                # should I stop to sell food?
                we_stop = True if abs(randrange(21) - randrange(21)) <= 2 else False
                #print(stop_choice)
                if we_stop:
                    self.order_producer.poll(0)
                    print(f'{self.courier}\'s stopping to sell some food.')
                    self._create_order()
                    self.order_producer.produce(self.order_topic, json.dumps(self._create_order()).encode('utf-8'), callback=self._delivery_report)
                    self.order_producer.flush()

                self.route_producer.produce(self.route_topic, json.dumps(json_pr).encode('utf-8'), callback=self._delivery_report)
                time.sleep(self.rate)
            self.record_counter +=1

        self.route_producer.flush()

    def run(self):
        self._execute()
        #self._create_order()

if __name__ == '__main__':
    app()

    # r1 = Route(route='CHI', courier='Paul', product=None)
    # r2 = Route(route='KC', courier='Chad', product=None)
    # r3 = Route(route='LIB', courier='Scott', product=None)
    # r1.run()

    #p1 = Process(target = r1.run)
    #p1.start()
    #p1.join()

    #p2 = Process(target = r2.run)
    #p2.start()
    #p2.join()

    #p3 = Process(target = r3.run)
    #p3.start()

    #procs = [p1, p2, p3]
    #for p in procs:
    #    p.join()