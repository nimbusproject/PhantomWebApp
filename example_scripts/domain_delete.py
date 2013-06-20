#!/usr/bin/env python

import os
import sys
import requests

user_id = os.environ['USER_ID']
token = os.environ['TOKEN']
api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")

if len(sys.argv) != 2:
    sys.exit("usage: %s name" % sys.argv[0])

name = sys.argv[1]

r = requests.get("%s/domains" % api_url, auth=(user_id, token))
all_domains = r.json()

domain_id = None
for domain in all_domains:
    if domain.get('name') == name:
        domain_id = domain.get('id')
        break
else:
    sys.exit("Couldn't find domain with name %s" % name)

print "deleting %s" % (domain_id)
r = requests.delete("%s/domains/%s" % (api_url, domain_id), auth=(user_id, token))

if r.status_code != 204:
    sys.exit("Problem deleting domain %s" % r.text)
