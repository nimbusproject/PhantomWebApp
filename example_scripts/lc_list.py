#!/usr/bin/env python

import os
import sys
import json
import requests

user_id = os.environ['USER_ID']
token = os.environ['TOKEN']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")

r = requests.get("%s/launchconfigurations" % api_url, auth=(user_id, token))
if r.status_code == 200:
    all_lcs = r.json()
else:
    sys.exit("Failed to list launch configurations: %s" % r.text)

for lc in all_lcs:
    print lc['name']
