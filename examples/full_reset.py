# usage: python full_reset.py [mac]
from __future__ import print_function
import sys
from mbientlab.metawear import MetaWear, libmetawear
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

device = MetaWear(sys.argv[1])
device.connect()
print("Connected")

libmetawear.mbl_mw_logging_stop(device.board)
libmetawear.mbl_mw_logging_clear_entries(device.board)
libmetawear.mbl_mw_macro_erase_all(device.board)
libmetawear.mbl_mw_debug_reset_after_gc(device.board)
print("Erase logger and clear all entries")
sleep(1.0)

libmetawear.mbl_mw_debug_disconnect(device.board)
sleep(1.0)

device.disconnect()
print("Disconnect")
sleep(1.0)
