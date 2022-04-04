# usage: python3 macro_remove.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

event = Event()
          
# connect
device = MetaWear(sys.argv[1])
device.connect()
print("Connected to " + device.address + " over " + ("USB" if device.usb.is_connected else "BLE"))
sleep(1.0)

# remove macros    
print("Removing all macros")
libmetawear.mbl_mw_macro_erase_all(device.board)
sleep(1.0)

# reset
print("Debug reset and garbage collect")
libmetawear.mbl_mw_debug_reset_after_gc(device.board)
sleep(1.0)

# disconnect
print("Disconnect")
device.on_disconnect = lambda status: event.set()
libmetawear.mbl_mw_debug_disconnect(device.board)
event.wait()
