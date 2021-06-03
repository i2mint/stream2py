import ctypes
from contextlib import suppress
from dataclasses import dataclass
from pprint import pprint
from typing import List, Optional, Callable

from snap7.common import check_error
from snap7.exceptions import Snap7Exception
from snap7.types import (
    S7DataItem,
    S7AreaDB,
    S7WLBit,
    S7WLReal,
    S7WLByte,
    S7WLWord,
    S7WLDWord,
)

from stream2py import SourceReader
import snap7


def get_byte(_bytearray, byte_index):
    """
    Get the boolean value from location in bytearray
    """
    return _bytearray[byte_index]


@dataclass
class PlcDataItem:

    area: int
    word_len: int
    db_number: int
    start: int
    amount: int

    key: str  # for multiple items read, represents key name in returned dictionary
    convert: snap7.util.get_bool or snap7.util.get_real or snap7.util.get_real or snap7.util.get_int or snap7.util.get_string or snap7.util.get_dword
    convert_args: Optional or None

    def __init__(
        self,
        area: int,
        word_len: int,
        db_number: int,
        start: int,
        amount: int,
        key: str,
        convert: Callable,
        convert_args: Optional or None = None,
    ):

        self.area = area
        self.word_len = int(word_len)
        self.db_number = int(db_number)
        self.start = eval(str(start))
        self.amount = int(amount)
        self.key = str(key)
        self.convert = convert
        self.convert_args = convert_args

        # allocate memory for data
        _size = 0
        if self.word_len in [S7WLBit, S7WLByte]:
            _size = 1
        elif self.word_len == S7WLWord:
            _size = 2
        elif self.word_len == S7WLDWord:
            _size = 4
        elif self.word_len == S7WLReal:
            _size = 8

        assert _size != 0, 'Unknown word len'

        print(f'PlcDataItem {self.key}: size = {_size}, amount = {self.amount}')

        try:
            self.buffer = ctypes.create_string_buffer(_size * self.amount)
        except Exception as ex:
            print(f'ERROR: Failed to allocate string buffer for item {self.key} : {ex}')
            return

        try:
            self.buffer = ctypes.cast(
                ctypes.pointer(self.buffer), ctypes.POINTER(ctypes.c_uint8)
            )
        except Exception as ex:
            return

    def get_item(self):
        return S7DataItem(
            Area=self.area,
            WordLen=self.word_len,
            DBNumber=self.db_number,
            Start=self.start,
            Amount=self.amount,
            pData=self.buffer,
        )

    def decode_item(self, item_read: S7DataItem):
        check_error(item_read.Result)

        if self.convert_args is not None:
            return self.convert(item_read.pData, *self.convert_args)
        else:
            return self.convert(item_read.pData, 0)


class PlcRawRead:
    def __init__(self, ip_address: str, *, rack: int, slot: int, tcp_port: int = 102):

        self._plc = snap7.client.Client()
        self._ip_address = ip_address
        self._rack = rack
        self._slot = slot
        self._tcp_port = tcp_port

        self.plc_info = {}

    def open(self):
        self._plc.connect(self._ip_address, self._rack, self._slot, self._tcp_port)
        return self._plc.get_connected()

    @classmethod
    def todict(cls, struct):
        return dict((field, getattr(struct, field)) for field, _ in struct._fields_)

    def get_info(self):
        if self._plc.get_connected():

            with suppress(Snap7Exception):
                self.plc_info.update(cpu_info=self.todict(self._plc.get_cpu_info()))

            with suppress(Snap7Exception):
                self.plc_info.update(cpu_state=self._plc.get_cpu_state())

            with suppress(Snap7Exception):
                self.plc_info.update(pdu_len=self._plc.get_pdu_length())

        return self.plc_info

    def close(self):
        if self._plc.get_connected():
            self._plc.disconnect()

        self._plc.destroy()

    def write_items(self, items: List[PlcDataItem]) -> bool:
        return False

    def read_items(self, items: List[PlcDataItem]) -> List[dict] or None:

        _items = (S7DataItem * len(items))()
        for _i in range(0, len(items)):
            _items[_i] = items[_i].get_item()

        result, items_read = self._plc.read_multi_vars(_items)
        if result:
            return None

        _bt = SourceReader.get_timestamp()
        result = []
        for _idx in range(0, len(items)):
            result.append(
                {
                    'key': items[_idx].key,
                    'value': items[_idx].decode_item(items_read[_idx]),
                    'bt': _bt,
                }
            )

        return result


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
    # PlcDataItem(
    #     key='PLC Motor Speed',
    #     area=S7AreaDB,
    #     word_len=S7WLByte,
    #     db_number=1,
    #     start=1,
    #     amount=1,
    #     convert=get_byte,
    #     convert_args=(0,)),
    #
    # PlcDataItem(
    #     key='PLC LED Brightness',
    #     area=S7AreaDB,
    #     word_len=S7WLByte,
    #     db_number=1,
    #     start=2,
    #     amount=1,
    #     convert=get_byte,
    #     convert_args=(0,)),
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


if __name__ == '__main__':
    plcTest = PlcRawRead('192.168.0.19', rack=0, slot=0)
    plcTest.open()
    pprint(plcTest.get_info())

    while True:
        _d = plcTest.read_items(read_items)
        #
        #     [
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
        # ])
        pprint(_d)
        print()

    plcTest.close()

    """
        Output example of get info:
        {'cpu_info': {'ASName': b'S71500/ET200MP station_1',
              'Copyright': b'Original Siemens Equipment',
              'ModuleName': b'PLC_1',
              'ModuleTypeName': b'CPU 1511C-1 PN',
              'SerialNumber': b'S V-L9AL98812019'},
     'cpu_state': 'S7CpuStatusRun',
     'pdu_len': 480}

     Output example of get Item

    [{'key': 'temperature', 'value': 10.0, 'ts': 1583086607352911}, {'key': 'led1', 'value': False, 'ts': 1583086607352923}, {'key': 'led2', 'value': False, 'ts': 1583086607352927}]

    """
