.. highlight:: python

Data Signal
===========
Data signals are an abstract representation of data producers.  The API treats them as an event that contains data and represents 
them with the `MblMwDataSignal <https://mbientlab.com/docs/metawear/cpp/latest/datasignal__fwd_8h.html#a1ce49f0af124dfa7984a59074c11e789>`_ struct.
  
They can be safely typecasted to an `MblMwEvent <https://mbientlab.com/docs/metawear/cpp/latest/event__fwd_8h.html#a569b89edd88766619bb41a2471743695>`_ as seen in the example in the previous section.

Data signals can come from the accelerometer:

::

    # Get accelerometer data
    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)


Reading the battery level:

::

    # Get battery level
    signal = libmetawear.mbl_mw_settings_get_battery_state_data_signal(board)

Getting the switch state (is the button pushed or not):

::

    # Get switch state
    switch = mbl_mw_switch_get_state_data_signal(board)

There are many signals which are highlighted in the sections of our documentation:

::

    # Get analog gpio value
    an_signal = libmetawear.mbl_mw_gpio_get_analog_input_data_signal(self.board, 3, GpioAnalogReadMode.ABS_REF)


Data Handling
-------------
Signal data is encapsulated by the `MblMwData <https://mbientlab.com/docs/metawear/cpp/latest/structMblMwData.html>`_ struct.  

The struct contains a: 

* Timestamp of when the data was created
* Pointer to the data
* Data type id indicating how to cast the pointer

There is a helper function called `parse_value <https://github.com/mbientlab/MetaWear-SDK-Python/blob/master/mbientlab/metawear/__init__.py>`_ to help with data types between Pythong and CPP.

Let's take a look at the most common data type for the accelerometer which is in units of degrees per second. The ``x``, ``y``, and ``z`` fields contain the angular velocity of the spin around that axis.

::

    def data_handler(self, ctx, data):
        print("%s -> %s" % (device.address, parse_value(data)))

You can take a look at our `swift binding file <https://github.com/mbientlab/MetaWear-SDK-Cpp/blob/master/bindings/swift/cbindings.swift>`_ for all the available data types.

Streaming
---------
Streaming data is sending live data from the sensors on the MetaWear board, through the Bluetooth link, to the device of your choice in real-time.

Aside from the latency of the Bluetooth link, data is received instantaneously.

Note that there are limits to the Bluetooth link as well as the sensors. Please see the `Bluetooth SIG <https://www.bluetooth.com/specifications/bluetooth-core-specification/>`_ and the MetaWear `datasheet <https://mbientlab.com/documentation>`_  to learn more.

To stream data live to your device, call 
`mbl_mw_datasignal_subscribe <https://mbientlab.com/docs/metawear/cpp/latest/datasignal_8h.html#ab2708a821b8cca7c0d67cf61acec42c3>`_  with the 
desired data signal and a callback function for handling the received data.  Terminating the live stream is done by calling 
`mbl_mw_datasignal_unsubscribe <https://mbientlab.com/docs/metawear/cpp/latest/datasignal_8h.html#ab2708a821b8cca7c0d67cf61acec42c3>`_. ::

    class State:
        def __init__(self, device):
            self.device = device
            self.samples = 0
            self.callback = FnVoid_VoidP_DataP(self.data_handler)

        def data_handler(self, ctx, data):
            print("%s -> %s" % (self.device.address, parse_value(data)))
            self.samples+= 1

    states = []
    for i in range(len(sys.argv) - 1):
        d = MetaWear(sys.argv[i + 1])
        d.connect()
        print("Connected to " + d.address)
        states.append(State(d))

    for s in states:
        print("Configuring device")
        libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)

        libmetawear.mbl_mw_acc_set_odr(s.device.board, 100.0)
        libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0)
        libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)

        signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
        libmetawear.mbl_mw_datasignal_subscribe(signal, None, s.callback)

        libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
        libmetawear.mbl_mw_acc_start(s.device.board)

    sleep(30.0)

    for s in states:
        libmetawear.mbl_mw_acc_stop(s.device.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)

        signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(signal)
        libmetawear.mbl_mw_debug_disconnect(s.device.board)

    print("Total Samples Received") 
    for s in states:
        print("%s -> %d" % (s.device.address, s.samples))


Logging
-------
Alternatively, data can be logged and retrieved at a later time.  

When the data is logged, it is stored in the board memory. The memory is finite and once it is full, old data may be overwritten by new data. Please consult the `Tutorials <https://mbientlab.com/tutorials/>`_ and the `datasheet <https://mbientlab.com/documentation>`_ of your board for more information.

The data must be retrieved at some point in time from the MetaWear board to the device of your choice using the logger APIs.

See the :doc:`logger` section for more details. ::


    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(d.board)
    logger = create_voidp(lambda fn: libmetawear.mbl_mw_datasignal_log(signal, None, fn), resource = "acc_logger")
    
    libmetawear.mbl_mw_logging_start(d.board, 0)
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(d.board)
    libmetawear.mbl_mw_acc_start(d.board)

    print("Logging data for 15s")
    sleep(15.0)

    libmetawear.mbl_mw_acc_stop(d.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(d.board)
    libmetawear.mbl_mw_logging_stop(d.board)

    print("Downloading data")
    libmetawear.mbl_mw_settings_set_connection_parameters(d.board, 7.5, 7.5, 0, 6000)
    sleep(1.0)

    e = Event()
    def progress_update_handler(context, entries_left, total_entries):
        if (entries_left == 0):
            e.set()
    
    fn_wrapper = FnVoid_VoidP_UInt_UInt(progress_update_handler)
    download_handler = LogDownloadHandler(context = None, \
        received_progress_update = fn_wrapper, \
        received_unknown_entry = cast(None, FnVoid_VoidP_UByte_Long_UByteP_UByte), \
        received_unhandled_entry = cast(None, FnVoid_VoidP_DataP))

    callback = FnVoid_VoidP_DataP(lambda ctx, p: print("{epoch: %d, value: %s}" % (p.contents.epoch, parse_value(p))))
    libmetawear.mbl_mw_logger_subscribe(logger, None, callback)
    libmetawear.mbl_mw_logging_download(d.board, 0, byref(download_handler))
    e.wait()

Readable Signals
----------------
Some sensors will only send data when they receive a command to do so. These are typically either slower sensors or analog sensors where data doesn't need to be read at 100Hz (such as the temperature sensor). 

Data signals that represent this type of data source are called readable signals.  
You can check if a data signal is readable by calling 
`mbl_mw_datasignal_is_readable <https://mbientlab.com/docs/metawear/cpp/latest/datasignal_8h.html#a9633497a3785ba2369f57b939bd156c2>`_.  

The read command is issued by calling 
`mbl_mw_datasignal_read <https://mbientlab.com/docs/metawear/cpp/latest/datasignal_8h.html#a0a456ad1b6d7e7abb157bdf2fc98f179>`_ or 
`mbl_mw_datasignal_read_with_parameters <https://mbientlab.com/docs/metawear/cpp/latest/datasignal_8h.html#a71391d5862eb18327ce2aaaac4a12159>`_.  Most 
readable data signals will use the former function which does not require any additional parameters.  The latter function is for reads that require 
additional parameters which are bundled into one struct.

Reading the humidity from the barometer is a good example of a single read:

::

    signal = libmetawear.mbl_mw_sensor_fusion_calibration_state_data_signal(device.board)
    
    def calibration_handler(ctx, pointer):
        value = parse_value(pointer)
        print("state: %s" % (value))

    if (value.accelerometer == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH and \
            value.gyroscope == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH and \
            value.magnetometer == Const.SENSOR_FUSION_CALIBRATION_ACCURACY_HIGH):
        libmetawear.mbl_mw_sensor_fusion_read_calibration_data(device.board, None, fn_wrapper_01)
    else:
        sleep(1.0)
        libmetawear.mbl_mw_datasignal_read(signal)

    fn_wrapper = FnVoid_VoidP_DataP(calibration_handler)

    libmetawear.mbl_mw_sensor_fusion_set_mode(device.board, SensorFusionMode.NDOF)
    libmetawear.mbl_mw_sensor_fusion_write_config(device.board)

    libmetawear.mbl_mw_datasignal_subscribe(signal, None, fn_wrapper)

When using readable signals, you must decide up front if the data will be streamed or logged before interacting with it.  That is, you should either 
have subscribed to or setup a logger for a readable signal before reading it.

Data Processing
---------------
Data signals can be fed through the on-board data processors to filter and/or transform the data in the firmware.  By performing computations on the 
MetaWear side, you can reduce the amount of data that is sent over the radio and the amount of postprocessing that is done on your mobile device.  

For example, a threshold processor can be used to determine if the ambient temperature has exceeded 40 degrees. A highpass filter can be used to determine if the board has moved or the comparison processor can be used to determine if and when the light in the room has been turned on.

Data processors can also be chained together to perform more complex tasks, such as using the rss, average, and threshold processors to determine if the 
board is in freefall based on the XYZ acceleration data. 

See the :doc:`dataprocessor` section for more details on the data processing system. 

Here is an example where the x,y,z components of the accelerometer are combined using the rss processor to calculate the vector magnitude:

::

    rss_handler = FnVoid_VoidP_VoidP(lambda ctx, p: e.set())
    accel_signal= libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_rss_create(accel_signal, None, rss_handler)
    e.wait()

Component Signals
-----------------
Some signals, such as the acceleration data signal, are composed of multiple values.  While you can interact with them as a whole, sometimes it is more 
convenient to only use individual values.  

To access the component values, call 
`mbl_mw_datasignal_get_component <https://mbientlab.com/docs/metawear/cpp/latest/datasignal_8h.html#abf5eaa69c5f5978cb7bdd9ea04a910e0>`_ with the signal 
and an index represnting which component to retrieve.  If a signal is single valued, the function will return null. 

In this example, only the z-axis is from the accelerometer is retrieved:

::

    def sensorDataHandler(self, context, data):
        data_ptr= cast(data.contents.value, POINTER(CartesianFloat))
        self.data_cartesian_float= copy.deepcopy(data_ptr.contents)
        self.data = self.data_cartesian_float

    sensor_data_handler= FnVoid_VoidP_DataP(sensorDataHandler)

    signal= libmetawear.mbl_mw_acc_bosch_get_acceleration_data_signal(board)
    acc_component = libmetawear.mbl_mw_datasignal_get_component(signal, Const.ACC_ACCEL_X_AXIS_INDEX)
    libmetawear.mbl_mw_datasignal_subscribe(acc_component, None, sensor_data_handler)
    libmetawear.mbl_mw_acc_bosch_set_range(self.board, AccBoschRange._8G)
