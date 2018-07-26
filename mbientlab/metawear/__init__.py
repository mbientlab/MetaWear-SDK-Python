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
    DataTypeId.CALIBRATION_STATE: lambda p: cast(p.contents.value, POINTER(CalibrationState)).contents
}
def parse_value(p_data):
    """
    Helper function to extract the value from a Data object.  If you are storing the values to be used at a later time, 
    call copy.deepcopy preserve the value.  You do not need to do this if the underlying type is a native type or a byte array
    @params:
        p_data      - Required  : Pointer to a Data object
    """
    if (p_data.contents.type_id in _value_parsers):
        return _value_parsers[p_data.contents.type_id](p_data)
    elif (p_data.contents.type_id == DataTypeId.SENSOR_ORIENTATION):
        return _value_parsers[DataTypeId.INT32](p_data)
    elif (p_data.contents.type_id == DataTypeId.BYTE_ARRAY):
        array_ptr= cast(p_data.contents.value, POINTER(c_ubyte * p_data.contents.length))
        return [array_ptr.contents[i] for i in range(0, p_data.contents.length)]
    else:
        raise RuntimeError('Unrecognized data type id: ' + str(p_data.contents.type_id))
