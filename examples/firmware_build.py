# usage: python3 firmware_build.py [mac]
from ctypes import *
from mbientlab.metawear import MetaWear, libmetawear
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import sys

# connect
m = MetaWear(sys.argv[1])
m.connect()
print("Connected to " + m.address + " over " + ("USB" if m.usb.is_connected else "BLE"))

# get board info
size = c_uint(0)
info = libmetawear.mbl_mw_metawearboard_get_module_info(m.board, byref(size))

i = 15
print(info[i].name == b'Settings')

if (info[i].extra_len >= 2):
    print(info[i].extra[1])
else:
    print("Firmware build not available")

libmetawear.mbl_mw_memory_free(info)
