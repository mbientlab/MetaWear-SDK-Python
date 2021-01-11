.. highlight:: python

Macro
=====
The on-board flash memory can also be used to store MetaWear commands instead of sensor data. 

A good example of this feature is to change the name of a device permanently so that is does not advertise as MetaWear. 

Recorded commands can be executed any time after being 
programmed with the functions in `macro.h <https://mbientlab.com/docs/metawear/cpp/0/macro_8h.html>`_ header file.  

Recording Commands
------------------
To record commands:

1. Call `mbl_mw_macro_record <https://mbientlab.com/docs/metawear/cpp/0/macro_8h.html#aa99e58c7cbc1bbecb10985bd08643bba>`_ to put the API in macro mode  
2. Use the MetaWear commands that you want programmed  
3. Exit macro mode with `mbl_mw_macro_end_record <https://mbientlab.com/docs/metawear/cpp/0/macro_8h.html#aa79694ef4d711d84da302983162517eb>`_

::

    libmetawear.mbl_mw_macro_record(board, 1)
    # COMMANDS TO RECORD GO HERE
    libmetawear.mbl_mw_macro_end_record(board, None, callback)

Macros can be set to run on boot by setting the ``exec_on_boot`` parameter with a non-zero value.

::

    libmetawear.mbl_mw_macro_record(board, 1) # ON BOOT
    libmetawear.mbl_mw_macro_record(board, 0) # NOT ON BOOT

In this example, the LED will blink blue on boot:

::

    e = threading.Event()
    
    callback = FnVoid_VoidP_VoidP_Int(lambda ctx, board, status: e.set())

    pattern = LedPattern(rise_time_ms = 0, pulse_duration_ms = 1000, repeat_count = 5, high_time_ms = 500, high_intensity = 16, low_intensity = 16)

    libmetawear.mbl_mw_macro_record(board, 1)

    libmetawear.mbl_mw_led_write_pattern(board, byref(pattern), LedColor.BLUE)
    libmetawear.mbl_mw_led_play(board)

    libmetawear.mbl_mw_macro_end_record(board, None, callback)

    e.wait()


Erasing Macros
--------------
Erasing macros is done with the `mbl_mw_macro_erase_all <https://mbientlab.com/docs/metawear/cpp/0/macro_8h.html#aa1c03d8f08b5058d8f81b532a6930d67>`_ 
method.  The erase operation will not occur until you disconnect from the board.

::

    libmetawear.mbl_mw_macro_erase_all(board)

