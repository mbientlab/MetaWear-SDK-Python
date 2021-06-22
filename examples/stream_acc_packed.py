# usage: python3 stream_acc_packed.py [mac1] [mac2] ... [mac(n)]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

if sys.version_info[0] == 2:
    range = xrange

class State:
    # init
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.accCallback = FnVoid_VoidP_DataP(self.acc_data_handler)
        
    # acc callback
    def acc_data_handler(self, ctx, data):
        values = parse_value(data)
        print("ACC: %s -> epoch: %s, data: %s" % (self.device.address, data.contents.epoch, values))
        self.samples+= 1

states = []

# connect
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

# configure
for s in states:
    print("Configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)

    # setup acc
    libmetawear.mbl_mw_acc_bmi270_set_odr(s.device.board, AccBmi270Odr._50Hz)
    #libmetawear.mbl_mw_acc_bmi160_set_odr(s.device.board, AccBmi160Odr._50Hz)
    libmetawear.mbl_mw_acc_bosch_set_range(s.device.board, AccBoschRange._4G)
    libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)

    # get acc and subscribe
    acc = libmetawear.mbl_mw_acc_get_packed_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(acc, None, s.accCallback)

    # start acc
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
    libmetawear.mbl_mw_acc_start(s.device.board)

# sleep
sleep(10.0)

# stop
for s in states:
    libmetawear.mbl_mw_acc_stop(s.device.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)
    
    acc = libmetawear.mbl_mw_acc_get_packed_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(acc)

    libmetawear.mbl_mw_debug_disconnect(s.device.board)

# recap
print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))
