# usage: python update_firmware.py [mac] [version](optional)
from mbientlab.metawear import MetaWear, libmetawear
from threading import Event

import sys

device = MetaWear(sys.argv[1])
device.connect()
print("Connected")

args = {
    'progress_handler': lambda p: print("upload: %d%%" % (p)),
}
if (len(sys.argv) >= 3):
    args['version'] = sys.argv[2]

e = Event()
result = []
def dfu_handler(err):
    result.append(err)
    e.set()

device.update_firmware_async(dfu_handler, **args)
e.wait()

if (result[0] != None):
    raise result[0]