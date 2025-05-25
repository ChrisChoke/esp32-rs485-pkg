from machine import unique_id
from binascii import hexlify

import asyncio

from uart import Uart
from relay import Relay


unique_id = hexlify(unique_id()).decode()
uart = Uart(unique_id, 2, baudrate=115200)

# uart.write("mymessage", rcvr="client1") to address a specific client on the bus.
def gpio_switch(gpio: int, state: int | bool) -> tuple:
    """function to control gpios.

    :param int gpio: the gpio int to control
    :param int bool state: the value to switch 
    :return int: the current state of gpio or None if gpio is invalid
    """
    try:
        relay = Relay(gpio)
        state = relay.set(state)
    except ValueError:
        return gpio, None
    return gpio , state


async def main(uart: Uart):
    """main loop"""
    while True:
        sndr , cmd = await uart.read() # block here until data is received
        print(f"main.py cmd: {cmd} from sndr: {sndr}")
        if cmd[0] == "gpio":
            gpio, state = gpio_switch(int(cmd[1]), cmd[2])
            await uart.write(f"gpio,{gpio},{state}")

def start():
    loop = asyncio.get_event_loop()
    loop.create_task(main(uart))
    loop.run_forever()

start()
