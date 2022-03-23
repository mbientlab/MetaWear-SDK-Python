# usage: python3 stream_mag.py [mac1] [mac2] ... [mac(n)]
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
        self.magCallback = FnVoid_VoidP_DataP(self.mag_data_handler)

    # mag callback
    def mag_data_handler(self, ctx, data):
        print("MAG: %s -> %s" % (self.device.address, parse_value(data)))
        self.samples+= 1

states = []

# connect
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to %s over %s" % (d.address, "USB" if d.usb.is_connected else "BLE"))
    states.append(State(d))

# configure
for s in states:
    print("Configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)

    # setup mag
    libmetawear.mbl_mw_mag_bmm150_stop(s.device.board)
    libmetawear.mbl_mw_mag_bmm150_set_preset(s.device.board, MagBmm150Preset.REGULAR)

    # get mag and subscribe
    mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(mag, None, s.magCallback)

    # start mag
    libmetawear.mbl_mw_mag_bmm150_enable_b_field_sampling(s.device.board)
    libmetawear.mbl_mw_mag_bmm150_start(s.device.board)

# sleep
sleep(10.0)

# stop
for s in states:
    libmetawear.mbl_mw_mag_bmm150_stop(s.device.board)
    libmetawear.mbl_mw_mag_bmm150_disable_b_field_sampling(s.device.board)

    mag = libmetawear.mbl_mw_mag_bmm150_get_b_field_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(mag)

    libmetawear.mbl_mw_debug_disconnect(s.device.board)

# recap
print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))
