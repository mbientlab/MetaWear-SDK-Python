.. highlight:: python

Sensors
=======
MetaWear comes with plenty of sensors ready to be used with only a few API calls.  

All boards have a different combination of sensors or even different sensor models so it is important to check the result of the 
`mbl_mw_metawearboard_lookup_module <https://mbientlab.com/docs/metawear/cpp/latest/metawearboard_8h.html#ad9c7e7f60f77fc1e929ac48c6a3ffb9b>`_ method 
if your app is to be used with different board models e.g. the `MetaBase <https://www.microsoft.com/en-us/store/p/metabase/9nblggh4txj3>`_ app.  

::

    mbl_mw_metawearboard_lookup_module(board, MBL_MW_MODULE_LED)

In this section we will look at everything from accelerometers to magnetometers.

.. toctree::
    :hidden:
    :maxdepth: 1

    accelerometer
    ambientlightsensor
    barometer
    gyro
    humidity
    magnetometer
    temperature
