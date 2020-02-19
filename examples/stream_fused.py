# usage: python data_fuser.py [mac1] [mac2] ... [mac(n)]
from __future__ import print_function
from ctypes import c_void_p, cast, POINTER
from mbientlab.metawear import MetaWear, libmetawear, parse_value, cbindings, create_voidp
from time import sleep
from threading import Event
from sys import argv
import numpy as np
import os

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

states = []

# f = open('validateGyro.csv', 'w')

class State:
    def __init__(self, device):
        self.device = device
        self.callback = cbindings.FnVoid_VoidP_DataP(self.data_handler)
        self.processor = None
        self.sensor_data = []
        self.samples = 0

    def data_handler(self, ctx, data):
        values = parse_value(data, n_elem = 2)
        # f.write('%.4f,%.4f,%.4f\n' % (values[1].x, values[1].y, values[1].z))
        self.sensor_data.append([data.contents.epoch, 0, values[0].x, values[0].y, values[0].z, values[1].x, values[1].y, values[1].z])
        print("time: %s\tacc: (%.4f,%.4f,%.4f),\tgyro; (%.4f,%.4f,%.4f)" % (data.contents.epoch, values[0].x, values[0].y, values[0].z, values[1].x, values[1].y, values[1].z))

        self.samples += 1

    def setup(self):
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)

        e = Event()

        def processor_created(context, pointer):
            self.processor = pointer
            e.set()
        fn_wrapper = cbindings.FnVoid_VoidP_VoidP(processor_created)

        # set accelerometer to 100Hz sampling rate and range to +/- 16 g's
        libmetawear.mbl_mw_acc_set_odr(s.device.board, 100.0)
        libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0)
        libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)
        
        # set gyro to 100Hz sampling rate and +/- 1000 deg/sec. 
        libmetawear.mbl_mw_gyro_bmi160_set_odr(s.device.board, MBL_MW_GYRO_BMI160_ODR_100Hz)
        libmetawear.mbl_mw_gyro_bmi160_set_range(s.device.board, MBL_MW_GYRO_BMI160_RANGE_1000dps)
        libmetawear.mbl_mw_gyro_bmi160_write_config(s.device.board)


        acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
        gyro = libmetawear.mbl_mw_gyro_bmi160_get_rotation_data_signal(self.device.board)

        signals = (c_void_p * 1)()
        signals[0] = gyro

        # libmetawear.mbl_mw_dataprocessor_accounter_create(signals, None, fn_wrapper)
        fuser = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_fuser_create(acc, signals, 1, None, fn), resource = "fuser", event = e)
        accounter = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_accounter_create(fuser, None, fn), resource = "accounter", event = e)

        # libmetawear.mbl_mw_datasignal_subscribe(self.processor, None, self.callback)
        libmetawear.mbl_mw_datasignal_subscribe(accounter, None, self.callback)

    def start(self):
    
        libmetawear.mbl_mw_gyro_bmi160_enable_rotation_sampling(self.device.board)
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.device.board)

        libmetawear.mbl_mw_gyro_bmi160_start(self.device.board)
        libmetawear.mbl_mw_acc_start(self.device.board)
        
for i in range(len(argv) - 1):
    d = MetaWear(argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

for s in states:
    print("Configuring %s" % (s.device.address))
    s.setup()

for s in states:
    s.start()

sleep(2.0)

print("Resetting devices\n")
events = []
for s in states:
    e = Event()
    events.append(e)

    s.device.on_disconnect = lambda s: e.set()
    libmetawear.mbl_mw_debug_reset(s.device.board)

for e in events:
    e.wait()


trial_name = input("Please enter trial name: ")

for s in states:
    s.sensor_data = np.asarray(s.sensor_data, dtype=np.float64)
    
    timeStart = s.sensor_data[0,0]

    s.sensor_data[:,1] = [(x - timeStart) / 1000 for x in s.sensor_data[:,0]]

    filename = '../TestData/fused_data_' + trial_name + '.csv'
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, 'w') as f:
        f.write('epoch, elapseds, xacc, yacc, zacc, xgyro, ygyro, zgyro\n')
        for row in s.sensor_data:
            f.write('%d,%.3f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n' % (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))

    print("Data saved to \'" + filename + "\'\n")

print("Total Samples Received")
for s in states:
    print("%s -> %d" % (s.device.address, s.samples))

# f.close()