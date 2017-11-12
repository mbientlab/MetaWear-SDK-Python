from ctypes import *
from distutils.version import LooseVersion
from gattlib import GATTRequester, GATTResponse
from threading import Event
from .cbindings import *

import copy
import errno
import json
import os
import requests
import sys
import time
import uuid

if sys.version_info[0] == 2:
    range = xrange

so_path = os.path.join(os.path.dirname(__file__), 'libmetawear.so')
libmetawear= CDLL(so_path)
init_libmetawear(libmetawear)

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

def parse_value(p_data):
    """
    Helper function to extract the value from a Data object.  If you are storing the values to be used at a later time, 
    call copy.deepcopy preserve the value.  You do not need to do this if the underlying type is a native type or a byte array
    @params:
        p_data      - Required  : Pointer to a Data object
    """
    if (p_data.contents.type_id == DataTypeId.UINT32):
        return cast(p_data.contents.value, POINTER(c_uint)).contents.value
    elif (p_data.contents.type_id == DataTypeId.INT32 or p_data.contents.type_id == DataTypeId.SENSOR_ORIENTATION):
        return cast(p_data.contents.value, POINTER(c_int)).contents.value
    elif (p_data.contents.type_id == DataTypeId.FLOAT):
        return cast(p_data.contents.value, POINTER(c_float)).contents.value
    elif (p_data.contents.type_id == DataTypeId.CARTESIAN_FLOAT):
        return cast(p_data.contents.value, POINTER(CartesianFloat)).contents
    elif (p_data.contents.type_id == DataTypeId.BATTERY_STATE):
        return cast(p_data.contents.value, POINTER(BatteryState)).contents
    elif (p_data.contents.type_id == DataTypeId.BYTE_ARRAY):
        p_data_ptr= cast(p_data.contents.value, POINTER(c_ubyte * p_data.contents.length))

        byte_array= []
        for i in range(0, p_data.contents.length):
            byte_array.append(p_data_ptr.contents[i])
        return byte_array
    elif (p_data.contents.type_id == DataTypeId.TCS34725_ADC):
        return cast(p_data.contents.value, POINTER(Tcs34725ColorAdc)).contents
    elif (p_data.contents.type_id == DataTypeId.EULER_ANGLE):
        return cast(p_data.contents.value, POINTER(EulerAngles)).contents
    elif (p_data.contents.type_id == DataTypeId.QUATERNION):
        return cast(p_data.contents.value, POINTER(Quaternion)).contents
    elif (p_data.contents.type_id == DataTypeId.CORRECTED_CARTESIAN_FLOAT):
        return cast(p_data.contents.value, POINTER(CorrectedCartesianFloat)).contents
    elif (p_data.contents.type_id == DataTypeId.OVERFLOW_STATE):
        return cast(p_data.contents.value, POINTER(OverflowState)).contents
    else:
        raise RuntimeError('Unrecognized data type id: ' + str(p_data.contents.type_id))

class _PyBlueZGatt(GATTRequester):
    def __init__(self, address, device):
        GATTRequester.__init__(self, address, False, device)

        self.dc_handler = None
        self.notify_handlers = {}

    def on_notification(self, handle, data):
        stripped = data[3:len(data)]

        buffer = create_string_buffer(stripped, len(stripped))
        handler = self.notify_handlers[handle];
        handler[1](handler[0], cast(buffer, POINTER(c_ubyte)), len(buffer.raw))

class MetaWear(object):
    _METABOOT_SERVICE = uuid.UUID("00001530-1212-efde-1523-785feabcd123")

    @staticmethod
    def _convert(value):
        return value if sys.version_info[0] == 2 else value.encode('utf8')

    def __init__(self, address, **kwargs):
        """
        Creates a MetaWear object
        @params:
            address     - Required  : MAC address of the board to connect to e.g. E8:C9:8F:52:7B:07
            cache_path  - Optional  : Path the SDK uses for cached data, defaults to '.metawear' in the local directory
            device      - Optional  : hci device to use, defaults to 'hci0'
            deserialize - Optional  : Deserialize the cached C++ SDK state if available, defaults to true
        """
        self.info = {}

        self.address = address
        self.cache = kwargs['cache_path'] if ('cache_path' in kwargs) else ".metawear"
        self.gatt = _PyBlueZGatt(address, "hci0" if 'device' not in kwargs else kwargs['device'])
        self.response = GATTResponse()
        self.on_notification = self.gatt.on_notification

        self._write_fn= FnVoid_VoidP_GattCharWriteType_GattCharP_UByteP_UByte(self._write_gatt_char)
        self._read_fn= FnVoid_VoidP_GattCharP_FnIntVoidPtrArray(self._read_gatt_char)
        self._notify_fn = FnVoid_VoidP_GattCharP_FnIntVoidPtrArray_FnVoidVoidPtrInt(self._enable_notifications)
        self._disconnect_fn = FnVoid_VoidP_FnVoidVoidPtrInt(self._on_disconnect)
        self._btle_connection= BtleConnection(write_gatt_char = self._write_fn, read_gatt_char = self._read_fn, 
                enable_notifications = self._notify_fn, on_disconnect = self._disconnect_fn)

        self.board = libmetawear.mbl_mw_metawearboard_create(byref(self._btle_connection))

        if 'deserialize' not in kwargs or kwargs['deserialize']:
            self.deserialize()

        try:
            os.makedirs(self.cache)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    @property
    def in_metaboot_mode(self):
        """
        True if the board is in MetaBoot mode.  The only permitted operation for MetaBoot boards is to update the firmware
        """
        return str(MetaWear._METABOOT_SERVICE) in self.services

    def disconnect(self):
        """
        Disconnects from the MetaWear board
        """
        self.gatt.disconnect()

    def connect(self, **kwargs):
        """
        Connects to the MetaWear board and initializes the SDK.  You must first connect to the board before using 
        any of the SDK functions
        @params:
            serialize   - Optional  : Serialize and cached C++ SDK state after initializaion, defaults to true
        """
        self.gatt.connect(True, channel_type='random')

        self.services = set()
        for s in self.gatt.discover_primary():
            self.services.add(s['uuid'])

        self.characteristics = {}
        for c in self.gatt.discover_characteristics():
            self.characteristics[c['uuid']] = c['value_handle']

        if ('hardware' not in self.info):
            self.info['hardware'] = self.gatt.read_by_uuid("00002a27-0000-1000-8000-00805f9b34fb")[0]

        if ('manufacturer' not in self.info):
            self.info['manufacturer'] = self.gatt.read_by_uuid("00002a29-0000-1000-8000-00805f9b34fb")[0]

        if ('serial' not in self.info):
            self.info['serial'] = self.gatt.read_by_uuid("00002a25-0000-1000-8000-00805f9b34fb")[0]

        if ('model' not in self.info):
            self.info['model'] = self.gatt.read_by_uuid("00002a24-0000-1000-8000-00805f9b34fb")[0]

        if not self.in_metaboot_mode:
            init_event = Event()
            def init_handler(device, status):
                self.init_status = status
                init_event.set()

            init_handler_fn = FnVoid_VoidP_Int(init_handler)
            libmetawear.mbl_mw_metawearboard_initialize(self.board, init_handler_fn)
            init_event.wait()

            if self.init_status != Const.STATUS_OK:
                self.disconnect()
                raise RuntimeError("Error initializing the API (%d)" % (self.init_status))

            if 'serialize' not in kwargs or kwargs['serialize']:
                self.serialize()
        else:
            self.info['firmware'] = self.gatt.read_by_uuid("00002a26-0000-1000-8000-00805f9b34fb")[0]

    def _read_gatt_char(self, caller, ptr_gattchar, handler):
        uuid = _gattchar_to_string(ptr_gattchar.contents)
        raw = self.gatt.read_by_uuid(uuid)[0]

        if (('model' not in self.info) and uuid == "00002a24-0000-1000-8000-00805f9b34fb"):
            self.info['model'] = raw
        elif (uuid == "00002a26-0000-1000-8000-00805f9b34fb"):
            self.info['firmware'] = raw

        value = MetaWear._convert(raw)
        buffer = create_string_buffer(value, len(value))
        handler(caller, cast(buffer, POINTER(c_ubyte)), len(buffer.raw))

    def _write_gatt_char(self, caller, write_type, ptr_gattchar, value, length):
        buffer= []
        for i in range(0, length):
            buffer.append(value[i])

        handle = self.characteristics[_gattchar_to_string(ptr_gattchar.contents)]
        if (write_type == GattCharWriteType.WITH_RESPONSE):
            self.gatt.write_by_handle_async(handle, bytes(bytearray(buffer)), self.response)
        else:
            self.gatt.write_cmd_by_handle(handle, bytes(bytearray(buffer)))

    def _enable_notifications(self, caller, ptr_gattchar, handler, ready):
        handle = self.characteristics[_gattchar_to_string(ptr_gattchar.contents)]
        self.gatt.write_by_handle(handle + 1, b'\x01\x00')
        self.gatt.notify_handlers[handle] = [caller, handler];
        ready(caller, 0)

    def _on_disconnect(self, caller, handler):
        pass

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
                raw = (c_ubyte * len(content)).from_buffer_copy(bytearray(content["cpp_state"]))
                libmetawear.mbl_mw_metawearboard_deserialize(self.board, raw, len(content))
            return True

        return False

    def update_firmware_async(self, handler, **kwargs):
        """
        Updates the firmware on the device.  The function is asynchronous and will update the caller 
        with the result of the task via a two parameter callback function.  If the first parameter is set 
        with a BaseException object, then the task failed.
        @params:
            handler             - Required  : Callback function to handle the result of the task
            progress_handler    - Optional  : Callback function to handle progress updates
            version             - Optional  : Specific firmware version to update to, defaults to latest available version
        """
        if not self.in_metaboot_mode:
            libmetawear.mbl_mw_debug_jump_to_bootloader(self.board)
            time.sleep(10)

            self.disconnect()
            self.connect()
            if not self.in_metaboot_mode:
                raise RuntimeError("DFU service not found")

        self._dfu_handler = handler
        self._progress_handler = None if 'progress_handler' not in kwargs else kwargs['progress_handler']

        def print_dfu_start():
            pass

        self._on_successful = FnVoid(lambda: self._dfu_handler(None, None))
        self._on_transfer = FnVoid_Int(self._dfu_progress)
        self._on_started = FnVoid(print_dfu_start)
        self._on_cancelled = FnVoid(lambda: self._dfu_error("DFU operation cancelled"))
        self._on_error = FnVoid_charP(self._dfu_error)

        path = self._download_firmware() if 'version' not in kwargs else self._download_firmware(version = kwargs['version'])
        buffer = create_string_buffer(path.encode('ascii'))
        self._dfu_delegate = DfuDelegate(on_dfu_started = self._on_started, on_dfu_cancelled = self._on_cancelled, 
                on_transfer_percentage = self._on_transfer, on_successful_file_transferred = self._on_successful, on_error = self._on_error)
        libmetawear.mbl_mw_metawearboard_perform_dfu(self.board, byref(self._dfu_delegate), buffer.raw)

    def _dfu_error(self, msg):
        self._dfu_handler(RuntimeError(msg), None)
        
    def _dfu_progress(self, p):
        if self._progress_handler != None:
            self._progress_handler(p)
