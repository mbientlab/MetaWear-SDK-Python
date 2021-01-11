.. highlight:: python

Bridge to CPP SDK
===================
As mentioned previously, the MetaWear Python APIs are a wrapper around the CPP APIs.  ::

    from mbientlab.metawear import MetaWear
    from mbientlab.metawear.cbindings import *
    from mbientlab.warble import * 

The core libraries are written in C++ and many of the calls made are from the CPP library. You will find the `C++ documentation <https://mbientlab.com/cppdocs/latest/>`_ and `API reference <https://mbientlab.com/docs/metawear/cpp/latest/globals.html>`_ useful.

MetaWear
---------
The MetaWear import holds all of the CPP source code for our SDK. For example, the sensor fusion function in CPP: ::

    /**
    * Stop sensor fusion
    * @param board         Calling object
    */
    METAWEAR_API void mbl_mw_sensor_fusion_stop(const MblMwMetaWearBoard* board);

The MetaWear classes can be found `here <https://github.com/mbientlab/MetaWear-SDK-Python/blob/master/mbientlab/metawear/metawear.py>`_ and helper functions `here <https://github.com/mbientlab/MetaWear-SDK-Python/blob/master/mbientlab/metawear/__init__.py>`_.

Bindings
---------------
The bindings file called `cbindings <https://github.com/mbientlab/MetaWear-SDK-Cpp/blob/master/bindings/python/mbientlab/metawear/cbindings.py>`_ is the glue between Python and the CPP SDK. Here is the binding for the sensor fusion function above: ::

    def init_libmetawear(libmetawear):
        libmetawear.mbl_mw_sensor_fusion_stop.restype = None
        libmetawear.mbl_mw_sensor_fusion_stop.argtypes = [c_void_p]

Warble
---------------
PyWarble provides Python classes that wrap around the exported functions of the `Warble C library <https://github.com/mbientlab/Warble>`_. Warble is a wrapper around various Bluetooth LE libraries, providing a common C API for Linux. On Linux, Warble wraps around the libblepp library, which is included as a submodule.