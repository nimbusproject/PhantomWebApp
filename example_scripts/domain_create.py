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
vm_count = int(sys.argv[3])
de_name = "multicloud"

new_domain = {
    'name': name,
    'de_name': de_name,
    'lc_name': lc_name,
    'vm_count': vm_count
}

r = requests.post("%s/domains" % api_url, data=json.dumps(new_domain), auth=(user_id, token))
if r.status_code != 201:
    sys.exit("Error %d: %s" % (r.status_code, r.text))
