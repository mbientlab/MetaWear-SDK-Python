# usage: python calibrate.py [mac]
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import sys

device = MetaWear(sys.argv[1])
device.connect()
print("Connected")

e = Event()

def calibration_data_handler(ctx, board, pointer):
    print("calibration data: %s" % (pointer.contents))
    libmetawear.mbl_mw_sensor_fusion_write_calibration_data(board, pointer)
    libmetawear.mbl_mw_memory_free(pointer)
    e.set()
fn_wrapper_01 = FnVoid_VoidP_VoidP_CalibrationDataP(calibration_data_handler)

signal = libmetawear.mbl_mw_sensor_fusion_calibration_state_data_signal(device.board)
def calibration_handler(ctx, pointer):
    value = parse_value(pointer)
    print("state: %s" % (value))

    if (value.accelrometer == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH and \
            value.gyroscope == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH and \
            value.magnetometer == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH):
        
        libmetawear.mbl_mw_sensor_fusion_read_calibration_data(device.board, None, fn_wrapper_01)
    else:
        sleep(1.0)
        libmetawear.mbl_mw_datasignal_read(signal)
fn_wrapper_02 = FnVoid_VoidP_DataP(calibration_handler)

libmetawear.mbl_mw_sensor_fusion_set_mode(device.board, SensorFusionMode.NDOF)
libmetawear.mbl_mw_sensor_fusion_write_config(device.board)

libmetawear.mbl_mw_datasignal_subscribe(signal, None, fn_wrapper_02)
libmetawear.mbl_mw_sensor_fusion_start(device.board)
libmetawear.mbl_mw_datasignal_read(signal)
e.wait()

print("Disconnecting")
e.clear()
device.on_disconnect = lambda s: e.set()
libmetawear.mbl_mw_sensor_fusion_stop(device.board)
libmetawear.mbl_mw_debug_disconnect(device.board)

e.wait()