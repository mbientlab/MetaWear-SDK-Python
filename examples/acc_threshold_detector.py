# usage: python acc_threshold_detector [mac]
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

# CURRENT:
# Sample accelerometer at 50Hz
# Use the rms to combine X,Y,Z
# Use the average to downsample to about 4Hz (averaging 8 samples)
# Use the threshold detector to detect a bump 
# Also log all the event and download it later
        
print("Searching for device...")
d = MetaWear(sys.argv[1])
d.connect()
print("Connected to " + d.address)
print("Configuring device")
libmetawear.mbl_mw_settings_set_connection_parameters(d.board, 7.5, 7.5, 0, 6000)
sleep(1.0)

e = Event()
def create_voidp(create, resource):
    result = [None]
    def handler(ctx, pointer):
        result[0] = RuntimeError("Could not create " + resource) if pointer == None else pointer
        e.set()

    callback_wrapper = FnVoid_VoidP_VoidP(handler)
    create(callback_wrapper)
    e.wait()

    e.clear()
    if (result[0] is RuntimeError):
        raise result[0]
    return result[0]

def end_event_record(evt):
    result = [None]
    def handler(ctx, pointer, status):
        if (status != Const.STATUS_OK):
            result[0] = RuntimeError("Event recording returned a non-zero status (%d)" % (status))
        e.set()

    callback_wrapper = FnVoid_VoidP_VoidP_Int(handler)
    libmetawear.mbl_mw_event_end_record(evt, None, callback_wrapper)
    e.wait()

    e.clear()
    if (result[0] is RuntimeError):
        raise result[0]

try:
    # setup accelerometer (odr 50Hz and 2Gs)
    libmetawear.mbl_mw_acc_bmi160_set_odr(d.board, AccBmi160Odr._50Hz)
    libmetawear.mbl_mw_acc_set_range(d.board, 2.0)
    libmetawear.mbl_mw_acc_write_acceleration_config(d.board)

    # start to setup rms->avg->thresh->log chain
    acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(d.board)

    # create RMS - root mean square of acc X,Y,Z
    rms = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_rms_create(acc_signal, None,  fn), "RMS")
    print("RMS created")

    # setup averager - averages over 8 RMS samples @ 50Hz
    avg = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_average_create(rms, 8, None, fn), "averager")
    print("Averager created")

    # setup event on avg - reset averager
    libmetawear.mbl_mw_event_record_commands(avg)
    libmetawear.mbl_mw_dataprocessor_average_reset(avg)
    end_event_record(avg)

    # setup threshold detector - detect anything above 1
    ths = create_voidp(lambda fn: libmetawear.mbl_mw_dataprocessor_threshold_create(avg, ThresholdMode.BINARY, 1.0, 0.0, None, fn), "threshold detector")
    print("Threshold detector created")

    # setup logger - log the final signal of the averaged data
    ths_logger = create_voidp(lambda fn: libmetawear.mbl_mw_datasignal_log(ths, None, fn), "threshold logger")
    print("Threshold logger created")
    
    # start accelerometer and event logging
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(d.board)
    libmetawear.mbl_mw_acc_start(d.board)        
    libmetawear.mbl_mw_logging_start(d.board, 0)

    # change this to any time amount you want
    print("Logging data for 10s")
    sleep(10.0)
    
    libmetawear.mbl_mw_acc_stop(d.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(d.board)
    libmetawear.mbl_mw_logging_stop(d.board)

    def progress_update_handler(context, entries_left, total_entries):
        if (entries_left == 0):
            e.set()

    fn_wrapper = FnVoid_VoidP_UInt_UInt(progress_update_handler)
    download_handler= LogDownloadHandler(context = None, \
        received_progress_update = fn_wrapper, \
        received_unknown_entry = cast(None, FnVoid_VoidP_UByte_Long_UByteP_UByte), \
        received_unhandled_entry = cast(None, FnVoid_VoidP_DataP))

    callback = FnVoid_VoidP_DataP(lambda ctx, p: print("threshold crossed: {epoch: %d, value: %s}" % (p.contents.epoch, parse_value(p))))
    libmetawear.mbl_mw_logger_subscribe(ths_logger, None, callback)
    libmetawear.mbl_mw_logging_download(d.board, 0, byref(download_handler))
    e.wait()

except RuntimeError as err:
    print(err)
finally:
    e.clear()
    print("Resetting device")
    
    d.on_disconnect = lambda status: e.set()
    libmetawear.mbl_mw_debug_reset(d.board)
    e.wait()
