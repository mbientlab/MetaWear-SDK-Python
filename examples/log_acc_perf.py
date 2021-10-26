# usage: python3 log_acc_perf.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value, create_voidp, create_voidp_int
from mbientlab.metawear.cbindings import *
from threading import Event

import sys
import time

print("Searching for device...")
d = MetaWear(sys.argv[1])
d.connect()
print("Connected to " + d.address)

print("Configuring device")

try:
    print("Get and log acc signal")
    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(d.board)
    logger = create_voidp(lambda fn: libmetawear.mbl_mw_datasignal_log(signal, None, fn), resource = "acc_logger")
    
    print("Start logging")
    libmetawear.mbl_mw_logging_start(d.board, 0)
    
    print("Start acc")
    libmetawear.mbl_mw_acc_set_odr(d.board, 400.)
    libmetawear.mbl_mw_acc_write_acceleration_config(d.board)
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(d.board)
    libmetawear.mbl_mw_acc_start(d.board)

    print("Logging data for 10s")
    time.sleep(10.0)

    print("Setop acc")
    libmetawear.mbl_mw_acc_stop(d.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(d.board)
    
    print("Stop logging")
    libmetawear.mbl_mw_logging_stop(d.board)

    print("Flush cache if MMS")
    libmetawear.mbl_mw_logging_flush_page(d.board)
    
    print("Downloading data")
    libmetawear.mbl_mw_settings_set_connection_parameters(d.board, 7.5, 7.5, 0, 6000)
    time.sleep(1.0)

    print("Setup Download handler")
    e = Event()
    read_count = 0
    def progress_update_handler(context, entries_left, total_entries):
        if (entries_left == 0):
            e.set()
    
    fn_wrapper = FnVoid_VoidP_UInt_UInt(progress_update_handler)
    download_handler = LogDownloadHandler(context = None, \
        received_progress_update = fn_wrapper, \
        received_unknown_entry = cast(None, FnVoid_VoidP_UByte_Long_UByteP_UByte), \
        received_unhandled_entry = cast(None, FnVoid_VoidP_DataP))

    def data_handler(p):
        global read_count
        read_count += 2
        #print("{epoch: %d, value: %s}" % (p.contents.epoch, parse_value(p)))

    callback = FnVoid_VoidP_DataP(lambda ctx, p: data_handler(p))
    
    print("Subscribe to logger")
    libmetawear.mbl_mw_logger_subscribe(logger, None, callback)
    
    print("Download data")
    dl_time = time.time()
    libmetawear.mbl_mw_logging_download(d.board, 0, byref(download_handler))
    e.wait()
    dl_time = time.time() - dl_time
    print("Entry Read Count: %d" % (read_count))
    print("Entry Read Rate: %0.1f entries/s" % (read_count/dl_time))	

except RuntimeError as err:
    print(err)
finally:
    print("Resetting device")
    
    e = Event()
    d.on_disconnect = lambda status: e.set()
    print("Debug reset")
    libmetawear.mbl_mw_debug_reset(d.board)
    e.wait()
