# usage: python3 stream_acc_gyro_bmi160.py [mac1] [mac2] ... [mac(n)]
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
    # init state
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.accCallback = FnVoid_VoidP_DataP(self.acc_data_handler)
        self.gyroCallback = FnVoid_VoidP_DataP(self.gyro_data_handler)
        
    # acc callback function
    def acc_data_handler(self, ctx, data):
        print("ACC: %s -> %s" % (self.device.address, parse_value(data)))
        self.samples+= 1
                
    # gyro callback function
    def gyro_data_handler(self, ctx, data):
        print("GYRO: %s -> %s" % (self.device.address, parse_value(data)))
        self.samples+= 1

# init
states = []
# connect to all mac addresses in arg
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
    states.append(State(d))

# configure all metawears
for s in states:
    print("Configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)

    # config acc
    #libmetawear.mbl_mw_acc_set_odr(s.device.board, 50.0) # Generic call
    libmetawear.mbl_mw_acc_bmi160_set_odr(s.device.board, AccBmi160Odr._50Hz) # BMI 160 specific call
    libmetawear.mbl_mw_acc_bosch_set_range(s.device.board, AccBoschRange._4G)
    libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)

    # config gyro
    libmetawear.mbl_mw_gyro_bmi160_set_range(s.device.board, GyroBoschRange._1000dps);
    libmetawear.mbl_mw_gyro_bmi160_set_odr(s.device.board, GyroBoschOdr._50Hz);
    libmetawear.mbl_mw_gyro_bmi160_write_config(s.device.board);

    # get acc signal and subscribe
    acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(acc, None, s.accCallback)

    # get gyro signal and subscribe
    gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_subscribe(gyro, None, s.gyroCallback)

    # start acc
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
    libmetawear.mbl_mw_acc_start(s.device.board)

    # start gyro
    libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(s.device.board)
    libmetawear.mbl_mw_gyro_bmi160_start(s.device.board)

# sleep 10 s
sleep(10.0)

# breakdown metawears
for s in states:
    # stop acc
    libmetawear.mbl_mw_acc_stop(s.device.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)
    
    # stop gyro
    libmetawear.mbl_mw_gyro_bmi160_stop(s.device.board)
    libmetawear.mbl_mw_gyro_bmi160_disable_rotation_sampling(s.device.board)

    # unsubscribe acc
    acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(acc)
    
    # unsubscribe gyro
    gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
    libmetawear.mbl_mw_datasignal_unsubscribe(gyro)
    
    # disconnect
    libmetawear.mbl_mw_debug_disconnect(s.device.board)

# download recap
print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))
