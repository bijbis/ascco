from Queue import Queue
from threading import Thread
from datetime import datetime
from influxdb import InfluxDBClient
# import psutil
import time
import socket
# import numpy as np
import sys
import jinja2
import re
import schedule
import sched
import json
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
NUMBER_OF_REGS = 1


class DBClient(object):
    db_created_already = False
    db = None

    def __init__(self, dbname, port, host="localhost", user="root", passcode="root"):
        self.host = host
        self.port = port
        self.user = user
        self.passcode = passcode
        self.dbName = dbname

    def create(self):
        if not DBClient.db_created_already:
            DBClient.db = InfluxDBClient(self.host, self.port, self.user, self.passcode, self.dbName)
            DBClient.db.create_database(self.dbName)
            DBClient.db_created_already = True

    def write(self, json_data):
        DBClient.db.write_points(json_data)


power_queue = Queue()
energy_queue = Queue()
c = DBClient('ascco_world', 8086)
c.create()
modC = ModbusClient(socket.gethostbyname('ascoworldmodem.hopto.org'), port=502)
modC.connect()
s1 = sched.scheduler(time.time, time.sleep)
s2 = sched.scheduler(time.time, time.sleep)


def worker1(q, c):
    while True:
        data = q.get()
        ##############################
        templateLoader = jinja2.FileSystemLoader(searchpath='./', followlinks=True)
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "EMeter2_others.jinja"
        template = templateEnv.get_template(TEMPLATE_FILE)
        templateVars = {
            "m1": "remote_monitor",
            "ip": "123.209.113.35",
            "location": "Australia Perth",
            "date": str(data[0]),
            "v": data[1],
            "i": data[2],
            "p": data[3],
            "pf": data[4]
        }
        json_body = template.render(templateVars).replace('\n', '').replace('\r', '')
        json_body = re.sub(' +', ' ', json_body)
        json_data = [json.loads(json_body)]
        json_data[0]['fields']['voltage'] = float(json_data[0]['fields']['voltage'])
        json_data[0]['fields']['current'] = float(json_data[0]['fields']['current'])
        json_data[0]['fields']['power'] = float(json_data[0]['fields']['power'])
        json_data[0]['fields']['power_factor'] = float(json_data[0]['fields']['power_factor'])
        # print(json_data)
        c.write(json_data)
        q.task_done()


def worker2(q, c):
    while True:
        data = q.get()
        ##############################
        templateLoader = jinja2.FileSystemLoader(searchpath="./", followlinks=True)
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "EMeter2_energy.jinja"
        template = templateEnv.get_template(TEMPLATE_FILE)
        templateVars = {
            "m1": "energy_consumption",
            "ip": "123.209.113.35",
            "location": "Australia Perth",
            "date": str(data[0]),
            "energy": data[1]
        }
        json_body = template.render(templateVars).replace('\n', '').replace('\r', '')
        json_body = re.sub(' +', ' ', json_body)
        json_data = [json.loads(json_body)]
        json_data[0]['fields']['total_energy'] = float(json_data[0]['fields']['total_energy'])
        # print(json_data)
        c.write(json_data)
        q.task_done()


################################
influxWriter = Thread(target=worker1, args=(power_queue, c, ))
influxWriter.setDaemon(True)
influxWriter.start()
################################
influxWriter = Thread(target=worker2, args=(energy_queue, c, ))
influxWriter.setDaemon(True)
influxWriter.start()
################################
# while True:
#     now = datetime.now()
#     t = str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
#     rr1 = float(modC.read_input_registers(13696, NUMBER_OF_REGS, unit=1).registers[0]) / 1000.0
#     rr2 = float(modC.read_input_registers(7576, NUMBER_OF_REGS, unit=1).registers[0]) / 1000.0
#     power_queue.put((t, rr1))
#     power_queue.join()
#     energy_queue.put((t, rr2))
#     energy_queue.join()
#     time.sleep(4)


def log_monitoring():
    now = datetime.now()
    t = str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
    v = float(modC.read_input_registers(13716, NUMBER_OF_REGS, unit=1).registers[0]) * 0.1
    i = float(modC.read_input_registers(13720, NUMBER_OF_REGS, unit=1).registers[0]) * 0.01
    p = float(modC.read_input_registers(13696, NUMBER_OF_REGS, unit=1).registers[0]) * 0.001
    pf = float(modC.read_input_registers(13702, NUMBER_OF_REGS, unit=1).registers[0]) * 0.001
    # print((t, v1, i1, p1, pf))
    power_queue.put((t, v, i, p, pf))
    power_queue.join()


def log_billing():
    now = datetime.now()
    t = str(now.day) + '-' + str(now.month) + '-' + str(now.year) + '__' + str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)
    rr2 = float(modC.read_input_registers(7576, NUMBER_OF_REGS, unit=1).registers[0])
    # print (t, rr2)
    energy_queue.put((t, rr2))
    energy_queue.join()


schedule.every(10).seconds.do(log_billing)
schedule.every(10).seconds.do(log_monitoring)

while True:
    schedule.run_pending()
