from winreg import *
from datetime import datetime, timedelta
from dateutil import tz
from PySide6.QtCore import (Slot, QRunnable)
from enum import Enum
import log_handler, time, urllib.request, json, logging

# TODO make this a changable option
CONST_TIMEZONE = 'America/Edmonton'


# The ping ping class
class JobRunner(QRunnable):

    def __init__(self, url):
        super().__init__()
        self.state = False
        self.killed = False
        self.url = url
        self.mic_hkey = r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\NonPackaged'
        self.cam_hkey = r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged'

        # This is the logging piece
        self.logger = logging.getLogger("JobRunner")
        self.logHandler = log_handler.RunnableLogger()
        self.logHandler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(self.logHandler)
        self.logger.setLevel(logging.INFO)

    # The core of it! WooOo!
    @Slot()
    def run(self):
        while self.state is False:
            time.sleep(0)
        while True:
            mic_state = self.determine_call_status(self.get_time_stamp('microphone'))
            vid_state = self.determine_call_status(self.get_time_stamp('camera'))

            if mic_state[1] is True:
                self.logger.info("%s is using the microphone.", mic_state[0])

            if vid_state[1] is True:
                self.logger.info("%s is using the webcam.", vid_state[0])

            try:
                self.json_request(self.url, {'mic_state': mic_state[1],
                                             'vid_state': vid_state[1]})
                self.logger.info('Sending state to %s', format(self.url))
            except urllib.error.URLError:
                self.logger.error("Connection Error, is server up?")

            time.sleep(1)
            while self.state is False:
                time.sleep(0)
                if self.killed is True:
                    break
            if self.killed is True:
                break

    # Let us know if we should be running or not
    @Slot()
    def clicked(self):
        if self.state is False:
            self.state = True
        else:
            self.state = False

    @Slot()
    def set_url(self, url):
        self.url = url

    def exit(self):
        self.killed = True

    # Convert Microsoft's screwy registry values into something usable
    def return_posix_time(self, registry_time_val):
        last_used_sec = int(hex(registry_time_val), 16) / 10
        last_used_date = datetime(1601, 1, 1) + timedelta(microseconds=last_used_sec)
        last_used_date = last_used_date.replace(tzinfo=tz.gettz('UTC'))
        return last_used_date.astimezone(tz.gettz(CONST_TIMEZONE))

    # Get retrieve the time stamps for the selected device
    def get_time_stamp(self, device):
        if device == 'microphone':
            hkey_string = self.mic_hkey
        elif device == 'camera':
            hkey_string = self.cam_hkey
        else:
            raise Exception("No valid device was requested")

        registry = ConnectRegistry(None, HKEY_CURRENT_USER)
        base_hkey = OpenKey(registry, hkey_string)
        app_time_stamps = {}
        # iterate through the available applications to see if their start time is later than the stored end time
        for i in range(99999):
            try:
                sub_hkey_str = EnumKey(base_hkey, i)
                sub_hkey = OpenKey(registry, hkey_string + "\\" + sub_hkey_str)
                last_time_start = self.return_posix_time(QueryValueEx(sub_hkey, 'LastUsedTimeStart')[0])
                last_time_stop = self.return_posix_time(QueryValueEx(sub_hkey, 'LastUsedTimeStop')[0])
                app_name = sub_hkey_str.split('#')[-1]
                app_time_stamps[app_name] = {'last_time_start': last_time_start, 'last_time_stop': last_time_stop}
            except EnvironmentError:
                break
        return app_time_stamps

    # Helper function for maths
    def get_min_sec(self, difference):
        return divmod(difference.days * 86400 + difference.seconds, 60)

    # Get call status, if in a call return the app name as well
    def determine_call_status(self, app_time_stamps):
        current_time = datetime.now().replace(tzinfo=tz.gettz(CONST_TIMEZONE))
        # iterate throw the apps and check their time difference.
        for app in app_time_stamps:
            diff_app = self.get_min_sec((app_time_stamps[app]['last_time_stop'] - app_time_stamps[app]['last_time_start']))
            if diff_app[0] < 0:
                return app, True
        return None, False

    # Json request sender
    def json_request(self, myurl, json_body):
        req = urllib.request.Request(myurl)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        json_data = json.dumps(json_body)
        json_bytes = json_data.encode('utf-8')
        req.add_header('Content-Length', len(json_bytes))
        urllib.request.urlopen(req, json_bytes)

