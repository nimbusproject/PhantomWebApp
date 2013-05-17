import json

from django.contrib.auth.models import User
from django.test.client import Client
from django.utils import unittest
from mock import patch

from phantomweb.models import HostMaxPairDB, LaunchConfiguration, PhantomUser, RabbitInfoDB


def setUpModule():
    user = User.objects.create_user('fred', password='secret')
    user.save()
    phantom_user = PhantomUser(username='fred', access_key_id='freds_access_key_id')
    phantom_user.save()
    rabbitmq_info = RabbitInfoDB(rabbithost='localhost',
                                 rabbituser='guest',
                                 rabbitpassword='guest',
                                 rabbitexchange='default_dashi_exchange',
                                 rabbitport=5782,
                                 rabbitssl=False)
    rabbitmq_info.save()
    launch_configuration = LaunchConfiguration(name='testlc', username='fred')
    launch_configuration.save()
    host_max_pair = HostMaxPairDB.objects.create(cloud_name="site1", max_vms=-1,
        launch_config=launch_configuration, rank=1, common_image=True)
    host_max_pair.save()

    launch_configuration = LaunchConfiguration(name='deletabletestlc', username='fred')
    launch_configuration.save()
    host_max_pair = HostMaxPairDB.objects.create(cloud_name="site1", max_vms=-1,
        launch_config=launch_configuration, rank=1, common_image=True)
    host_max_pair.save()


class SitesTestCase(unittest.TestCase):
    def test_get_sites(self):
        with patch('ceiclient.client.DTRSClient.list_sites') as mock_method:
            mock_method.return_value = ['site1', 'site2']
            c = Client()
            c.login(username='fred', password='secret')

            response = c.get('/api/dev/sites')
            self.assertEqual(response.status_code, 200)
            content = json.loads(response.content)
            self.assertEqual(len(content), 2)
            self.assertIn({'credentials': '/api/dev/credentials/site1', 'id': 'site1',
                'uri': '/api/dev/sites/site1'}, content)
            self.assertIn({'credentials': '/api/dev/credentials/site2', 'id': 'site2',
                'uri': '/api/dev/sites/site2'}, content)

    def test_not_get_sites(self):
        c = Client()
        c.login(username='fred', password='secret')

        response = c.post('/api/dev/sites')
        self.assertEqual(response.status_code, 405)

        response = c.put('/api/dev/sites')
        self.assertEqual(response.status_code, 405)

        response = c.delete('/api/dev/sites')
        self.assertEqual(response.status_code, 405)

    def test_get_one_site(self):
        with patch('ceiclient.client.DTRSClient.list_sites') as mock_method:
            mock_method.return_value = ['site1', 'site2']
            c = Client()
            c.login(username='fred', password='secret')

            response = c.get('/api/dev/sites/site1')
            self.assertEqual(response.status_code, 200)
            content = json.loads(response.content)
            self.assertEqual({'credentials': '/api/dev/credentials/site1', 'id': 'site1',
                'uri': '/api/dev/sites/site1'}, content)

            response = c.get('/api/dev/sites/site2')
            self.assertEqual(response.status_code, 200)
            content = json.loads(response.content)
            self.assertEqual({'credentials': '/api/dev/credentials/site2', 'id': 'site2',
                'uri': '/api/dev/sites/site2'}, content)

            response = c.get('/api/dev/sites/site3')
            self.assertEqual(response.status_code, 404)

    def test_not_get_one_site(self):
        c = Client()
        c.login(username='fred', password='secret')

        response = c.post('/api/dev/sites/site1')
        self.assertEqual(response.status_code, 405)

        response = c.put('/api/dev/sites/site1')
        self.assertEqual(response.status_code, 405)

        response = c.delete('/api/dev/sites/site1')
        self.assertEqual(response.status_code, 405)


class CredentialsTestCase(unittest.TestCase):
    def test_get_credentials(self):
        with patch('ceiclient.client.DTRSClient.describe_site') as mock_describe_site:
            mock_describe_site.return_value = {}

            with patch('ceiclient.client.DTRSClient.list_credentials') as mock_list_credentials:
                mock_list_credentials.return_value = ['site1', 'site2']

                def describe_credentials(caller, site_name):
                    if caller == "freds_access_key_id" and site_name == "site1":
                        return {
                            "access_key": "site1_access_key_id",
                            "secret_key": "site1_secret_access_key",
                            "key_name": "site1_phantom_ssh_key"
                        }
                    elif caller == "freds_access_key_id" and site_name == "site2":
                        return {
                            "access_key": "site2_access_key_id",
                            "secret_key": "site2_secret_access_key",
                            "key_name": "site2_phantom_ssh_key"
                        }
                    else:
                        self.fail("Unknown arguments received")

                with patch('ceiclient.client.DTRSClient.describe_credentials', side_effect=describe_credentials):
                    c = Client()
                    c.login(username='fred', password='secret')

                    response = c.get('/api/dev/credentials')
                    self.assertEqual(response.status_code, 200)
                    content = json.loads(response.content)
                    self.assertEqual(len(content), 2)
                    self.assertIn(
                        {
                            "id": "site1",
                            "access_key": "site1_access_key_id",
                            "secret_key": "site1_secret_access_key",
                            "key_name": "site1_phantom_ssh_key",
                            "uri": "/api/dev/credentials/site1"
                        },
                        content)
                    self.assertIn(
                        {
                            "id": "site2",
                            "access_key": "site2_access_key_id",
                            "secret_key": "site2_secret_access_key",
                            "key_name": "site2_phantom_ssh_key",
                            "uri": "/api/dev/credentials/site2"
                        },
                        content)

    def test_get_credentials_resource(self):
        with patch('ceiclient.client.DTRSClient.describe_site') as mock_describe_site:
            mock_describe_site.return_value = {}

            with patch('ceiclient.client.DTRSClient.list_credentials') as mock_list_credentials:
                mock_list_credentials.return_value = ['site1', 'site2']

                def describe_credentials(caller, site_name):
                    if caller == "freds_access_key_id" and site_name == "site1":
                        return {
                            "access_key": "site1_access_key_id",
                            "secret_key": "site1_secret_access_key",
                            "key_name": "site1_phantom_ssh_key"
                        }
                    elif caller == "freds_access_key_id" and site_name == "site2":
                        return {
                            "access_key": "site2_access_key_id",
                            "secret_key": "site2_secret_access_key",
                            "key_name": "site2_phantom_ssh_key"
                        }
                    else:
                        self.fail("Unknown arguments received")

                with patch('ceiclient.client.DTRSClient.describe_credentials', side_effect=describe_credentials):
                    c = Client()
                    c.login(username='fred', password='secret')

                    response = c.get('/api/dev/credentials/site1')
                    self.assertEqual(response.status_code, 200)
                    content = json.loads(response.content)
                    self.assertEqual(
                        {
                            "id": "site1",
                            "access_key": "site1_access_key_id",
                            "secret_key": "site1_secret_access_key",
                            "key_name": "site1_phantom_ssh_key",
                            "uri": "/api/dev/credentials/site1"
                        },
                        content)

                    response = c.get('/api/dev/credentials/site2')
                    self.assertEqual(response.status_code, 200)
                    content = json.loads(response.content)
                    self.assertEqual(
                        {
                            "id": "site2",
                            "access_key": "site2_access_key_id",
                            "secret_key": "site2_secret_access_key",
                            "key_name": "site2_phantom_ssh_key",
                            "uri": "/api/dev/credentials/site2"
                        },
                        content)

                    response = c.get('/api/dev/credentials/site3')
                    self.assertEqual(response.status_code, 404)

    def test_post_credentials(self):
        with patch('ceiclient.client.DTRSClient.list_sites') as mock_list_sites:
            mock_list_sites.return_value = ["site1", "site2", "site3"]

            with patch('ceiclient.client.DTRSClient.describe_site') as mock_describe_site:
                mock_describe_site.return_value = {}

                with patch('ceiclient.client.DTRSClient.list_credentials') as mock_list_credentials:
                    mock_list_credentials.return_value = ['site1', 'site2']

                    def describe_credentials(caller, site_name):
                        if caller == "freds_access_key_id" and site_name == "site1":
                            return {
                                "access_key": "site1_access_key_id",
                                "secret_key": "site1_secret_access_key",
                                "key_name": "site1_phantom_ssh_key"
                            }
                        elif caller == "freds_access_key_id" and site_name == "site2":
                            return {
                                "access_key": "site2_access_key_id",
                                "secret_key": "site2_secret_access_key",
                                "key_name": "site2_phantom_ssh_key"
                            }
                        else:
                            self.fail("Unknown arguments received")

                    with patch('ceiclient.client.DTRSClient.add_credentials', return_value=None):
                        with patch('ceiclient.client.DTRSClient.describe_credentials',
                                side_effect=describe_credentials):
                            c = Client()
                            c.login(username='fred', password='secret')

                            post_content = {
                                "id": "site3",
                                "access_key": "site3_access_key_id",
                                "secret_key": "site3_secret_access_key",
                                "key_name": "site3_phantom_ssh_key"
                            }
                            response = c.post('/api/dev/credentials',
                                json.dumps(post_content), content_type='application/json')
                            self.assertEqual(response.status_code, 201)
                            content = json.loads(response.content)
                            self.assertEqual(
                                {
                                    "id": "site3",
                                    "access_key": "site3_access_key_id",
                                    "secret_key": "site3_secret_access_key",
                                    "key_name": "site3_phantom_ssh_key",
                                    "uri": "/api/dev/credentials/site3"
                                },
                                content)

    def test_put_credentials(self):
        with patch('ceiclient.client.DTRSClient.list_sites') as mock_list_sites:
            mock_list_sites.return_value = ["site1", "site2"]

            with patch('ceiclient.client.DTRSClient.describe_site') as mock_describe_site:
                mock_describe_site.return_value = {}

                with patch('ceiclient.client.DTRSClient.list_credentials') as mock_list_credentials:
                    mock_list_credentials.return_value = ['site1', 'site2']

                    def describe_credentials(caller, site_name):
                        if caller == "freds_access_key_id" and site_name == "site1":
                            return {
                                "access_key": "site1_access_key_id",
                                "secret_key": "site1_secret_access_key",
                                "key_name": "site1_phantom_ssh_key"
                            }
                        elif caller == "freds_access_key_id" and site_name == "site2":
                            return {
                                "access_key": "site2_access_key_id",
                                "secret_key": "site2_secret_access_key",
                                "key_name": "site2_phantom_ssh_key"
                            }
                        else:
                            self.fail("Unknown arguments received")

                    with patch('ceiclient.client.DTRSClient.update_credentials', return_value=None):
                        with patch('ceiclient.client.DTRSClient.describe_credentials',
                                side_effect=describe_credentials):
                            c = Client()
                            c.login(username='fred', password='secret')

                            post_content = {
                                "id": "site2",
                                "access_key": "site2_access_key_id",
                                "secret_key": "site2_secret_access_key",
                                "key_name": "site2_phantom_ssh_key"
                            }
                            response = c.put('/api/dev/credentials/site2', json.dumps(post_content),
                                content_type='application/json')
                            self.assertEqual(response.status_code, 201)
                            content = json.loads(response.content)
                            self.assertEqual(
                                {
                                    "id": "site2",
                                    "access_key": "site2_access_key_id",
                                    "secret_key": "site2_secret_access_key",
                                    "key_name": "site2_phantom_ssh_key",
                                    "uri": "/api/dev/credentials/site2"
                                },
                                content)

    def test_delete_credentials(self):
        with patch('ceiclient.client.DTRSClient.list_sites') as mock_list_sites:
            mock_list_sites.return_value = ["site1", "site2"]

            with patch('ceiclient.client.DTRSClient.describe_site') as mock_describe_site:
                mock_describe_site.return_value = {}

                with patch('ceiclient.client.DTRSClient.list_credentials') as mock_list_credentials:
                    mock_list_credentials.return_value = ['site1', 'site2']

                    def describe_credentials(caller, site_name):
                        if caller == "freds_access_key_id" and site_name == "site1":
                            return {
                                "access_key": "site1_access_key_id",
                                "secret_key": "site1_secret_access_key",
                                "key_name": "site1_phantom_ssh_key"
                            }
                        elif caller == "freds_access_key_id" and site_name == "site2":
                            return {
                                "access_key": "site2_access_key_id",
                                "secret_key": "site2_secret_access_key",
                                "key_name": "site2_phantom_ssh_key"
                            }
                        else:
                            self.fail("Unknown arguments received")

                    with patch('ceiclient.client.DTRSClient.remove_credentials', return_value=None):
                        with patch('ceiclient.client.DTRSClient.describe_credentials',
                                side_effect=describe_credentials):
                            c = Client()
                            c.login(username='fred', password='secret')

                            response = c.delete('/api/dev/credentials/site2')
                            self.assertEqual(response.status_code, 204)


class LaunchConfigurationTestCase(unittest.TestCase):
    def test_get_launchconfigurations(self):
        def describe_dt(caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "testlc":
                return {
                    "mappings": {
                        "site1": {
                            "iaas_image": "hello-phantom.gz",
                            "iaas_allocation": "m1.small"
                        }
                    },
                    "contextualization": {
                        "method": "userdata",
                        "userdata": "Hello Cloud!"
                    }
                }
            else:
                self.fail("Unknown arguments received")

        with patch('ceiclient.client.DTRSClient.describe_dt', side_effect=describe_dt):
            c = Client()
            c.login(username='fred', password='secret')

            response = c.get('/api/dev/launchconfigurations')
            self.assertEqual(response.status_code, 200)
            content = json.loads(response.content)
            self.assertEqual(len(content), 1)
            lc = content[0]
            lc_id = lc["id"]
            self.assertEqual(lc["name"], "testlc")
            self.assertEqual(lc["owner"], "fred")
            self.assertEqual(lc["uri"], "/api/dev/launchconfigurations/%s" % lc_id)

            cloud_param = lc["cloud_params"][lc["cloud_params"].keys()[0]]
            self.assertEqual(cloud_param["max_vms"], -1)
            self.assertEqual(cloud_param["common"], True)
            self.assertEqual(cloud_param["rank"], 1)
            self.assertEqual(cloud_param["image_id"], "hello-phantom.gz")
            self.assertEqual(cloud_param["instance_type"], "m1.small")
            self.assertEqual(cloud_param["user_data"], "Hello Cloud!")

    def test_get_launchconfiguration_resource(self):
        def describe_dt(caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "testlc":
                return {
                    "mappings": {
                        "site1": {
                            "iaas_image": "hello-phantom.gz",
                            "iaas_allocation": "m1.small"
                        }
                    },
                    "contextualization": {
                        "method": "userdata",
                        "userdata": "Hello Cloud!"
                    }
                }
            else:
                self.fail("Unknown arguments received")

        with patch('ceiclient.client.DTRSClient.describe_dt', side_effect=describe_dt):
            c = Client()
            c.login(username='fred', password='secret')
            lc = LaunchConfiguration.objects.get(name='testlc', username='fred')
            lc_id = lc.id

            response = c.get('/api/dev/launchconfigurations/%s' % lc_id)
            self.assertEqual(response.status_code, 200)
            lc = json.loads(response.content)
            #print lc
            self.assertEqual(lc["name"], "testlc")
            self.assertEqual(lc["owner"], "fred")
            self.assertEqual(lc["uri"], "/api/dev/launchconfigurations/%s" % lc_id)

            cloud_param = lc["cloud_params"][lc["cloud_params"].keys()[0]]
            self.assertEqual(cloud_param["max_vms"], -1)
            self.assertEqual(cloud_param["common"], True)
            self.assertEqual(cloud_param["rank"], 1)
            self.assertEqual(cloud_param["image_id"], "hello-phantom.gz")
            self.assertEqual(cloud_param["instance_type"], "m1.small")
            self.assertEqual(cloud_param["user_data"], "Hello Cloud!")

            response = c.get('/api/dev/launchconfigurations/UnknownID')
            self.assertEqual(response.status_code, 404)

    def test_post_launchconfiguration_resource(self):
        def describe_dt(caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "testlc":
                return {
                    "mappings": {
                        "hotel": {
                            "iaas_image": "hello-phantom.gz",
                            "iaas_allocation": "m1.small"
                        }
                    },
                    "contextualization": {
                        "method": "userdata",
                        "userdata": "Hello Cloud!"
                    }
                }
            else:
                self.fail("Unknown arguments received")

        def list_credentials(self, caller):
            if caller == "freds_access_key_id":
                return ['hotel', 'site2']
            else:
                self.fail("Unknown arguments received")

        def describe_site(self, caller, site):
            if caller == "freds_access_key_id":
                return {}
            else:
                self.fail("Unknown arguments received")

        def describe_credentials(self, caller, site):
            if caller == "freds_access_key_id":
                r = {
                    'access_key': 'hello',
                    'secret_key': 'secret',
                    'key_name': 'key'
                }
                return r
            else:
                self.fail("Unknown arguments received")

        with patch.multiple('ceiclient.client.DTRSClient', describe_dt=describe_dt,
                list_credentials=list_credentials, describe_site=describe_site,
                describe_credentials=describe_credentials):
            c = Client()
            c.login(username='fred', password='secret')

            post_content = {
                "name": "mysecondlc",
                "cloud_params": {
                    "hotel": {
                        "image_id": "hello-cloud",
                        "instance_type": "m1.large",
                        "max_vms": -1,
                        "common": True,
                        "rank": 1,
                        "user_data": "Hello World"
                    }
                }
            }
            response = c.post('/api/dev/launchconfigurations', json.dumps(post_content),
                content_type='application/json')
            self.assertEqual(response.status_code, 201)
            lc = json.loads(response.content)
            self.assertEqual(lc["name"], "mysecondlc")
            self.assertEqual(lc["owner"], "fred")
            assert lc["id"]
            assert lc["uri"].startswith("/api/dev/launchconfigurations/")

            cloud_param = lc["cloud_params"][lc["cloud_params"].keys()[0]]
            self.assertEqual(cloud_param["max_vms"], -1)
            self.assertEqual(cloud_param["common"], True)
            self.assertEqual(cloud_param["rank"], 1)
            self.assertEqual(cloud_param["image_id"], "hello-cloud")
            self.assertEqual(cloud_param["instance_type"], "m1.large")
            self.assertEqual(cloud_param["user_data"], "Hello World")

            # Ensure we can't post twice
            response = c.post('/api/dev/launchconfigurations', json.dumps(post_content),
                content_type='application/json')
            self.assertEqual(response.status_code, 302)
            assert response['Location'].endswith("/api/dev/launchconfigurations/%s" % lc["id"])

    def test_put_launchconfiguration_resource(self):
        def describe_dt(caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "testlc":
                return {
                    "mappings": {
                        "hotel": {
                            "iaas_image": "hello-phantom.gz",
                            "iaas_allocation": "m1.small"
                        }
                    },
                    "contextualization": {
                        "method": "userdata",
                        "userdata": "Hello Cloud!"
                    }
                }
            else:
                self.fail("Unknown arguments received")

        def list_credentials(self, caller):
            if caller == "freds_access_key_id":
                return ['hotel', 'site2']
            else:
                self.fail("Unknown arguments received")

        def describe_site(self, caller, site):
            if caller == "freds_access_key_id":
                return {}
            else:
                self.fail("Unknown arguments received")

        def describe_credentials(self, caller, site):
            if caller == "freds_access_key_id":
                r = {
                    'access_key': 'hello',
                    'secret_key': 'secret',
                    'key_name': 'key'
                }
                return r
            else:
                self.fail("Unknown arguments received")

        with patch.multiple('ceiclient.client.DTRSClient', describe_dt=describe_dt,
                list_credentials=list_credentials, describe_site=describe_site,
                describe_credentials=describe_credentials):
            c = Client()
            c.login(username='fred', password='secret')

            put_content = {
                "name": "testlc",
                "cloud_params": {
                    "hotel": {
                        "image_id": "goodbye-cloud",
                        "instance_type": "m2.large",
                        "max_vms": 3,
                        "common": False,
                        "rank": 2,
                        "user_data": "Goodbye, Cruel World"
                    }
                }
            }
            lc = LaunchConfiguration.objects.get(name='testlc', username='fred')
            lc_id = lc.id

            response = c.put('/api/dev/launchconfigurations/%s' % lc_id, json.dumps(put_content),
                content_type='application/json')
            self.assertEqual(response.status_code, 200)
            lc = json.loads(response.content)
            self.assertEqual(lc["name"], "testlc")
            self.assertEqual(lc["owner"], "fred")
            self.assertEqual(lc["uri"], "/api/dev/launchconfigurations/%s" % lc_id)

            cloud_param = lc["cloud_params"][lc["cloud_params"].keys()[0]]
            self.assertEqual(cloud_param["max_vms"], 3)
            self.assertEqual(cloud_param["common"], False)
            self.assertEqual(cloud_param["rank"], 2)
            self.assertEqual(cloud_param["image_id"], "goodbye-cloud")
            self.assertEqual(cloud_param["instance_type"], "m2.large")
            self.assertEqual(cloud_param["user_data"], "Goodbye, Cruel World")

    def test_delete_launchconfiguration(self):
        def describe_dt(self, caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "deletabletestlc":
                return {
                    "mappings": {
                        "site1": {
                            "iaas_image": "hello-phantom.gz",
                            "iaas_allocation": "m1.small"
                        }
                    },
                    "contextualization": {
                        "method": "userdata",
                        "userdata": "Hello Cloud!"
                    }
                }
            else:
                self.fail("Unknown arguments received")

        def remove_dt(self, caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "deletabletestlc":
                return None
            else:
                self.fail("Unknown arguments received")

        with patch.multiple('ceiclient.client.DTRSClient', describe_dt=describe_dt, remove_dt=remove_dt):
            c = Client()
            c.login(username='fred', password='secret')
            lc = LaunchConfiguration.objects.get(name='deletabletestlc', username='fred')
            lc_id = lc.id

            response = c.get('/api/dev/launchconfigurations/%s' % lc_id)
            self.assertEqual(response.status_code, 200)

            response = c.delete('/api/dev/launchconfigurations/%s' % lc_id)
            self.assertEqual(response.status_code, 204)

            response = c.get('/api/dev/launchconfigurations/%s' % lc_id)
            self.assertEqual(response.status_code, 404)


class DomainTestCase(unittest.TestCase):
    def test_get_domains(self):
        def list_domains(self, caller):
            print caller
            if caller == "freds_access_key_id":
                return ["domain1", "domain2"]
            else:
                self.fail("Unknown arguments received")

        def describe_domain(self, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "domain1":
                return {
                    'name': 'domain1',
                    'config': {
                        'engine_conf': {
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            if caller == "freds_access_key_id" and domain == "domain2":
                return {
                    'name': 'domain2',
                    'config': {
                        'engine_conf': {
                            'phantom_de_name': 'sensor',
                            'minimum_vms': 1,
                            'maximum_vms': 2,
                            'metric': 'df.1kblocks.used',
                            'monitor_sensors': ['df.1kblocks.used', 'df.1kblocks.total'],
                            'monitor_domain_sensors': ['testy', ],
                            'sample_function': 'Average',
                            'scale_down_n_vms': 1,
                            'scale_down_threshold': 0.1,
                            'scale_up_n_vms': 1,
                            'scale_up_threshold': 0.5,
                            'cooldown_period': 10,
                            'dtname': 'mylc'
                        }
                    }
                }
            else:
                self.fail("Unknown arguments received")

        with patch.multiple('ceiclient.client.EPUMClient', list_domains=list_domains,
                describe_domain=describe_domain):
            c = Client()
            c.login(username='fred', password='secret')

            response = c.get('/api/dev/domains')
            self.assertEqual(response.status_code, 200)

            domains = json.loads(response.content)

            self.assertEqual(len(domains), 2)

            domain_dict = {}
            for domain in domains:
                domain_dict[domain['name']] = domain
            domain1 = domain_dict['domain1']
            domain2 = domain_dict['domain2']

            self.assertEqual(domain1['lc_name'], 'mylc')
            self.assertEqual(domain1['de_name'], 'multicloud')
            self.assertEqual(domain1['name'], 'domain1')
            self.assertEqual(domain1['vm_count'], 1)
            self.assertEqual(domain1['lc_name'], 'mylc')

            self.assertEqual(domain2['de_name'], 'sensor')
            self.assertEqual(domain2['name'], 'domain2')
            self.assertEqual(domain2['monitor_sensors'], 'df.1kblocks.used,df.1kblocks.total')
            self.assertEqual(domain2['sensor_minimum_vms'], 1)
            self.assertEqual(domain2['sensor_maximum_vms'], 2)
            self.assertEqual(domain2['sensor_metric'], 'df.1kblocks.used')
            self.assertEqual(domain2['sensor_scale_down_threshold'], 0.1)
            self.assertEqual(domain2['sensor_scale_down_vms'], 1)
            self.assertEqual(domain2['sensor_scale_up_threshold'], 0.5)
            self.assertEqual(domain2['sensor_scale_up_vms'], 1)

    def test_post_domains(self):
        c = Client()
        c.login(username='fred', password='secret')

        post_content = {
            "name": "myseconddomain",
            "de_name": "sensor",
            "lc_name": "mysecondlc",
            "monitor_sensors": "proc.loadavg.1min,df.inodes.free",
            "sensor_minimum_vms": 1,
            "sensor_maximum_vms": 10,
            "sensor_metric": "proc.loadavg.1min",
            "sensor_scale_down_threshold": "0.5",
            "sensor_scale_down_vms": 1,
            "sensor_scale_up_threshold": 1,
            "sensor_scale_up_vms": 1,
            "sensor_cooldown": 60
        }
        response = c.post('/api/dev/domains',
            json.dumps(post_content), content_type='application/json')
        self.assertEqual(response.status_code, 201)

        domain = json.loads(response.content)
        self.assertEqual(domain["name"], "myseconddomain")
        self.assertEqual(domain["owner"], "fred")
        assert domain["id"]
        assert domain["uri"].startswith("/api/dev/domains/")

        #cloud_param = lc["cloud_params"][lc["cloud_params"].keys()[0]]
        #self.assertEqual(cloud_param["max_vms"], -1)
        #self.assertEqual(cloud_param["common"], True)
        #self.assertEqual(cloud_param["rank"], 1)
        #self.assertEqual(cloud_param["image_id"], "hello-cloud")
        #self.assertEqual(cloud_param["instance_type"], "m1.large")
        #self.assertEqual(cloud_param["user_data"], "Hello World")
