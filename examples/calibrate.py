# usage: python3 calibrate.py [mac]
# This example is showing how to calibrate the sensor fusion on the metawear
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import sys

# connect
device = MetaWear(sys.argv[1])
device.connect()
print("Connected to " + device.address + " over " + ("USB" if device.usb.is_connected else "BLE"))

# event
e = Event()

# calibration data fxn
def calibration_data_handler(ctx, board, pointer):
    print("calibration data: %s" % (pointer.contents))
    # write the calib data to the metawear
    libmetawear.mbl_mw_sensor_fusion_write_calibration_data(board, pointer)
    libmetawear.mbl_mw_memory_free(pointer)
    e.set()
# calibration data fxn ptr
fn_wrapper_01 = FnVoid_VoidP_VoidP_CalibrationDataP(calibration_data_handler)

# get calibration state signal
signal = libmetawear.mbl_mw_sensor_fusion_calibration_state_data_signal(device.board)

# calibration handler fxn
def calibration_handler(ctx, pointer):
    value = parse_value(pointer)
    print("state: %s" % (value))
    if (value.accelrometer == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH and \
            value.gyroscope == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH and \
            value.magnetometer == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH):
        # read
        libmetawear.mbl_mw_sensor_fusion_read_calibration_data(device.board, None, fn_wrapper_01)
    else:
        sleep(1.0)
        libmetawear.mbl_mw_datasignal_read(signal)
# calbration handle fxn ptr
fn_wrapper_02 = FnVoid_VoidP_DataP(calibration_handler)

# setup sensor fusion config
libmetawear.mbl_mw_sensor_fusion_set_mode(device.board, SensorFusionMode.NDOF)
libmetawear.mbl_mw_sensor_fusion_write_config(device.board)

# subscribe to the calibration sensor fusion signal
libmetawear.mbl_mw_datasignal_subscribe(signal, None, fn_wrapper_02)

# start
libmetawear.mbl_mw_sensor_fusion_start(device.board)

# read
libmetawear.mbl_mw_datasignal_read(signal)

# wait for event
e.wait()

print("Disconnecting")
e.clear()
device.on_disconnect = lambda s: e.set()
# stop
libmetawear.mbl_mw_sensor_fusion_stop(device.board)
sleep(2.0)
# disconnect
libmetawear.mbl_mw_debug_disconnect(device.board)
# wait until done
e.wait()
