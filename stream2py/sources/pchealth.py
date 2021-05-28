#!/usr/bin/env python
import operator
import os
import threading
import time
from collections import deque
from pprint import pprint

import psutil
import platform

from stream2py import SourceReader
from stream2py.utility.typing_hints import ComparableType, Any

"""
    Provide computer status info. 
    
    To get network upload and download speeds, speedtest-cli app should be installed 
"""

__all__ = ['StatusInfo', 'StatusInfoReader']

DFLT_STATUS_INFO_READ_INTERVAL = 1000  # in ms


class StatusInfo:

    SPEEDTEST_CMD = 'speedtest'

    @staticmethod
    def disk_free_bytes(path: str = '/') -> dict:
        return {'val': int(psutil.disk_usage(path).free), 'unit': 'bytes'}

    @staticmethod
    def disk_used_percents(path: str = '/') -> dict:
        return {'val': float(psutil.disk_usage(path).percent), 'unit': '%'}

    @staticmethod
    def cpu_used_percents():
        return {'val': psutil.cpu_percent(), 'unit': '%'}

    @staticmethod
    def cpu_temp():

        _t = -1
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as ftemp:
                _t = ftemp.readline()
                _t = float(int(_t) / 1000)
        except Exception as ex:
            _t = -1

        return {'val': _t, 'unit': 'C'}

    @staticmethod
    def mem_total():
        """
         - total:
           total physical memory available.
        """
        return {'val': psutil.virtual_memory().total, 'unit': 'bytes'}

    @staticmethod
    def mem_available():
        """
         - available:
           the memory that can be given instantly to processes without the
           system going into swap.
           This is calculated by summing different memory values depending
           on the platform and it is supposed to be used to monitor actual
           memory usage in a cross platform fashion.
        """
        return {'val': psutil.virtual_memory().available, 'unit': 'bytes'}

    @staticmethod
    def mem_used_percent():
        """
        - used:
          the percentage usage calculated as (total - available) / total * 100
        """
        return {'val': psutil.virtual_memory().percent, 'unit': '%'}

    @staticmethod
    def mem_used_bytes():
        """
         - used:
            memory used, calculated differently depending on the platform and
            designed for informational purposes only:
            macOS: active + wired
            BSD: active + wired + cached
            Linux: total - free
        """
        return {'val': psutil.virtual_memory().used, 'unit': 'bytes'}

    @staticmethod
    def mem_free():
        """
         - free:
           memory not being used at all (zeroed) that is readily available;
           note that this doesn't reflect the actual memory available
           (use 'available' instead)

        """
        return {'val': psutil.virtual_memory().free, 'unit': 'bytes'}

    @staticmethod
    def platform():
        _info = platform.uname()
        if _info is None or len(_info._fields) == 0:
            return {'val': None, 'unit': None}

        _values = dict()
        for _f in _info._fields:
            _values[_f] = _info.__getattribute__(_f)
        return {'val': _values, 'unit': 'json'}

    @staticmethod
    def network_download_speed() -> dict or None:
        """
            Method to get download speed by testing real network speed.
            It requires speedtest python  system app to be installed.

            WARNING: The method is very slow
        :return:
        """
        try:
            with os.popen(
                StatusInfo.SPEEDTEST_CMD + ' --no-upload --simple '
            ) as speedtest_output:
                for line in speedtest_output:
                    label, value, unit = line.split()
                    if 'download' in label.lower():
                        return {'val': float(value), 'unit': unit}
        except Exception as ex:
            return {'val': float(0), 'unit': 'not installed'}

    @staticmethod
    def network_upload_speed() -> dict:
        """
            Method to get upload speed by testing real network speed.
            It requires speedtest python  system app to be installed.

            WARNING: The method is very slow
        :return:
        """
        try:
            with os.popen(
                StatusInfo.SPEEDTEST_CMD + ' --no-download --simple '
            ) as speedtest_output:
                for line in speedtest_output:
                    label, value, unit = line.split()
                    if 'upload' in label.lower():
                        return {'val': float(value), 'unit': unit}
        except Exception as ex:
            return {'val': float(0), 'unit': 'not installed'}

    @staticmethod
    def all(
        include_network_download_speed: bool = False,
        include_network_upload_speed: bool = False,
    ):

        _info = {
            'memory': {
                'total': StatusInfo.mem_total(),
                'available': StatusInfo.mem_available(),
                'free': StatusInfo.mem_free(),
                'used_bytes': StatusInfo.mem_used_bytes(),
                'used_percents': StatusInfo.mem_used_percent(),
            },
            'disk': {
                'free': StatusInfo.disk_free_bytes(),
                'used': StatusInfo.disk_used_percents(),
            },
            'cpu': {
                'used': StatusInfo.cpu_used_percents(),
                'temp': StatusInfo.cpu_temp(),
            },
            'platform': StatusInfo.platform(),
        }

        if include_network_download_speed or include_network_upload_speed:
            _info['network'] = dict()

        if include_network_download_speed:
            _info['network']['download'] = StatusInfo.network_download_speed()

        if include_network_upload_speed:
            _info['network']['upload'] = StatusInfo.network_upload_speed()

        return _info


_ITEMGETTER_0 = operator.itemgetter(0)


class SyncQueue:
    def __init__(self):
        self.lock = threading.Lock()
        self.queue = deque()

    def len(self):
        with self.lock:
            return len(self.queue)

    def popleft(self):
        with self.lock:
            return self.queue.popleft()

    def popleft_no_block(self):
        with self.lock:
            if len(self.queue):
                return self.queue.popleft()

    def clear(self):
        with self.lock:
            return self.queue.clear()

    def append(self, item):
        with self.lock:
            return self.queue.append(item)


class StatusInfoReader(SourceReader, threading.Thread):
    _index: int = 0
    _data: SyncQueue = SyncQueue()
    _stop: threading.Event = threading.Event()
    _bt: int = None

    def __init__(
        self,
        read_interval_ms=DFLT_STATUS_INFO_READ_INTERVAL,
        include_network_download_speed: bool = False,
        include_network_upload_speed: bool = False,
    ):

        self.read_interval_ms = read_interval_ms
        self.include_network_download_speed = include_network_download_speed
        self.include_network_upload_speed = include_network_upload_speed

        threading.Thread.__init__(self, daemon=True)

    def open(self):
        self._data.clear()
        self._bt = self.get_timestamp()
        self._index = 0

        self._stop.clear()
        self.start()

    def read(self):
        """Returns one data item

        :return: (index, timestamp, character)
        """
        return self._data.popleft_no_block()

    def close(self):
        self._stop.set()

    @property
    def info(self) -> dict:
        return {'bt': self._bt}

    def key(self, data: Any) -> ComparableType:
        """
        :param data: (index, timestamp, character)
        :return: index
        """
        return _ITEMGETTER_0(data)

    def run(self):
        try:
            while not self._stop.is_set():

                self._data.append(
                    (
                        self._index,
                        self.get_timestamp(),
                        StatusInfo.all(
                            self.include_network_download_speed,
                            self.include_network_upload_speed,
                        ),
                    )
                )  # (index, timestamp, character)
                self._index += 1
                if self.read_interval_ms > 0:
                    time.sleep(self.read_interval_ms / 1000)

        except Exception:
            self.close()
            raise


if __name__ == '__main__':

    # As separated info
    # print(f"Memory:\n---------------------------------")
    # print(f"\tmem total {StatusInfo.mem_total()}")
    # print(f"\tmem available {StatusInfo.mem_available()}")
    # print(f"\tmem free {StatusInfo.mem_free()}")
    # print(f"\tmem used bytes {StatusInfo.mem_used_bytes()}")
    # print(f"\tmem used percents {StatusInfo.mem_used_percent()}")
    #
    # print(f"\nDisk:\n---------------------------------")
    # print(f"\tdisk free {StatusInfo.disk_free_bytes()}")
    # print(f"\tdisk used {StatusInfo.disk_used_percents()}")
    #
    # print(f"\nCPU:\n---------------------------------")
    # print(f"\tcpu used {StatusInfo.cpu_used_percents()}")
    # print(f"\tcpu temp {StatusInfo.cpu_temp()}")
    #
    # print(f"\nPlatform:\n---------------------------------")
    # print(f"\tplatform info {StatusInfo.platform()}")
    #
    # print(f"\nNetwork:\n---------------------------------")
    # print(f"\tDownload speed {StatusInfo.network_download_speed()}")
    # print(f"\tUpload speed {StatusInfo.network_upload_speed()}")

    # or as a single JSON
    # print(StatusInfo.all(include_network_download_speed=True, include_network_upload_speed=True))

    with StatusInfoReader() as source:
        print('Ctrl+C to exit')
        time.sleep(3)
        while True:
            try:
                data = source.read()
                if data is not None:
                    index, timestamp, info = data
                    pprint(f'{index}.{timestamp}: {info}')

            except KeyboardInterrupt as kb:
                break

    print('Done!')
