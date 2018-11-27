# usage: python scan_connect.py
from __future__ import print_function
from mbientlab.metawear import MetaWear
from mbientlab.metawear.cbindings import *
from mbientlab.warble import * 
from time import sleep

import platform
import six

selection = -1
devices = None

while selection == -1:
    print("scanning for devices...")
    devices = {}
    def handler(result):
        devices[result.mac] = result.name

    BleScanner.set_handler(handler)
    BleScanner.start()

    sleep(10.0)
    BleScanner.stop()

    i = 0
    for address, name in six.iteritems(devices):
        print("[%d] %s (%s)" % (i, address, name))
        i+= 1

    msg = "Select your device (-1 to rescan): "
    selection = int(raw_input(msg) if platform.python_version_tuple()[0] == '2' else input(msg))

address = list(devices)[selection]
print("Connecting to %s..." % (address))
device = MetaWear(address)
device.connect()

print("Connected")
print("Device information: " + str(device.info))
sleep(5.0)

device.disconnect()
sleep(1.0)
print("Disconnected") 
