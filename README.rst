MetaWear Python SDK
###################
Python SDK for creating MetaWear apps on the Linux platform.  This is a thin wrapper around the `MetaWear C++ API <https://github.com/mbientlab/MetaWear-SDK-Cpp>`_ so you will find the C++ 
`documentation <https://mbientlab.com/cppdocs/latest/>`_ and `API reference <https://mbientlab.com/docs/metawear/cpp/latest/globals.html>`_ useful.  Also, check out the scripts in the 
`examples <https://github.com/mbientlab/MetaWear-SDK-Python/tree/master/examples>`_ folder for full sample code.

**This is not the pymetawear package.  That is a community developed Python SDK which you can find over** 
`here <https://github.com/mbientlab-projects/pymetawear>`_ **.**

Install
#######
Use pip to install the metawear package.  It depends on `pygattlib <https://bitbucket.org/OscarAcena/pygattlib>`_ so ensure your Linux environment first has the necessary 
`dependencies <https://bitbucket.org/OscarAcena/pygattlib/src/a858e8626a93cb9b4ad56f3fb980a6517a0702c6/DEPENDS?at=default&fileviewer=file-view-default>`_ installed.  

.. code-block:: bash

    pip install metawear --process-dependency-links

Usage
#####
Import the MetaWear class and libmetawear variable from the metawear module and everything from the cbindings module.  

.. code-block:: python

    from mbientlab.metawear import MetaWear, libmetawear
    from mbientlab.metawear.cbindings import *

If you do not know the MAC address of your device, use ``pygattlib`` to scan for nearby devices.  

.. code-block:: python

    from gattlib import DiscoveryService
    service = DiscoveryService("hci0")
    devices = service.discover(2)

    # grab the first scanned device
    address = devices.items()[0][0]

Once you have the device's MAC address, create a MetaWear object with the MAC address and connect to the device.

.. code-block:: python

    device = MetaWear(address)
    status = device.connect()

Upon a successful connection, you can begin calling any of the functions from the C++ SDK, for example, blinking the LED green.

.. code-block:: python

    pattern= LedPattern(repeat_count= Const.LED_REPEAT_INDEFINITELY)
    libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.BLINK)
    libmetawear.mbl_mw_led_write_pattern(device.board, byref(pattern), LedColor.GREEN)
    libmetawear.mbl_mw_led_play(device.board)
