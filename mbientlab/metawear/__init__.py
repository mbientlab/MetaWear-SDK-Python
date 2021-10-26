from .cbindings import *
from ctypes import CDLL

import os
import platform

if (platform.system() == 'Windows'):
    _so_path = os.path.join(os.path.dirname(__file__), 'MetaWear.Win32.dll')
elif (platform.system() == 'Linux'):
    _so_path = os.path.join(os.path.dirname(__file__), 'libmetawear.so')
else:
    raise RuntimeError("MetaWear Python SDK is not supported for '%s'" % platform.system())

libmetawear= CDLL(_so_path)
init_libmetawear(libmetawear)

from .metawear import MetaWear
from .metawear import MetaWearUSB

_value_parsers = {
    DataTypeId.UINT32: lambda p: cast(p.contents.value, POINTER(c_uint)).contents.value,
    DataTypeId.INT32: lambda p: cast(p.contents.value, POINTER(c_int)).contents.value,
    DataTypeId.FLOAT: lambda p: cast(p.contents.value, POINTER(c_float)).contents.value,
    DataTypeId.CARTESIAN_FLOAT: lambda p: cast(p.contents.value, POINTER(CartesianFloat)).contents,
    DataTypeId.BATTERY_STATE: lambda p: cast(p.contents.value, POINTER(BatteryState)).contents,
    DataTypeId.TCS34725_ADC: lambda p: cast(p.contents.value, POINTER(Tcs34725ColorAdc)).contents,
    DataTypeId.EULER_ANGLE: lambda p: cast(p.contents.value, POINTER(EulerAngles)).contents,
    DataTypeId.QUATERNION: lambda p: cast(p.contents.value, POINTER(Quaternion)).contents,
    DataTypeId.CORRECTED_CARTESIAN_FLOAT: lambda p: cast(p.contents.value, POINTER(CorrectedCartesianFloat)).contents,
    DataTypeId.OVERFLOW_STATE: lambda p: cast(p.contents.value, POINTER(OverflowState)).contents,
    DataTypeId.LOGGING_TIME: lambda p: cast(p.contents.value, POINTER(LoggingTime)).contents,
    DataTypeId.BTLE_ADDRESS: lambda p: cast(p.contents.value, POINTER(BtleAddress)).contents,
    DataTypeId.BOSCH_ANY_MOTION: lambda p: cast(p.contents.value, POINTER(BoschAnyMotion)).contents,
    DataTypeId.CALIBRATION_STATE: lambda p: cast(p.contents.value, POINTER(CalibrationState)).contents,
    DataTypeId.BOSCH_TAP: lambda p: cast(p.contents.value, POINTER(BoschTap)).contents
}
def parse_value(pointer, **kwargs):
    """
    Helper function to extract the value from a Data object.  If you are storing the values to be used at a later time, 
    call copy.deepcopy preserve the value.  You do not need to do this if the underlying type is a native type or a byte array
    @params:
        pointer     - Required  : Pointer to a Data object
        n_elem      - Optional  : Nummber of elements in the value array if the type_id attribute is DataTypeId.DATA_ARRAY
    """
    if (pointer.contents.type_id in _value_parsers):
        return _value_parsers[pointer.contents.type_id](pointer)
    elif (pointer.contents.type_id == DataTypeId.SENSOR_ORIENTATION):
        return _value_parsers[DataTypeId.INT32](pointer)
    elif (pointer.contents.type_id == DataTypeId.BYTE_ARRAY):
        array_ptr= cast(pointer.contents.value, POINTER(c_ubyte * pointer.contents.length))
        return [array_ptr.contents[i] for i in range(0, pointer.contents.length)]
    elif (pointer.contents.type_id == DataTypeId.DATA_ARRAY):
        if 'n_elem' in kwargs:
            values = cast(pointer.contents.value, POINTER(POINTER(Data) * kwargs['n_elem']))
            return [parse_value(values.contents[i]) for i in range(0, kwargs['n_elem'])]
        else:
            raise RuntimeError("Missing optional parameter 'n_elem' for parsing DataTypeId.DATA_ARRAY value")
    else:
        raise RuntimeError('Unrecognized data type id: ' + str(pointer.contents.type_id))

from threading import Event

def create_voidp(fn, **kwargs):
    """
    Helper function that converts a libmetawear FnVoid_VoidP_VoidP async functions into a synchronous one
    @params:
        fn          - Required  : `(FnVoid_VoidP_VoidP) -> void` function that wraps the call to a libmetawear FnVoid_VoidP_VoidP async function
        resource    - Optional  : Name of the resource the fn is attempting to create
        event       - Optional  : Event object used to block until completion.  If not provided, the function will instantiate its own Event object
    """
    e = kwargs['event'] if 'event' in kwargs else Event()

    result = [None]
    def handler(ctx, pointer):
        result[0] = RuntimeError("Could not create " + (kwargs['resource'] if 'resource' in kwarg else "resource") ) if pointer == None else pointer
        e.set()

    callback_wrapper = FnVoid_VoidP_VoidP(handler)
    fn(callback_wrapper)
    e.wait()

    e.clear()
    if (result[0] is RuntimeError):
        raise result[0]
    return result[0]

def create_voidp_int(fn, **kwargs):
    """
    Helper function that converts a libmetawear FnVoid_VoidP_VoidP_Int async function into a synchronous one
    @params:
        fn          - Required  : `(FnVoid_VoidP_VoidP_Int) -> void` function that wraps the call to a libmetawear FnVoid_VoidP_VoidP_Int async function
        resource    - Optional  : Name of the resource the fn is attempting to create
        event       - Optional  : Event object used to block until completion.  If not provided, the function will instantiate its own Event object
        is_error    - Optional  : `(int) -> bool` function used to check if the async function failed, checks if the int value is equal to Const.STATUS_OK if not specified
    """
    e = kwargs['event'] if 'event' in kwargs else Event()

    result = [None]
    def handler(ctx, pointer, status):
        is_error = kwargs['is_error'] if 'is_error' in kwargs else lambda v: v != Const.STATUS_OK
        if (is_error(status)):
            result[0] = RuntimeError("Non-zero status returned (%d)" % (status))
        e.set()

    callback_wrapper = FnVoid_VoidP_VoidP_Int(handler)
    fn(callback_wrapper)
    e.wait()

    e.clear()
    if (result[0] is RuntimeError):
        raise result[0]

