from . import libmetawear
from .cbindings import *
from collections import deque
from ctypes import *
from distutils.version import LooseVersion
from bleak import BleakClient
from threading import Event
from types import SimpleNamespace

import asyncio
import functools
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
import warnings

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

    SERIAL_XFER_SIZE =          1024
    SERIAL_BYTE_START =         b'\x1f'
    SERIAL_BYTE_STOP =          b'\n'

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

    async def connect(self):
        """Connect to device by establishing USB serial comm link"""
        future = asyncio.get_running_loop().create_future()
        self.connect_async(
            handler=lambda error: future.set_result(None) if error is None else future.set_error(error)
        )
        await future

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

        # Try to return an awaitable Future for bleak compatability
        # If we're not in an async context, return nothing for warble compatibility
        try:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            future.set_result(None)
            return future
        except RuntimeError:
            pass

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
        # Warble backwards compatibility
        return self._get_service(uuid)

    async def services(self):
        return SimpleNamespace(
            get_service = self._get_service,
            get_characteristic = self._get_characteristic,
        )

    def _get_service(self, uuid):
        if uuid.lower() == MetaWear.GATT_SERVICE or uuid.lower() == MetaWearUSB.GATT_DIS:
            return SimpleNamespace() # only care that it exists
        return None

    def find_characteristic(self, uuid):
        """Find GATT Characteristic by UUID"""
        # Warble backwards compatibility
        if uuid.lower() == MetaWear.GATT_SERVICE or uuid.lower() == MetaWearUSB.GATT_MW_CHAR_COMMAND:
            return SimpleNamespace(write_async = self._write_async,
                                   write_without_resp_async = self._write_without_resp_async)
        if uuid.lower() == MetaWearUSB.GATT_MW_CHAR_NOTIFICATION:
            return SimpleNamespace(enable_notifications_async = lambda x: x(None),
                                   on_notification_received = self.on_notification_received)
        if uuid.lower() in MetaWear._DEV_INFO.keys():
            return SimpleNamespace(read_value_async = lambda x: x(self.info[MetaWear._DEV_INFO[uuid]].encode(), None))
        return None

    def _get_characteristic(self, uuid):
        """Find GATT Characteristic by UUID"""
        if self.find_characteristic(uuid) is not None:
            return SimpleNamespace(uuid=uuid.lower())

    def on_notification_received(self, handler):
        """Registers notification received handler"""
        # Warble backwards compatibility
        self._notify_handler = handler

    async def start_notify(self, uuid, callback):
        if uuid == MetaWearUSB.GATT_MW_CHAR_NOTIFICATION:
            self.on_notification_received(lambda value: callback(uuid, value))
        else:
            raise ValueError("UUID uuid not supported")

    def on_disconnect(self, handler):
        """Registers disconnect handler"""
        # Warble backwards compatibility
        self._disconnect_handler = handler

    def set_disconnected_callback(self, handler):
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
            elif c == MetaWearUSB.SERIAL_BYTE_STOP:
                self._cmd_started = False
                return self._cmd_buffer
        elif c == MetaWearUSB.SERIAL_BYTE_START:
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
                read_len = max(1, min(MetaWearUSB.SERIAL_XFER_SIZE, self.ser.in_waiting))
                line_bytes = self.ser.read(read_len)
            except serial.SerialException:
                self._read_poll = False
                self.disconnect()
                return

            if len(line_bytes) < 1:
                continue
            for i in range(len(line_bytes)):
                cmd = self._bin_cmd_decode(line_bytes[i:i+1])
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
        
def synchronous(asyncio_function):
    """Decorator to convert asyncio function to synchronous function."""

    @functools.wraps(asyncio_function)
    def sync_function(*args, **kwargs):
        """Synchronous function wrapper"""
        loop = asyncio.get_event_loop()
        coroutine = asyncio_function(*args, **kwargs)
        if not loop.is_running():
            loop.run_until_complete(coroutine)
        else:
            asyncio.run_coroutine_threadsafe(coroutine, loop).result(timeout=None)

    warnings.warn(
        "Using this function is deprecated. "
        "Please use the asyncio {asyncio_function.__name__} directly instead",
        DeprecationWarning,
    )
    return sync_function

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
                                      The OS may also have it's own BLE Device cache.
            hci_mac     - Optional  : Mac address of the hci device to uses.
                                      Deprecated, as bleak does not yet support this.
            hci_device  - Optional  : Name of the hci device to use. bleak defaults to `hci0`.
            deserialize - Optional  : Deserialize the cached C++ SDK state if available, defaults to true
        """
        args = {}
        if (_is_linux and 'hci_mac' in kwargs):
            warnings.warn(
                "The hci_mac parameter is deprecated, as bleak does not yet support this. ",
                "Please use the hci_device parameter instead.",
                DeprecationWarning,
            )
            import subprocess
            result = subprocess.run(["hcitool", "dev"], capture_output=True, check=True, timeout=1, encoding="utf8")
            device_list = result.stdout.splitlines()[1:]

            devices = {
                device_line.split()[1]: device_line.split()[0]
                for device_line in device_list
            }
            if kwargs["hci_mac"] in devices:
                args["adapter"] = devices[kwargs["hci_mac"]]
            else:
                raise RuntimeError(
                    f"Could not find hci device matching {kwargs['hci_mac']}. "
                    f"Devices found were: {result.stdout}"
                )
        elif _is_linux and 'hci_device' in kwargs:
            args['adapter'] = kwargs['hci_device']
        self.bleak = BleakClient(address, **args)
        self.conn = self.bleak

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
        return synchronous(self.in_metaboot_mode_asyncio)()

    async def in_metaboot_mode_asyncio(self):
        services = await self.conn.get_services()
        return services.get_service("00001530-1212-efde-1523-785feabcd123") is not None

    def disconnect(self):
        """
        Disconnects from the MetaWear board
        """
        synchronous(self.disconnect_asyncio)()

    async def disconnect_asyncio(self):
        """
        Disconnects the MetaWear board asynchronously.
        """
        await self.conn.disconnect()

    def connect_async(self, handler, **kwargs):
        """
        Connects to the MetaWear board and initializes the SDK.  You must first connect to the board before using
        any of the SDK functions
        @params:
            handler     - Required  : `(BaseException) -> void` function to handle the result of the task
            serialize   - Optional  : Serialize and cached C++ SDK state after initializaion, defaults to true
        """
        asyncio.ensure_future(
            self.connect_asyncio(**kwargs)
        ).add_done_callback(lambda f: handler(f.exception()))

    async def connect_asyncio(self, **kwargs):
        """
        Connects to the MetaWear board and initializes the SDK.  You must first connect to the board before using
        any of the SDK functions
        @params:
            serialize   - Optional  : Serialize and cached C++ SDK state after initializaion, defaults to true
        """

        if 'firmware' in self.info: del self.info['firmware']

        self.conn = self.usb if self.usb.is_enumerated else self.bleak
        await self.conn.connect()

        in_metaboot_mode = await self.in_metaboot_mode_asyncio()

        loop = asyncio.get_running_loop()

        if not in_metaboot_mode:
            initalised = loop.create_future()
            def init_handler(context, device, status):
                if status != Const.STATUS_OK:
                    self.disconnect()
                    initalised.set_exception(RuntimeError("Error initializing the API (%d)" % (status)))
                else:
                    if 'serialize' not in kwargs or kwargs['serialize']:
                        self.serialize()
                    initalised.set_result(None)

            self._init_handler = FnVoid_VoidP_VoidP_Int(init_handler)
            libmetawear.mbl_mw_metawearboard_initialize(self.board, None, self._init_handler)

            await initalised
        else:
            services = await self.conn.get_services()

            for uuid in MetaWear._DEV_INFO:
                gatt_char = services.get_characteristic(uuid)
                if gatt_char is None:
                    raise RuntimeError("Missing gatt char '%s'" % (next))

                gatt_value_bytes = await self.conn.read_gatt_char(uuid)
                self.info[MetaWear._DEV_INFO[uuid]] = bytearray(gatt_value_bytes).decode('utf8')

    def connect(self, **kwargs):
        """
        Synchronous variant of `connect_async`
        """
        synchronous(self.connect_asyncio)(**kwargs)

    def _read_gatt_char(self, context, caller, ptr_gattchar, handler):
        uuid = _gattchar_to_string(ptr_gattchar.contents)

        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(
            self._read_gatt_char_asyncio(caller, uuid, handler),
            loop
        )

    async def _read_gatt_char_asyncio(self, caller, uuid, handler):
        services = await self.conn.get_services()
        gatt_char = services.get_characteristic(uuid)
        if (gatt_char == None):
            print("gatt char '%s' does not exist" % (uuid))
            return

        gatt_value_bytes = await self.conn.read_gatt_char(gatt_char)
        self.info[MetaWear._DEV_INFO[uuid]] = gatt_value_bytes.decode('utf8')

        handler(
            caller, cast(_array_to_buffer(gatt_value_bytes), POINTER(c_ubyte)), len(gatt_value_bytes),
        )

    async def _write_char_asyncio(self):
        """Loops over the contents of self.write_queue and writes them to the board.

        This function returns instantly if it's already being run by another thread.
        """
        if len(self.write_queue) > 1:
            # if self.write_queue is greater than 1,
            # assume that there's already another
            # sender task running
            return

        while len(self.write_queue):
            gatt_char_uuid, value, write_type = self.write_queue[0]
            try:
                await self.conn.write_gatt_char(gatt_char_uuid, value, write_type == GattCharWriteType.WITH_RESPONSE)
                self.write_queue.popleft()
            except Exception as e:
                print(e)

    def _write_gatt_char(self, context, caller, write_type, ptr_gattchar, value, length):
        gatt_char_uuid = _gattchar_to_string(ptr_gattchar.contents)
        buffer = [value[i] for i in range(0, length)]

        self.write_queue.append([gatt_char_uuid, buffer, write_type])

        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(self._write_char_asyncio(), loop)

    def _enable_notifications(self, context, caller, ptr_gattchar, handler, ready):
        uuid = _gattchar_to_string(ptr_gattchar.contents)
        loop = asyncio.get_event_loop()
        asyncio.run_coroutine_threadsafe(
            self._enable_notifications_asyncio(caller, uuid, handler, ready),
            loop,
        )

    async def _enable_notifications_asyncio(self, caller, uuid, handler, ready):
        services = await self.conn.get_services()
        gatt_char = services.get_characteristic(uuid)

        if (gatt_char == None):
            ready(caller, Const.STATUS_ERROR_ENABLE_NOTIFY)
        else:
            try:
                await self.conn.start_notify(
                    gatt_char, lambda _uuid, value: handler(caller, cast(_array_to_buffer(value), POINTER(c_ubyte)), len(value)),
                )
                ready(caller, Const.STATUS_OK)
            except Exception as err:
                print(str(err))
                ready(caller, Const.STATUS_ERROR_ENABLE_NOTIFY)

    def _on_disconnect(self, context, caller, handler):
        def event_handler(_connection):
            # todo, check if this status is correct?
            # looks like this status value is being ignored, so maybe we can just set it to anything
            # https://github.com/mbientlab/MetaWear-SDK-Cpp/blob/c25b278a18fd2aff0fd9553aa5f5eca43e235e0a/src/metawear/impl/cpp/metawearboard.cpp#L503
            status = Const.STATUS_OK
            if (self.on_disconnect != None):
                self.on_disconnect(status)
            handler(caller, status)

        self.conn.set_disconnected_callback(event_handler)

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
