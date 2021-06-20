# usage: python3 data_processor.py [mac1] [mac2] ... [mac(n)]
from __future__ import print_function
from ctypes import c_void_p, cast, POINTER
from mbientlab.metawear import MetaWear, libmetawear, parse_value, cbindings
from time import sleep
from threading import Event
from sys import argv

states = []

class State:
    # init
    def __init__(self, device):
        self.device = device
        self.callback = cbindings.FnVoid_VoidP_DataP(self.data_handler)
        self.processor = None
    # data callback fxn
    def data_handler(self, ctx, data):
        print("%s -> %s" % (self.device.address, parse_value(data)))
    # setup fxn
    def setup(self):
        # setup ble
        libmetawear.mbl_mw_settings_set_connection_parameters(self.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)
        # setup event
        e = Event()
        # processor callback fxn
        def processor_created(context, pointer):
            self.processor = pointer
            e.set()
        fn_wrapper = cbindings.FnVoid_VoidP_VoidP(processor_created)
        # get acc signal
        acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
        # create acc averager (averages 4 consecutive acc data entriess)
        libmetawear.mbl_mw_dataprocessor_average_create(acc, 4, None, fn_wrapper)
        # wait for averager to be created
        e.wait()
        # subscribe to signal
        libmetawear.mbl_mw_datasignal_subscribe(self.processor, None, self.callback)
    # start fxn
    def start(self):
        # start acc
        libmetawear.mbl_mw_acc_enable_acceleration_sampling(self.device.board)
        libmetawear.mbl_mw_acc_start(self.device.board)
        
# connect
for i in range(len(argv) - 1):
    d = MetaWear(argv[i + 1])
    d.connect()
    print("Connected to " + d.address)
    states.append(State(d))

# configure
for s in states:
    print("Configuring %s" % (s.device.address))
    s.setup()

# start
for s in states:
    s.start()

# wait
sleep(5.0)

# reset
print("Resetting devices")
events = []
for s in states:
    e = Event()
    events.append(e)
    s.device.on_disconnect = lambda s: e.set()
    libmetawear.mbl_mw_debug_reset(s.device.board)
for e in events:
    e.wait()
