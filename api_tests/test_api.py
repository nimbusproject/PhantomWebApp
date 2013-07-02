#!/usr/bin/env python

import json
import os
import sys
import time
import uuid

import requests

username = os.environ['PHANTOM_USERNAME']
password = os.environ['PHANTOM_IAAS_SECRET_KEY']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")
image_id = os.environ['PHANTOM_IMAGE']
cloud = os.environ['PHANTOM_IAAS']

# Get token first
r = requests.post("%s/token" % api_url, data={"username": username, "password": password})
token_response = r.json()
if token_response.get("success", False):
    user_id = token_response.get("user")
    token = token_response.get("token")
else:
    print "Failed to create token: %s" % r.text
    sys.exit(1)

r = requests.get("%s/launchconfigurations" % api_url, auth=(user_id, token))
initial_lc = r.json()

lc_name = 'lc-' + uuid.uuid4().hex
max_vms = -1
common = True
it = "m1.small"
user_data = 'USERDATA_TEST_STRING'

new_lc = {
    'name': lc_name,
    'cloud_params': {
        cloud: {
            "image_id": image_id,
            "instance_type": it,
            "max_vms": max_vms,
            "common": common,
            "rank": 1,
            "user_data": 'USERDATA_TEST_STRING'
        }
    }
}

created_lc = None
try:
    r = requests.post("%s/launchconfigurations" % api_url, data=json.dumps(new_lc), auth=(user_id, token))
    created_lc = r.json()

    r = requests.get("%s/launchconfigurations" % api_url, auth=(user_id, token))
    after_create = r.json()

    assert len(after_create) == len(initial_lc) + 1
    assert after_create[0].get('name') == lc_name
    assert after_create[0]['cloud_params'][cloud].get('image_id') == image_id
    assert after_create[0]['cloud_params'][cloud].get('instance_type') == it
    assert after_create[0]['cloud_params'][cloud].get('user_data') == user_data

    r = requests.get("%s/domains" % api_url, auth=(user_id, token))
    initial = r.json()

    name = 'asg-' + uuid.uuid4().hex
    vm_count = 1
    de_name = "multicloud"

    new_domain = {
        'name': name,
        'de_name': de_name,
        'lc_name': lc_name,
        'vm_count': vm_count
    }

    r = requests.post("%s/domains" % api_url, data=json.dumps(new_domain), auth=(user_id, token))
    if r.status_code != 201:
        sys.exit("Error: %s" % r.text)

    new_domain = r.json()
    domain_id = new_domain.get('id')

    time.sleep(10)

    r = requests.get("%s/domains" % api_url, auth=(user_id, token))
    after_create = r.json()

    asg_list = filter(lambda a: a['name'] == name, after_create)
    assert len(asg_list) == 1

    r = requests.get("%s/domains/%s/instances" % (api_url, domain_id), auth=(user_id, token))
    instances = r.json()
    assert len(instances) == vm_count

    r = requests.delete("%s/domains/%s" % (api_url, domain_id), auth=(user_id, token))
    if r.status_code != 204:
        sys.exit("Problem deleting domain %s" % r.text)

    time.sleep(30)

    r = requests.get("%s/domains" % api_url, auth=(user_id, token))
    after_delete = r.json()
    assert len(after_delete) == len(initial)

finally:
    if created_lc is not None:
        r = requests.delete("%s/launchconfigurations/%s" % (api_url, created_lc.get('id')), auth=(user_id, token))
        if r.status_code != 204:
            sys.exit("Problem deleting launch configuration %s" % r.text)

    r = requests.get("%s/launchconfigurations" % api_url, auth=(user_id, token))
    after_delete = r.json()
    assert len(after_delete) == len(initial_lc)
