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
