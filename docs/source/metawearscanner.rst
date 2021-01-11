.. highlight:: python

MetaWear Scanner
================
The python API uses `PyWarble <https://github.com/mbientlab/PyWarble>`_ to scan for nearby devices. ::

    from mbientlab.warble import *
    from time import sleep

    def scan_result_printer(result):
        print("mac: %s" % result.mac)
        print("name: %s" % result.name)
        print("rssi: %ddBm" % result.rssi)

        print("metawear service? %d" % result.has_service_uuid("326a9000-85cb-9195-d9dd-464cfbbae75a"))
    
        data = result.get_manufacturer_data(0x626d)
        if data != None:
            print("mbientlab manufacturer data? ")
            print("    value: [%s]" % (', '.join([("0x%02x" % d) for d in data])))
        else:
            print("mbientlab manufacturer data? false")
        print("======")
    
    BleScanner.set_handler(scan_result_printer)

    print("-- active scan --")
    BleScanner.start()
    sleep(5.0)
    BleScanner.stop()

    print("-- passive scan --")
    BleScanner.start(**{'scan_type': 'passive'})
    sleep(5.0)
    BleScanner.stop()

Scanning for MetaWears
----------------------
It's simple to start scanning for advertising MetaWear devices using the `BleScanner <https://github.com/mbientlab/PyWarble/blob/master/mbientlab/warble/scanner.py>`_:

::

    selection = -1
    devices = None

    while selection == -1:
        print("scanning for devices...")
        devices = {}
        def handler(result):
            devices[result.mac] = result.name

        BleScanner.set_handler(handler)
        BleScanner.start()

        sleep(10.0)
        BleScanner.stop()

        i = 0
        for address, name in six.iteritems(devices):
            print("[%d] %s (%s)" % (i, address, name))
            i+= 1

        msg = "Select your device (-1 to rescan): "
        selection = int(raw_input(msg) if platform.python_version_tuple()[0] == '2' else input(msg))

        address = list(devices)[selection]
    print("Connecting to %s..." % (address))
    device = MetaWear(address)
    device.connect()