# MetaWear  SDK for Python by MBIENTLAB

[![Platforms](https://img.shields.io/badge/platform-linux--64%20%7C%20win--32%20%7C%20win--64-lightgrey?style=flat)](https://github.com/mbientlab/MetaWear-SDK-Python)
[![License](https://img.shields.io/cocoapods/l/MetaWear.svg?style=flat)](https://github.com/mbientlab/MetaWear-SDK-Python/blob/master/LICENSE.md)
[![Version](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue?style=flat)](https://github.com/mbientlab/MetaWear-SDK-Python)

![alt tag](https://raw.githubusercontent.com/mbientlab/MetaWear-SDK-iOS-macOS-tvOS/master/Images/Metawear.png)

SDK for creating MetaWear apps on the Linux platform.  This is a thin wrapper around the [MetaWear C++ API](https://github.com/mbientlab/MetaWear-SDK-Cpp) so you will find the C++ [documentation](https://mbientlab.com/cppdocs/latest/) and [API reference](https://mbientlab.com/docs/metawear/cpp/latest/globals.html) useful.

Also, check out the scripts in the [examples](https://github.com/mbientlab/MetaWear-SDK-Python/tree/master/examples) folder for sample code.

> ADDITIONAL NOTES  
This is not the pymetawear package.  That is a community developed Python SDK which you can find over [here](https://github.com/mbientlab-projects/pymetawear).

### Overview

[MetaWear](https://mbientlab.com) is a complete development and production platform for wearable and connected device applications.

MetaWear features a number of sensors and peripherals all easily controllable over Bluetooth 4.0 Low Energy using this SDK, no firmware or hardware experience needed!

The MetaWear hardware comes pre-loaded with a wirelessly upgradeable firmware, so it keeps getting more powerful over time.

### Requirements
- [MetaWear board](https://mbientlab.com/store/)
- A Linux or Windows 10+ machine with Bluetooth 4.0

### License
See the [License](https://github.com/mbientlab/MetaWear-SDK-Python/blob/master/LICENSE.md).

### Support
Reach out to the [community](https://mbientlab.com/community/) if you encounter any problems, or just want to chat :)

## Getting Started

### Installation

Use pip to install the metawear package.  It depends on [PyWarble](https://github.com/mbientlab/PyWarble) so ensure your target environment has the necessary [dependencies](https://github.com/mbientlab/Warble#build) installed.  

```ruby
pip install metawear
```

### Usage

Import the MetaWear class and libmetawear variable from the metawear module and everything from the cbindings module.  
```python
from mbientlab.metawear import MetaWear, libmetawear
from mbientlab.metawear.cbindings import *
```

If you do not know the MAC address of your device, use ``PyWarble`` to scan for nearby devices.  
```python
from mbientlab.warble import *
from mbientlab.metawear import *
from threading import Event

e = Event()
address = None
def device_discover_task(result):
    global address
    if (result.has_service_uuid(MetaWear.GATT_SERVICE)):
        # grab the first discovered metawear device
        address = result.mac
        e.set()

BleScanner.set_handler(device_discover_task)
BleScanner.start()
e.wait()

BleScanner.stop()
```

Once you have the device's MAC address, create a MetaWear object with the MAC address and connect to the device.
```python
device = MetaWear(address)
device.connect()
```

Upon a successful connection, you can begin calling any of the functions from the C++ SDK, for example, blinking the LED green.
```python
pattern= LedPattern(repeat_count= Const.LED_REPEAT_INDEFINITELY)
libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.BLINK)
libmetawear.mbl_mw_led_write_pattern(device.board, byref(pattern), LedColor.GREEN)
libmetawear.mbl_mw_led_play(device.board)
```

### Tutorials

Tutorials can be found [here](https://mbientlab.com/tutorials/).
