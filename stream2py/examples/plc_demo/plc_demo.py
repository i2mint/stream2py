import threading
import time
from pprint import pprint
import npyscreen as nps
import numpy as np
import snap7
from snap7.snap7types import S7AreaDB, S7WLBit, S7WLByte

from stream2py.sources.audio import PyAudioSourceReader
from stream2py.sources.plc import PlcReader
from stream2py.sources.raw_plc import PlcDataItem, get_byte
import logging

def print_log(x):
    print(x)

def no_log_function(*args, **kwargs):
    pass

logging.basicConfig(level=logging.INFO,
                    format = "%(asctime)s %(levelname)s::> %(message)s")

dflt_log = print_log

logi=logging.info
logw=logging.warning
loge=logging.error
MAX_ABS_INT16 = 32767/10
AUDIO_SILENCE_THRESHOLD = 10


"""
    PLC database 1 items 
	dbMotorStatus	        Bool	0.0		
	dbLedStatus	            Bool	0.1			
	dbMotorSpeed	        Byte	1.0			
	dbLedBrightness	        Byte	2.0			
	dbNetHATMotorSpeed	    Byte	3.0		
	dbNetHATLedBrightness	Byte	4.0		
 
"""
read_items = [
    PlcDataItem(

        key='PLC Motor Status',
        area=S7AreaDB,
        word_len=S7WLBit,
        db_number=1,
        start=0 * 8 + 0,  # bit offset
        amount=1,
        convert=snap7.util.get_bool,
        convert_args=(0, 0)),

    PlcDataItem(
        key='PLC LED Status',
        area=S7AreaDB,
        word_len=S7WLBit,
        db_number=1,
        start=0 * 8 + 1,  # bit offset
        amount=1,
        convert=snap7.util.get_bool,
        convert_args=(0, 0)),

    PlcDataItem(
        key='PLC Motor Speed',
        area=S7AreaDB,
        word_len=S7WLByte,
        db_number=1,
        start=1,
        amount=1,
        convert=get_byte,
        convert_args=(0,)),

    PlcDataItem(
        key='PLC LED Brightness',
        area=S7AreaDB,
        word_len=S7WLByte,
        db_number=1,
        start=2,
        amount=1,
        convert=get_byte,
        convert_args=(0,)),

    PlcDataItem(
        key='NetHAT Motor Speed',
        area=S7AreaDB,
        word_len=S7WLByte,
        db_number=1,
        start=3,
        amount=1,
        convert=get_byte,
        convert_args=(0,)),

    PlcDataItem(
        key='NetHAT LED Brightness',
        area=S7AreaDB,
        word_len=S7WLByte,
        db_number=1,
        start=4,
        amount=1,
        convert=get_byte,
        convert_args=(0,)),
]


class DemoForm(nps.Form):

    def __init__(self,  **kwargs):

        self._plcreader = kwargs['plcreader']
        self._audioreader = kwargs['audioreader']
        del kwargs['plcreader']
        del kwargs['audioreader']
        super().__init__(**kwargs)

    def setup_ui(self):
        y, x = self.useable_space()

        self.t = self.add(nps.BoxTitle, name="PLC Info", rely=1, max_width=x - 4, max_height=8)

        self.add(nps.Textfield, readonly=True)
        self.add(nps.Textfield, readonly=True)

        self.motor_status = self.add(nps.TitleMultiSelectFixed, max_height=4, value=[1, ], name="Motor Status",
                    values=["Motor OFF", "Motor ON"], scroll_exit=True)

        self.motor_speed = self.add(nps.TitleSlider, out_of=100, name="\t\tMotor Speed: ", color='DANGER', readonly=True)

        self.add(nps.Textfield, readonly=True)
        self.add(nps.Textfield, readonly=True)
        self.add(nps.Textfield, readonly=True)
        self.add(nps.Textfield, readonly=True)

        self.led_status = self.add(nps.TitleMultiSelectFixed, max_height=4, value=[1, ], name="LED Status",
                    values=["LED OFF", "LED ON"], scroll_exit=True)

        self.led_brigthness = self.add(nps.TitleSlider, out_of=100, name="\t\tLED Brigthness: ", color='DANGER',
                                       readonly=True)


        self.add(nps.Textfield, readonly=True)
        self.add(nps.Textfield, readonly=True)
        self.add(nps.Textfield, readonly=True)
        self.add(nps.Textfield, readonly=True)

        self.audio_volume = self.add(nps.TitleSlider, out_of=MAX_ABS_INT16, name="\t\tAudio Volume: ", color='DANGER',
                                       readonly=True)

        _cpu_info=self._plcreader.info["plc_info"]["cpu_info"]
        self.t.values = []
        self.t.values.append(f"Module Type:\t{_cpu_info['ModuleTypeName'].decode()}")
        self.t.values.append(f"Serial:\t{_cpu_info['SerialNumber'].decode()}")
        self.t.values.append(f"Name:\t{_cpu_info['ModuleName'].decode()}")
        self.t.values.append(f"Copyright:\t{_cpu_info['Copyright'].decode()}")
        self.t.values.append(f"Status:\t{self._plcreader.info['plc_info']['cpu_state']}")

    def create(self):
        self.setup_ui()
        self._plc_th = threading.Thread(target=self.async_data_reading)

    def read_plc_data(self) -> bool:
        try:

            plc_data = self._plcreader.read()
            if plc_data is None:
                return False

            for _d in plc_data:
                _key = _d['key']
                if _key == 'PLC Motor Status':
                    self.motor_status.value = [1, ] if _d["value"] else [0, ]
                    self.motor_status.display()
                elif _key == 'PLC LED Status':
                    self.led_status.value = [1, ] if _d["value"] else [0, ]
                    self.led_status.display()
                elif _key == 'NetHAT Motor Speed':
                    self.motor_speed.value = _d["value"]
                    self.motor_speed.display()
                elif _key == 'NetHAT LED Brightness':
                    self.led_brigthness.value = _d["value"]
                    self.led_brigthness.display()

        except Exception as ex:
            return False
        return True


    def wf_stats(self, wf):

        abs_wf = np.abs(wf.astype(int))
        return {'saturation': np.sum(abs_wf >= MAX_ABS_INT16) / len(wf), 'mean_abs': np.mean(abs_wf)}

    def read_audio_data(self) -> bool:
        try:

            audio_data = self._audioreader.read()
            if audio_data is None:
                return False

            timestamp, in_data, frame_count, time_info, status_flags = audio_data

            if in_data is None or len(in_data) == 0:
                return False

            _stats = self.wf_stats(np.frombuffer(in_data, dtype='int16'))
            _vol =_stats["mean_abs"]

            if _vol > MAX_ABS_INT16 - 1:
                _vol = MAX_ABS_INT16 - 1

            self.audio_volume.value = _vol
            self.audio_volume.display()
            #if _stats["mean_abs"] < AUDIO_SILENCE_THRESHOLD:

        except Exception as ex:
            return False

        return True

    def async_data_reading(self):

        time.sleep(2)  # allow npyscreen to start
        while self.editing:
            if not self.read_plc_data() and not self.read_audio_data():
                time.sleep(0.1)

        self._plcreader.close()
        self._audioreader.close()

    def edit(self):
        self._plc_th.start()
        super().edit()


class TestApp(nps.NPSApp):
    def __init__(self, plcreader: PlcReader, audioreader: PyAudioSourceReader):
        super().__init__()
        self._plcreader = plcreader
        self._audioreader=audioreader


    def main(self):
        _f = DemoForm(name="PLC Monitor", plcreader = self._plcreader, audioreader = self._audioreader)
        _f.edit()


if __name__ == '__main__':

    # workon p3
    # cd /Users/vmacari/projects/OtoBox/python/stream2py/stream2py/examples
    # export PYTHONPATH=/Users/vmacari/projects/OtoBox/python/stream2py/


    preader = PlcReader('192.168.0.19', items_to_read=read_items,
                        rack=0, slot=0, sleep_time=0)

    areader = PyAudioSourceReader(rate=44100, width=2, channels=1,
                                  input_device_index=1, frames_per_buffer=4096)

    try:
        areader.open()
        pprint(areader.info)
    except Exception as ex:
        loge(ex)
        exit(-1)

    try:
        if not preader.open():
            preader.close()
            loge("ERROR: Failed to connect to PLC ?")
            exit(-1)

    except Exception as ex:
        loge(ex)
        exit(-1)

    logi("Connected")



    TestApp(plcreader= preader, audioreader = areader).run()


