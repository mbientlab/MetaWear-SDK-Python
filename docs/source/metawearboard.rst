.. highlight:: python

MetaWear Board
==============
The `MetaWear <https://www.mbientlab.com/docs/metawear/ios/latest/Classes/MetaWear.html>`_ interface is a software representation of the MetaWear boards and is the central class of the MetaWear API.  It contains methods for connecting, disconnecting, saving and restoring state.

Bluetooth LE Connection
-----------------------
Before using any API features, you must first connect to the board with ``connect``.  ::

    from mbientlab.metawear import MetaWear
    from mbientlab.metawear.cbindings import *
    from mbientlab.warble import * 

    device = MetaWear(address)
    device.connect()

Conversely, call ``disconnect`` to close the connection.  ::

    device.disconnect()

Watching for Disconnects
^^^^^^^^^^^^^^^^^^^^^^^^
It is often useful to handle BLE disconnection events.  The MetaWear interface has a ``on_disconnect`` event.  ::

    d = MetaWear(address)
    d.connect()
    d.on_disconnect = lambda status: print("disconnected")

Saving MetaWears
-----------------
If you expect to re-connect to a specific MetaWear device, you should remember it.

::

    # for loop for the argv which is multiple MAC addresses of MetaWear devices
    for i in range(len(argv) - 1): 
        d = MetaWear(argv[i + 1])
        d.connect()
        print("Connected to " + d.address)
        states.append(State(d))

    for s in states:
        print("Configuring %s" % (s.device.address))
        s.setup()

    for s in states:
        print("Starting %s" % (s.device.address))
        s.start()

Connection State
----------------
Get the state of the SDK connection.

::

    d = MetaWear(address)
    d.connect()
    print((State(d)))

Identifier
----------
Apple generates a unique identifier for each BLE device.  Note, two different Apple devices will generate two different identifiers for the same MetaWear.  It might be useful to use ``device.address`` instead.

::

    print("Connected to " + d.address)

Reset
----------
To fully reset your MetaWear board:

::

    libmetawear.mbl_mw_debug_reset(d.board)
