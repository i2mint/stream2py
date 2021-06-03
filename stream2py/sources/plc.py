import threading
import time
from asyncio import Queue
from collections import deque
from pprint import pprint
from typing import List, Optional, Any

import snap7
from snap7.types import S7AreaDB, S7WLReal, S7WLBit, S7WLByte

from stream2py import SourceReader
from stream2py.sources.raw_plc import PlcRawRead, PlcDataItem, get_byte

from stream2py.utility.typing_hints import ComparableType


class PlcReader(SourceReader):
    """
        TODO: Finish class implementation
    """

    def __init__(
        self,
        ip_address: str,
        *,
        items_to_read: List[PlcDataItem],
        rack: int,
        slot: int,
        tcp_port: int = 102,
        sleep_time=1.0
    ):

        self._init_kwargs = {
            k: v for k, v in locals().items() if k not in ('self', '__class__')
        }

        self._ip_address = ip_address
        self._rack = rack
        self._slot = slot
        self._tcp_port = tcp_port
        self._items_to_read = items_to_read
        self._sleep_time = sleep_time

        # validate IP address
        import socket

        socket.inet_aton(self._ip_address)  # validate IP Address
        self._plc_raw_reader = PlcRawRead(
            self._ip_address, rack=self._rack, slot=self._slot, tcp_port=self._tcp_port,
        )

        self.bt = None
        self._start_time = None
        # self._data_lock = threading.Lock()
        self._data_read_thread_exit = threading.Event()
        self._data_read_thread = None
        self._data_read_thread_exit.clear()
        self.data = deque()  # Queue()
        self.plc_info = dict()

        self.reader_thread = None

    def _stream_thread(self):
        _sleep_time = self.sleep_time_on_read_none_s

        while not self._data_read_thread_exit.is_set():
            data_item = self._plc_raw_reader.read_items(self._items_to_read)
            self.data.append(data_item)
            if _sleep_time > 0:
                time.sleep(_sleep_time)

    @property
    def sleep_time_on_read_none_s(self) -> float:
        return self._sleep_time

    def open(self) -> bool:

        if self._plc_raw_reader.open():
            self.bt = self.get_timestamp()
            self._start_time = self.bt
            self.plc_info = self._plc_raw_reader.get_info()
            if self._data_read_thread is None:
                self._data_read_thread = threading.Thread(target=self._stream_thread)
                self._data_read_thread.start()
            return True
        return False

    def read(self, blocking: bool = False, timeout: int = 0) -> Optional[Any]:
        """
        :return: timestamp, plc info, read db items as key:value
        """
        if len(self.data):
            return self.data.popleft()
        # return self.data.get(block = blocking, timeout=timeout)

    def close(self) -> None:
        """Close and clean up source reader.
        Will be called when StreamBuffer stops or if an exception is raised during read and append loop.
        """
        self._data_read_thread_exit.set()
        self._plc_raw_reader.close()

    @property
    def info(self) -> dict:
        _info = {'bt': self.bt}
        _info.update(**self._init_kwargs)
        _info.update(plc_info=self.plc_info)
        return _info

    def key(self, data_item: Any or None) -> ComparableType:

        assert (
            data_item is not None and len(data_item) > 0 and 'bt' in data_item[0]
        ), 'Cannot get key because bt is missing from data_item'

        import operator

        return operator.itemgetter('bt')(data_item[0])


if __name__ == '__main__':
    #
    # read_items = [
    #     PlcDataItem(
    #         key='temperature',
    #         area=S7AreaDB,
    #         word_len=S7WLReal,
    #         db_number=3,
    #         start=2,
    #         amount=1,
    #         convert=snap7.util.get_real),
    #
    #     PlcDataItem(
    #         key='led1',
    #         area=S7AreaDB,
    #         word_len=S7WLBit,
    #         db_number=3,
    #         start=0 * 8 + 0,  # bit ofsset
    #         amount=1,
    #         convert=snap7.util.get_bool,
    #         convert_args=(0, 0)),
    #
    #     PlcDataItem(
    #         key='led2',
    #         area=S7AreaDB,
    #         word_len=S7WLBit,
    #         db_number=3,
    #         start=0 * 8 + 1,  # bit ofsset
    #         amount=1,
    #         convert=snap7.util.get_bool,
    #         convert_args=(0, 0)),
    # ]

    read_items = [
        PlcDataItem(
            key='PLC Motor Status',
            area=S7AreaDB,
            word_len=S7WLBit,
            db_number=1,
            start=0 * 8 + 0,  # bit offset
            amount=1,
            convert=snap7.util.get_bool,
            convert_args=(0, 0),
        ),
        PlcDataItem(
            key='PLC LED Status',
            area=S7AreaDB,
            word_len=S7WLBit,
            db_number=1,
            start=0 * 8 + 1,  # bit offset
            amount=1,
            convert=snap7.util.get_bool,
            convert_args=(0, 0),
        ),
        PlcDataItem(
            key='NetHAT Motor Speed',
            area=S7AreaDB,
            word_len=S7WLByte,
            db_number=1,
            start=3,
            amount=1,
            convert=get_byte,
            convert_args=(0,),
        ),
        PlcDataItem(
            key='NetHAT LED Brightness',
            area=S7AreaDB,
            word_len=S7WLByte,
            db_number=1,
            start=4,
            amount=1,
            convert=get_byte,
            convert_args=(0,),
        ),
    ]

    preader = PlcReader(
        '192.168.0.19', items_to_read=read_items, rack=0, slot=0, sleep_time=0
    )

    if not preader.open():
        preader.close()
        exit(-1)
    can_run: bool = True

    _i = preader.info
    pprint(preader.info)
    while can_run:
        try:
            data = preader.read()
            if data is None:
                time.sleep(0.5)
            else:
                pass
                # pprint(data)
                # print()
        except KeyboardInterrupt as kb:
            can_run = False


"""

    Ouptut::

{'bt': 1584040986041418,
 'ip_address': '192.168.0.19',
 'items_to_read': [PlcDataItem(area=132, word_len=8, db_number=3, start=2, amount=1, key='temperature', convert=<function get_real at 0x7f8488038200>, convert_args=None),
                   PlcDataItem(area=132, word_len=1, db_number=3, start=0, amount=1, key='led1', convert=<function get_bool at 0x7f84780c2b00>, convert_args=(0, 0)),
                   PlcDataItem(area=132, word_len=1, db_number=3, start=1, amount=1, key='led2', convert=<function get_bool at 0x7f84780c2b00>, convert_args=(0, 0))],
 'plc_info': {'cpu_info': {'ASName': b'S71500/ET200MP station_1',
                           'Copyright': b'Original Siemens Equipment',
                           'ModuleName': b'PLC_1',
                           'ModuleTypeName': b'CPU 1511C-1 PN',
                           'SerialNumber': b'S V-L9AL98812019'},
              'cpu_state': 'S7CpuStatusRun',
              'pdu_len': 480},
 'rack': 0,
 'sleep_time': 1.0,
 'slot': 0,
 'tcp_port': 102}



[{'key': 'temperature', 'ts': 1584040986051531, 'value': 11.0},
 {'key': 'led1', 'ts': 1584040986051538, 'value': False},
 {'key': 'led2', 'ts': 1584040986051540, 'value': True}]

[{'key': 'temperature', 'ts': 1584040987061010, 'value': 11.0},
 {'key': 'led1', 'ts': 1584040987061022, 'value': False},
 {'key': 'led2', 'ts': 1584040987061029, 'value': True}]

[{'key': 'temperature', 'ts': 1584040988080404, 'value': 11.0},
 {'key': 'led1', 'ts': 1584040988080412, 'value': False},
 {'key': 'led2', 'ts': 1584040988080415, 'value': True}]

[{'key': 'temperature', 'ts': 1584040989104420, 'value': 11.0},
 {'key': 'led1', 'ts': 1584040989104428, 'value': False},
 {'key': 'led2', 'ts': 1584040989104431, 'value': True}]


"""
