# usage: python macro_setup.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value, create_voidp_int, create_voidp
from mbientlab.metawear.cbindings import *
from threading import Event

import platform
import sys

device = MetaWear(sys.argv[1])
device.connect()
print("Connected to " + device.address)

e = Event()
    
print("Configuring device")
accel_signal= libmetawear.mbl_mw_acc_get_acceleration_data_signal(device.board)

libmetawear.mbl_mw_macro_record(device.board, 1)
rss = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_rss_create(accel_signal, None, fn), resource = "rss", event = e)
avg = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_average_create(rss, 4, None, fn), resource = "avg", event = e)
threshold = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_threshold_create(avg, ThresholdMode.BINARY, 0.5, 0.0, None, fn), resource = "threhsold", event = e)
ths_below = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_comparator_create(threshold, ComparatorOperation.EQ, -1.0, None, fn), resource = "ths_below", event = e)
ths_above = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_comparator_create(threshold, ComparatorOperation.EQ, 1.0, None, fn), resource = "ths_above", event = e)

pattern= LedPattern(pulse_duration_ms=1000, high_time_ms=500, high_intensity=16, low_intensity=16, repeat_count=Const.LED_REPEAT_INDEFINITELY)
libmetawear.mbl_mw_event_record_commands(ths_below) 
libmetawear.mbl_mw_led_write_pattern(device.board, byref(pattern), LedColor.BLUE)
libmetawear.mbl_mw_led_play(device.board)
create_voidp_int(lambda fn: libmetawear.mbl_mw_event_end_record(ths_below, None, fn), event = e)

libmetawear.mbl_mw_event_record_commands(ths_above) 
libmetawear.mbl_mw_led_stop_and_clear(device.board)
create_voidp_int(lambda fn: libmetawear.mbl_mw_event_end_record(ths_above, None, fn), event = e)

libmetawear.mbl_mw_acc_enable_acceleration_sampling(device.board)
libmetawear.mbl_mw_acc_start(device.board)

create_voidp_int(lambda fn: libmetawear.mbl_mw_macro_end_record(device.board, None, fn), event = e)

print("Resetting device")
device.on_disconnect = lambda status: e.set()
libmetawear.mbl_mw_debug_reset(device.board)
e.wait()