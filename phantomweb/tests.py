import json

from django.contrib.auth.models import User
from django.test.client import Client
from django.utils import unittest
from mock import patch, Mock
from dashi.exceptions import DashiError

from phantomweb.models import LaunchConfiguration, PhantomUser, RabbitInfoDB


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

    launch_configuration = LaunchConfiguration(name='deletabletestlc', username='fred')
    launch_configuration.save()


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
                'uri': '/api/dev/sites/site1',
                'instance_types': ['m1.small', 'm1.large', 'm1.xlarge']}, content)
            self.assertIn({'credentials': '/api/dev/credentials/site2', 'id': 'site2',
                'uri': '/api/dev/sites/site2',
                'instance_types': ['m1.small', 'm1.large', 'm1.xlarge']}, content)

    def test_get_sites_with_details(self):
        def list_sites(obj, key):
            return ['site1', 'site2']

        def list_credentials(obj, key):
            return ['site1', 'site2']

        def describe_site(obj, key, site):
            if site == 'site1':
                return {'type': 'nimbus'}
            else:
                return {}

        def describe_credentials(obj, key, site):
            if site == 'site1':
                return {'access_key': 'blah', 'secret_key': 'blorp', 'key_name': 'blap'}
            else:
                return {}

        def get_user_images(obj):
            return ['image1']

        with patch.multiple('ceiclient.client.DTRSClient', list_sites=list_sites,
                list_credentials=list_credentials, describe_site=describe_site,
                describe_credentials=describe_credentials):
            with patch.multiple('phantomweb.util.UserCloudInfo',
                    get_user_images=get_user_images):
                c = Client()
                c.login(username='fred', password='secret')

                response = c.get('/api/dev/sites?details=true')
                self.assertEqual(response.status_code, 200)
                content = json.loads(response.content)
                self.assertEqual(len(content), 2)
                self.assertIn({'credentials': '/api/dev/credentials/site1', 'id': 'site1',
                    'uri': '/api/dev/sites/site1', 'user_images': ['image1'], 'public_images': [],
                    'instance_types': ['m1.small', 'm1.large', 'm1.xlarge']}, content)
                self.assertIn({'credentials': '/api/dev/credentials/site2', 'id': 'site2',
                    'uri': '/api/dev/sites/site2', 'user_images': [], 'public_images': [],
                    'instance_types': ['m1.small', 'm1.large', 'm1.xlarge']}, content)

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
        def describe_dt(obj, caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "testlc":
                return {
                    "mappings": {
                        "site1": {
                            "iaas_image": "hello-phantom.gz",
                            "iaas_allocation": "m1.small",
                            "max_vms": -1,
                            "rank": 1,
                            "common": True
                        }
                    },
                    "contextualization": {
                        "method": "userdata",
                        "userdata": "Hello Cloud!"
                    }
                }
            else:
                self.fail("Unknown arguments received: %s, %s" % (caller, dt_name))

        with patch.multiple('ceiclient.client.DTRSClient', describe_dt=describe_dt):
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
                            "iaas_allocation": "m1.small",
                            "max_vms": -1,
                            "rank": 1,
                            "common": True
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
        def describe_dt(obj, caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "mysecondlc":
                return {
                    "mappings": {
                        "hotel": {
                            "iaas_image": "hello-phantom.gz",
                            "iaas_allocation": "m1.small",
                            "max_vms": -1,
                            "rank": 1,
                            "common": True
                        }
                    },
                    "contextualization": {
                        "method": "userdata",
                        "userdata": "Hello Cloud!"
                    }
                }
            else:
                self.fail("Unknown arguments received: %s %s" % (caller, dt_name))

        def update_dt(obj, caller, dt_name, dt):
            if caller == "freds_access_key_id" and dt_name == "mysecondlc":
                return
            else:
                self.fail("Unknown arguments received: %s %s" % (caller, dt_name))

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
                describe_credentials=describe_credentials, update_dt=update_dt):
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
        def describe_dt(obj, caller, dt_name):
            if caller == "freds_access_key_id" and dt_name == "testlc":
                return {
                    "mappings": {
                        "hotel": {
                            "iaas_image": "goodbye-cloud",
                            "iaas_allocation": "m2.large",
                            "max_vms": 3,
                            "common": False,
                            "rank": 2,
                        }
                    },
                    "contextualization": {
                        "method": "userdata",
                        "userdata": "Goodbye, Cruel World",
                    }
                }
            else:
                self.fail("Unknown arguments received")

        def update_dt(obj, caller, dt_name, dt):
            if caller == "freds_access_key_id" and dt_name == "testlc":
                return
            else:
                self.fail("Unknown arguments received: %s %s" % (caller, dt_name))

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
                describe_credentials=describe_credentials, update_dt=update_dt):
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
            if caller == "freds_access_key_id":
                return ["domain1", "domain2"]
            else:
                self.fail("Unknown arguments received")

        def describe_domain(self, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "domain1":
                return {
                    'name': 'this-is-a-uuid',
                    'sensor_data': {
                        'my.domain.metric': {
                            'Series': [0.0],
                            'Average': 0.0
                        }
                    },
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain1',
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            if caller == "freds_access_key_id" and domain == "domain2":
                return {
                    'name': 'this-is-a-uuid-number-two',
                    'sensor_data': {
                        'my.domain.metric': {
                            'Series': [0.0],
                            'Average': 0.0
                        }
                    },
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain2',
                            'phantom_de_name': 'sensor',
                            'minimum_vms': 1,
                            'maximum_vms': 2,
                            'metric': 'df.1kblocks.used',
                            'monitor_sensors': ['df.1kblocks.used', 'df.1kblocks.total'],
                            'monitor_domain_sensors': ['my.domain.metric', ],
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
            self.assertEqual(domain1['sensor_data'],
                    {"my.domain.metric": {"series": [0.0], "average": 0.0}})

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
        def add_domain(obj, name, definition, conf, caller=None):
            if caller == "freds_access_key_id":
                return {}
            else:
                self.fail("Unknown arguments received")

        def list_domains(self, caller):
            if caller == "freds_access_key_id":
                return ["this-is-a-uuid", "this-is-a-uuid-number-two"]
            else:
                self.fail("Unknown arguments received")

        def describe_domain(self, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return {
                    'name': 'this-is-a-uuid',
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain1',
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid-number-two":
                return {
                    'name': 'this-is-a-uuid-number-two',
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain2',
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

        def describe_dt(obj, caller, dt_name):
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
                self.fail("Unknown arguments received: %s, %s" % (caller, dt_name))

        with patch.multiple('ceiclient.client.DTRSClient', describe_dt=describe_dt):
            with patch.multiple('ceiclient.client.EPUMClient', add_domain=add_domain,
                    list_domains=list_domains, describe_domain=describe_domain):
                c = Client()
                c.login(username='fred', password='secret')

                post_content = {
                    "name": "myseconddomain",
                    "de_name": "sensor",
                    "lc_name": "testlc",
                    "monitor_sensors": "proc.loadavg.1min,df.inodes.free",
                    "sensor_minimum_vms": 1,
                    "sensor_maximum_vms": 10,
                    "sensor_metric": "proc.loadavg.1min",
                    "sensor_scale_down_threshold": 0.5,
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
                self.assertEqual(domain["de_name"], "sensor")
                self.assertEqual(domain["lc_name"], "testlc")
                self.assertEqual(domain["monitor_sensors"], "proc.loadavg.1min,df.inodes.free")
                self.assertEqual(domain["sensor_minimum_vms"], 1)
                self.assertEqual(domain["sensor_maximum_vms"], 10)
                self.assertEqual(domain["sensor_metric"], "proc.loadavg.1min")
                self.assertEqual(domain["sensor_scale_down_threshold"], 0.5)
                self.assertEqual(domain["sensor_scale_down_vms"], 1)
                self.assertEqual(domain["sensor_scale_up_threshold"], 1)
                self.assertEqual(domain["sensor_scale_up_vms"], 1)
                self.assertEqual(domain["sensor_cooldown"], 60)
                self.assertEqual(domain["owner"], "fred")
                assert domain["id"]
                domain_id = domain["id"]
                self.assertEqual(domain["uri"], "/api/dev/domains/%s" % domain_id)

                broken_post_content = {
                }
                response = c.post('/api/dev/domains',
                    json.dumps(broken_post_content), content_type='application/json')
                self.assertEqual(response.status_code, 400)

                broken_post_content = {
                    'name': 'stillbroken'
                }
                response = c.post('/api/dev/domains',
                    json.dumps(broken_post_content), content_type='application/json')
                self.assertEqual(response.status_code, 400)

                broken_post_content = {
                    'name': 'stillbroken',
                    'de_name': 'fake_de'
                }
                response = c.post('/api/dev/domains',
                    json.dumps(broken_post_content), content_type='application/json')
                self.assertEqual(response.status_code, 400)

                broken_post_content = {
                    'name': 'stillbroken',
                    'de_name': 'sensor'
                }
                response = c.post('/api/dev/domains',
                    json.dumps(broken_post_content), content_type='application/json')
                self.assertEqual(response.status_code, 400)

                broken_post_content = {
                    'name': 'stillbroken',
                    'de_name': 'multicloud'
                }
                response = c.post('/api/dev/domains',
                    json.dumps(broken_post_content), content_type='application/json')
                self.assertEqual(response.status_code, 400)

                duplicate_domain_content = {
                    'name': 'domain1',
                    'de_name': 'multicloud'
                }
                response = c.post('/api/dev/domains',
                    json.dumps(duplicate_domain_content), content_type='application/json')
                self.assertEqual(response.status_code, 302)
                assert response['Location'].endswith("/api/dev/domains/this-is-a-uuid")

    def test_get_domain_resource(self):
        def list_domains(self, caller):
            if caller == "freds_access_key_id":
                return ["domain1", "domain2"]
            else:
                self.fail("Unknown arguments received")

        def describe_domain(self, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return {
                    'name': 'this-is-a-uuid',
                    'sensor_data': {"my.domain.metric": {"Series": [0.0], "Average": 0.0}},
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain1',
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            elif caller == "freds_access_key_id" and domain == "this-is-a-uuid-number-two":
                return {
                    'name': 'this-is-a-uuid-number-two',
                    'sensor_data': {"my.domain.metric": {"Series": [0.0], "Average": 0.0}},
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain2',
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
            elif caller == "freds_access_key_id" and domain == "this-is-a-bad-url":
                raise DashiError("This domain don't exist")
            else:
                self.fail("Unknown arguments received")

        def describe_dt(obj, caller, dt_name):
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
                self.fail("Unknown arguments received: %s, %s" % (caller, dt_name))

        with patch.multiple('ceiclient.client.DTRSClient', describe_dt=describe_dt):
            with patch.multiple('ceiclient.client.EPUMClient', list_domains=list_domains,
                    describe_domain=describe_domain):
                c = Client()
                c.login(username='fred', password='secret')

                response = c.get('/api/dev/domains/this-is-a-uuid-number-two')
                self.assertEqual(response.status_code, 200)

                domain = json.loads(response.content)

                self.assertEqual(domain['de_name'], 'sensor')
                self.assertEqual(domain['name'], 'domain2')
                self.assertEqual(domain['monitor_sensors'], 'df.1kblocks.used,df.1kblocks.total')
                self.assertEqual(domain['sensor_minimum_vms'], 1)
                self.assertEqual(domain['sensor_maximum_vms'], 2)
                self.assertEqual(domain['sensor_metric'], 'df.1kblocks.used')
                self.assertEqual(domain['sensor_scale_down_threshold'], 0.1)
                self.assertEqual(domain['sensor_scale_down_vms'], 1)
                self.assertEqual(domain['sensor_scale_up_threshold'], 0.5)
                self.assertEqual(domain['sensor_scale_up_vms'], 1)
                self.assertEqual(domain['sensor_data'],
                        {"my.domain.metric": {"series": [0.0], "average": 0.0}})

                response = c.get('/api/dev/domains/this-is-a-bad-url')
                self.assertEqual(response.status_code, 404)

    def test_delete_domain_resource(self):

        def describe_domain(self, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return {
                    'name': 'this-is-a-uuid',
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain1',
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            elif caller == "freds_access_key_id" and domain == "this-is-a-bad-url":
                raise DashiError("This domain don't exist")
            else:
                self.fail("Unknown arguments received")

        def remove_domain(self, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return None
            elif caller == "freds_access_key_id" and domain == "this-is-a-bad-url":
                raise DashiError("This domain don't exist")
            else:
                self.fail("Unknown arguments received")

        with patch.multiple('ceiclient.client.EPUMClient',
                describe_domain=describe_domain, remove_domain=remove_domain):
            c = Client()
            c.login(username='fred', password='secret')

            response = c.get('/api/dev/domains/this-is-a-bad-url')
            self.assertEqual(response.status_code, 404)

            response = c.delete('/api/dev/domains/this-is-a-uuid')
            self.assertEqual(response.status_code, 204)

    def test_put_domain_resource(self):
        def add_domain(obj, name, definition, conf, caller=None):
            if caller == "freds_access_key_id":
                return {}
            else:
                self.fail("Unknown arguments received")

        def list_domains(obj, caller):
            if caller == "freds_access_key_id":
                return ["this-is-a-uuid", "this-is-a-uuid-number-two"]
            else:
                self.fail("Unknown arguments received")

            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return None
            else:
                self.fail("Unknown arguments received")

        def reconfigure_domain(obj, domain, conf, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return None
            else:
                self.fail("Unknown arguments received")

        def describe_domain(obj, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return {
                    'name': 'this-is-a-uuid',
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain1',
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            elif caller == "freds_access_key_id" and domain == "this-is-a-uuid-number-two":
                return {
                    'name': 'this-is-a-uuid-number-two',
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain2',
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
            elif caller == "freds_access_key_id" and domain == "this-is-a-nonexistent-uuid":
                raise DashiError("domain doesn't exist")
            else:
                self.fail("Unknown arguments received")

        with patch.multiple('ceiclient.client.EPUMClient', add_domain=add_domain,
                list_domains=list_domains, describe_domain=describe_domain,
                reconfigure_domain=reconfigure_domain):
            c = Client()
            c.login(username='fred', password='secret')

            put_content = {
                "name": "domain1",
                "de_name": "sensor",
                "lc_name": "mysecondlc",
                "monitor_sensors": "proc.loadavg.1min,df.inodes.free",
                "sensor_minimum_vms": 1,
                "sensor_maximum_vms": 10,
                "sensor_metric": "proc.loadavg.1min",
                "sensor_scale_down_threshold": 0.5,
                "sensor_scale_down_vms": 1,
                "sensor_scale_up_threshold": 1,
                "sensor_scale_up_vms": 1,
                "sensor_cooldown": 60
            }

            response = c.put('/api/dev/domains/this-is-a-nonexistent-uuid',
                json.dumps(put_content), content_type='application/json')
            self.assertEqual(response.status_code, 404)

            response = c.put('/api/dev/domains/this-is-a-uuid',
                json.dumps(put_content), content_type='application/json')
            self.assertEqual(response.status_code, 200)

            domain = json.loads(response.content)
            self.assertEqual(domain["name"], "domain1")
            self.assertEqual(domain["de_name"], "sensor")
            self.assertEqual(domain["lc_name"], "mysecondlc")
            self.assertEqual(domain["monitor_sensors"], "proc.loadavg.1min,df.inodes.free")
            self.assertEqual(domain["sensor_minimum_vms"], 1)
            self.assertEqual(domain["sensor_maximum_vms"], 10)
            self.assertEqual(domain["sensor_metric"], "proc.loadavg.1min")
            self.assertEqual(domain["sensor_scale_down_threshold"], 0.5)
            self.assertEqual(domain["sensor_scale_down_vms"], 1)
            self.assertEqual(domain["sensor_scale_up_threshold"], 1)
            self.assertEqual(domain["sensor_scale_up_vms"], 1)
            self.assertEqual(domain["sensor_cooldown"], 60)
            self.assertEqual(domain["owner"], "fred")
            assert domain["id"]
            domain_id = domain["id"]
            self.assertEqual(domain["uri"], "/api/dev/domains/%s" % domain_id)

            broken_post_content = {
            }
            response = c.post('/api/dev/domains',
                json.dumps(broken_post_content), content_type='application/json')
            self.assertEqual(response.status_code, 400)

            broken_post_content = {
                'name': 'stillbroken'
            }
            response = c.post('/api/dev/domains',
                json.dumps(broken_post_content), content_type='application/json')
            self.assertEqual(response.status_code, 400)

            broken_post_content = {
                'name': 'stillbroken',
                'de_name': 'fake_de'
            }
            response = c.post('/api/dev/domains',
                json.dumps(broken_post_content), content_type='application/json')
            self.assertEqual(response.status_code, 400)

            broken_post_content = {
                'name': 'stillbroken',
                'de_name': 'sensor'
            }
            response = c.post('/api/dev/domains',
                json.dumps(broken_post_content), content_type='application/json')
            self.assertEqual(response.status_code, 400)

            broken_post_content = {
                'name': 'stillbroken',
                'de_name': 'multicloud'
            }
            response = c.post('/api/dev/domains',
                json.dumps(broken_post_content), content_type='application/json')
            self.assertEqual(response.status_code, 400)

            duplicate_domain_content = {
                'name': 'domain1',
                'de_name': 'multicloud'
            }
            response = c.post('/api/dev/domains',
                json.dumps(duplicate_domain_content), content_type='application/json')
            self.assertEqual(response.status_code, 302)
            assert response['Location'].endswith("/api/dev/domains/this-is-a-uuid")


class InstancesTestCase(unittest.TestCase):
    def test_get_instances(self):

        def describe_domain(obj, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return {
                    'name': 'this-is-a-uuid',
                    "instances": [
                        {
                            "creator": "guJCD13gODRwXOeHxk3JX",
                            "site": "hotel",
                            "iaas_sshkeyname": "phantomkey",
                            "state_changes": [
                                [
                                    "200-REQUESTED",
                                    1369072098.508631
                                ],
                                [
                                    "400-PENDING",
                                    1369072099.406982
                                ],
                                [
                                    "600-RUNNING",
                                    1369072143.839346
                                ]
                            ],
                            "private_ip": "192.168.0.111",
                            "errors": None,
                            "iaas_allocation": "m1.small",
                            "deployable_type": "x",
                            "hostname": "vm-148-135.uc.futuregrid.org",
                            "error_time": None,
                            "state": "600-RUNNING",
                            "health": "UNKNOWN",
                            "pending_timestamp": 1369072099.406986,
                            "launch_id": "88c41340-5497-4f6c-a62d-8d2309317f41",
                            "client_token": "88c41340-5497-4f6c-a62d-8d2309317f41",
                            "allocation": None,
                            "extravars": None,
                            "update_counter": 2,
                            "public_ip": "149.165.148.135",
                            "state_time": 1369072143.854667,
                            "state_desc": None,
                            "sensor_data": {
                                "proc.loadavg.1min": {
                                    "Series": [
                                        0.0
                                    ],
                                    "Average": 0.0
                                }
                            },
                            "instance_id": "80bc3e1d-ffbe-4be1-b392-902fb6df10cb",
                            "iaas_id": "i-14a3d7df",
                            "iaas_image": "hello-phantom.gz"
                        }
                    ],
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain1',
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            else:
                self.fail("Unknown arguments received")

        with patch.multiple('ceiclient.client.EPUMClient', describe_domain=describe_domain):
            c = Client()
            c.login(username='fred', password='secret')

            response = c.get('/api/dev/domains/this-is-a-uuid/instances')
            self.assertEqual(response.status_code, 200)

            instances = json.loads(response.content)
            self.assertEqual(len(instances), 1)
            instance_0 = instances[0]
            self.assertEqual(instance_0['id'], "80bc3e1d-ffbe-4be1-b392-902fb6df10cb")
            self.assertEqual(instance_0['iaas_instance_id'], "i-14a3d7df")
            self.assertEqual(instance_0['lifecycle_state'], "600-RUNNING")
            self.assertEqual(instance_0['hostname'], "vm-148-135.uc.futuregrid.org")
            self.assertEqual(instance_0['cloud'], "/api/dev/sites/hotel")
            self.assertEqual(instance_0['image_id'], "hello-phantom.gz")
            self.assertEqual(instance_0['instance_type'], "m1.small")
            self.assertEqual(instance_0['keyname'], "phantomkey")
            self.assertEqual(instance_0['sensor_data'],
                {"proc.loadavg.1min": {"series": [0.0], "average": 0.0}}),
            self.assertEqual(instance_0['uri'],
                "/api/dev/domains/this-is-a-uuid/instances/80bc3e1d-ffbe-4be1-b392-902fb6df10cb")


class InstancesResourcesTestCase(unittest.TestCase):
    def test_get_instance(self):

        def describe_domain(obj, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return {
                    'name': 'this-is-a-uuid',
                    "instances": [
                        {
                            "creator": "guJCD13gODRwXOeHxk3JX",
                            "site": "hotel",
                            "iaas_sshkeyname": "phantomkey",
                            "state_changes": [
                                [
                                    "200-REQUESTED",
                                    1369072098.508631
                                ],
                                [
                                    "400-PENDING",
                                    1369072099.406982
                                ],
                                [
                                    "600-RUNNING",
                                    1369072143.839346
                                ]
                            ],
                            "sensor_data": {
                                "proc.loadavg.1min": {
                                    "Series": [
                                        0.0
                                    ],
                                    "Average": 0.0
                                }
                            },
                            "private_ip": "192.168.0.111",
                            "errors": None,
                            "iaas_allocation": "m1.small",
                            "deployable_type": "x",
                            "hostname": "vm-148-135.uc.futuregrid.org",
                            "error_time": None,
                            "state": "600-RUNNING",
                            "health": "UNKNOWN",
                            "pending_timestamp": 1369072099.406986,
                            "launch_id": "88c41340-5497-4f6c-a62d-8d2309317f41",
                            "client_token": "88c41340-5497-4f6c-a62d-8d2309317f41",
                            "allocation": None,
                            "extravars": None,
                            "update_counter": 2,
                            "public_ip": "149.165.148.135",
                            "state_time": 1369072143.854667,
                            "state_desc": None,
                            "instance_id": "80bc3e1d-ffbe-4be1-b392-902fb6df10cb",
                            "iaas_id": "i-14a3d7df",
                            "iaas_image": "hello-phantom.gz"
                        }
                    ],
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain1',
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            else:
                self.fail("Unknown arguments received")

        with patch.multiple('ceiclient.client.EPUMClient', describe_domain=describe_domain):
            c = Client()
            c.login(username='fred', password='secret')

            response = c.get('/api/dev/domains/this-is-a-uuid/instances/80bc3e1d-ffbe-4be1-b392-902fb6df10cb')
            self.assertEqual(response.status_code, 200)

            instance = json.loads(response.content)
            self.assertEqual(instance['id'], "80bc3e1d-ffbe-4be1-b392-902fb6df10cb")
            self.assertEqual(instance['iaas_instance_id'], "i-14a3d7df")
            self.assertEqual(instance['lifecycle_state'], "600-RUNNING")
            self.assertEqual(instance['hostname'], "vm-148-135.uc.futuregrid.org")
            self.assertEqual(instance['cloud'], "/api/dev/sites/hotel")
            self.assertEqual(instance['image_id'], "hello-phantom.gz")
            self.assertEqual(instance['instance_type'], "m1.small")
            self.assertEqual(instance['keyname'], "phantomkey")
            self.assertEqual(instance['sensor_data'],
                {"proc.loadavg.1min": {"series": [0.0], "average": 0.0}}),
            self.assertEqual(instance['uri'],
                "/api/dev/domains/this-is-a-uuid/instances/80bc3e1d-ffbe-4be1-b392-902fb6df10cb")

            response = c.get('/api/dev/domains/this-is-a-uuid/instances/not-real')
            self.assertEqual(response.status_code, 404)

    def test_delete_instance(self):

        def describe_domain(obj, domain, caller=None):
            if caller == "freds_access_key_id" and domain == "this-is-a-uuid":
                return {
                    'name': 'this-is-a-uuid',
                    "instances": [
                        {
                            "creator": "guJCD13gODRwXOeHxk3JX",
                            "site": "hotel",
                            "iaas_sshkeyname": "phantomkey",
                            "state_changes": [
                                [
                                    "200-REQUESTED",
                                    1369072098.508631
                                ],
                                [
                                    "400-PENDING",
                                    1369072099.406982
                                ],
                                [
                                    "600-RUNNING",
                                    1369072143.839346
                                ]
                            ],
                            "private_ip": "192.168.0.111",
                            "errors": None,
                            "iaas_allocation": "m1.small",
                            "deployable_type": "x",
                            "hostname": "vm-148-135.uc.futuregrid.org",
                            "error_time": None,
                            "state": "600-RUNNING",
                            "health": "UNKNOWN",
                            "pending_timestamp": 1369072099.406986,
                            "launch_id": "88c41340-5497-4f6c-a62d-8d2309317f41",
                            "client_token": "88c41340-5497-4f6c-a62d-8d2309317f41",
                            "allocation": None,
                            "extravars": None,
                            "update_counter": 2,
                            "public_ip": "149.165.148.135",
                            "state_time": 1369072143.854667,
                            "state_desc": None,
                            "instance_id": "80bc3e1d-ffbe-4be1-b392-902fb6df10cb",
                            "iaas_id": "i-14a3d7df",
                            "iaas_image": "hello-phantom.gz"
                        }
                    ],
                    'config': {
                        'engine_conf': {
                            'phantom_name': 'domain1',
                            'phantom_de_name': 'multicloud',
                            'minimum_vms': 1,
                            'dtname': 'mylc'
                        }
                    }
                }
            else:
                self.fail("Unknown arguments received")

        def list_credentials(obj, caller):
            if caller == "freds_access_key_id":
                return ["hotel", "site2"]

        def describe_credentials(obj, caller, site_name):
            if caller == "freds_access_key_id" and site_name == "hotel":
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

        def describe_site(self, caller, site):
            if caller == "freds_access_key_id":
                return {}
            else:
                self.fail("Unknown arguments received")

        def get_iaas_compute_con(obj):
            return Mock()

        with patch.multiple('ceiclient.client.EPUMClient', describe_domain=describe_domain):
            with patch.multiple('ceiclient.client.DTRSClient',
                    list_credentials=list_credentials, describe_credentials=describe_credentials,
                    describe_site=describe_site):
                with patch.multiple('phantomweb.util.UserCloudInfo',
                        get_iaas_compute_con=get_iaas_compute_con):

                    c = Client()
                    c.login(username='fred', password='secret')

                    response = c.delete(
                        '/api/dev/domains/this-is-a-uuid/instances/80bc3e1d-ffbe-4be1-b392-902fb6df10cb')
                    self.assertEqual(response.status_code, 204)

                    response = c.delete('/api/dev/domains/this-is-a-uuid/instances/not-real')
                    self.assertEqual(response.status_code, 404)


class SensorsTestCase(unittest.TestCase):
    def test_get_sensors(self):
        c = Client()
        c.login(username='fred', password='secret')

        response = c.get('/api/dev/sensors')
        self.assertEqual(response.status_code, 200)

        sensors = json.loads(response.content)

        self.assertIn({"id": "df.1kblocks.free", "uri": "/api/dev/sensors/df.1kblocks.free"},
            sensors)


class SensorsResourcesTestCase(unittest.TestCase):
    def test_get_sensor(self):
        c = Client()
        c.login(username='fred', password='secret')

        response = c.get('/api/dev/sensors/df.1kblocks.free')
        self.assertEqual(response.status_code, 200)

        sensor = json.loads(response.content)

        self.assertEqual({"id": "df.1kblocks.free", "uri": "/api/dev/sensors/df.1kblocks.free"},
            sensor)
