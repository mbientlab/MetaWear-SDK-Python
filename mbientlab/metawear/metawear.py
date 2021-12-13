from . import libmetawear
from .cbindings import *
from collections import deque
from ctypes import *
from distutils.version import LooseVersion
from mbientlab.warble import Gatt
from threading import Event
from types import SimpleNamespace

import copy
import errno
import json
import os
import platform
import requests
import sys
import time
import uuid
import serial
import serial.tools.list_ports as list_ports
import threading

_is_linux = platform.system() == 'Linux'

if sys.version_info[0] == 2:
    range = xrange

    def _array_to_buffer(value):
        return create_string_buffer(str(bytearray(value)), len(value))

elif sys.version_info[0] == 3:
    def _array_to_buffer(value):
        return create_string_buffer(bytes(value), len(value))

def _gattchar_to_string(gattchar):
    return str(uuid.UUID(int = ((gattchar.uuid_high << 64) | gattchar.uuid_low)))

def _lookup_path(path):
    return path if path is not None else ".metawear"

def _download_file(url, dest):
    try:
        os.makedirs(os.path.dirname(dest))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
    finally:
        r = requests.get(url, stream=True)
        content = r.content
        with open(dest, "wb") as f:
            f.write(content)
        return content

class MetaWearUSB(object):
    """Enables USB control of MetaWear devices via a warble-like abstraction"""

    GATT_DIS =                  '0000180A-0000-1000-8000-00805f9b34fb'
    GATT_MW_CHAR_COMMAND =      '326a9001-85cb-9195-d9dd-464cfbbae75a'
    GATT_MW_CHAR_NOTIFICATION = '326a9006-85cb-9195-d9dd-464cfbbae75a'

    @staticmethod
    def scan():
        """List MetaWear devices attached to USB"""
        devices = []
        for port in list_ports.grep('VID:PID=1915:D978'):
            name = 'MetaMotionS' if port.product is None else port.product
            mac = ':'.join(port.serial_number[i:i+2] for i in range(0,len(port.serial_number),2))
            devices.append({'address': mac, 'name': name, 'path': port.device})
        return devices

    @staticmethod
    def _device_path(address):
        """Returns OS path of device with given address if attached to USB"""
        devices = MetaWearUSB.scan()
        for d in devices:
            if address == d['address']:
                return d['path']
        return None

    def __init__(self, address):
        self._notify_handler = None
        self._disconnect_handler = None

        self.address = address
        self.ser = None

    def connect_async(self, handler):
        """Connect to device by establishing USB serial comm link"""
        status = None
        try:
            self.ser = serial.Serial(MetaWearUSB._device_path(self.address), 1000000, timeout=.1)
            time.sleep(0.10)

            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            # read device info via identification command
            self.ser.write("?\n".encode())
            self.ser.flush()
            id_str = self.ser.readline().strip().decode()
            self.info = dict(zip(('manufacturer','model_name','model','hardware','firmware','serial'), id_str.split(" ")))

            self._read_poll = True
            self._read_thread = threading.Thread(target=self._read_poller, daemon=True)

            self._write_disconnect = False
            self._write_poll = True
            self._write_resp_handler = None
            self._write_resp_event = Event() 
            self._write_thread = threading.Thread(target=self._write_poller, daemon=True)

            self._read_thread.start()
            self._write_thread.start()

        except serial.SerialException:
            self.ser = None
            status = Const.STATUS_ERROR_TIMEOUT

        handler(status)

    def __del__(self):
        self.disconnect()

    @property
    def is_enumerated(self):
        """True if the device is attached via USB, enumerated by the OS and ready for connections."""
        return MetaWearUSB._device_path(self.address) is not None

    @property
    def is_connected(self):
        """True if USB serial communication is established with the device."""
        return self.ser is not None and self.ser.is_open

    def disconnect(self):
        """Disconnect from device by closing the USB serial connection."""
        if self.is_connected:
            if self._read_poll:
                self._read_poll = False
                self._read_thread.join()

            if self._write_poll:
                self._write_poll = False
                self._write_resp_event.set()
                self._write_thread.join()

            self.ser.close()
            self.ser = None
        
        if self._disconnect_handler is not None:
            self._disconnect_handler(Const.STATUS_OK)

    def _write(self, cmd_str):
        """Encodes MetaWear command with serial line protocol."""
        bin_str = [0x1f, len(cmd_str)] + cmd_str + [ord('\n')]
        self.ser.write(bin_str)
        if cmd_str == list(map(ord, '\xfe\x06')): # disconnect cmd, flush and close serial port
            self._write_disconnect = True
            self._write_resp_event.set()

    def _write_async(self, cmd_str, handler):
        """Async write with response"""
        self._write(cmd_str)
        self._write_resp_handler = handler
        self._write_resp_event.set()

    def _write_without_resp_async(self, cmd_str, handler):
        """Async write without response"""
        self._write(cmd_str)
        handler(None)
    
    def service_exists(self, uuid):
        """Checks supported GATT services"""
        if uuid.lower() == MetaWear.GATT_SERVICE or uuid.lower() == MetaWearUSB.GATT_DIS:
            return True
        return False

    def find_characteristic(self, uuid):
        """Find GATT Characteristic by UUID"""
        if uuid.lower() == MetaWear.GATT_SERVICE or uuid.lower() == MetaWearUSB.GATT_MW_CHAR_COMMAND:
            return SimpleNamespace(write_async = self._write_async,
                                   write_without_resp_async = self._write_without_resp_async)
        if uuid.lower() == MetaWearUSB.GATT_MW_CHAR_NOTIFICATION:
            return SimpleNamespace(enable_notifications_async = lambda x: x(None),
                                   on_notification_received = self.on_notification_received)
        if uuid.lower() in MetaWear._DEV_INFO.keys():
            return SimpleNamespace(read_value_async = lambda x: x(self.info[MetaWear._DEV_INFO[uuid]].encode(), None))
        return None

    def on_notification_received(self, handler):
        """Registers notification received handler"""
        self._notify_handler = handler

    def on_disconnect(self, handler):
        """Registers disconnect handler"""
        self._disconnect_handler = handler

    def _bin_cmd_decode(self, c):
        """Decodes MetaWear event from line protocol character by character"""
        if self._cmd_started:
            if self._cmd_len == 0:
                self._cmd_len = ord(c)
            elif self._cmd_recv_len < self._cmd_len:
                self._cmd_recv_len += 1
                self._cmd_buffer += c
            elif c == b'\n':
                self._cmd_started = False
                return self._cmd_buffer
        elif c == b'\x1f':
            self._cmd_started = True
            self._cmd_len = 0
            self._cmd_recv_len = 0
            self._cmd_buffer = []
        return []

    def _read_poller(self):
        """Read polling loop to convert synchronous serial operations to async notifications."""
        self._cmd_started = False
        while self._read_poll:
            try:
                c = self.ser.read()
            except serial.SerialException:
                self._read_poll = False
                self.disconnect()
                return

            if len(c) < 1:
                continue
            cmd = self._bin_cmd_decode(c)
            if len(cmd) > 0:
                if self._notify_handler is not None:
                    self._notify_handler(cmd)

    def _write_poller(self):
        """Write poller enabling async writes and write response callbacks."""
        while self._write_poll:
            self._write_resp_event.wait() 
            self._write_resp_event.clear()
            if not self._write_poll:
                return
            self.ser.flush()
            if self._write_resp_handler is not None:
                self._write_resp_handler(None)
                self._write_resp_handler = None
            if self._write_disconnect:
                self._write_poll = False
                self.disconnect()
        
class MetaWear(object):
    GATT_SERVICE = "326a9000-85cb-9195-d9dd-464cfbbae75a"
    _DEV_INFO = {
        "00002a27-0000-1000-8000-00805f9b34fb": "hardware",
        "00002a29-0000-1000-8000-00805f9b34fb": "manufacturer",
        "00002a25-0000-1000-8000-00805f9b34fb": "serial",
        "00002a24-0000-1000-8000-00805f9b34fb": "model",
        "00002a26-0000-1000-8000-00805f9b34fb": "firmware"
    }

    @staticmethod
    def _convert(value):
        return value if sys.version_info[0] == 2 else value.encode('utf8')

    def __init__(self, address, **kwargs):
        """
        Creates a MetaWear object
        @params:
            address     - Required  : Mac address of the board to connect to e.g. E8:C9:8F:52:7B:07
            cache_path  - Optional  : Path the SDK uses for cached data, defaults to '.metawear' in the local directory
            hci_mac     - Optional  : Mac address of the hci device to uses, Warble will pick one if not set
            deserialize - Optional  : Deserialize the cached C++ SDK state if available, defaults to true
        """
        args = {}
        if (_is_linux and 'hci_mac' in kwargs):
            args['hci'] = kwargs['hci_mac']
        self.warble = Gatt(address.upper(), **args)
        self.conn = self.warble

        self.usb = MetaWearUSB(address.upper())

        self.info = {}
        self.write_queue = deque([])
        self.on_disconnect = None
        self.address = address.upper()
        self.cache = kwargs['cache_path'] if ('cache_path' in kwargs) else ".metawear"

        self._write_fn= FnVoid_VoidP_VoidP_GattCharWriteType_GattCharP_UByteP_UByte(self._write_gatt_char)
        self._read_fn= FnVoid_VoidP_VoidP_GattCharP_FnIntVoidPtrArray(self._read_gatt_char)
        self._notify_fn = FnVoid_VoidP_VoidP_GattCharP_FnIntVoidPtrArray_FnVoidVoidPtrInt(self._enable_notifications)
        self._disconnect_fn = FnVoid_VoidP_VoidP_FnVoidVoidPtrInt(self._on_disconnect)
        self._btle_connection= BtleConnection(write_gatt_char = self._write_fn, read_gatt_char = self._read_fn, 
                enable_notifications = self._notify_fn, on_disconnect = self._disconnect_fn)

        self.board = libmetawear.mbl_mw_metawearboard_create(byref(self._btle_connection))
        libmetawear.mbl_mw_metawearboard_set_time_for_response(self.board, 1000)

        if 'deserialize' not in kwargs or kwargs['deserialize']:
            self.deserialize()

        try:
            os.makedirs(self.cache)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    @property
    def is_connected(self):
        """
        True if the MetaWear board is connected.
        """
        return self.conn.is_connected

    @property
    def in_metaboot_mode(self):
        """
        True if the board is in MetaBoot mode.  The only permitted operation for MetaBoot boards is to update the firmware
        """
        return self.conn.service_exists("00001530-1212-efde-1523-785feabcd123")

    def disconnect(self):
        """
        Disconnects from the MetaWear board
        """
        self.conn.disconnect()

    def connect_async(self, handler, **kwargs):
        """
        Connects to the MetaWear board and initializes the SDK.  You must first connect to the board before using 
        any of the SDK functions
        @params:
            handler     - Required  : `(BaseException) -> void` function to handle the result of the task
            serialize   - Optional  : Serialize and cached C++ SDK state after initializaion, defaults to true
        """

        def completed(err):
            if (err != None):
                handler(err)
            else:
                if not self.in_metaboot_mode:
                    def init_handler(context, device, status):
                        if status != Const.STATUS_OK:
                            self.disconnect()
                            handler(RuntimeError("Error initializing the API (%d)" % (status)))
                        else:
                            if 'serialize' not in kwargs or kwargs['serialize']:
                                self.serialize()
                            handler(None)

                    self._init_handler = FnVoid_VoidP_VoidP_Int(init_handler)
                    libmetawear.mbl_mw_metawearboard_initialize(self.board, None, self._init_handler)
                else:
                    def read_task():
                        uuids = self._read_dev_info_state['uuids']
                        if(len(uuids)):
                            next = uuids.popleft()
                            self._read_dev_info_state['next'] = next                         
                            if (MetaWear._DEV_INFO[next] not in self.info):
                                gatt_char = self.conn.find_characteristic(next)
                                if (gatt_char == None):
                                    handler(RuntimeError("Missing gatt char '%s'" % (next)))
                                else:
                                    gatt_char.read_value_async(self._read_dev_info_state['completed'])
                            else:
                                read_task()
                        else:
                            handler(None)

                    def completed(value, error):
                        if (error == None): 
                            self.info[MetaWear._DEV_INFO[self._read_dev_info_state['next']]] = bytearray(value).decode('utf8')
                            read_task()
                        else:
                            handler(error)

                    self._read_dev_info_state = {
                        'uuids': deque(MetaWear._DEV_INFO.keys()),
                        'completed': completed,
                        'read_task': read_task
                    }

                    read_task()

        if 'firmware' in self.info: del self.info['firmware']
        
        self.conn = self.usb if self.usb.is_enumerated else self.warble
        self.conn.connect_async(completed)

    def connect(self, **kwargs):
        """
        Synchronous variant of `connect_async`
        """
        e = Event()
        result = []

        def completed(error):
            result.append(error)
            e.set()

        self.connect_async(completed)
        e.wait()

        if (result[0] != None):
            raise result[0]

    def _read_gatt_char(self, context, caller, ptr_gattchar, handler):
        uuid = _gattchar_to_string(ptr_gattchar.contents)

        gatt_char = self.conn.find_characteristic(uuid)

        if (gatt_char == None):
            print("gatt char '%s' does not exist" % (uuid))
            
        def completed(value, error):
            if error == None:
                read_value = bytearray(value)
                self.info[MetaWear._DEV_INFO[uuid]] = read_value.decode('utf8')

                handler(caller, cast(_array_to_buffer(value), POINTER(c_ubyte)), len(value))
            else:
                print("%s: Error reading gatt char (%s)" % (gatt_char.uuid, error))

        gatt_char.read_value_async(completed)
        
    def _write_char_async(self, force):
        count = len(self.write_queue)
        if (count > 0 and (force or count == 1)):
            next = self.write_queue[0]

            def completed(err):
                if (err != None):
                    print(str(err))
                temp = self.write_queue.popleft()
                self._write_char_async(True)

            if (next[2] == GattCharWriteType.WITH_RESPONSE):
                next[0].write_async(next[1], completed)
            else:
                next[0].write_without_resp_async(next[1], completed)

    def _write_gatt_char(self, context, caller, write_type, ptr_gattchar, value, length):
        gatt_char = self.conn.find_characteristic(_gattchar_to_string(ptr_gattchar.contents))
        buffer = [value[i] for i in range(0, length)]

        self.write_queue.append([gatt_char, buffer, write_type])
        
        self._write_char_async(False)
        
    def _enable_notifications(self, context, caller, ptr_gattchar, handler, ready):
        uuid = _gattchar_to_string(ptr_gattchar.contents)
        gatt_char = self.conn.find_characteristic(uuid)

        if (gatt_char == None):
            ready(caller, Const.STATUS_ERROR_ENABLE_NOTIFY)
        else:
            def completed(err):
                if err != None:
                    print(str(err))
                    ready(caller, Const.STATUS_ERROR_ENABLE_NOTIFY)
                else:
                    gatt_char.on_notification_received(lambda value: handler(caller, cast(_array_to_buffer(value), POINTER(c_ubyte)), len(value)))
                    ready(caller, Const.STATUS_OK)

            gatt_char.enable_notifications_async(completed)

    def _on_disconnect(self, context, caller, handler):
        def event_handler(status):
            if (self.on_disconnect != None):
                self.on_disconnect(status)
            handler(caller, status)
        self.conn.on_disconnect(event_handler)

    def _download_firmware(self, version=None):
        firmware_root = os.path.join(self.cache, "firmware")

        info1 = os.path.join(firmware_root, "info1.json")
        if not os.path.isfile(info1) or (time.time() - os.path.getmtime(info1)) > 1800.0:
            info1_content = json.loads(_download_file("https://releases.mbientlab.com/metawear/info1.json", info1))
        else:
            with open(info1, "rb") as f:
                info1_content = json.load(f)

        if version is None:
            versions = []
            for k in info1_content[self.info['hardware']][self.info['model']]["vanilla"].keys():
                versions.append(LooseVersion(k))
            versions.sort()
            target = str(versions[-1])
        else:
            if version not in info1_content[self.info['hardware']][self.info['model']]["vanilla"]:
                raise ValueError("Firmware '%s' not available for this board" % (version))
            target = version

        filename = info1_content[self.info['hardware']][self.info['model']]["vanilla"][target]["filename"]
        local_path = os.path.join(firmware_root, self.info['hardware'], self.info['model'], "vanilla", target, filename)

        if not os.path.isfile(local_path):
            url = "https://releases.mbientlab.com/metawear/{}/{}/{}/{}/{}".format(
                self.info['hardware'], self.info['model'], "vanilla", target, filename
            )
            _download_file(url, local_path)
        return local_path

    def serialize(self):
        """
        Serialize and cache the SDK state
        """
        mac_str = self.address.replace(':','')
        path = os.path.join(self.cache, '%s.json' % (mac_str))

        state = { "info": copy.deepcopy(self.info) }

        size = c_uint(0)
        cpp_state = cast(libmetawear.mbl_mw_metawearboard_serialize(self.board, byref(size)), POINTER(c_ubyte * size.value))
        state["cpp_state"] = [cpp_state.contents[i] for i in range(0, size.value)]
        libmetawear.mbl_mw_memory_free(cpp_state)

        with open(path, "w") as f:
            f.write(json.dumps(state, indent=2))
        
    def deserialize(self):
        """
        Deserialize the cached SDK state
        """
        mac_str = self.address.replace(':','')

        # See if old serialized state exists, if it does, read that then remove it
        path = os.path.join(self.cache, '%s.bin' % (mac_str))
        if os.path.isfile(path):
            with(open(path, "rb")) as f:
                content = f.read()
                raw = (c_ubyte * len(content)).from_buffer_copy(content)
                libmetawear.mbl_mw_metawearboard_deserialize(self.board, raw, len(content))

            os.remove(path)
            return True

        path = os.path.join(self.cache, '%s.json' % (mac_str))
        if os.path.isfile(path):
            with(open(path, "r")) as f:
                content = json.loads(f.read())
                self.info = content["info"]
                raw = (c_ubyte * len(content["cpp_state"])).from_buffer_copy(bytearray(content["cpp_state"]))
                libmetawear.mbl_mw_metawearboard_deserialize(self.board, raw, len(content))
            return True

        return False

    def update_firmware_async(self, handler, **kwargs):
        """
        Updates the firmware on the device.  The function is asynchronous and will update the caller 
        with the result of the task via a one parameter callback function.  If the parameter is set 
        with a BaseException object, then the task failed.
        @params:
            handler             - Required  : `(BaseException) -> void` function to handle the result of the task
            progress_handler    - Optional  : `(int) -> void` function to handle progress updates
            version             - Optional  : Specific firmware version to update to, defaults to latest available version
        """
        if not self.in_metaboot_mode:
            dc_copy = self.on_disconnect

            e = Event()
            self.on_disconnect = lambda status: e.set()

            libmetawear.mbl_mw_debug_jump_to_bootloader(self.board)
            e.wait()

            self.on_disconnect = dc_copy

            try:
                self.connect()
                if not self.in_metaboot_mode:
                    handler(RuntimeError("DFU service not found"))
            except BaseException as err:
                handler(err)
                return

        self._progress_handler = None if 'progress_handler' not in kwargs else kwargs['progress_handler']

        def completed(ctx):
            time.sleep(5.0)
            handler(None)

        self._on_successful = FnVoid_VoidP(completed)
        self._on_transfer = FnVoid_VoidP_Int(self._dfu_progress)
        self._on_started = FnVoid_VoidP(lambda ctx: None)
        self._on_cancelled = FnVoid_VoidP(lambda ctx: self._dfu_error("DFU operation cancelled"))
        self._on_error = FnVoid_VoidP_charP(lambda ctx, msg: self._dfu_handler(RuntimeError(msg)))

        try:
            path = self._download_firmware() if 'version' not in kwargs else self._download_firmware(version = kwargs['version'])
            buffer = create_string_buffer(path.encode('ascii'))
            self._dfu_delegate = DfuDelegate(context = None, on_dfu_started = self._on_started, on_dfu_cancelled = self._on_cancelled, 
                    on_transfer_percentage = self._on_transfer, on_successful_file_transferred = self._on_successful, on_error = self._on_error)
            libmetawear.mbl_mw_metawearboard_perform_dfu(self.board, byref(self._dfu_delegate), buffer.raw)
        except ValueError as e:
            handler(e)

    def _dfu_progress(self, ctx, p):
        if self._progress_handler != None:
            self._progress_handler(p)
