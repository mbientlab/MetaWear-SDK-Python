from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event

import copy
import signal
import sys

device = MetaWear(sys.argv[1])
device.deserialize()
device.connect()
print("Connected")

event = Event()
init_handler = FnVoid_VoidP_Int(lambda caller, status: event.set())
libmetawear.mbl_mw_metawearboard_initialize(device.board, init_handler)
event.wait()

if libmetawear.mbl_mw_metawearboard_is_initialized(device.board) != 0:
    device.serialize()

    print("model = " + str(libmetawear.mbl_mw_metawearboard_get_model_name(device.board)))
    libmetawear.mbl_mw_settings_set_connection_parameters(device.board, 7.5, 7.5, 0, 6000);
    libmetawear.mbl_mw_acc_set_odr(device.board, 50.0);
    libmetawear.mbl_mw_acc_set_range(device.board, 4.0);
    libmetawear.mbl_mw_acc_write_acceleration_config(device.board);

    samples = []
    def counter(data):
        samples.append(copy.deepcopy(parse_value(data)))

    data_handler = FnVoid_DataP(counter)
    signal = libmetawear.mbl_mw_acc_get_packed_acceleration_data_signal(device.board);
    libmetawear.mbl_mw_datasignal_subscribe(signal, data_handler)

    libmetawear.mbl_mw_acc_enable_acceleration_sampling(device.board);
    libmetawear.mbl_mw_acc_start(device.board);
    print("Sampling data")

    sleep(30.0)

    libmetawear.mbl_mw_acc_stop(device.board);
    libmetawear.mbl_mw_acc_disable_acceleration_sampling(device.board);

    for s in samples:
        print(str(s))
    print("collected samples = %d" % (len(samples)))

    

device.disconnect()
print("disconnected")
