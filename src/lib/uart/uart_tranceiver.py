import asyncio
import json


class UartTranceiver():

    def __init__(
        self,
        device_id: str,
        reader,
        writer,
        loop = None,
    ):
        """
        :param str device_id: A unique name for your device
        :param StreamReader reader: asyncio.StreamReader
        :param StreamWriter writer: asyncio.StreamWriter
        :param event_loop loop: asyncio.event_loop()
        """

        self.device_id = device_id
        self.sreader = reader
        self.swriter = writer
        self.event_loop = loop
        self.isannounced = False
        self.oversize_cache = ""
        self.message_cache = []

        if self.event_loop is None:
            self.event_loop = asyncio.get_event_loop()

        if self.device_id != "main":
            self.event_loop.create_task(self._hello())

    async def write(self, msg: str, rcvr: str | None = None):
        """send json formatted message on uart"""

        message = { "sndr": self.device_id, "msg": msg }
        if rcvr is not None:
            message["rcvr"] = rcvr
        s_msg = f"{json.dumps(message)}\n"
        
        self.swriter.write(s_msg.encode())
        await self.swriter.drain()

    async def read(self) -> tuple[str,list]:
        """read uart streamreader.

        read and parse uart message. split msg by comma.
        ATTENTION,MAYBE MAXIMUM RECUSION LIMIT ISSUE ON MICROPYTHON SATELLITES!

        :return tuple: With sndr and list from comma seperated msg
        """
        if self.message_cache:
            message = self.message_cache[0]
            self.message_cache.pop(0)
            #print(self.message_cache)
            return message
        else:
            await self._read()
            return await self.read()

    async def _read(self) -> list | None:
        """wait for new message if newline \n arrived.
        """

        msg: list = []
        buff = await self.sreader.readline() # waits for incoming
        buff_: str = buff.decode()
        #print(f"read: buff_ = {buff_}")
        msg = self._parse_buffer(buff_)

        for m in msg:
            parsed = self._parse_message(m["msg"])
            if m.get("rcvr", "main") == self.device_id:
                if parsed[0] == "hello-ack":
                    self.isannounced = True
                    self.event_loop.create_task(self._healthcheck())
                    continue
                self.message_cache.append((m["sndr"],parsed))
        return None
        
    def _parse_buffer(self, msg: str) -> list:
        """parse buffer and convert to python dictionary

        """
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
                    #print("start > end: ",self.oversize_cache)
                    msg_loaded: dict = json.loads(self.oversize_cache)
                    messages.append(msg_loaded)
                    self.oversize_cache = ""
                end = msg.find(END_CHAR, start +1)

            indexes.append((start, end+1))
            #print("while:",start, end)
            if end == -1:
                # no END_CHAR found but START_CHAR. keep in cache for next buffer receive.
                self.oversize_cache = msg[start:]
                #print("no END_CHAR: ",self.oversize_cache)
                break
            start = msg.find(START_CHAR, start +1)
            end = msg.find(END_CHAR, start +1)
        
        # parsing completed by no further START_CHAR found or not found any START_CHAR,
        # but oversize_cache is full from earlier receive.
        # so in oversize_cache is the start of message "{ "sndr": "blabla", "
        if start == -1:
            if self.oversize_cache:
                ocache = self.oversize_cache + msg[:end +1]
                self.oversize_cache = ""
                #print("ocache: ", ocache)
                try:
                    msg_loaded: dict = json.loads(ocache)
                    messages.append(msg_loaded)
                except:
                    print(f"_parse_buffer: broken json string:\n{ocache}")
            
        # indexes list can contain 0 from find() error -1 and addition from me +1 when put into indexes list
        # on slicing in for loop we result into empty string, we check truethy before json.loads come into place.
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