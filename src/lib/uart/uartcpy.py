import asyncio

from serial_asyncio import open_serial_connection

from .uart_tranceiver import UartTranceiver

class Uartcpy(UartTranceiver):

    def __init__(self, device_id: str, port: str, **kwargs) -> None:
        """
        :param str device_id: A unique name for your device
        :param str port: The port path of yout UART interface e.g. /dev/ttyUSB0
        :param kwargs: Arguments passed to open_serial_connection() -> Serial()
        """
        
        event_loop = asyncio.get_event_loop()
        reader, writer = event_loop.run_until_complete(open_serial_connection(url=port, loop=event_loop, **kwargs))
        super().__init__(device_id, reader, writer, loop=event_loop)
