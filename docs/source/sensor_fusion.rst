.. highlight:: python

Sensor Fusion
=============
Sensor fusion software is a complete 9-axis fusion solution, which combines the measurements from 3-axis gyroscope, 3-axis geomagnetic sensor and a 3-axis accelerometer to provide a robust absolute orientation vector. The algorithm fuses the sensor raw data from three sensors in an intelligent way to improve each sensor’s output.

This includes algorithms for offset calibration of each sensor, monitoring of the calibration status and Kalman filter fusion to provide distortion-free and refined orientation vectors.

There are 5 outputs of sensor fusion:

 - Quaternion
 - Linear Acceleration
 - Rotation
 - Gravity
 - Robust Heading

The `sensor_fusion.h <https://mbientlab.com/docs/metawear/cpp/latest/sensor__fusion_8h.html>`_ header file interfaces with the sensor fusion algorithm 
running on MetaMotion boards.  When using the sensor fusion algorithm, it is important that you do not simultaneously use the 
Accelerometer, Gyro, and Magnetometer modules; the algorithm configures those sensors internally based on the selected fusion mode.

The Sensor fusion algorithm we use is from BOSCH and is hardcoded at 100Hz.

To activate the sensor fusion algorithm, first set the fusion mode and data ranges, then subscribe to and enable the desired output data, and finally, 
call `mbl_mw_sensor_fusion_start <https://mbientlab.com/docs/metawear/cpp/latest/sensor__fusion_8h.html#a941e51e4831b5a7a2426ecf328dddddf>`_.

Mode
----
The sensor fusion algorithm has 4 
`fusion modes <https://mbientlab.com/docs/metawear/cpp/latest/sensor__fusion_8h.html#ac5064d8edcb6ffa988f25f4f66e09c48>`_, listed in the below table:

======== ==========================================================================
Mode     Description                             
======== ==========================================================================
NDoF     Calculates absolute orientation from accelerometer, gyro, and magnetometer
IMUPlus  Calculates relative orientation in space from accelerometer and gyro data
Compass  Determines geographic direction from the Earth's magnetic field
M4G      Similar to IMUPlus except rotation is detected with the magnetometer
======== ==========================================================================

The sensor fusion algorithm provides raw acceleration, rotation, and magnetic field values along with quaternion values and Euler angles. 

Furthermore, the source of acceleration can be separated into gravity and linear acceleration and both values are also provided. Keep in mind that each sensor fusion mode has different sets of available data and produces it at different rates.

======== ====== ====== =====
Mode	 Acc	Gyro   Mag
======== ====== ====== =====
NDoF	 100Hz  100Hz  25Hz
IMUPlus	 100Hz  100Hz  N/A
Compass	 25Hz   N/A	   25Hz
M4G      50Hz   N/A    50Hz
======== ====== ====== =====

The mode is set with 
`mbl_mw_sensor_fusion_set_mode <https://mbientlab.com/docs/metawear/cpp/latest/sensor__fusion_8h.html#a138a2d52134dee3772f0df3f9a7d9098>`_ and written 
to the board by calling 
`mbl_mw_sensor_fusion_write_config <https://mbientlab.com/docs/metawear/cpp/latest/sensor__fusion_8h.html#a09bb5d96b305c0ee0cf57e2a37300295>`_.  Before 
writing the configuration, you can also set the acceleration and rotation ranges of the accelerometer and gyroscope respectively. 

::

    libmetawear.mbl_mw_sensor_fusion_set_mode(board, SensorFusionMode.NDOF)
    libmetawear.mbl_mw_sensor_fusion_set_acc_range(board, SensorFusionAccRange._4G)
    libmetawear.mbl_mw_sensor_fusion_set_gyro_range(board, SensorFusionGyroRange._2000DPS)
    libmetawear.mbl_mw_sensor_fusion_write_config(board)

NDOF
"""""
This is a fusion mode with 9 degrees of freedom where the fused absolute orientation data is calculated from accelerometer, gyroscope and the magnetometer. 

The advantages of combining all three sensors are a fast calculation, resulting in high output data rate, and high robustness from magnetic field distortions. 

IMUPlus 
"""""""""
In the IMU mode the relative orientation of the device in space is calculated from the accelerometer and gyroscope data. The calculation is fast (i.e. high output data rate).

Compass
""""""""
The COMPASS mode is intended to measure the magnetic earth field and calculate the geographic direction.

The measurement accuracy depends on the stability of the surrounding magnetic field (magnets can interfere with the magnetometer and provide false readings since the earth magnetic field is usually much smaller than the magnetic fields that occur around and inside electronic devices).

M4G 
"""""
The M4G mode is similar to the IMU mode, but instead of using the gyroscope signal to detect rotation, the changing orientation of the magnetometer in the magnetic field is used. 

Since the magnetometer has much lower power consumption than the gyroscope, this mode is less power consuming in comparison to the IMU mode. There are no drift effects in this mode which are inherent to the gyroscope.

However, as for compass mode, the measurement accuracy depends on the stability of the surrounding magnetic field. For this mode no magnetometer calibration is required and also not available.

Data
----
The sensor fusion algorithm provides raw acceleration, rotation, and magnetic field values along with quaternion values and Euler angles.  Furthermore, 
the source of acceleration can be separated into gravity and linear acceleration and both values are also provided.  Keep in mind that each sensor  
fusion mode has different sets of available data and produces it at different rates.

======== ===== ===== ====
Mode     Acc   Gyro  Mag                       
======== ===== ===== ====
NDoF     100Hz 100Hz 25Hz
IMUPlus  100Hz 100Hz N/A
Compass  25Hz  N/A   25Hz
M4G      50Hz  N/A   50Hz
======== ===== ===== ====

Also note that the units and type casting of the sensor fusion data is different for each type of data..

============== ======= ============================
Data           Units   Casted Data
============== ======= ============================
Acceleration    g      MblMwCorrectedCartesianFloat
Rotation       deg/s   MblMwCorrectedCartesianFloat
Magnetic Field uT      MblMwCorrectedCartesianFloat
Quaternion      None   MblMwQuaternion
Euler Angles   degrees MblMwEulerAngles
Linear Acc      g      MblMwCartesianFloat
Gravity         g      MblMwCartesianFloat
============== ======= ============================

::

    def data_handler(self, ctx, data):
        print("%s -> %s" % (self.device.address, parse_value(data)))

    callback = FnVoid_VoidP_DataP(data_handler)

    libmetawear.mbl_mw_sensor_fusion_set_mode(board, SensorFusionMode.NDOF);
    libmetawear.mbl_mw_sensor_fusion_set_acc_range(board, SensorFusionAccRange._8G)
    libmetawear.mbl_mw_sensor_fusion_set_gyro_range(board, SensorFusionGyroRange._2000DPS)
    libmetawear.mbl_mw_sensor_fusion_write_config(board)

    signal = libmetawear.mbl_mw_sensor_fusion_get_data_signal(board, SensorFusionData.QUATERNION);
    libmetawear.mbl_mw_datasignal_subscribe(signal, None, callback)

    libmetawear.mbl_mw_sensor_fusion_enable_data(board, SensorFusionData.QUATERNION);
    libmetawear.mbl_mw_sensor_fusion_start(board);

    sleep(10.0) # TIME PASSES

    libmetawear.mbl_mw_sensor_fusion_stop(board);

    signal = libmetawear.mbl_mw_sensor_fusion_get_data_signal(board, SensorFusionData.QUATERNION);
    libmetawear.mbl_mw_datasignal_unsubscribe(signal)
    libmetawear.mbl_mw_debug_disconnect(board)