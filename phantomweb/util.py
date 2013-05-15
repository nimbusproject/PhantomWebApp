import logging
import urlparse

from boto.ec2.connection import EC2Connection
from boto.exception import BotoServerError
from ceiclient.client import DTRSClient, EPUMClient
from ceiclient.connection import DashiCeiConnection
from django.http import HttpResponse
from django.template import Context, loader
import boto.ec2

from phantomweb.models import RabbitInfoDB, PhantomUser
from phantomweb.phantom_web_exceptions import PhantomWebException

g_general_log = logging.getLogger('phantomweb.general')


def LogEntryDecorator(func):
    def wrapped(*args, **kw):
        try:
            g_general_log.debug("Entering %s." % (func.func_name))
            return func(*args, **kw)
        except Exception, ex:
            g_general_log.exception("exiting %s with error: %s." % (func.func_name, str(ex)))
            raise
        finally:
            g_general_log.debug("Exiting %s." % (func.func_name))
    wrapped.__name__ = func.__name__
    return wrapped

def PhantomWebDecorator(func):
    def wrapped(*args, **kw):
        try:
            response_dict = func(*args,**kw)
        except PhantomWebException, pex:
            g_general_log.exception("Phantom Error %s" % (pex.message))
            response_dict = {
                'error_message': pex.message,
            }
        except BotoServerError, bex:
            g_general_log.exception("Boto Error %s : %s" % (bex.reason, bex.body))
            response_dict = {
                'error_message': "Error communiting with the cloud service: %s" % (bex.reason),
            }
        g_general_log.debug("returning response_dict %s" % (str(response_dict)))
        return response_dict
    wrapped.__name__ = func.__name__
    return wrapped


class UserCloudInfo(object):

    def __init__(self, cloudname, username, iaas_key, iaas_secret, keyname, site_desc):
        self.cloudname = cloudname
        self.username = username
        self.iaas_key = iaas_key
        self.iaas_secret = iaas_secret
        self.keyname = keyname
        self.site_desc = site_desc.copy()

    def get_iaas_compute_con(self):
        site_url = "INVALID"
        if self.site_desc['type'] == "nimbus":
            return self._connect_nimbus()
        elif self.site_desc['type'] == "ec2":
            return self._connect_ec2()
        elif self.site_desc['type'] == "openstack":
            return self._connect_euca()

        raise PhantomWebException("Unknown site type")

    def _connect_nimbus(self):
        if 'host' and 'port' not in self.site_desc:
            raise PhantomWebException("The site %s is misconfigured." % (self.cloudname))
        if self.site_desc['secure']:
            scheme = "https"
        else:
            scheme = "http"
        site_url = "%s://%s:%s" % (scheme, self.site_desc['host'], str(self.site_desc['port']))

        uparts = urlparse.urlparse(site_url)
        is_secure = uparts.scheme == 'https'
        ec2conn = EC2Connection(self.iaas_key, self.iaas_secret, host=uparts.hostname, port=uparts.port, is_secure=is_secure, validate_certs=False)
        ec2conn.host = uparts.hostname
        return ec2conn

    def _connect_ec2(self):
        ec2_region = self.site_desc.get("region")
        if ec2_region is not None:
            region = boto.ec2.get_region(ec2_region)

        ec2conn = EC2Connection(self.iaas_key, self.iaas_secret, region=region)
        return ec2conn

    def _connect_euca(self):
        if 'host' and 'port' not in self.site_desc:
            raise PhantomWebException("The site %s is misconfigured." % (self.cloudname))
        if self.site_desc['secure']:
            scheme = "https"
        else:
            scheme = "http"
        site_url = "%s://%s:%s" % (scheme, self.site_desc['host'], str(self.site_desc['port']))

        kwargs = {}
        uparts = urlparse.urlparse(site_url)
        is_secure = uparts.scheme == 'https'
        if self.site_desc.get('path') is not None:
            kwargs['path'] = self.site_desc['path']

        ec2conn = EC2Connection(self.iaas_key, self.iaas_secret, host=uparts.hostname, port=uparts.port, is_secure=is_secure, validate_certs=False, **kwargs)
        ec2conn.host = uparts.hostname
        return ec2conn


class UserObject(object):
    pass


class UserObjectMySQL(UserObject):
    def __init__(self, username):
        self.username = username

        phantom_user = PhantomUser.objects.get(username=username)
        if phantom_user is None:
            raise PhantomWebException('The user %s is not associated with an access key ID. Please contact your sysadmin' % (username))
        self.access_key = phantom_user.access_key_id

        rabbit_info_objects = RabbitInfoDB.objects.all()
        if not rabbit_info_objects:
            raise PhantomWebException('The service is mis-configured.  Please contact your sysadmin')
        self.rabbit_info = rabbit_info_objects[0]

        ssl = self.rabbit_info.rabbitssl
        self._dashi_conn = DashiCeiConnection(self.rabbit_info.rabbithost, self.rabbit_info.rabbituser, self.rabbit_info.rabbitpassword, exchange=self.rabbit_info.rabbitexchange, timeout=60, port=self.rabbit_info.rabbitport, ssl=ssl)
        self.epum = EPUMClient(self._dashi_conn)
        self.dtrs = DTRSClient(self._dashi_conn)

    def describe_domain(self, username, domain):
        # TODO: this should eventually be part of the REST API
        describe = self.epum.describe_domain(domain, caller=username)
        return describe

    def get_all_groups(self):
        domain_names = self.epum.list_domains(caller=self.access_key)
        domains = []
        for domain in domain_names:
            domain_description = self.epum.describe_domain(domain, caller=self.access_key)
            domains.append(domain_description)
        return domains

    def get_dt(self, dt_name):
        return self.dtrs.describe_dt(self.access_key, dt_name)

    def get_all_lcs(self):
        dt_names = self.dtrs.list_dts(self.access_key)
        dts = []
        for dt_name in dt_names:
            dt = self.dtrs.describe_dt(self.access_key, dt_name)
            dts.append(dt)
        return dts

    def _load_clouds(self):
        dtrs_client = DTRSClient(self._dashi_conn)
        sites = dtrs_client.list_credentials(self.access_key)
        self.iaasclouds = {}
        for site_name in sites:
            try:
                site_desc = dtrs_client.describe_site(self.access_key, site_name)
                desc = dtrs_client.describe_credentials(self.access_key, site_name)
                uci = UserCloudInfo(site_name, self.username, desc['access_key'], desc['secret_key'], desc['key_name'], site_desc)
                self.iaasclouds[site_name] = uci
            except Exception, ex:
                g_general_log.error("Failed trying to add the site %s to the user %s | %s" % (site_name, self.username, str(ex)))

    def get_cloud(self, name):
        self._load_clouds()
        if name not in self.iaasclouds:
            raise PhantomWebException("No cloud named %s associated with the user" % (name))
        return self.iaasclouds[name]

    def get_clouds(self):
        self._load_clouds()
        return self.iaasclouds

    def get_possible_sites(self):
        site_client = DTRSClient(self._dashi_conn)
        l = site_client.list_sites(self.access_key)
        return l

    def add_site(self, site_name, access_key, secret_key, key_name):
        cred_client = DTRSClient(self._dashi_conn)
        site_credentials = {
            'access_key': access_key,
            'secret_key': secret_key,
            'key_name': key_name
        }
        self.get_clouds()
        if site_name in self.iaasclouds:
            cred_client.update_credentials(self.access_key, site_name, site_credentials)
        else:
            cred_client.add_credentials(self.access_key, site_name, site_credentials)
        self._load_clouds()

    def delete_site(self, site_name):
        cred_client = DTRSClient(self._dashi_conn)
        cred_client.remove_credentials(self.access_key, site_name)
        self._load_clouds()


def get_user_object(username):
    return UserObjectMySQL(username)
