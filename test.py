# from pymodbus.client.sync import ModbusTcpClient as ModbusClient
# import time
# NUMBER_OF_REGS = 1
# client = ModbusClient('192.168.0.203', port=502)
# client.connect()
# while True:
# 	rr2 = float(client.read_input_registers(7576, NUMBER_OF_REGS, unit=1).registers[0]) / 1000.0
# 	# rr2 = client.read_input_registers(256 + 6, NUMBER_OF_REGS, unit=1).registers[0]
# 	# print float(rr1) * (8.31 - (-8.31)) / (9999.0 - 0.0) + (-8.31
# 	print rr2
# 	time.sleep(1)
# # rr = client.read_input_registers(256 + 6, NUMBER_OF_REGS, unit=1)
# # for i in xrange(NUMBER_OF_REGS):
# # 	print rr.registers[i]
# import sched
# import time
# s1 = sched.scheduler(time.time, time.sleep)
# s2 = sched.scheduler(time.time, time.sleep)


# def do_something(sc):
# 	print "Hello"
# 	s1.enter(10, 1, do_something, (sc, ))


# def do_something_else(sc):
# 	print "Hi"
# 	s2.enter(5, 1, do_something_else, (sc, ))


# s1.enter(10, 1, do_something, (s1, ))
# s1.run()
# s2.enter(5, 1, do_something_else, (s2, ))
# s2.run()

import schedule
from datetime import datetime


def job1():
	print "Hello" + str(datetime.now().second)


def job2():
	print "Hi" + str(datetime.now().second)


schedule.every(10).seconds.do(job1)
schedule.every(5).seconds.do(job2)

while True:
	schedule.run_pending()
