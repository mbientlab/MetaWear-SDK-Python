.. highlight:: python

Haptic
======
The haptic module controls a high current driver to power a motor or buzzer (or similar devices).

In the MMR+ model, the coin vibration motor provides haptic feedback by vibrating using the haptic module.

Functions are defined in the 
`haptic.h <https://mbientlab.com/docs/metawear/cpp/latest/haptic_8h.html>`_ header filer.  Circuit diagrams for the driver pin are in section 8 of the 
`product specification <https://mbientlab.com/docs/MetaWearPPSv0.7.pdf>`_. ::

    # Run buzzer for 7500ms
    libmetawear.mbl_mw_haptic_start_buzzer(board, 7500)
    
    # Run motor at 100% strength for 5000ms
    libmetawear.mbl_mw_haptic_start_motor(board, 100.0, 5000)

The haptic module does not provide PWM (pulse-width modulation) capability.