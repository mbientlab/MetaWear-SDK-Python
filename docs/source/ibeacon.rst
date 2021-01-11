.. highlight:: python

iBeacon
=======
iBeacon is a protocol developed by Apple. The main purpose of Beacons (which are simply Bluetooth advertisers - not connectable) is for location-data and proximity marketing. 

The MetaWear firmware supports the iBeacon format and can advertise itself as an iBeacon.  

To enable iBeacon mode, all you need to do is call 
`mbl_mw_ibeacon_enable <https://mbientlab.com/docs/metawear/cpp/latest/ibeacon_8h.html#a29227024839d419f2d536b6b3cc42481>`_ and disconnect from the 
board.  

The other functions in the `ibeacon.h <https://mbientlab.com/docs/metawear/cpp/latest/ibeacon_8h.html>`_ header file configure the 
advertisement parameters. ::

    libmetawear.mbl_mw_ibeacon_set_minor(board, 7453);
    libmetawear.mbl_mw_ibeacon_set_period(board, 15027);
    libmetawear.mbl_mw_ibeacon_set_rx_power(board, -55);
    libmetawear.mbl_mw_ibeacon_set_tx_power(board, -12);

    bytes = uuid.UUID('{326a9006-85cb-9195-d9dd-464cfbbae75a}').bytes[::-1]
    ad_uuid = cast(bytes, POINTER(c_ubyte * 16))
    
    libmetawear.mbl_mw_ibeacon_set_uuid(board, ad_uuid.contents)

    libmetawear.mbl_mw_ibeacon_enable(board);
