#!/usr/bin/env python

import os
import sys
import json
import requests

user_id = os.environ['USER_ID']
token = os.environ['TOKEN']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")


try:
    name = sys.argv[1]
    image_id = sys.argv[2]
    cloud = sys.argv[3]
except:
    sys.exit("Usage: %s LCNAME IMAGE_ID CLOUDNAME" % sys.argv[0])
max_vms = -1
common = True
key_name = "phantomkey"
it = "m1.small"

new_lc = {
    'name': name,
    'cloud_params': {
        cloud: {
            "image_id": image_id,
            "instance_type": it,
            "max_vms": max_vms,
            "common": common,
            "rank": 1,
            "user_data": None
        }
    }
}

r = requests.post("%s/launchconfigurations" % api_url, data=json.dumps(new_lc), auth=(user_id, token))
if r.status_code != 201:
    sys.exit("Failed to create LC: %s" % r.text)
created_lc = r.json()

print "LC created with id %s" % created_lc.get("id")
