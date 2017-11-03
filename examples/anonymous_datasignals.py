# usage: python anonymous_datasignals.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

if sys.version_info[0] == 2:
    range = xrange

metawear = MetaWear(sys.argv[1])
metawear.connect()
print("Connected")

sync_event = Event()
result = {}
def handler(board, signals, len):
    result['length'] = len
    result['signals'] = cast(signals, POINTER(c_void_p * len)) if signals is not None else None
    sync_event.set()
handler_fn = FnVoid_VoidP_VoidP_UInt(handler)

class DataHandler:
    def __init__(self, signal):
        raw = libmetawear.mbl_mw_anonymous_datasignal_get_identifier(signal)
        self.identifier = cast(raw, c_char_p).value.decode("ascii")
        self.data_handler_fn = FnVoid_DataP(lambda ptr: print({"identifier": self.identifier, "epoch": ptr.contents.epoch, "value": parse_value(ptr)}))

        libmetawear.mbl_mw_memory_free(raw)

print("Creating anonymous signals")
libmetawear.mbl_mw_settings_set_connection_parameters(metawear.board, 7.5, 7.5, 0, 6000)
sleep(1.0)
libmetawear.mbl_mw_metawearboard_create_anonymous_datasignals(metawear.board, handler_fn)
sync_event.wait()

if (result['signals'] == None):
    if (result['length'] != 0):
        print("Error creating anonymous signals, status = " + str(result['length']))
    else:
        print("No active loggers detected")
else:
    dl_event = Event()
    libmetawear.mbl_mw_logging_stop(metawear.board)

    print(str(result['length']) + " active loggers discovered")
    handlers = []
    for x in range(0, result['length']):
        wrapper = DataHandler(result['signals'].contents[x])
        libmetawear.mbl_mw_anonymous_datasignal_subscribe(result['signals'].contents[x], wrapper.data_handler_fn)
        handlers.append(wrapper)

    def progress_update_handler(left, total):
        if (left == 0):
            dl_event.set()

    def unknown_entry_handler(id, epoch, data, length):
        print("unknown entry = " + str(id))

    print("Downloading log")
    progress_update_fn = FnVoid_UInt_UInt(progress_update_handler)
    unknown_entry_fn = FnVoid_UByte_Long_UByteP_UByte(unknown_entry_handler)
    download_handler= LogDownloadHandler(received_progress_update = progress_update_fn, 
            received_unknown_entry = unknown_entry_fn, received_unhandled_entry = cast(None, FnVoid_DataP))
    libmetawear.mbl_mw_logging_download(metawear.board, 10, byref(download_handler))
    dl_event.wait()

    print("Download completed")
    libmetawear.mbl_mw_macro_erase_all(metawear.board)
    libmetawear.mbl_mw_debug_reset_after_gc(metawear.board)
    libmetawear.mbl_mw_debug_disconnect(metawear.board)

    sleep(1.0)
