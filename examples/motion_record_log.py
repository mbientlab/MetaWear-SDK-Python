# usage: python3 motion_record_log.py [mac1] [mac2] ... [mac(n)]
# will only log acc data when there is significant motion with bmi160
# won't do much on bmi270
from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value, create_voidp_int, create_voidp
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import platform
import sys

if sys.version_info[0] == 2:
    range = xrange

class State:
    # init
    def __init__(self, device):
        self.device = device
        self.samples = 0
        self.events = {"processor" : Event(), "event" : Event(), "log" : Event(), "download" : Event() }
    # proc callback fxn
    def processor_created(self, context, signal):
        self.passthrough_signal = signal
        self.events["processor"].set()
    # logger callback fxn
    def logger_ready(self, context, pointer):
        self.logger = pointer
        self.events["log"].set()
    # event callback fxn
    def event_ready(self, context, board, status):
        print(status)
        self.events["event"].set()
    # generic callback fxn
    def wont_be_used():
        print("nothing")

states = []
# connect
for i in range(len(sys.argv) - 1):
    d = MetaWear(sys.argv[i + 1])
    d.connect()
    print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
    states.append(State(d))

# configure
for s in states:
    # setup callback pointers
    processor_created_fn= FnVoid_VoidP_VoidP(s.processor_created)
    logger_created_fn= FnVoid_VoidP_VoidP(s.logger_ready)
    event_created_fn = FnVoid_VoidP_VoidP_Int(s.event_ready)

    # ble config
    print("Configuring device")
    libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
    sleep(1.5)
    
    # setup accelerometer 
    libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0)
    libmetawear.mbl_mw_acc_set_odr(s.device.board, 25)
    libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)
    print("setup accelerometer sensor")

    # get acc signal
    acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
    print("get accelerometer signal")

    # setup passthrough on acc data for x samples and log it 
    s.events["processor"].clear()
    print("setup passthrough")
    passthrough = libmetawear.mbl_mw_dataprocessor_passthrough_create(acc_signal, PassthroughMode.COUNT, 0, None, processor_created_fn)
    s.events["processor"].wait()

    # setup logger
    s.events["log"].clear()
    libmetawear.mbl_mw_datasignal_log(s.passthrough_signal, None, logger_created_fn)
    s.events["log"].wait()

    # wait 1s
    sleep(1.0)

    # setup any motion
    libmetawear.mbl_mw_acc_bosch_set_any_motion_count(s.device.board, 2)
    libmetawear.mbl_mw_acc_bosch_set_any_motion_threshold(s.device.board, 0.1)
    libmetawear.mbl_mw_acc_bosch_write_motion_config(s.device.board, AccBoschMotion.ANYMOTION)
    print("setup bmi160 motion recognition")

    # get motion signal    
    motion_signal = libmetawear.mbl_mw_acc_bosch_get_motion_data_signal(s.device.board)
    print("get motion signal")

    # create event that changes count based on motion signal
    s.events["event"].clear()
    libmetawear.mbl_mw_event_record_commands(motion_signal)
    libmetawear.mbl_mw_dataprocessor_passthrough_set_count(s.passthrough_signal, 10)
    print("create event that changes counter based on motion")
    libmetawear.mbl_mw_event_end_record(motion_signal, None, event_created_fn)
    s.events["event"].wait()

    # start
    print("Start")
    libmetawear.mbl_mw_logging_start(s.device.board, 0)
    libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
    libmetawear.mbl_mw_acc_start(s.device.board)       
    libmetawear.mbl_mw_acc_bosch_enable_motion_detection(s.device.board, 1)
    libmetawear.mbl_mw_acc_bosch_start(s.device.board)

print("0 min")
sleep(60.0)
print("1 min")
sleep(60.0)
print("2 min")
sleep(60.0)
print("3 min")
sleep(60.0)
print("4 min")
sleep(60.0)
print("5 min")
sleep(60.0)
print("6 min")
sleep(60.0)
print("7 min")
sleep(60.0)
print("8 min")
sleep(60.0)
print("9 min")
sleep(60.0)
print("10 min")

# tear down
for s in states:
    # setup logging and acc
    print("Stop")
    libmetawear.mbl_mw_acc_stop(s.device.board)
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)
    libmetawear.mbl_mw_acc_bosch_disable_motion_detection(s.device.board)
    libmetawear.mbl_mw_acc_bosch_stop(s.device.board)
    libmetawear.mbl_mw_logging_stop(s.device.board)

    # wait 1s
    print("Downloading data")
    sleep(1.0)

    # download handlers
    s.events["download"].clear()
    def progress_update_handler(context, entries_left, total_entries):
        if (entries_left == 0):
            s.events["download"].set()
    
    fn_wrapper = FnVoid_VoidP_UInt_UInt(progress_update_handler)
    download_handler = LogDownloadHandler(context = None, \
        received_progress_update = fn_wrapper, \
        received_unknown_entry = cast(None, FnVoid_VoidP_UByte_Long_UByteP_UByte), \
        received_unhandled_entry = cast(None, FnVoid_VoidP_DataP))

    log_callback = FnVoid_VoidP_DataP(lambda ctx, p: print("{epoch: %d, value: %s}" % (p.contents.epoch, parse_value(p))))
    libmetawear.mbl_mw_logger_subscribe(s.logger, None, log_callback)
    libmetawear.mbl_mw_logging_download(s.device.board, 0, byref(download_handler))
    s.events["download"].wait()

