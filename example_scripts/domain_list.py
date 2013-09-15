#!/usr/bin/env python

import os
import sys

import requests

user_id = os.environ['USER_ID']
token = os.environ['TOKEN']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")

r = requests.get("%s/domains" % api_url, auth=(user_id, token))
if r.status_code != 200:
    sys.exit("Request failed with status code %d" % r.status_code)

all_domains = r.json()

for domain in all_domains:
    r = requests.get("%s/domains/%s/instances" % (api_url, domain.get('id')), auth=(user_id, token))
    instances = r.json()
    print domain.get('name')
    print "\t%s : %s" % (domain.get('lc_name'), domain.get('vm_count'))
    print "\tInstances:"
    print "\t---------"
    for i in instances:
        print "\t\t%s : %s " % (i.get("cloud").split("/")[-1], i.get('lifecycle_state'))
