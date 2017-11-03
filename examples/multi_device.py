# usage: python multi_device [mac1] [mac2] ... [mac(n)]
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

if sys.version_info[0] == 2:
    range = xrange

class State:
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.callback = FnVoid_DataP(self.data_handler)

    def data_handler(self, data):
        print("%s -> %s" % (self.device.address, parse_value(data)))
        self.samples+= 1

states = []
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

for s in states:
    print("configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    libmetawear.mbl_mw_acc_set_odr(s.device.board, 25.0);
    libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0);
    libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board);

    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(signal, s.callback)

    libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board);
    libmetawear.mbl_mw_acc_start(s.device.board);

sleep(30.0)

for s in states:
    libmetawear.mbl_mw_acc_stop(s.device.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)

    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(signal)
    libmetawear.mbl_mw_debug_disconnect(s.device.board)

sleep(1.0)

print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))
