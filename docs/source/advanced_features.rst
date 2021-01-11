.. highlight:: cpp

Advanced Features 
=================
There are a few advanced features available on the MetaWear board described in this section.

High Frequency Streaming
------------------------
Some developers may want to stream data from multiple motion sensors simultaneously or individually at frequencies higher than 100Hz.  

To accommodate this use case, acceleration, angular velocity, and magnetic field data have a packed output mode that combines 3 data samples into 1 ble packet increasing the data throughput by 3x.

::

    mbl_mw_acc_set_odr(board, 200.0f);
    mbl_mw_acc_set_range(board, 4.0f);
    mbl_mw_acc_write_acceleration_config(board);

    auto packed = mbl_mw_acc_get_packed_acceleration_data_signal(board);
    mbl_mw_datasignal_subscribe(packed, [](const MblMwData* data) {
        auto value = (MblMwCartesianFloat*) data->value;
        printf("{x: %.3f, y: %.3f, z: %.3f}\n", value->x, value->y, value->z);
    });

    mbl_mw_acc_enable_acceleration_sampling(board);
    mbl_mw_acc_start(board);

In addition to using packed output, developers will also need to reduce the max connection interval to 7.5ms.  Reducing the max connection interval can 
also be used to speed up log downloads.  ::

    mbl_mw_settings_set_connection_parameters(board, 7.5f, 7.5f, 0, 6000);
    
Don't forget the connection parameters can be rejected.

Serialization
-------------
The internal state of the 
`MblMwMetaWearBoard <https://mbientlab.com/docs/metawear/cpp/latest/metawearboard__fwd_8h.html#a2c238febd06fcaaa403e937489a12652>`_ object can be 
converted into a byte array, which can then be saved to the disk.  

You will need to free the allocated memory after you are done using the byte array.  ::

    uint32_t size;
    uint8_t* state = mbl_mw_metawearboard_serialize(board, &size);
    
    for (uint32_t i = 0; i < size; i++) {
        // write content to a stream
    }

    mbl_mw_memory_free(state);

To restore the board state, pass the byte array into mbl_mw_metawearboard_deserialize.  You must still call 
`mbl_mw_metawearboard_initialize <https://mbientlab.com/docs/metawear/cpp/latest/metawearboard_8h.html#a079fea07f792de97a34c481a31e43101>`_ after 
deserializing the state.  ::

    uint8_t* state;
    uint32_t state_size;

    // assign state and state_size

    mbl_mw_metawearboard_deserialize(board, state, sizeof(state));
    mbl_mw_metawearboard_initialize(board, [](MblMwMetaWearBoard* board, int32_t status) -> void {
        
    });

Anonymous Signals
------------------
Anonymous data signals are a variant of the `Logger <https://mbientlab.com/cppdocs/latest/mblmwlogger.html>`_ type used to retrieve logged data from a board that was not programmed by the current host device.  

For example, a linux device was used to start a log of accelerometer data at 20Hz on a MetaWear board and an Android device is expected to download it from that board at a later time (the Android device therefore does not know about which loggers are running).

Use `mbl_mw_metawearboard_create_anonymous_datasignals <https://mbientlab.com/docs/metawear/cpp/0/metawearboard_8h.html#a218adea4ebd0df4061940325964488b5>`_ to sync the host device with the board's current logger state.  

If the function fails, a null pointer will be returned and the uint32_t parameter instead corresponds to a status code from the SDK.

Because of the anonymous nature of the object, users will need to rely on an identifier string to determine what kind of data is being passed to each 
route.  Generate the identifier string by calling `mbl_mw_logger_generate_identifier <https://mbientlab.com/docs/metawear/cpp/0/logging_8h.html#a86d098570698a184ee93087a6ffc00bb>`_ for each 
``MblMwDataLogger`` type and match these values with `mbl_mw_anonymous_datasignal_get_identifier <https://mbientlab.com/docs/metawear/cpp/0/anonymous__datasignal_8h.html#a253a854d9b326efc501df320284a6ae6>`_.  ::

    #include "metawear/core/datasignal.h"
    #include "metawear/core/logging.h"
    #include "metawear/platform/memory.h"
    #include "metawear/sensor/gyro_bmi160.h"

    void identifier_demo(MblMwMetaWearBoard* board) {
        auto gyro = mbl_mw_gyro_bmi160_get_rotation_data_signal(board);
        auto gyro_y = mbl_mw_datasignal_get_component(gyro, MBL_MW_GYRO_ROTATION_Y_AXIS_INDEX);
        mbl_mw_datasignal_log(gyro_y, [](MblMwDataLogger* logger) -> void {
            char* identifier = mbl_mw_logger_generate_identifier(logger);
            cout << "gyro_y identifier = " << identifier << endl;
            mbl_mw_memory_free(identifier);
        });
    }

A quick example:

::

    #include "metawear/core/anonymous_datasignal.h"

    // Use mbl_mw_metawearboard_create_anonymous_datasignals to retrieve log data from 
    // another device
    void anonymous_signal_demo(MblMwMetaWearboard* board) {
        mbl_mw_metawearboard_create_anonymous_datasignals(board, [](MblMwMetaWearBoard* board, 
                MblMwAnonymousDataSignal** anonymous_signals, uint32_t size) {
            if (anonymous_signals == nullptr) {
                cerr << "Failed to create anonymous signals, status = " << (int32_t) size << endl;
                return;
            }
            for (uint32_t i = 0; i < size; i++) {
                char* identifier = mbl_mw_anonymous_datasignal_get_identifier(anonymous_signals[i]);

                // identifier earlier extracted from calling
                // mbl_mw_logger_generate_identifier, use in if-else statements to identify
                // which anonymous signal represents gyro y-axis data
                if (!strcmp(identifier, "angular-velocity[1]")) {
                    mbl_mw_anonymous_datasignal_subscribe(anonymous_signals[i], [](const MblMwData* data) {
                        printf("gyro y-axis: %.3f", *((float*) data->value));
                    });
                }

                mbl_mw_memory_free(identifier);
            }
        });
    }

:: 

    device.createAnonymousDatasignals().continueOnSuccessWith(device.apiAccessExecutor) { signals in
        var states: [State] = []
        signals.forEach {
            let cString = mbl_mw_anonymous_datasignal_get_identifier($0)!
            let identifier = String(cString: cString)
            if let config = configs.first(where: { $0.isConfigForAnonymousEventName(identifier) }) {
                let state = State(sensor: config, device: device, isStreaming: false)
                states.append(state)
                mbl_mw_anonymous_datasignal_subscribe($0, bridgeRetained(obj: state), state.handler)
            }
        }
        return states
    }

As the C++ SDK does not yet support all available data sources, you will not be able to use this SDK to sync data from the accelerometer's detection 
algorithms except the BMI160's step and BMI160/BMA255 orientation detectors.
