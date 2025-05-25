try:
    from .uartmpy import Uartmpy as Uart
except:
    from .uartcpy import Uartcpy as Uart