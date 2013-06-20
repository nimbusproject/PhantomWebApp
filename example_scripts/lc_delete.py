#!/usr/bin/env python

import os
import sys
import requests

user_id = os.environ['USER_ID']
token = os.environ['TOKEN']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")

try:
    name = sys.argv[1]
except:
    sys.exit("USAGE: %s lcname")

r = requests.get("%s/launchconfigurations" % api_url, auth=(user_id, token))
all_lcs = r.json()

lc_id = None
for lc in all_lcs:
    if lc.get('name') == name:
        lc_id = lc.get('id')
        break
else:
    sys.exit("Could not find LC with name %s" % name)

r = requests.delete("%s/launchconfigurations/%s" % (api_url, lc_id), auth=(user_id, token))

if r.status_code != 204:
    sys.exit("Problem deleting lc %s" % r.text)
