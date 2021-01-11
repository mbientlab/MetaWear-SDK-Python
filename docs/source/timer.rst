.. highlight:: python

Timer
=====
A MetaWear timer can be thought of as an event that is fired at fixed intervals.  

These timers are represented by the 
`MblMwTimer <https://mbientlab.com/docs/metawear/cpp/latest/timer__fwd_8h.html#ac32a834c8b7bc7230ce6947425f43926>`_ struct and can be safely typcased to a 
`MblMwEvent <https://mbientlab.com/docs/metawear/cpp/latest/event__fwd_8h.html#a569b89edd88766619bb41a2471743695>`_ struct.  

Timers can be used to schedule periodic tasks or setup a delayed task execution. For example, you can use the timer to record temperature samples are extremely low frequencies such as once per day or once per hour.

ID
--
MblMwTimer objects are identified by a numerical id; you can retrieve the id by calling 
`mbl_mw_timer_get_id <https://mbientlab.com/docs/metawear/cpp/latest/timer_8h.html#a695e95e035825b626b78416b5df5611e>`_.  

The id is used to retrieve existing timers from the API with the 
`mbl_mw_timer_lookup_id <https://mbientlab.com/docs/metawear/cpp/latest/timer_8h.html#a84d84562f66090e61061b67321c22961>`_ function.

As with previous sections, you may want to keep the id handy so that you can retrieve a timer at a later time.

Task Scheduling
---------------
Before you can schedule tasks, you first need to create a timer, by calling either 
`mbl_mw_timer_create <https://mbientlab.com/docs/metawear/cpp/latest/timer_8h.html#a749457dc6c8a181990367d8b1f92284c>`_ or 
`mbl_mw_timer_create_indefinite <https://mbientlab.com/docs/metawear/cpp/latest/timer_8h.html#ae6a58f97ba8e443aec84769a9cc84453>`_.  These functions are asynchronous and 
will pass a pointer to the caller when the timer is created.  

When you have a valid `MblMwTimer <https://mbientlab.com/docs/metawear/cpp/latest/timer__fwd_8h.html#ac32a834c8b7bc7230ce6947425f43926>`_, you can use the command recording system outlined in 
:doc:`event` section to program the board to respond to the periodic events.  

Upon recording timer task commands, call 
`mbl_mw_timer_start <https://mbientlab.com/docs/metawear/cpp/latest/timer_8h.html#a90455d9e29548c1332ef7ad9db46c50e>`_ to start the timer.

::

    def timer_created(self, context, timer_signal):
        self.timerSignals.append(timer_signal)
        self.e.set()

    timer_signal_ready = FnVoid_VoidP_VoidP(timer_created)

    libmetawear.mbl_mw_timer_create(board, 1000, 10, 0, None, timer_signal_ready)
    e.wait()
    libmetawear.mbl_mw_timer_start(timerSignal)

    # TIME PASSES

    libmetawear.mbl_mw_timer_create(self.board, 1000, -1, 0, None, timer_signal_ready)
    e.wait()

    libmetawear.mbl_mw_timer_stop(timerSignal)

When you are done using a timer, you can remove it with 
`mbl_mw_timer_remove <https://mbientlab.com/docs/metawear/cpp/latest/timer_8h.html#a96d102b4f39a46ccbaf8ee5a37a2a55e>`_. 

A good example is the one mentioned above. Because the temperature sensor is a slow sensor, it must be read using a timer to get periodic readings (unlike setting the ODR for the accelerometer):

::

    callback = FnVoid_VoidP_DataP(lambda ctx, p: print("{epoch: %d, value: %s}" % (p.contents.epoch, parse_value(p))))

    signal = libmetawear.mbl_mw_multi_chnl_temp_get_temperature_data_signal(board, MetaWearRProChannel.ON_BOARD_THERMISTOR)
    libmetawear.mbl_mw_datasignal_subscribe(signal, None, callback)

    timer = create_voidp(lambda fn: libmetawear.mbl_mw_timer_create_indefinite(board, 1000, 0, None, fn), resource = "timer", event = e)
    
    libmetawear.mbl_mw_event_record_commands(timer)
    libmetawear.mbl_mw_datasignal_read(signal)

    create_voidp_int(lambda fn: libmetawear.mbl_mw_event_end_record(timer, None, fn), event = e)

    libmetawear.mbl_mw_timer_start(timer)

    sleep(5.0)

    libmetawear.mbl_mw_timer_remove(timer)
    libmetawear.mbl_mw_datasignal_unsubscribe(signal)