.. highlight:: python

Logger
======
The MetaWear board can log sensor data and store it in the internal memory of the device using ``loggers`` to be retrieved at a later time.

Loggers record data from a data signal and are represented by the 
`MblMwDataLogger <https://mbientlab.com/docs/metawear/cpp/0/logging__fwd_8h.html#a84a99b569b691df5017c03721645b49d>`_ struct.  

Create an 
``MblMwDataLogger`` object by calling 
`mbl_mw_datasignal_log <https://mbientlab.com/docs/metawear/cpp/latest/datasignal_8h.html#aa7ec82a61e31616ff2eaedb0a96160d8>`_ with the data signal 
you want to log.  

If successful, the callback function will be executed with a  
`MblMwDataLogger <https://mbientlab.com/docs/metawear/cpp/0/logging__fwd_8h.html#a84a99b569b691df5017c03721645b49d>`_ pointer and if creating the 
logger failed, a ``null`` pointer will be returned.  ::

    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(d.board)
    logger = create_voidp(lambda fn: libmetawear.mbl_mw_datasignal_log(signal, None, fn), resource = "acc_logger")

::

    def logger_ready(self, context, pointer):
        self.logger = pointer

    logger_created_fn= FnVoid_VoidP_VoidP(logger_ready)

    libmetawear.mbl_mw_datasignal_log(signal, None, logger_created_fn)

MblMwDataLogger objects only interact with the specific data signal, they do not control the logging features.  Logging control functions are detailed in the :doc:`logging` section.

ID
--
MblMwDataLogger objects are identified by a numerical id. 

This id can be used to keep track of loggers when there is considerable time between the start of a log and the download of a log. It is also useful to get the state of the device (i.e is my device still downloading?).

You can retrieve the id by calling 
`mbl_mw_logger_get_id <https://mbientlab.com/docs/metawear/cpp/0/logging_8h.html#ab32e4ae06e057cbb0180558ef8ec8165>`_.  

The id is used to retrieve existing loggers from the API with the 
`mbl_mw_logger_lookup_id <https://mbientlab.com/docs/metawear/cpp/0/logging_8h.html#a1b95ca107021c1e8f6ddaef0fbc85c4b>`_ function. ::

    sensor_data_handler= FnVoid_VoidP_DataP(sensorDataHandler)

    logger = libmetawear.mbl_mw_logger_lookup_id(board, 0)
    libmetawear.mbl_mw_logger_subscribe(logger, None, sensor_data_handler)

Handling Data
-------------
Like a data signal, you can subscribe to an MblMwDataLogger to process the downloaded data.  

Call `mbl_mw_logger_subscribe <https://mbientlab.com/docs/metawear/cpp/0/logging_8h.html#ac1fa6f2a678f61d86ccc80b092e8c098>`_ to attach a callback 
function to the MblMwDataLogger which handles all received data.  

There is a helper function from the SDK CPP called sensorDataHandler() which you can use (found in `common.py <https://github.com/mbientlab/MetaWear-SDK-Cpp/blob/master/test/common.py>`_). ::

    def sensorDataHandler(self, context, data): // See full definition in common.py
        if (data.contents.type_id == DataTypeId.UINT32):
            data_ptr= cast(data.contents.value, POINTER(c_uint))
            self.data_uint32= c_uint()
            self.data_uint32.value= data_ptr.contents.value
            self.data = self.data_uint32
        elif (data.contents.type_id == DataTypeId.INT32 or data.contents.type_id == DataTypeId.SENSOR_ORIENTATION):
            data_ptr= cast(data.contents.value, POINTER(c_int))
            self.data_int32= c_int()
            self.data_int32.value= data_ptr.contents.value
            self.data = self.data_int32
        elif (data.contents.type_id == DataTypeId.FLOAT):
            data_ptr= cast(data.contents.value, POINTER(c_float))
            self.data_float= c_float()
            self.data_float.value= data_ptr.contents.value
            self.data = self.data_float
        elif (data.contents.type_id == DataTypeId.CARTESIAN_FLOAT):
            data_ptr= cast(data.contents.value, POINTER(CartesianFloat))
            self.data_cartesian_float= copy.deepcopy(data_ptr.contents)
            self.data = self.data_cartesian_float
        elif (data.contents.type_id == DataTypeId.QUATERNION):
            data_ptr= cast(data.contents.value, POINTER(Quaternion))
            self.data= copy.deepcopy(data_ptr.contents)
        else:
            raise RuntimeError('Unrecognized data type id: ' + str(data.contents.type_id))

There is also a helper function called `parse_value <https://github.com/mbientlab/MetaWear-SDK-Python/blob/master/mbientlab/metawear/__init__.py>`_ which will handle the data types for you as part of the MetaWear class: ::

    callback = FnVoid_VoidP_DataP(lambda ctx, p: print("{epoch: %d, value: %s}" % (p.contents.epoch, parse_value(p))))
    libmetawear.mbl_mw_logger_subscribe(logger, None, callback)

::

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

Removal
-------
When you no longer want to log the values from a data signal, call 
`mbl_mw_logger_remove <https://mbientlab.com/docs/metawear/cpp/0/logging_8h.html#a8877b9a3f6c8571c41c21cda4a9c90cb>`_ to remove the logger.  ::

    mbl_mw_logger_remove(logger)
