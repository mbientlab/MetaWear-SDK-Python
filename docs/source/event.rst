.. highlight:: python

Events
======
An event is an asynchronous notification from the MetaWear board represented in the C++ API by the 
`MblMwEvent <https://mbientlab.com/docs/metawear/cpp/latest/event__fwd_8h.html#a569b89edd88766619bb41a2471743695>`_ struct.  

Recording Commands
------------------
The board can be programmed to execute MetaWear commands in response to an event firing.  

An event can be many things such as a data filter (average the accelerometer signal), a disconnect (the board has disconnected from the Bluetooth link), or even a timer (10 seconds have passed).

To start recording commands, call 
`mbl_mw_event_record_commands <https://mbientlab.com/docs/metawear/cpp/latest/event_8h.html#a771158b2eedeea765163a7df5f6c51e7>`_.  While in a recording 
state, all MetaWear functions called will instead be recorded on the board and executed when the event is fired.  

To stop recording, call `mbl_mw_event_end_record <https://mbientlab.com/docs/metawear/cpp/latest/event_8h.html#a5d4f44a844d2ff90b9e97ed33613fca8>`_. This function is asynchronous and will alert the caller when it is completed via a callback function.

In this example, when an event occurs from the ``control_signal``, the led blinks:

::

    event_handler = FnVoid_VoidP_VoidP_Int(lambda ctx, e, s: event.set())
    pattern= LedPattern(pulse_duration_ms=1000, high_time_ms=500, high_intensity=16, low_intensity=16, repeat_count=Const.LED_REPEAT_INDEFINITELY)
    libmetawear.mbl_mw_event_record_commands(control_signal)
    libmetawear.mbl_mw_led_write_pattern(self.board, byref(pattern), LedColor.BLUE)
    libmetawear.mbl_mw_led_play(self.board)
    libmetawear.mbl_mw_event_end_record(control_signals[0], None, event_handler)

In this example, we create an event that reads the temperature data signal every time the timer reaches 1000ms: ::

    signal = libmetawear.mbl_mw_multi_chnl_temp_get_temperature_data_signal(d.board, MetaWearRProChannel.ON_BOARD_THERMISTOR)
    logger = create_voidp(lambda fn: libmetawear.mbl_mw_datasignal_log(signal, None, fn), resource = "temp_logger", event = e)

    timer = create_voidp(lambda fn: libmetawear.mbl_mw_timer_create_indefinite(d.board, 1000, 0, None, fn), resource = "timer", event = e)
    libmetawear.mbl_mw_event_record_commands(timer)
    libmetawear.mbl_mw_datasignal_read(signal)
    create_voidp_int(lambda fn: libmetawear.mbl_mw_event_end_record(timer, None, fn), event = e)

    libmetawear.mbl_mw_logging_start(d.board, 0)
    libmetawear.mbl_mw_timer_start(timer)