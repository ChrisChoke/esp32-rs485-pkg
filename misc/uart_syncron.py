import asyncio
import json
from machine import UART

class Uart(UART):

    def __init__(
        self,
        device_id: str,
        id: int,
        baudrate: int = 9600,
        bits: int = 8,
        parity: int | None = None,
        stop: int = 1,
        **kwargs
    ):
        """device_id = main for the main device on bus"""
        super().__init__(
            id,
            baudrate=baudrate,
            bits=bits,
            parity=parity,
            stop=stop,
            **kwargs
        )

        self.device_id = device_id
        self.isannounced = False
        self.buffer_cache = bytearray(100)
        self.oversize_cache = ""
        self.message_cache = []
        self.event_loop = asyncio.get_event_loop()

    async def write(self, msg: str, rcvr: str | None = None):

        message = { "sndr": self.device_id, "msg": msg }
        if rcvr is not None:
            message["rcvr"] = rcvr
        s_msg = f"{json.dumps(message)}\n"

        super().write(s_msg.encode())

    async def read(self) -> list | None:
        self._read()
        if self.message_cache:
            message = self.message_cache[0]
            self.message_cache.pop(0)
            print(self.message_cache)
            return message
        return None

    def _read(self) -> list | None:
        """read the messages from buffer and return messages addressed to this device.
        """
        # i think i need new implementation. the thing is not well designed.
        # i think better is readinto(buff) where buff = bytarray() (bytearray is bytes but like a list, mutable. bytes are immutable)
        # so we can read() in a while loop on main.py and always have the buffer read, but return one full message addressed to this device on
        # every loop iteration. return always one list with the commands. or None when no messages in buffer for this device.

        msg: list = []
        data_avail = super().any()
        if data_avail:
            super().readinto(self.buffer_cache)
            buff = self.buffer_cache[0:data_avail]
            self.buffer_cache[:] = b'\x00' * len(self.buffer_cache) # clear data in buffer and keep buffer size. fill with 0 bytes. so no message inside.

            buff_: str = buff.decode()
            print(f"read: buff_ = {buff_}")
            msg = self._parse_buffer(buff_)

        for m in msg:
            # i want to give back an object with message part in side to controll gpio
            parsed = self._parse_message(m["msg"])
            if m.get("rcvr", "main") == self.device_id: # always true on main device because defaulting
                if parsed[0] == "hello-ack":
                    self.isannounced = True
                    self.event_loop.create_task(self._healthcheck())
                self.message_cache.append(parsed) # currently return only the first item in list when msg contains more than one item
        return None # return None if the received message is not for me
        
    def _parse_buffer(self, msg: str) -> list:
        """parse buffer string

        convert to dictionary
        """
        # maybe enhance parsing. when working with self.buffer_cache i need to know if a {} json string is incomplete.
        # when incomplete i need to remove only complete json string, and let the rest in a oversize_cache string.
        # so i have a chance to not missing any messages. i can concat the rest of the string on the next buffer read.
        # keep in mind the default buffer size is 256. if this is reached, no messages can received until we read the buffer.
        START_CHAR: str = "{"
        END_CHAR: str = "}"
        messages: list[dict] = []
        start: int = msg.find(START_CHAR)
        end: int = msg.find(END_CHAR)
        
        indexes: list[tuple[int,int]] = []
        while start != -1:
            # START_CHAR is behind END_CHAR. Maybe the start of string is in oversize_cache from prior receive.
            if start > end:
                if self.oversize_cache:
                    self.oversize_cache = self.oversize_cache + msg[:start]
                    print("start > end: ",self.oversize_cache)
                    msg_loaded: dict = json.loads(self.oversize_cache)
                    messages.append(msg_loaded)
                    self.oversize_cache = ""
                end = msg.find(END_CHAR, start +1)

            indexes.append((start, end+1))
            print("while:",start, end)
            if end == -1:
                # no END_CHAR found but START_CHAR. keep in cache for next buffer receive.
                self.oversize_cache = msg[start:]
                print("no END_CHAR: ",self.oversize_cache)
                break
            start = msg.find(START_CHAR, start +1)
            end = msg.find(END_CHAR, start +1)
        
        print("indexes", indexes)
        print("start", start)
        print("end", end)
        # parsing completed by no further START_CHAR found or not found any START_CHAR, but oversize_cache is full from earlier receive.
        # so in oversize_cache is the start of message "{ "sndr": "blabla", "
        if start == -1:
            if self.oversize_cache:
                ocache = self.oversize_cache + msg[:end +1]
                self.oversize_cache = ""
                print("ocache: ", ocache)
                try:
                    msg_loaded: dict = json.loads(ocache)
                    messages.append(msg_loaded)
                except:
                    print(f"_parse_buffer: broken json string:\n{ocache}")
            
        # indexes list can contain 0 from find() error -1 and addition from me +1 when put into indexes list
        # on slicing in for loop we result into empty string, we check truethy before json.loads come into place
        # is there any missmatch on slicing that end is greater than start, then we loosing the other messages. i will see if that happen
        # on weak bus connections or not
        for s, e in indexes:
            msg_ = msg[s:e]
            if msg_:
                try:
                    msg_loaded: dict = json.loads(msg_)
                    messages.append(msg_loaded)
                except:
                    print(f"_parse_buffer: broken json string:\n{msg_}")

        return messages

    def _parse_message(self, msg: str):
        """convert the message part

        expected format: type,device,value

        from the buffer i create a dictionary. convert the message key into a python object
        """
        partials: list = msg.split(",")
        new_partials: list = []
        for i, item in enumerate(partials):
            if i == 2:
                new_partials.insert(i, self._str2bool(item))
            else:
                new_partials.insert(i, item)
        return new_partials

    def _str2bool(self, v: str):
        """convert string to boolean True/False else return origin value"""
        if v.lower() in ("true", "1", "yes", "on"):
            value = True
        elif v.lower() in ("false", "0", "no", "off"):
            value = False
        else:
            value = v
        return value

    async def _healthcheck(self):
        """coroutine: sending heahlty message"""
        while self.isannounced:
            await self.write("healthy")
            await asyncio.sleep(10)

    async def _hello(self):
        """coroutine: sending hello message to announce this device"""
        while not self.isannounced:
            await self.write("hello")
            await asyncio.sleep(10)