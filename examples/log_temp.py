# usage: python log_temp [mac]
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

        #streaming and logging
        signal = libmetawear.mbl_mw_multi_chnl_temp_get_temperature_data_signal(self.device.board, \
            MetaWearRProChannel.ON_BOARD_THERMISTOR)
        libmetawear.mbl_mw_datasignal_log(signal, None, fn_wrapper)
        e.wait()
        
        if (result[0] is RuntimeError):
            raise result[0]

        self.logger = result[0]
        self.timer = self._setup_timer()
        self._setup_read_event(self.timer, signal)

        libmetawear.mbl_mw_logging_start(self.device.board, 0);
        libmetawear.mbl_mw_timer_start(self.timer)

    def _setup_timer(self):
        e = Event()
        result = [None]

        def timer_handler(ctx, pointer):
            result[0] = RuntimeError("Could not create timer") if pointer == None else pointer
            e.set()
        fn_wrapper = FnVoid_VoidP_VoidP(timer_handler)

        libmetawear.mbl_mw_timer_create_indefinite(self.device.board, 1000, 0, None, fn_wrapper)
        e.wait()

        if (result[0] is RuntimeError):
            raise result[0]

        return result[0]

    def _setup_read_event(self, timer, signal):
        e = Event()
        result = [None]

        def commands_recorded(ctx, event, status):
            result[0] = RuntimeError("Could not create read event") if status != Const.STATUS_OK else None
            e.set()
        fn_wrapper = FnVoid_VoidP_VoidP_Int(commands_recorded)

        libmetawear.mbl_mw_event_record_commands(timer)
        libmetawear.mbl_mw_datasignal_read(signal)
        libmetawear.mbl_mw_event_end_record(timer, None, fn_wrapper)
        e.wait()
        
        if (result[0] is RuntimeError):
            raise result[0]

    def download_data(self):
        libmetawear.mbl_mw_timer_remove(self.timer)
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

        callback = FnVoid_VoidP_DataP(lambda ctx, p: print("%f" % (parse_value(p))))
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
    #logging
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
