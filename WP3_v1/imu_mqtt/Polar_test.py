import asyncio
from bleak import BleakScanner, BleakClient
import struct
import logging
from multiprocessing import Queue

# UUIDs for Heart Rate Service and Measurement Characteristic
HR_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT_CHAR_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

def parse_heart_rate(data):
    """
    Parses the heart rate and RR interval data according to the Bluetooth specification.
    Returns a tuple: (heart_rate, [rr_intervals])
    """
    flags = data[0]
    hr_format = flags & 0x01
    rr_interval_present = (flags >> 4) & 0x01

    offset = 1
    # Parse Heart Rate
    if hr_format == 0:
        # Heart Rate Value Format is in UINT8
        heart_rate = data[offset]
        offset += 1
    else:
        # Heart Rate Value Format is in UINT16
        heart_rate = struct.unpack_from("<H", data, offset)[0]
        offset += 2

    # Parse RR-Intervals if present
    rr_intervals = []
    if rr_interval_present:
        while offset + 1 < len(data):
            rr = struct.unpack_from("<H", data, offset)[0]
            rr_intervals.append(rr / 1024.0)  # Convert to seconds
            offset += 2

    return heart_rate, rr_intervals

async def ble_process(adapter_index, output_queue):
    """
    Asynchronous BLE process that connects to the Polar H10 and sends heart rate and RR interval data to the queue.
    """
    logging.info(f"Scanning for BLE devices using adapter hci{adapter_index}...")
    devices = await BleakScanner.discover(adapter=adapter_index)

    polar_h10 = None
    for device in devices:
        # Modify the condition to match your device's name or address
        if "Polar H10" in device.name:
            polar_h10 = device
            break

    if not polar_h10:
        logging.error("Polar H10 device not found. Ensure it's in pairing mode.")
        output_queue.put(None)
        return

    logging.info(f"Found Polar H10: {polar_h10.name}, Address: {polar_h10.address}")

    async with BleakClient(polar_h10.address, adapter=adapter_index) as client:
        if not client.is_connected:
            logging.error("Failed to connect to Polar H10.")
            output_queue.put(None)
            return

        logging.info("Connected to Polar H10.")

        # Define a notification handler
        def handle_hr_measurement(sender, data):
            heart_rate, rr_intervals = parse_heart_rate(data)
            output_queue.put((heart_rate, rr_intervals))

        # Start receiving heart rate measurements
        await client.start_notify(HR_MEASUREMENT_CHAR_UUID, handle_hr_measurement)

        logging.info("Receiving heart rate and RR interval data. Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("BLE process cancelled.")
        finally:
            await client.stop_notify(HR_MEASUREMENT_CHAR_UUID)
            logging.info("Disconnected from Polar H10.")
            output_queue.put(None)

def start_ble_process(adapter_index, output_queue):
    """
    Starts the BLE process in an asyncio event loop.
    """
    try:
        asyncio.run(ble_process(adapter_index, output_queue))
    except Exception as e:
        logging.error(f"Error in BLE process: {e}")
        output_queue.put(None)