# usage: python log_acc [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

if sys.version_info[0] == 2:
    range = xrange

class State:
    def __init__(self, device):
        self.device = device
        
    def setup_logger(self):
        e = Event()
        result = [None]

        def logger_handler(ctx, pointer):
            result[0] = RuntimeError("Could not create logger") if pointer == None else pointer
            e.set()
        fn_wrapper = FnVoid_VoidP_VoidP(logger_handler)

        signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
        libmetawear.mbl_mw_datasignal_log(signal, None, fn_wrapper)
        e.wait()
        
        if (result[0] is RuntimeError):
            raise result[0]

        self.logger = result[0]
        
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.device.board)
        libmetawear.mbl_mw_acc_start(self.device.board)
        libmetawear.mbl_mw_logging_start(self.device.board, 0);

    def download_data(self):
        libmetawear.mbl_mw_acc_stop(self.device.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(self.device.board)
        libmetawear.mbl_mw_logging_stop(self.device.board)

        e = Event()
        def progress_update_handler(context, entries_left, total_entries):
            if (entries_left == 0):
                e.set()
        
        fn_wrapper = FnVoid_VoidP_UInt_UInt(progress_update_handler)
        download_handler= LogDownloadHandler(context = None, \
            received_progress_update = fn_wrapper, \
            received_unknown_entry = cast(None, FnVoid_VoidP_UByte_Long_UByteP_UByte), \
            received_unhandled_entry = cast(None, FnVoid_VoidP_DataP))

        callback = FnVoid_VoidP_DataP(lambda ctx, p: print("%s -> %s" % (self.device.address, parse_value(p))))
        libmetawear.mbl_mw_logger_subscribe(self.logger, None, callback)
        libmetawear.mbl_mw_logging_download(self.device.board, 0, byref(download_handler))
        e.wait()

print("Searching for device...")
d = MetaWear(sys.argv[1])
d.connect()
print("Connected to " + d.address)
s = State(d) 

print("Configuring device")
libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
sleep(1.0)

try:
    s.setup_logger()

    print("Logging data for 15s")
    sleep(15.0)

    s.download_data()
	
except RuntimeError as e:
    print(e)

finally:
    print("Resetting device")
    e = Event()
    s.device.on_disconnect = lambda status: e.set()
    libmetawear.mbl_mw_debug_reset(s.device.board)
    e.wait()
