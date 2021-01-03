# MetaWear SDK for Python by MBIENTLAB

[![Platforms](https://img.shields.io/badge/platform-linux-lightgrey?style=flat)](https://github.com/mbientlab/MetaWear-SDK-Python)
[![License](https://img.shields.io/cocoapods/l/MetaWear.svg?style=flat)](https://github.com/mbientlab/MetaWear-SDK-Python/blob/master/LICENSE.md)
[![Version](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue?style=flat)](https://github.com/mbientlab/MetaWear-SDK-Python)

![alt tag](https://raw.githubusercontent.com/mbientlab/MetaWear-SDK-iOS-macOS-tvOS/master/Images/Metawear.png)

SDK for creating MetaWear apps on the Linux platform.  Supported for Linux only.

This is a thin wrapper around the [MetaWear C++ API](https://github.com/mbientlab/MetaWear-SDK-Cpp) so you will find the C++ [documentation](https://mbientlab.com/cppdocs/latest/) and [API reference](https://mbientlab.com/docs/metawear/cpp/latest/globals.html) useful.

Also, check out the Python [examples](https://github.com/mbientlab/MetaWear-SDK-Python/tree/master/examples).

> ADDITIONAL NOTES  
This is not the pymetawear package.  That is a community developed Python SDK which you can find over [here](https://github.com/mbientlab-projects/pymetawear).
You can try to get our Python SDK running on OSX or Windows at your own risk. This requires that you get Warble to work under those OSs yourself. We do not provide examples or support for this; experts ONLY. Please see the Noble README.

### Overview

[MetaWear](https://mbientlab.com) is a complete development and production platform for wearable and connected device applications.

MetaWear features a number of sensors and peripherals all easily controllable over Bluetooth 4.0/5.0 Low Energy using this SDK, no firmware or hardware experience needed!

The MetaWear hardware comes pre-loaded with a wirelessly upgradeable firmware, so it keeps getting more powerful over time.

### Requirements
- [MetaWear board](https://mbientlab.com/store/)
- A linux machine with Bluetooth 4.0/5.0

### License
See the [License](https://github.com/mbientlab/MetaWear-SDK-Python/blob/master/LICENSE.md).

### Support
Reach out to the [community](https://mbientlab.com/community/) if you encounter any problems, or just want to chat :)

## Getting Started

### Pre-Installation

#### Python
You need to make sure you have Python2 or Python3 installed as well as Pip. We don't cover this in this README, you can google-fu how to install Python and Pip.
```
python -V
python3 -V
```

You installation might look like this for Python3:
```
sudo apt update
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
sudo apt install python3
```
Or like this:
```
wget https://www.python.org/ftp/python/3.9.0/Python-3.9.0.tar.xz
tar xf Python-3.9.0.tar.xz
cd Python-3.9.0
./configure --prefix=/usr/local/opt/python-3.9.0
make -j 4
sudo make altinstall
```
It will be entirely up to you to figure out how you want to install Python and if you want to use Python 2 or 3.

You should also check where Python was installed:
```
which python
which python3
```

##### Pip
You can install packages from the Python Package Index (PyPI). To do so, use the pip tool (google-fu how to install). 

It will look something like this:
```
curl -O https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py
```

There are two versions of pip:

- pip for installing Python 2 modules
- pip3 for Python 3 modules

Under normal circumstances, you should only be using Python 3 and therefore pip3.

You can install modules using the pip3 install command. For example, if you wanted to download the guizero module, you would type this into a terminal window:
```
sudo pip3 install guizero
```
You may or may not need to install with sudo:
```
pip3 install guizero
```
And you may or may want to install packages for the local user only:
```
pip3 install --user guizero
```
Again this is all up to you.

Here are a few useful commands:
- Upgrade an already installed module:
```
sudo pip3 install --upgrade name_of_module
```
- Uninstall a module:
```
sudo pip3 uninstall name_of_module
```
- List all installed modules:
```
sudo pip3 list
```

You will need to make sure when you install packages/libraries/dependencies using pip, that they are installed in the correct directory. Some can be installed in /usr/bin/, some in /usr/local/bin/ or /usr/.local/bin/. If you are having issues with modules not being found, a little google-fu will go a long way.

Using sudo python and non-sudo python might even change which Python is being used.

For example, this might work:
```
/usr/local/bin/python3 -m pip install cassandra-driver 
```
But this might not work:
```
pip3 install cassandra-driver
```
But this might works also:
```
sudo pip3 install cassandra-driver
```
It entirely depends on your setup because a different location/version of Python may be called in each case such that cassandra-driver may be installed in `/usr/local/lib/python3/dist-packages` or

To make sure you're installing it for the version of python you're using:
```
/path/to/your/python -m pip install <package>
```
Or you will get the error: 
```
ImportError: No module named <package_name>
```
You can also update your $PATH but the best way to avoid all this is to use Python virtual environments (google-fu this).

##### Using sudo - a Warning
It is important to note that because our scripts use OS level Bluetooth libraries, it may be required to use sudo (or you will get a Bluetooth warning).
```
terminate called after throwing an instance of 'BLEPP::HCIScanner::IOError'
what():  Setting scan parameters: Operation not permitted
```

##### Using bluez, BLE Dongles, and Python
At the time of this release, Python3.7 is supported. We are moving away from Python 2.7 (use the older 1.2.0 release for Python2).

Bluez 5.50 works but 5.54 might not work. Here's a good [tutorial](https://learn.adafruit.com/install-bluez-on-the-raspberry-pi/installation)

If you are not using a BLE dongle, you need to make sure your system is working and supports Bluetooth 4.0 or later (Bluetooth low energy).

If you are using a BLE dongle, you need to make sure it's working. You can google-fu how to use tools such as `bluetoothctl`, `hciconfig`, `btmon` and more to confirm this.

#### Pre-Requisites
MetaWear depends on [PyWarble](https://github.com/mbientlab/PyWarble) so ensure your target environment has the necessary [dependencies](https://github.com/mbientlab/Warble#build) installed.  

### Installation
You have two options for installation:

#### 1. Use PIP (recommended)
You can simply install the MetaWear package lib with Pip using the command line: 
```
pip install metawear
```
For Python 3:
```
pip3 install metawear
```
Or maybe (depends on your setup - see section above): 
```
/usr/bin/python3 -m pip install metawear
```

If you install metawear with Python2, you will get an older version (we are no longer supporting Python2 but the older libs work). 
We recommend using Python3 and our Pypi3 metawear package (this should automatically be resolved with pip).

#### 2. Clone our Repository (local deps - developers only)
We packaged everything for you already in this repository.

Make sure that when you clone this repository, that you clone the submodule with it.
```
git clone --recurse-submodules https://github.com/mbientlab/MetaWear-SDK-Python.git
```

Then you can simply install:
```
python3 setup.py build
```
This will compile the underlying cpp libraries and may take a few seconds.

#### Errors and Issues
If you have any issues with the installation, make sure you have warble and all the dependencies installed correctly.

Make sure all python, and warble dependencies are installed:
```
sudo apt update
sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev
sudo apt-get install bluetooth bluez libbluetooth-dev libudev-dev libboost-all-dev build-essential
```

Make sure warble is installed and listed:
```
pip3 list
pip3 freeze
```

Make sure your bluetooth system and dongles are working usin `bluetoothctl`.

#### Running your first Script
Once the install is successful, you can run our example scripts in the example folder (see the example folder in our repository):
```
sudo python3 scan_connect.py
```

If you get the following error:
```
error 1609703819.483035: Setting scan parameters: Operation not permitted
```
Please ignore it, it is coming from a low level third party dependence (blecpp) and does not affect your script.

#### Notes
You should familiarize yourself with this README and our tutorials since there a few limitiations and other gotchas spelled out, such as the maximum number of simultaneous Bluetooth connections. 

### Usage
Require the metawear package by importing the MetaWear class and libmetawear variable from the metawear module and everything from the cbindings module.
```python
from mbientlab.metawear import MetaWear, libmetawear
from mbientlab.metawear.cbindings import *
```

If you do not know the MAC address of your device, use `PyWarble` to scan for nearby devices.
```python
BleScanner.set_handler(device_discover_task)
BleScanner.start()
e.wait()
BleScanner.stop()
```

Or a specific MAC address
```python
address = C8:4B:AA:97:50:05 
```

After that, you must connect to the device
```python
device = MetaWear(address)
device.connect()
```

At this point you can call any of the MetaWear API's, for example, you can blink the LED green
```python
pattern= LedPattern(repeat_count= Const.LED_REPEAT_INDEFINITELY)
libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.SOLID)
libmetawear.mbl_mw_led_write_pattern(device.board, byref(pattern), LedColor.GREEN)
libmetawear.mbl_mw_led_play(device.board)
```

### Example
```python
# usage: python led.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event
import sys
device = MetaWear(sys.argv[1])
device.connect()
print("Connected")
pattern= LedPattern(repeat_count= Const.LED_REPEAT_INDEFINITELY)
libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.SOLID)
libmetawear.mbl_mw_led_write_pattern(device.board, byref(pattern), LedColor.GREEN)
libmetawear.mbl_mw_led_play(device.board)
sleep(5.0)
libmetawear.mbl_mw_led_stop_and_clear(device.board)
sleep(1.0)
device.disconnect()
```

### Tutorials
Tutorials can be found [here](https://mbientlab.com/tutorials/).

