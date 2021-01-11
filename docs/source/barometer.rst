.. highlight:: python

Barometer
=========
A barometer is a scientific instrument that is used to measure air pressure in a certain environment. The absolute barometric pressure sensor can measure pressure from 300 Pascal to 1100 hPa.

MetaWear RPro and Cpro, MMR, MMC, MTR, and MetaEnvironment boards come with a Bosch barometer.  

The specific barometer model varies between the boards although both barometers are nearly identical save for a few settings.  Bosch barometer functions are defined in the 
`barometer_bosch.h <https://mbientlab.com/docs/metawear/cpp/latest/barometer__bosch_8h.html>`_ header file where functions containing ``baro_bosch`` 
are barometer agnostic where as functions with ``baro_bmp280`` and ``baro_bme280`` are for those specific barometers. 

Users can programatically determine which barometer is on their board with the 
`mbl_mw_metawearboard_lookup_module <https://mbientlab.com/docs/metawear/cpp/latest/metawearboard_8h.html#ad9c7e7f60f77fc1e929ac48c6a3ffb9b>`_ function. ::

    gyroType = mbl_mw_metawearboard_lookup_module(board, MBL_MW_MODULE_BAROMETER)
    switch gyroType {
        case MODULE_BARO_TYPE_BMP280:
            break
        case MODULE_BARO_TYPE_BME280:
            break
        case MODULE_TYPE_NA:
            break
        default:
            break
    }

Sensor Configuration
--------------------
The Bosch barometers have 3 configurable parameters: 

* Oversampling
* Infinite impulse filter (iir) coefficient
* Standby time

These operational parameters work in conjunction to control the noise, output resolution, and sampling rate.  When you are done setting the configuration, 
call `mbl_mw_baro_bosch_write_config <https://mbientlab.com/docs/metawear/cpp/latest/barometer__bosch_8h.html#ac763f27505e504d7c7ebd37c7bc98aa6>`_ to 
write the changes to the sensor. ::

    # Set oversampling to low power mode
    libmetawear.mbl_mw_baro_bosch_set_oversampling(board, BaroBoschOversampling.LOW_POWER)
    
    # Set standby time to 500ms
    libmetawear.mbl_mw_baro_bmp280_set_standby_time(board, BaroBmp280StandbyTime._500ms)
    
    # Set iir filter coefficient
    libmetawear.mbl_mw_baro_bosch_set_iir_filter(board, BaroBoschIirFilter.AVG_16)
    
    # Write configuration to the sensor
    libmetawear.mbl_mw_baro_bosch_write_config(board)

Pressure Sampling
-----------------
Pressure data is represented as a float and is in units of Pascals.   To receive pressure data, simply subscribe or log the pressure data signal and 
then start the sensor. ::

    pa_data_signal = libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(board)
    libmetawear.mbl_mw_datasignal_subscribe(pa_data_signal, None, sensor_data_handler)

Altitude Sampling
-----------------
Altitude data is represented as a float and is in units of meters.  To receive altitude data, simply subscribe or log the altitude data signal and then 
start the sensor. :: 

    def sensorDataHandler(self, context, data):
        data_ptr= cast(data.contents.value, POINTER(CartesianFloat))
        self.data_cartesian_float= copy.deepcopy(data_ptr.contents)
        self.data = self.data_cartesian_float

    sensor_data_handler= FnVoid_VoidP_DataP(self.sensorDataHandler)

    libmetawear.mbl_mw_baro_bosch_set_oversampling(board, BaroBoschOversampling.LOW_POWER)
    libmetawear.mbl_mw_baro_bmp280_set_standby_time(board, BaroBmp280StandbyTime._500ms)
    libmetawear.mbl_mw_baro_bosch_set_iir_filter(board, BaroBoschIirFilter.AVG_16)
    libmetawear.mbl_mw_baro_bosch_write_config(board)
        
    m_data_signal= self.libmetawear.mbl_mw_baro_bosch_get_altitude_data_signal(board)
    libmetawear.mbl_mw_datasignal_subscribe(m_data_signal, None, sensor_data_handler)
    libmetawear.mbl_mw_baro_bosch_start(board)