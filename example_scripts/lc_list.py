#!/usr/bin/env python

import os
import sys
import json
import requests

user_id = os.environ['user_id']
token = os.environ['token']
api_url = os.environ.get('phantom_url', "https://phantom.nimbusproject.org/api/dev")

r = requests.get("%s/launchconfigurations" % api_url, auth=(user_id, token))
all_lcs = r.json()

for lc in all_lcs:
    print lc['name']
