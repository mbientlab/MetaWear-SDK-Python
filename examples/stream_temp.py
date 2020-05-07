# usage: python log_temp.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value, create_voidp, create_voidp_int
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import sys

print("Searching for device...")
d = MetaWear(sys.argv[1])
d.connect()
print("Connected to " + d.address)
e = Event()

callback = FnVoid_VoidP_DataP(lambda ctx, p: print("{epoch: %d, value: %s}" % (p.contents.epoch, parse_value(p))))

print("Configuring device")
signal = libmetawear.mbl_mw_multi_chnl_temp_get_temperature_data_signal(d.board, MetaWearRProChannel.ON_BOARD_THERMISTOR)
libmetawear.mbl_mw_datasignal_subscribe(signal, None, callback)

timer = create_voidp(lambda fn: libmetawear.mbl_mw_timer_create_indefinite(d.board, 1000, 0, None, fn), resource = "timer", event = e)
    
libmetawear.mbl_mw_event_record_commands(timer)
libmetawear.mbl_mw_datasignal_read(signal)
create_voidp_int(lambda fn: libmetawear.mbl_mw_event_end_record(timer, None, fn), event = e)

libmetawear.mbl_mw_timer_start(timer)

print("Stream temp data for 5s")
sleep(5.0)

libmetawear.mbl_mw_timer_remove(timer)
libmetawear.mbl_mw_datasignal_unsubscribe(signal)
sleep(1.0)

print("Resetting device")
e = Event()
d.on_disconnect = lambda status: e.set()
libmetawear.mbl_mw_debug_reset(d.board)
e.wait()
