# usage: python stream_acc.py [mac1] [mac2] ... [mac(n)]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event
import numpy as np

import platform
import sys

# Available output data rates on the BMI160 gyro
MBL_MW_GYRO_BMI160_ODR_25Hz= 6
MBL_MW_GYRO_BMI160_ODR_50Hz= 7
MBL_MW_GYRO_BMI160_ODR_100Hz= 8
MBL_MW_GYRO_BMI160_ODR_200Hz= 9
MBL_MW_GYRO_BMI160_ODR_400Hz= 10
MBL_MW_GYRO_BMI160_ODR_800Hz= 11
MBL_MW_GYRO_BMI160_ODR_1600Hz= 12
MBL_MW_GYRO_BMI160_ODR_3200Hz= 13

# Available degrees per second ranges on the BMI160 gyro
MBL_MW_GYRO_BMI160_RANGE_2000dps= 0      # +/-2000 degrees per second
MBL_MW_GYRO_BMI160_RANGE_1000dps= 1      # +/-1000 degrees per second
MBL_MW_GYRO_BMI160_RANGE_500dps= 2       # +/-500 degrees per second
MBL_MW_GYRO_BMI160_RANGE_250dps= 3       # +/-250 degrees per second
MBL_MW_GYRO_BMI160_RANGE_125dps= 4       # +/-125 degrees per second


if sys.version_info[0] == 2:
    range = xrange

class State:
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.processor = None
        self.callback = FnVoid_VoidP_DataP(self.data_handler)
        self.sensor_data = []

    def data_handler(self, ctx, data):
        newData = str(parse_value(data)).strip('{}').replace(',', '').split()
        self.sensor_data.append([data.contents.epoch, 0, float(newData[2]), float(newData[5]), float(newData[8])])
        # print(newData)
        # f.write('%.3f,%.3f,%.3f\n' % (float(newData[2]), float(newData[5]), float(newData[8])))
        print("%s -> %s,\ttime: %s" % (self.device.address, parse_value(data), data.contents.epoch))
        self.samples+= 1

states = []
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

for s in states:
    print("Configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)

    e = Event()

    def processor_created(context, pointer):
        print(pointer)
        s.processor = pointer
        e.set()
    fn_wrapper = FnVoid_VoidP_VoidP(processor_created)

    # libmetawear.mbl_mw_acc_set_odr(s.device.board, 100.0)
    # libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0)
    # libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)

    libmetawear.mbl_mw_gyro_bmi160_set_odr(s.device.board, MBL_MW_GYRO_BMI160_ODR_100Hz)
    libmetawear.mbl_mw_gyro_bmi160_set_range(s.device.board, MBL_MW_GYRO_BMI160_RANGE_1000dps)
    libmetawear.mbl_mw_gyro_bmi160_write_config(s.device.board)

    # signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    signal = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(s.device.board)
    libmetawear.mbl_mw_dataprocessor_accounter_create(signal, None, fn_wrapper)
    e.wait()

    # libmetawear.mbl_mw_datasignal_subscribe(signal, None, s.callback)  
    libmetawear.mbl_mw_datasignal_subscribe(s.processor, None, s.callback)

    libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(s.device.board)
    libmetawear.mbl_mw_gyro_bmi160_start(s.device.board)

sleep(10.0)

# for s in states:
#     libmetawear.mbl_mw_acc_stop(s.device.board)
#     libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)

#     signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
#     libmetawear.mbl_mw_datasignal_unsubscribe(signal)
#     libmetawear.mbl_mw_debug_disconnect(s.device.board)

print("Resetting devices")
events = []

for s in states:
    e = Event()
    events.append(e)

    s.device.on_disconnect = lambda s: e.set()
    libmetawear.mbl_mw_debug_reset(s.device.board)

for e in events:
    e.wait()

# write sensor data to output csv file
i = 0
for s in states:
    s.sensor_data = np.asarray(s.sensor_data, dtype=np.float64)
    
    timeStart = s.sensor_data[0,0]

    s.sensor_data[:,1] = [(x - timeStart) / 1000 for x in s.sensor_data[:,0]]

    with open('gyro_data_' + str(i) + '.csv', 'w') as f:
        for row in s.sensor_data:
            f.write('%d,%.3f,%.3f,%.3f,%.3f\n' % (row[0], row[1], row[2], row[3], row[4]))
    i = i+1

print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))
