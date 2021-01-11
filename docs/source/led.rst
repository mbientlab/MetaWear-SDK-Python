.. highlight:: python

Led
===
All boards come with an on-board RGB LED.  The RGB LED is able to light up the board in various colors and patterns.

Users can control the LED with the functions in the `led.h <https://mbientlab.com/docs/metawear/cpp/latest/led_8h.html>`_ header file.

Setting Patterns
----------------
An led pattern is represented by the `MblMwLedPattern <https://mbientlab.com/docs/metawear/cpp/latest/structMblMwLedPattern.html>`_ struct.  Users can 
configure every part of the pulse or load one of the preset patterns using the 
`mbl_mw_led_load_preset_pattern <https://mbientlab.com/docs/metawear/cpp/latest/led_8h.html#a033cf02db3dd86ca41e4a0a2eee054d3>`_ function.  Patterns 
are written to the board with the 
`mbl_mw_led_write_pattern <https://mbientlab.com/docs/metawear/cpp/latest/led_8h.html#a85e85092c649a75bf8f5a8749b7331a2>`_ function.

To remove patterns, call `mbl_mw_led_stop_and_clear <https://mbientlab.com/docs/metawear/cpp/latest/led_8h.html#a34624667cd8f52bedc818a8900377c01>`_;  
this will also stop pattern playback. ::

    pattern = LedPattern(delay_time_ms= 5000, repeat_count= 10)
    libmetawear.mbl_mw_led_load_preset_pattern(byref(pattern), LedPreset.BLINK) 
    libmetawear.mbl_mw_led_write_pattern(board, byref(pattern), LedColor.GREEN)

Pattern Playback
----------------
After writing patterns to the board, you can playback the pattern, similar to playing a music track, using  
`mbl_mw_led_play <https://mbientlab.com/docs/metawear/cpp/latest/led_8h.html#ae6dbd4d6e272522003137c5456576aaa>`_, 
`mbl_mw_led_pause <https://mbientlab.com/docs/metawear/cpp/latest/led_8h.html#aba0961b6734c8dda2b6d155814d0089c>`_, and 
`mbl_mw_led_stop <https://mbientlab.com/docs/metawear/cpp/latest/led_8h.html#a25f9c37cf33bf43cedf04535e76c5b7b>`_. ::

    # Start playing the programmed patterns
    libmetawear.mbl_mw_led_play(board)

    # Stop and Clear
    libmetawear.mbl_mw_led_stop_and_clear(board)

