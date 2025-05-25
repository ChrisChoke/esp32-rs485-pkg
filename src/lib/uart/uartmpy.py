from machine import UART

import asyncio

from .uart_tranceiver import UartTranceiver

class Uartmpy(UartTranceiver):

    def __init__(self, device_id: str, port: int, **kwargs) -> None:
        """
        :param str device_id: A unique name for your device
        :param int port: The UART number of your board
        :param kwargs: Arguments passed to machine.UART
        """
        
        uart = UART(port, **kwargs)
        writer = asyncio.StreamWriter(uart, {})
        reader = asyncio.StreamReader(uart)
        super().__init__(device_id, reader, writer)
