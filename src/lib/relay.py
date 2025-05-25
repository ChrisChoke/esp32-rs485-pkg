# sys.implementation._build == "ESP32_GENERIC_C3" or "ESP32_GENERIC"
# _build sicnce Micropython 1.25
import sys
from machine import Pin

class Relay():
    """Relay class with typical relay functionalitys.
    
    :param int gpio: The gpio number
    :raises ValueError: If gpio number not valid for output
    """

    def __init__(self, gpio: int, invert=False) -> None:
        if gpio not in self._output_pins:
            raise ValueError(f"gpio number {gpio} not valid")
        self.pin = Pin(gpio, Pin.OUT)
        self.invert = invert

    @property
    def _output_pins(self) -> tuple:
        board_info = sys.implementation._build
        if board_info == "ESP32_GENERIC":
            return (4,5,13,14,15,16,17,18,19,21,22,23,25,26,27,32,33) # 16,17 UART2
        elif board_info == "ESP32_GENERIC_C3":
            return (0,1,2,3,4,5,6,7,8,9,10)
        else:
            return ()

    @property
    def state(self) -> int:
        return self.pin.value()

    def on(self) -> int:
        self.pin.value(1) if not self.invert else self.pin.value(0)
        return self.state

    def off(self) -> int:
        self.pin.value(0) if not self.invert else self.pin(1)
        return self.state

    def toggle(self) -> int:
        values = (1,0)
        self.pin.value(values[self.state])
        return self.state
    
    def set(self, value: int) -> int:
        if value:
            state = self.on()
        else:
            state = self.off()
        return state