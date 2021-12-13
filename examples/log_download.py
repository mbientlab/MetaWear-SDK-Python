# usage: python3 log_download.py [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep, strftime
from threading import Event

import platform
import sys

if sys.version_info[0] == 2:
    range = xrange

# connect
metawear = MetaWear(sys.argv[1])
metawear.connect()
print("Connected")

# setup
e = Event()
result = {}

# handler fxn
def handler(ctx, board, signals, len):
    result['length'] = len
    result['signals'] = cast(signals, POINTER(c_void_p * len)) if signals is not None else None
    e.set()
# handler fxn ptr
handler_fn = FnVoid_VoidP_VoidP_VoidP_UInt(handler)

# datahandler class
class DataHandler:
    def __init__(self, signal):
        self.identifier = libmetawear.mbl_mw_anonymous_datasignal_get_identifier(signal)
        self.filename = self.identifier.decode() + '-' + strftime("%m-%d-%Y-%H-%M-%S") + '.csv'
        self.file = None
        #self.data_handler_fn = FnVoid_VoidP_DataP(lambda ctx, ptr: print({"identifier": self.identifier, "epoch": ptr.contents.epoch, "value": parse_value(ptr)}))
        self.data_handler_fn = FnVoid_VoidP_DataP(lambda ctx, ptr: self.write(ctx, ptr))
    def write(self, ctx, ptr):
        d_struct = parse_value(ptr)
        if self.file is None:
            print("Opening %s for write." % (self.filename))
            self.file = open(self.filename, 'w')
            self.file.write('epoch,' + ','.join([f[0] for f in d_struct._fields_]) + '\n')
        data = [str(getattr(d_struct, f[0])) for f in d_struct._fields_]
        self.file.write(str(ptr.contents.epoch) + ',' + ','.join(data) + '\n')
    def __del__(self):
        if self.file is not None:
            self.file.close()

# setup ble
libmetawear.mbl_mw_settings_set_connection_parameters(metawear.board, 7.5, 7.5, 0, 6000)
sleep(1.0)

# create anonymous signal
print("Creating anonymous signals")
libmetawear.mbl_mw_metawearboard_create_anonymous_datasignals(metawear.board, None, handler_fn)
e.wait()

# make sense of logging signals found
if (result['signals'] == None):
    if (result['length'] != 0):
        print("Error creating anonymous signals, status = " + str(result['length']))
    else:
        print("No active loggers detected")
else:
    e.clear()
    # stop logging
    libmetawear.mbl_mw_logging_stop(metawear.board)
    # print results
    print(str(result['length']) + " active loggers discovered")
    handlers = []
    # analyze results
    for x in range(0, result['length']):
        wrapper = DataHandler(result['signals'].contents[x])
        # subscribe to download if good signal
        libmetawear.mbl_mw_anonymous_datasignal_subscribe(result['signals'].contents[x], None, wrapper.data_handler_fn)
        handlers.append(wrapper)
    # progress handler fxn
    def progress_update_handler(ctx, left, total):
        if (left == 0):
            e.set()
    # unknown entry handler fxn
    def unknown_entry_handler(ctx, id, epoch, data, length):
        print("unknown entry = " + str(id))
    # download handlers
    print("Downloading log")
    progress_update_fn = FnVoid_VoidP_UInt_UInt(progress_update_handler)
    unknown_entry_fn = FnVoid_VoidP_UByte_Long_UByteP_UByte(unknown_entry_handler)
    download_handler= LogDownloadHandler(context = None, received_progress_update = progress_update_fn, 
            received_unknown_entry = unknown_entry_fn, received_unhandled_entry = cast(None, FnVoid_VoidP_DataP))
    # download
    libmetawear.mbl_mw_logging_download(metawear.board, 10, byref(download_handler))
    # wait until done
    e.wait()
    # wait 1s
    sleep(1.0)
    print("Download completed")
    e.clear()
    metawear.on_disconnect = lambda status: e.set()
    # disconnect
    libmetawear.mbl_mw_debug_disconnect(metawear.board)
    e.wait()

