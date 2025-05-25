# UART Package

The uart package under lib directory contains a package for cpython and micropython to work with a serial uart interface.
I wanted to standardized the messages which arrived and sent on the uart. I begun with synchronous functions and end up
in this asyncronous package.\
So maybe the parsing methods have some features which do not used anymore.

I will use this mainly with rs-485 breakout modules between esp32 and a rpi.
So full project is coming in the future.

### For RS-485 communication between esp32 micropython and rpi or other Cpython platforms

Since RS-485 is an electricity standard, we need here a hardware-module to convert ttl to rs-485. The Software part comes with this package.

Rpi --> ttl_to_RS485 ----- RS485_to_ttl --> esp32.

The Rpi should be the "main" and the esp32 should be the satellite devices/client on the bus.

For Cpython usage:

```pip install pyserial-asyncio``` \
or \
```apt install python3-serial-asyncio```

### Message Format

```json
{ "sndr": "main", "rcvr": "f008d1c78390","msg": "gpio,4,0"}

{"sndr": "f008d1c78390", "msg": "healthy"}
```

The Message ("msg") you write can anything you want. But this Class methods split the message by comma into a list.
If no comma found, then the list contains just one item.

```python
# read() method return a tuple as follows:
# ("string", [list])
("sndr-device-1", [gpio,4,1])
```

My Goal is to use as "gpio,10,on" as example. So it means: "TYPE,DEVICE,VALUE".
TYPE: identify what i have to to \
DEVICE: is the integer of the gpio \
VALUE: to which state i want to switch.

```python
# write() method
uart.write(gpio,10,on) # to address the main
uart.write(gpio,10,on, rcvr="esp32-5") # to address specific device
```

The sndr in the message are filled automatically and the rcvr is per default the main on the bus.
so the main device has to use rcvr= on write method to address a specific satellite/device on the bus.

## Wiring TTL to USB adapter and ESP32 to PC

USB_to_TTL --> tx,rx to RS485 Converter --> A+ B- --> A+ B- --> connect pins to esp32 uart2 (tx=17, rx=16)

connect GND between both. Baudrate DSDTech UO9C adapter upper 19200. lower doesnt work for me. i use typically 115200.
for vcc i just use 3.3V from esp32 board and disconnect outgoiung vcc from ttl-usb adapter completely.

then you can connect with picocom to esp32 and with coolterm to the usb to ttl adapter.

on coolterm go to Options/Terminal and set up Line Mode and LF for "Enter Key Emulation"