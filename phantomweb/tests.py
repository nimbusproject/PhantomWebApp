import json

from django.contrib.auth.models import User
from django.test.client import Client
from django.utils import unittest
from mock import patch

from phantomweb.models import PhantomUser, RabbitInfoDB


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
            self.assertIn({'credentials': '/api/dev/credentials/site1', 'id': 'site1', 'uri': '/api/dev/sites/site1'}, content)
            self.assertIn({'credentials': '/api/dev/credentials/site2', 'id': 'site2', 'uri': '/api/dev/sites/site2'}, content)

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
            self.assertEqual({'credentials': '/api/dev/credentials/site1', 'id': 'site1', 'uri': '/api/dev/sites/site1'}, content)

            response = c.get('/api/dev/sites/site2')
            self.assertEqual(response.status_code, 200)
            content = json.loads(response.content)
            self.assertEqual({'credentials': '/api/dev/credentials/site2', 'id': 'site2', 'uri': '/api/dev/sites/site2'}, content)

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
                        with patch('ceiclient.client.DTRSClient.describe_credentials', side_effect=describe_credentials):
                            c = Client()
                            c.login(username='fred', password='secret')

                            post_content = {
                                "id": "site3",
                                "access_key": "site3_access_key_id",
                                "secret_key": "site3_secret_access_key",
                                "key_name": "site3_phantom_ssh_key"
                            }
                            response = c.post('/api/dev/credentials', json.dumps(post_content), content_type='application/json')
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
                        with patch('ceiclient.client.DTRSClient.describe_credentials', side_effect=describe_credentials):
                            c = Client()
                            c.login(username='fred', password='secret')

                            post_content = {
                                "id": "site2",
                                "access_key": "site2_access_key_id",
                                "secret_key": "site2_secret_access_key",
                                "key_name": "site2_phantom_ssh_key"
                            }
                            response = c.put('/api/dev/credentials/site2', json.dumps(post_content), content_type='application/json')
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
