#!/usr/bin/env python

import os
import sys
import time
import json
import requests


class MyPhantomDecisionEngine(object):

    def __init__(self):

        self.user_id = os.environ['USER_ID']
        self.token = os.environ['TOKEN']
        self.api_url = os.environ.get('PHANTOM_URL', "https://phantom.nimbusproject.org/api/dev")

        self.domain_name = "my_domain"
        self.launch_config_name = "my_launch_config"
        self.vm_image = "hello-phantom.gz"
        self.max_vms = 4
        self.key_name = "phantomkey"
        self.image_type = "m1.small"
        self.clouds = ["hotel", "sierra"]

        self.create_launch_configuration()
        self.create_domain()
        self.run_policy()

    def create_launch_configuration(self):

        # Get a list of existing launch configurations
        r = requests.get("%s/launchconfigurations" % self.api_url, auth=(self.user_id, self.token))
        existing_launch_configurations = r.json()
        existing_lc_names = [lc.get('name') for lc in existing_launch_configurations]

        # Create launch configuration if it doesn't exist
        if self.launch_config_name not in existing_lc_names:

            print "Creating launch config '%s'" % self.launch_config_name
            new_lc = {
                'name': self.launch_config_name,
                'cloud_params': {}
            }

            rank = 0
            for cloud in self.clouds:
                rank = rank + 1
                cloud_param = {
                    'image_id': self.vm_image,
                    'instance_type': self.image_type,
                    'max_vms': self.max_vms,
                    'common': True,
                    'rank': rank,
                }
                new_lc['cloud_params'][cloud] = cloud_param

            r = requests.post("%s/launchconfigurations" % self.api_url,
                data=json.dumps(new_lc), auth=(self.user_id, self.token))

        else:
            print "Launch config '%s' has already been added, skipping..." % (
                self.launch_config_name,)

    def create_domain(self):

        # Check if domain already exists
        r = requests.get("%s/domains" % self.api_url, auth=(self.user_id, self.token))
        existing_domains = r.json()

        domain_exists = False
        domain_id = None
        for domain in existing_domains:
            if domain.get('name') == self.domain_name:
                domain_exists = True
                domain_id = domain.get('id')
                break

        # Create our domain
        print "Creating domain %s" % self.domain_name
        new_domain = {
            'name': self.domain_name,
            'de_name': 'multicloud',
            'lc_name': self.launch_config_name,
            'vm_count': 0
        }

        if domain_exists:
            r = requests.put("%s/domains/%s" % (self.api_url, domain_id),
                data=json.dumps(new_domain), auth=(self.user_id, self.token))
            if r.status_code != 200:
                sys.exit("Error: %s" % r.text)
        else:
            r = requests.post("%s/domains" % self.api_url,
                data=json.dumps(new_domain), auth=(self.user_id, self.token))
            if r.status_code != 201:
                sys.exit("Error: %s" % r.text)

    def run_policy(self):

        r = requests.get("%s/domains" % self.api_url, auth=(self.user_id, self.token))
        existing_domains = r.json()
        domain = None
        for _domain in existing_domains:
            if _domain.get('name') == self.domain_name:
                domain = _domain
                break
        else:
            raise SystemExit("Couldn't get domain %s" % self.domain_name)

        vm_count = 1
        print "set %s vm_count to %s" % (self.domain_name, vm_count)
        domain['vm_count'] = vm_count
        r = requests.put("%s/domains/%s" % (self.api_url, domain.get('id')),
                data=json.dumps(domain), auth=(self.user_id, self.token))
        time.sleep(10)

        vm_count += 1
        print "set %s vm_count to %s" % (self.domain_name, vm_count)
        domain['vm_count'] = vm_count
        r = requests.put("%s/domains/%s" % (self.api_url, domain.get('id')),
                data=json.dumps(domain), auth=(self.user_id, self.token))
        time.sleep(10)

        vm_count += 1
        print "set %s vm_count to %s" % (self.domain_name, vm_count)
        domain['vm_count'] = vm_count
        r = requests.put("%s/domains/%s" % (self.api_url, domain.get('id')),
                data=json.dumps(domain), auth=(self.user_id, self.token))
        time.sleep(10)

        vm_count += 1
        print "set %s vm_count to %s" % (self.domain_name, vm_count)
        domain['vm_count'] = vm_count
        r = requests.put("%s/domains/%s" % (self.api_url, domain.get('id')),
                data=json.dumps(domain), auth=(self.user_id, self.token))
        time.sleep(10)

        print "let domain settle for 60s"
        time.sleep(60)

        vm_count = 0
        domain['vm_count'] = vm_count
        r = requests.put("%s/domains/%s" % (self.api_url, domain.get('id')),
                data=json.dumps(domain), auth=(self.user_id, self.token))
        print "set %s vm_count back to %s" % (self.domain_name, vm_count)

MyPhantomDecisionEngine()
