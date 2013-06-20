#!/usr/bin/env python

import os
import sys
import json
import requests

user_id = os.environ['USER_ID']
token = os.environ['TOKEN']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")


name = "hterX"
image_id = "ami-deadbeaf"
cloud = "hotel"
max_vms = -1
common = True
key_name = "ooi"
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
created_lc = r.json()

print "LC created with id %s" % created_lc.get('id')

r = requests.delete("%s/launchconfigurations/%s" % (api_url, created_lc.get('id')), auth=(user_id, token))

if r.status_code != 204:
    sys.exit("Problem deleting lc %s" % r.text)

print "LC %s deleted" % created_lc.get('id')
