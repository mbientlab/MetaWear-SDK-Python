# usage: python macro_remove.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

event = Event()
          
device = MetaWear(sys.argv[1])
device.connect()

print("Connected to " + device.address)
sleep(1.0)
    
print("Removing all macros")
libmetawear.mbl_mw_macro_erase_all(device.board)
libmetawear.mbl_mw_debug_reset_after_gc(device.board)

device.on_disconnect = lambda status: event.set()
libmetawear.mbl_mw_debug_disconnect(device.board)
event.wait()