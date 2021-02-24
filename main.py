# This is code to tell a remote light that I made look like an Owl, to light up so my girlfriend would stop knocking
# on my door when I'm in a call
#
# Author: A homunculus

from winreg import *
from datetime import datetime, timedelta
from dateutil import tz
import time
import urllib.request
import json
import sys

CONST_TIMEZONE = 'America/Edmonton'


# Convert Microsoft's screwy registry values into something usable
def return_posix_time(registry_time_val):
    last_used_sec = int(hex(registry_time_val), 16) / 10
    last_used_date = datetime(1601, 1, 1) + timedelta(microseconds=last_used_sec)
    last_used_date = last_used_date.replace(tzinfo=tz.gettz('UTC'))
    return last_used_date.astimezone(tz.gettz(CONST_TIMEZONE))


# Helper function - mic - hkey
def get_microphone_time_stamp():
    hkey_string = r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\NonPackaged'

    return get_time_stamp(hkey_string)


# Helper function - webcam hkey
def get_webcam_time_stamp():
    hkey_string = r'SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam\NonPackaged'
    return get_time_stamp(hkey_string)


def get_time_stamp(hkey_string):
    registry = ConnectRegistry(None, HKEY_CURRENT_USER)
    base_hkey = OpenKey(registry, hkey_string)
    app_time_stamps = {}
    # iterate through the available applications to see if their start time is later than the stored end time
    for i in range(99999):
        try:
            sub_hkey_str = EnumKey(base_hkey, i)
            sub_hkey = OpenKey(registry, hkey_string + "\\" + sub_hkey_str)
            last_time_start = return_posix_time(QueryValueEx(sub_hkey, 'LastUsedTimeStart')[0])
            last_time_stop = return_posix_time(QueryValueEx(sub_hkey, 'LastUsedTimeStop')[0])
            app_name = sub_hkey_str.split('#')[-1]
            app_time_stamps[app_name] = {'last_time_start': last_time_start, 'last_time_stop': last_time_stop}
        except EnvironmentError:
            break
    return app_time_stamps


# Helper function for maths
def get_min_sec(difference):
    return divmod(difference.days * 86400 + difference.seconds, 60)


# Get call status, if in a call return the app name as well
def determine_call_status(app_time_stamps):
    current_time = datetime.now().replace(tzinfo=tz.gettz(CONST_TIMEZONE))

    for app in app_time_stamps:
        diff_start = get_min_sec(current_time - app_time_stamps[app]['last_time_start'])
        diff_stop = get_min_sec(current_time - app_time_stamps[app]['last_time_stop'])
        diff_app = get_min_sec(app_time_stamps[app]['last_time_stop'] - app_time_stamps[app]['last_time_start'])
        if diff_app[0] < 0:
            return app, True
    return None, False

# JSon request sender
def json_request(myurl, json_body):
    req = urllib.request.Request(myurl)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(json_body)
    jsondataasbytes = jsondata.encode('utf-8')  # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    response = urllib.request.urlopen(req, jsondataasbytes)


if __name__ == '__main__':
    while True:
        # Boring loop
        mic_state = determine_call_status(get_microphone_time_stamp())
        vid_state = determine_call_status(get_webcam_time_stamp())

        json_request(str(sys.argv[1]), {'mic_state': mic_state[1],
                                        'vid_state': vid_state[1]})
        time.sleep(5)
