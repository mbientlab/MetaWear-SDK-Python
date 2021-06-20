# usage: python3 motion_record_stream.py [mac1] [mac2] ... [mac(n)]
# will only display acc data when there is significant motion with bmi160
# won't do much on bmi270
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value, create_voidp_int, create_voidp
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

e = Event()

if sys.version_info[0] == 2:
    range = xrange

class State:
    def __init__(self, device):
        # init
        self.device = device
        self.samples = 0
        self.callback = FnVoid_VoidP_DataP(self.data_handler)
        self.passthrough_proc = 0

    def data_handler(self, ctx, data):
        # print acc data to terminal
        print("%s -> %s" % (self.device.address, parse_value(data)))
        self.samples+= 1

    def passthrough_created(self, context, signal):
        # stream passthrough data
        print(signal)
        print(context)
        self.passthrough_proc = signal
        libmetawear.mbl_mw_datasignal_subscribe(signal, None,  self.callback)
        print("stream passthrough data")
        e.set()

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
    # setup ble
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)
    
    # setup accelerometer 
    libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0)
    libmetawear.mbl_mw_acc_set_odr(s.device.board, 25)
    libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)
    print("setup accelerometer sensor")

    # get acc signal
    acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    print("get accelerometer signal")

    # setup passthrough on acc data for x samples and stream it (subscribe)
    e.clear()
    passthrough_handler = FnVoid_VoidP_VoidP(s.passthrough_created)
    print("setup passthrough")
    passthrough = libmetawear.mbl_mw_dataprocessor_passthrough_create(acc_signal, PassthroughMode.COUNT, 0, None, passthrough_handler)
    e.wait()

    # setup any motion
    libmetawear.mbl_mw_acc_bosch_set_any_motion_count(s.device.board, 2)
    libmetawear.mbl_mw_acc_bosch_set_any_motion_threshold(s.device.board, 0.1)
    libmetawear.mbl_mw_acc_bosch_write_motion_config(s.device.board, AccBoschMotion.ANYMOTION)
    print("setup bmi160 motion recognition")

    # get motion signal    
    motion_signal = libmetawear.mbl_mw_acc_bosch_get_motion_data_signal(s.device.board)
    print("get motion signal")

    # create event that changes count based on motion signal
    event_handler = FnVoid_VoidP_VoidP_Int(lambda event, ctx, s: e.set())
    e.clear()
    libmetawear.mbl_mw_event_record_commands(motion_signal)
    libmetawear.mbl_mw_dataprocessor_passthrough_set_count(s.passthrough_proc, 50)
    print("create event that changes counter based on motion")
    libmetawear.mbl_mw_event_end_record(motion_signal, None, event_handler)
    e.wait()

    # start
    print("Start")
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
    libmetawear.mbl_mw_acc_start(s.device.board)       
    libmetawear.mbl_mw_acc_bosch_enable_motion_detection(s.device.board, AccBoschMotion.ANYMOTION)
    libmetawear.mbl_mw_acc_bosch_start(s.device.board)

# wait 10 s
sleep(10.0)

# tear down
for s in states:
    print("Stop")
    # stop
    libmetawear.mbl_mw_acc_stop(s.device.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)
    # stop
    libmetawear.mbl_mw_acc_bosch_disable_motion_detection(d.board, AccBoschMotion.ANYMOTION)
    libmetawear.mbl_mw_acc_bosch_stop(d.board)
    # disconnect
    libmetawear.mbl_mw_debug_disconnect(s.device.board)

# recap
print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))


