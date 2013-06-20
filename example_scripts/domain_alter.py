#!/usr/bin/env python

import os
import sys
import json
import requests

user_id = os.environ['USER_ID']
token = os.environ['TOKEN']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")

if len(sys.argv) != 3:
    sys.exit("usage: %s name size" % sys.argv[0])

name = sys.argv[1]
size = int(sys.argv[2])

r = requests.get("%s/domains" % api_url, auth=(user_id, token))
all_domains = r.json()

domain_to_change = None
for domain in all_domains:
    if domain.get('name') == name:
        domain_to_change = domain
        break
else:
    sys.exit("Couldn't find domain with name %s" % name)

domain_to_change['vm_count'] = size

r = requests.put("%s/domains/%s" % (api_url, domain_to_change.get('id')),
        data=json.dumps(domain_to_change), auth=(user_id, token))
if r.status_code != 200:
    sys.exit("Problem updating domain %s" % r.text)
