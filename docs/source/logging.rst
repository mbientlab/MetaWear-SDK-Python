.. highlight:: python

Logging
=======
Logging functions in the `logging.h <https://mbientlab.com/docs/metawear/cpp/latest/logging_8h.html>`_ header file control the on-board logger.  

These functions go hand in hand with the data signal logger outlined in the :doc:`datasignal` section.  

Once a logger is created; logging functions can be used. After you have setup the signal loggers, start 
the logger by calling `mbl_mw_logging_start <https://mbientlab.com/docs/metawear/cpp/latest/logging_8h.html#acab2d6b1c4f5449a39fe3bf60205471f>`_. ::

    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    logger = create_voidp(lambda fn: libmetawear.mbl_mw_datasignal_log(signal, None, fn), resource = "acc_logger")
    
    libmetawear.mbl_mw_logging_start(board, 0)

Once we are done logging, simply call: ::

    libmetawear.mbl_mw_logging_stop(board)

Downloading Data
----------------
When you are ready to retrieve the data, execute 
`mbl_mw_logging_download <https://mbientlab.com/docs/metawear/cpp/latest/logging_8h.html#a5d972af91fc37cfcb235785e20974ed3>`_.  

You will need to pass in a `MblMwLogDownloadHandler <https://mbientlab.com/docs/metawear/cpp/latest/structMblMwLogDownloadHandler.html>`_ struct to handle notifications from the logger. 

::

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