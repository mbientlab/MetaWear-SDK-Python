# usage: python3 log_temp.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value, create_voidp, create_voidp_int
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import sys

# connect
print("Searching for device...")
d = MetaWear(sys.argv[1])
d.connect()
print("Connected to " + d.address)

try:
    # setup events
    e = Event()
    print("Configuring device")
    
    # get temp signal and setup logger
    signal = libmetawear.mbl_mw_multi_chnl_temp_get_temperature_data_signal(d.board, MetaWearRProChannel.ON_BOARD_THERMISTOR)
    logger = create_voidp(lambda fn: libmetawear.mbl_mw_datasignal_log(signal, None, fn), resource = "temp_logger", event = e)
    
    # create a timer
    timer = create_voidp(lambda fn: libmetawear.mbl_mw_timer_create_indefinite(d.board, 1000, 0, None, fn), resource = "timer", event = e)
    
    # record an event
    libmetawear.mbl_mw_event_record_commands(timer)
    
    # event is to read temp signal
    libmetawear.mbl_mw_datasignal_read(signal)
    create_voidp_int(lambda fn: libmetawear.mbl_mw_event_end_record(timer, None, fn), event = e)
    
    # start logging
    libmetawear.mbl_mw_logging_start(d.board, 0)
    
    # start timer
    libmetawear.mbl_mw_timer_start(timer)
    
    # log 10s
    print("Logging data for 10s")
    sleep(10.0)
    
    # remove timer
    libmetawear.mbl_mw_timer_remove(timer)
    
    # remove logger
    libmetawear.mbl_mw_logging_stop(d.board)
    
    # remove event
    libmetawear.mbl_mw_event_remove_all(d.board)
    
    # flush cache for mms
    libmetawear.mbl_mw_logging_flush_page(d.board)
    
    # setup ble
    libmetawear.mbl_mw_settings_set_connection_parameters(d.board, 7.5, 7.5, 0, 6000)
    
    # wait 1s
    sleep(1.0)
    print("Downloading data")
    
    # setup all items for downloading data
    def progress_update_handler(context, entries_left, total_entries):
        if (entries_left == 0):
            e.set()
            
    fn_wrapper = FnVoid_VoidP_UInt_UInt(progress_update_handler)
    download_handler = LogDownloadHandler(context = None, \
        received_progress_update = fn_wrapper, \
        received_unknown_entry = cast(None, FnVoid_VoidP_UByte_Long_UByteP_UByte), \
        received_unhandled_entry = cast(None, FnVoid_VoidP_DataP))
    callback = FnVoid_VoidP_DataP(lambda ctx, p: print("{epoch: %d, value: %s}" % (p.contents.epoch, parse_value(p))))
    
    # subscribe to logger and download
    libmetawear.mbl_mw_logger_subscribe(logger, None, callback)
    libmetawear.mbl_mw_logging_download(d.board, 0, byref(download_handler))
    e.wait()
    
except RuntimeError as err:
    print(err)
finally:
    print("Resetting device")
    e = Event()
    d.on_disconnect = lambda status: e.set()
    libmetawear.mbl_mw_debug_reset(d.board)
    e.wait()
