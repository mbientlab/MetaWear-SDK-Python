# usage: python3 full_reset.py [mac]
from __future__ import print_function
import sys
from mbientlab.metawear import MetaWear, libmetawear
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

# connect
device = MetaWear(sys.argv[1])
device.connect()
print("Connected")

# stop logging
libmetawear.mbl_mw_logging_stop(device.board)
sleep(1.0)

# flush cache if mms
libmetawear.mbl_mw_logging_flush_page(device.board)
sleep(1.0)

# clear logger
libmetawear.mbl_mw_logging_clear_entries(device.board)
sleep(1.0)

# remove events
libmetawear.mbl_mw_event_remove_all(device.board)
sleep(1.0)

# erase macros
libmetawear.mbl_mw_macro_erase_all(device.board)
sleep(1.0)

# debug and garbage collect
libmetawear.mbl_mw_debug_reset_after_gc(device.board)
sleep(1.0)

# delete timer and processors
libmetawear.mbl_mw_debug_disconnect(device.board)
sleep(1.0)

device.disconnect()
print("Disconnect")
sleep(1.0)
