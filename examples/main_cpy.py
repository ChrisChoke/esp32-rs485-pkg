from lib.uart import Uart

import asyncio


async def main(uart: Uart):
    """main loop"""
    while True:
        sndr, cmd = await uart.read() # block here until data is received
        print(f"main.py cmd: {cmd} from sndr: {sndr}")

def start():
    loop = asyncio.get_event_loop()
    uart = Uart("main", "/dev/ttyUSB0", baudrate=115200)
    loop.create_task(main(uart))
    loop.run_forever()

# set up event_loop because deprecation warning of cpython
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

start()