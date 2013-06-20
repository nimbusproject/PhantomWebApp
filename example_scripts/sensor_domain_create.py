#!/usr/bin/env python

import os
import sys
import json
import requests

user_id = os.environ['USER_ID']
token = os.environ['TOKEN']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")

if len(sys.argv) < 4:
    sys.exit("usage: %s name lc_name vm_count" % sys.argv[0])

name = sys.argv[1]
lc_name = sys.argv[2]
minimum_vms = sys.argv[3]
maximum_vms = sys.argv[4]
de_name = 'sensor'

scale_up_threshold = 2.0
scale_up_n_vms = 1
scale_down_threshold = 0.5
scale_down_n_vms = 1
cooldown = 60
monitor_sensors = "proc.loadavg.1min"
sensor_metric = "proc.loadavg.1min"

new_domain = {
    'name': name,
    'de_name': de_name,
    'lc_name': lc_name,
    'sensor_minimum_vms': minimum_vms,
    'sensor_maximum_vms': maximum_vms,
    'sensor_scale_up_threshold': scale_up_threshold,
    'sensor_scale_up_vms': scale_down_n_vms,
    'sensor_scale_down_threshold': scale_down_threshold,
    'sensor_scale_down_vms': scale_down_n_vms,
    'sensor_cooldown': cooldown,
    'monitor_sensors': monitor_sensors,
    'sensor_metric': sensor_metric,
}

r = requests.post("%s/domains" % api_url, data=json.dumps(new_domain), auth=(user_id, token))
if r.status_code != 200:
    sys.exit("Error: %s" % r.text)
