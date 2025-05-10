import asyncio
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_UUID = "0bd51666-e7cb-469b-8e4d-2742f1ba77cc"
COMMAND_UUID = "e7add780-b042-4876-aae1-112855353cc1"
NOTIFY_UUID = "e7add780-b042-4876-aae1-112855353cc4"

IROBOT_NAMES = {"iRobot Braava", "Braava Jet m6", "Altadena"}

COMMANDS = {
    'start': [0x8b, 0x02, 0x00, 0x00],
    'dock': [0x8b, 0x02, 0x00, 0x01],
    'stop': [0x8b, 0x02, 0x00, 0x02],
    'status': [0x8b, 0x02, 0x00, 0x03],
}

async def notification_handler(sender, data):
    logger.info(f"Notification: {data.hex(' ')}")

async def scan_devices():
    logger.info("Scanning for iRobot Braava Jet devices...")
    devices = []
    
    try:
        async with BleakScanner() as scanner:
            await asyncio.sleep(10.0)
            for device in scanner.discovered_devices:
                if device.name and any(name in device.name for name in IROBOT_NAMES):
                    logger.info(f"Found iRobot: {device.name} ({device.address})")
                    devices.append(device)
    except Exception as e:
        logger.error(f"Scanning failed: {e}")
    
    return devices

async def send_command(client, command_bytes):
    try:
        logger.info(f"Sending command: {bytes(command_bytes).hex(' ')}")
        await client.write_gatt_char(COMMAND_UUID, bytearray(command_bytes), response=True)
        return True
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return False

async def connect_and_control(device):
    logger.info(f"Connecting to {device.name} ({device.address})...")
    
    try:
        async with BleakClient(device) as client:
            logger.info("Connected successfully!")
            
            await client.start_notify(NOTIFY_UUID, notification_handler)
            logger.info("Notifications enabled")
            
            while True:
                print("\nAvailable commands:")
                print("  start: Start Cleaning")
                print("  dock: Return to Dock")
                print("  stop: Stop Cleaning")
                print("  status: Get Status")
                print("  q: Quit")
                
                command = input("Enter command: ").lower()
                
                if command == 'q':
                    break
                elif command in COMMANDS:
                    await send_command(client, COMMANDS[command])
                else:
                    print("Invalid command")
                    
            await client.stop_notify(NOTIFY_UUID)
            
    except Exception as e:
        logger.error(f"Connection error: {e}")

async def main():
    try:
        devices = await scan_devices()
        
        if not devices:
            logger.error("No iRobot Braava devices found")
            return
        
        await connect_and_control(devices[0])
        
    except KeyboardInterrupt:
        logger.info("Program stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
