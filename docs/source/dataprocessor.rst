.. highlight:: python

Data Processor Types
====================
Header files defining the data processors type are in the 
`processor <https://mbientlab.com/docs/metawear/cpp/latest/dir_ac375e5396e5f8152317e89ec5f046d1.html>`_ folder.  

.. list-table:: Data Processors
   :header-rows: 1

   * - #
     - Name
     - Description
   * - 1
     - Accounter
     - Adds additional information to the payload to facilitate packet reconstruction.
   * - 2
     - Accumulator
     - Tallies a running sum of the input.
   * - 3
     - Averager
     - Computes a running average of the input.
   * - 4
     - Buffer
     - Captures input data which can be retrieved at a later point in time.
   * - 5
     - Comparator
     - Only allows data through that satisfies a comparison operation.
   * - 6
     - Counter
     - Counts the number of times an event was fired.
   * - 7
     - Delta
     - Only allows data through that is a min distance from a reference value.
   * - 8
     - Fuser
     - Combine data from multiple data sources into 1 data packet.
   * - 9
     - Math
     - Performs arithmetic on sensor data.
   * - 10
     - Packer
     - Combines multiple data values into 1 BLE packet.
   * - 11
     - Passthrough
     - Gate that only allows data though based on a user configured internal state.
   * - 12
     - Pulse
     - Detects and quantifies a pulse over the input values.
   * - 13
     - RMS
     - Computes the root mean square of the input.
   * - 14
     - RSS
     - Computes the root sum square of the input.
   * - 15
     - Sample
     - Holds data until a certain amount has been collected.
   * - 16
     - Threshold
     - Allows data through that crosses a boundary.
   * - 17
     - Timer
     - Periodically allow data through.

The CPP APIs for the data processor are available in the file ``MblMwDataSignal+Async``.

To create a processor, call any functions that has ``create`` in its name.  ::

    libmetawear.mbl_mw_dataprocessor_comparator_create(pointer, ComparatorOperation.EQ, 1.0, context, comparator_odd_handler)
    libmetawear.mbl_mw_dataprocessor_counter_create(switch_signal, None, counter_handler)
    libmetawear.mbl_mw_dataprocessor_rss_create(accel_signal, None, rss_handler)

Here is a quick example: ::

    def processor_created(context, pointer):
        self.processor = pointer
        e.set()
    fn_wrapper = cbindings.FnVoid_VoidP_VoidP(processor_created)
        
    acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(self.device.board)
    libmetawear.mbl_mw_dataprocessor_average_create(acc, 4, None, fn_wrapper)

Input data signals that are marked with a `MblMwCartesianFloat <https://mbientlab.com/docs/metawear/cpp/latest/structMblMwCartesianFloat.html>`_ id, 
.i.e accelerometer, gyro, and magnetometer data, are limited to only using the :ref:`dataprocessor-math`, :ref:`dataprocessor-rms`, and 
:ref:`dataprocessor-rss` processors.  Once fed through an RMS or RSS processor however, they can utilize the rest of the data processing functions.

Accounter
---------
The accounter processor adds additional information to the BTLE packet to reconstruct the data's timestamp, typically used with streaming raw 
accelerometer, gyro, and magnetometer data.  

This processor is designed specifically for streaming, DO NOT use with the logger.  ::

    def processor_created(self, context, pointer):
        self.processors.append(pointer)
        self.e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)

    signal = self.libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_accounter_create(signal, None, processor_handler)
    e.wait()

Average
-------
The averager computes a running average over the over the inputs.  It will not produce any output until it has accumulated enough samples to match the specified sample size. 

There is no high level iOS API for the CPP ``mbl_mw_dataprocessor_averager_create`` function; so here is an example. ::
    
    def processor_created(self, context, pointer):
        self.processors.append(pointer)
        self.e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)

    baro_pa_signal = libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_average_create(self.baro_pa_signal, 8, None, processor_handler)
    e.wait()

Accumulator
-----------
The accumulator computes a running sum over the inputs.  Users can explicitly specify an output size (1 to 4 bytes) or 
let the API infer an appropriate size.  

The output data type id of an accumulator is the same as its input source. ::
        
    def dataprocessor_created(self, context, processor):
        self.created_proc= processor
        self.e.set()

    dataprocessor_created_fn= FnVoid_VoidP_VoidP(self.dataprocessor_created)

    signal = self.libmetawear.mbl_mw_switch_get_state_data_signal(self.board)
    libmetawear.mbl_mw_dataprocessor_accumulator_create(signal, None, dataprocessor_created_fn)
    e.wait()

Buffer
------
The buffer processor captures input data which can be read at a later time using 
`mbl_mw_datasignal_read <https://mbientlab.com/docs/metawear/cpp/latest/datasignal_8h.html#a0a456ad1b6d7e7abb157bdf2fc98f179>`_; no output is produced 
by this processor.  

The data type id of a buffer's state is the same as its input source. ::

    def accum_processor_created(context, acc):
        self.processors.append(acc)
        self.libmetawear.mbl_mw_dataprocessor_buffer_create(acc, context, buffer_handler)
    
    rms_handler = FnVoid_VoidP_VoidP(lambda ctx, p: self.libmetawear.mbl_mw_dataprocessor_accumulator_create_size(p, 4, ctx, accum_handler))
    buffer_handler = FnVoid_VoidP_VoidP(lambda ctx, p: e.set())

    accel_signal= self.libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_rms_create(accel_signal, None, rms_handler)
    e.wait()


Buffer processors can be used to capture data and retrieve it at a later time by reading its state.

Comparison
----------
The comparator removes data that does not satisfy the comparison operation.  Callers can force a signed or unsigned comparison, or let the API determine which is appropriate.  

The output data type id of comparator is the same as its input source. ::

    def comp_created(context, comp):
        self.e.set()

    ths_created = FnVoid_VoidP_VoidP(lambda ctx, t: libmetawear.mbl_mw_dataprocessor_comparator_create(t, ComparatorOperation.EQ, 1.0, ctx, comp_created))
    comp_created = FnVoid_VoidP_VoidP(comp_created)

    acc_y_signal = libmetawear.mbl_mw_datasignal_get_component(acc_signal, Const.ACC_ACCEL_Y_AXIS_INDEX)
    libmetawear.mbl_mw_dataprocessor_threshold_create(acc_y_signal, ThresholdMode.BINARY, 1.0, 0.0, None, ths_created)
    e.wait()

Multi-Value Comparison
^^^^^^^^^^^^^^^^^^^^^^
Starting from firmware v1.2.3, the comparator can accept multiple reference values to compare against and has additional operation modes that can 
modify output values and when outputs are produced.  The multi-value comparison filter is an extension of the comparison filter implemented on 
older firmware.

Operation modes are defined in the 
`MblMwComparatorOperation <https://mbientlab.com/docs/metawear/cpp/latest/comparator_8h.html#a021a5e13dd18fb4b5b2052bf547e5f54>`_ enum, copied below 
with a description on expected outputs:

===========  =====================================================================================================
Operation    Descripion
===========  =====================================================================================================
Absolute     Input value is returned when the comparison is satisfied, behavior of old comparator
Reference    The reference value is output when the comparison is satisfied
Zone         Outputs the index (0 based) of the reference value that satisfied the comparison, n if none are valid
Pass / Fail  0 if the comparison fails, 1 if it passed
===========  =====================================================================================================

Also note that you can only use one reference value when creating feedback/feedforward loops.  ::

    def processor_created(self, context, pointer):
        self.e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)

    references= (c_float * 4)(1024, 512, 256, 128)
    adc_signal = libmetawear.mbl_mw_gpio_get_analog_input_data_signal(board, 0x15, GpioAnalogReadMode.ADC)

    libmetawear.mbl_mw_dataprocessor_multi_comparator_create(adc_signal, ComparatorOperation.GTE, ComparatorMode.REFERENCE, references, len(references), None, processor_handler)
    e.wait()

Counter
-------
A counter keeps a tally of how many times it is called.  It can be used by 
`MblMwEvent <https://mbientlab.com/docs/metawear/cpp/latest/event__fwd_8h.html#a569b89edd88766619bb41a2471743695>`_ pointers to count the numbers of 
times a MetaWear event was fired and enable simple events to utilize the full set of firmware features.  

Counter data is only interpreted as an unsigned integer. ::

    def processor_created(self, context, pointer):
        self.e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)

    baro_pa_signal= libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_counter_create(baro_pa_signal, None, processor_handler)
    e.wait()

Delta
-----
A delta processor computes the difference between two successive data values and only allows data through that creates a difference greater in magnitude 
than the specified threshold.  

When creating a delta processor, users will also choose how the processor transforms the output which can, in some cases, alter the output data type id.  

=============  =======================================  ==============================================
Output         Transformation                           Data Type ID
=============  =======================================  ==============================================
Absolute       Input passed through untouched           Same as input source i.e. float -> float
Differential   Difference between current and previous  If input is unsigned int, output is signed int
Binary         1 if difference > 0, -1 if less than 0   Output is always signed int
=============  =======================================  ==============================================

Constants identifying the output modes are defined in the `MblMwDeltaMode <https://mbientlab.com/docs/metawear/cpp/latest/delta_8h.html#ac9e3bece74c3bafb355bb158cf93b843>`_ enum. ::

    def processor_created(self, context, pointer):
        self.e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)

    baro_pa_signal= libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_delta_create(baro_pa_signal, DeltaMode.DIFFERENTIAL, 25331.25, None, processor_handler)
    e.wait()

High Pass Filter
----------------
High pass filters compute the difference of the current value from a running average of the previous N samples.  

Output from this processor is delayed until the first N samples have been received.  ::

    def processor_created(self, context, pointer):
        self.e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)

    signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_highpass_create(signal, 4, None, processor_handler)
    e.wait()    

.. _dataprocessor-math:

Math
----
The math processor performs arithmetic or logical operations on the input.  Users can force signed or unsigned operation, or allow the API to determine which is appropriate.  

Depending on the operation, the output data type id can change.

========================    ====================================================
Operation                   Data Type ID
========================    ====================================================
Add, Sub, Mult, Div, Mod    If input is unsigned, output is signed
Sqrt, Abs                   If input is signed, output is unsigned
Const                       Output type id is the same as input type id
Remaining Ops               API cannot infer, up to user to reassemble the bytes
========================    ====================================================

Constants identifying the operations are defined in the 
`MblMwMathOperation <https://mbientlab.com/docs/metawear/cpp/latest/math_8h.html#acb93d624e6a4bdfcda9bac362197b232>`_ enum. ::

    def processor_created(self, context, pointer):
        self.e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)
    
    baro_pa_signal= libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_math_create(self.baro_pa_signal, MathOperation.DIVIDE, 1000.0, None, processor_handler)
    e.wait()

Like the comparator, the math processor also supports feedback/feedforward loops.  Using 
`mbl_mw_dataprocessor_math_modify_rhs_signal <https://mbientlab.com/docs/metawear/cpp/latest/math_8h.html#a7c7af2e8139e824b82c45b846b96abc6>`_, you can 
set the second operand with the output of another data signal.

Packer
------
The packer processor combines multiple data samples into 1 BLE packet to increase the data throughput.  You can pack between 4 to 8 samples per packet 
depending on the data size.

Note that if you use the packer processor with raw motion data instead of using their packed data producer variants, you will only be able to combine 2 
data samples into a packet instead of 3 samples however, you can chain an accounter processor to associate a timestamp with the packed data.  ::

    def processor_created(self, context, pointer):
        self.e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)
    
    acc = libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_packer_create(acc, 2, None, processor_handler)
    e.wait()


Passthrough
-----------
The passthrough processor is akin to a gate in which the user has manual control over, exercised by setting the processor's count value using  
`mbl_mw_dataprocessor_passthrough_set_count <https://mbientlab.com/docs/metawear/cpp/latest/passthrough_8h.html#a537a105294960629fd035adac1a5d65b>`_.  

It has three operation modes that each use the count value differently:

=========== ==========================================
Mode        Description
=========== ==========================================
All         Allow all data through
Conditional Only allow data through if the count > 0
Count       Only allow a set number of samples through
=========== ==========================================

Constants identifying the operation modes are defined in the 
`MblMwPassthroughMode <https://mbientlab.com/docs/metawear/cpp/latest/passthrough_8h.html#a3fdd23d48b54420240c112fa811a56dd>`_ enum. ::

    sample_handler = FnVoid_VoidP_VoidP(lambda ctx, p: self.libmetawear.mbl_mw_dataprocessor_passthrough_create(p, PassthroughMode.COUNT, 0, ctx, passthrough_handler))
    
    passthrough_handler = FnVoid_VoidP_VoidP(lambda ctx, p: e.set())

    gpio_adc_signal= libmetawear.mbl_mw_gpio_get_analog_input_data_signal(board, 0, GpioAnalogReadMode.ADC)
    libmetawear.mbl_mw_dataprocessor_sample_create(gpio_adc_signal, 16, None, sample_handler)
    e.wait()

Pulse
-----
The pulse processor detects and quantifies a pulse over a set of data.  

Pulses are defined as a minimum number of data points that rise above then fall below a threshold and quantified by transforming the collection of data into three different values:

========= ======================================== =================================
Output    Description                              Data Type ID
========= ======================================== =================================
Width     Number of samples that made up the pulse Unsigned integer
Area      Summation of all the data in the pulse   Same as input i.e. float -> float
Peak      Highest value in the pulse               Same as input i.e. float -> float
On Detect Return 0x1 as soon as pulse is detected  Unsigned integer
========= ======================================== =================================

Constants defining the different output modes are defined in the 
`MblMwPulseOutput <https://mbientlab.com/docs/metawear/cpp/latest/pulse_8h.html#abd7edcb82fd29ec984390673c60b4904>`_ enum. ::

    def sensorDataHandler(self, context, data):
        data_ptr= cast(data.contents.value, POINTER(CartesianFloat))
        self.data_cartesian_float= copy.deepcopy(data_ptr.contents)
        self.data = self.data_cartesian_float

    sensor_data_handler = FnVoid_VoidP_DataP(sensorDataHandler)

    def pulse_created(context, pulse):
        self.libmetawear.mbl_mw_datasignal_subscribe(pulse, None, sensor_data_handler)
        e.set()

    e = threading.Event()

    pulse_handler = FnVoid_VoidP_VoidP(pulse_created)

    acc_z_signal = libmetawear.mbl_mw_datasignal_get_component(acc_signal, Const.ACC_ACCEL_Z_AXIS_INDEX)
    libmetawear.mbl_mw_dataprocessor_pulse_create(acc_z_signal, PulseOutput.AREA, 1.0, 16, None, pulse_handler)
    e.wait()

.. _dataprocessor-rms:

RMS
---
The RMS processor computes the root mean square over multi component data i.e. XYZ values from acceleration data.  

The processor will convert `MblMwCartesianFloat <https://mbientlab.com/docs/metawear/cpp/latest/structMblMwCartesianFloat.html>`_ inputs into float outputs.  ::

    def processor_created(self, context, pointer):
        self.e.set()

    rms_handler = FnVoid_VoidP_VoidP(processor_created)

    accel_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_rms_create(accel_signal, None, rms_handler)
    e.wait()

.. _dataprocessor-rss:

RSS
---
The RSS processor computes the root sum square, or vector magnitude, over multi component data i.e. XYZ values from acceleration data.  

The processor will convert `MblMwCartesianFloat <https://mbientlab.com/docs/metawear/cpp/latest/structMblMwCartesianFloat.html>`_ inputs into float outputs.  ::

    def processor_created(self, context, pointer):
        self.e.set()

    rss_handler = FnVoid_VoidP_VoidP(processor_created)

    accel_signal = self.libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    libmetawear.mbl_mw_dataprocessor_rss_create(accel_signal, None, rss_handler)
    e.wait()

Sample
------
The sample processor acts like a bucket, only allowing data through once it has collected a set number of samples. It functions as a data historian of 
sorts providing a way to look at the data values prior to an event.  

The output data type id of an accumulator is the same as its input source. ::

    e = threading.Event()

    sample_handler= FnVoid_VoidP_VoidP(lambda ctx, p: self.libmetawear.mbl_mw_dataprocessor_passthrough_create(p, PassthroughMode.COUNT, 0, ctx, passthrough_handler))
    passthrough_handler = FnVoid_VoidP_VoidP(lambda ctx, p: e.set())

    gpio_adc_signal = libmetawear.mbl_mw_gpio_get_analog_input_data_signal(self.board, 0, GpioAnalogReadMode.ADC)
    libmetawear.mbl_mw_dataprocessor_sample_create(gpio_adc_signal, 16, None, sample_handler)
    e.wait()

Threshold
---------
The threshold processor only allows data through that crosses a boundary, either crossing above or below it.  

It has two output modes:

=============  ========================================== ==============================================
Output         Transformation                             Data Type ID
=============  ========================================== ==============================================
Absolute       Input passed through untouched             Same as input source i.e. float -> float
Binary         1 if value rose above, -1 if it fell below Output is always signed int
=============  ========================================== ==============================================

Constants identifying the output modes are defined by the 
`MblMwThresholdMode <https://mbientlab.com/docs/metawear/cpp/latest/threshold_8h.html#a63e1cc001aa56601099db511d3d3109c>`_ enum. ::

    def sensorDataHandler(self, context, data):
        data_ptr= cast(data.contents.value, POINTER(CartesianFloat))
        self.data_cartesian_float= copy.deepcopy(data_ptr.contents)
        self.data = self.data_cartesian_float

    def comp_created(context, comp):
        self.libmetawear.mbl_mw_datasignal_subscribe(comp, None, sensor_data_handler)
        e.set()

    sensor_data_handler = FnVoid_VoidP_DataP(sensorDataHandler)

    ths_created = FnVoid_VoidP_VoidP(lambda ctx, t: self.libmetawear.mbl_mw_dataprocessor_comparator_create(t, ComparatorOperation.EQ, 1.0, ctx, comp_created))
    comp_created = FnVoid_VoidP_VoidP(comp_created)

    acc_signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(board)
    acc_y_signal = libmetawear.mbl_mw_datasignal_get_component(acc_signal, Const.ACC_ACCEL_Y_AXIS_INDEX)
    libmetawear.mbl_mw_dataprocessor_threshold_create(acc_y_signal, ThresholdMode.BINARY, 1.0, 0.0, None, ths_created)
    e.wait()

Time
----
The time processor only allows data to pass at fixed intervals.  It can used to limit the rate at which data is received if your sensor does not have 
the desired sampling rate.  

The processor has two output modes:

=============  ======================================= ==============================================
Output         Transformation                          Data Type ID
=============  ======================================= ==============================================
Absolute       Input passed through untouched          Same as input source i.e. float -> float
Differential   Difference between current and previous If input is unsigned int, output is signed int
=============  ======================================= ==============================================

Constants identifying the the output modes are defined by the 
`MblMwTimeMode <https://mbientlab.com/docs/metawear/cpp/latest/time_8h.html#ac5166dcd417797f9bc13a5e388d9073c>`_. ::

    def processor_created(self, context, pointer):
        self.processors.append(pointer)
        e.set()

    processor_handler = FnVoid_VoidP_VoidP(processor_created)

    baro_pa_signal= libmetawear.mbl_mw_baro_bosch_get_pressure_data_signal(self.board)
    libmetawear.mbl_mw_dataprocessor_time_create(baro_pa_signal, TimeMode.DIFFERENTIAL, 1000, None, processor_handler)
    e.wait()