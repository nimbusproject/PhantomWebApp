import json
import logging
import urlparse
import boto.ec2
import statsd

from uuid import uuid4
from boto.ec2.connection import EC2Connection
from boto.exception import BotoServerError
from ceiclient.client import DTRSClient, EPUMClient
from ceiclient.connection import DashiCeiConnection
from dashi.exceptions import DashiError

from phantomweb.tevent import Pool, TimeoutError
from phantomweb.models import RabbitInfoDB, PhantomUser
from phantomweb.phantom_web_exceptions import PhantomWebException

log = logging.getLogger('phantomweb.general')

PHANTOM_DOMAIN_DEFINITION = "error_overflow_n_preserving"
IAAS_TIMEOUT = 10
INSTANCE_TYPES = ["m1.small", "m1.large", "m1.xlarge"]


def LogEntryDecorator(func):
    def wrapped(*args, **kw):
        try:
            log.debug("Entering %s." % (func.func_name))
            return func(*args, **kw)
        except Exception, ex:
            log.exception("exiting %s with error: %s." % (func.func_name, str(ex)))
            raise
        finally:
            log.debug("Exiting %s." % (func.func_name))
    wrapped.__name__ = func.__name__
    return wrapped


def PhantomWebDecorator(func):
    def wrapped(*args, **kw):
        try:
            response_dict = func(*args, **kw)
        except PhantomWebException, pex:
            log.exception("Phantom Error %s" % (pex.message))
            response_dict = {
                'error_message': pex.message,
            }
        except BotoServerError, bex:
            log.exception("Boto Error %s : %s" % (bex.reason, bex.body))
            response_dict = {
                'error_message': "Error communiting with the cloud service: %s" % (bex.reason),
            }
        log.debug("returning response_dict %s" % (str(response_dict)))
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
        if self.site_desc['type'] == "nimbus":
            return self._connect_nimbus()
        elif self.site_desc['type'] == "ec2":
            return self._connect_ec2()
        elif self.site_desc['type'] == "openstack":
            return self._connect_euca()

        raise PhantomWebException("Unknown site type")

    def get_user_images(self):
        connection = self.get_iaas_compute_con()
        timer = statsd.Timer('phantomweb')
        timer.start()
        l = connection.get_all_images(owners=['self'])
        timer.stop('get_all_images.timing')
        user_images = [u.id for u in l if not u.is_public]
        return user_images

    def get_public_images(self):
        connection = self.get_iaas_compute_con()
        timer = statsd.Timer('phantomweb')
        timer_cloud = statsd.Timer('phantomweb')
        timer.start()
        timer_cloud.start()
        l = connection.get_all_images()
        timer.stop('get_all_images.timing')
        timer_cloud.stop('get_all_images.%s.timing' % self.cloudname)
        public_images = [u.id for u in l if u.is_public]
        return public_images

    def get_keys(self):
        connection = self.get_iaas_compute_con()
        keyname_list = []
        try:
            timer = statsd.Timer('phantomweb')
            timer_cloud = statsd.Timer('phantomweb')
            timer.start()
            timer_cloud.start()
            keypairs = connection.get_all_key_pairs()
            timer.stop('get_all_key_pairs.timing')
            timer_cloud.stop('get_all_key_pairs.%s.timing' % self.cloudname)
            keyname_list = [k.name for k in keypairs]
        except Exception, boto_ex:
            log.error("Error connecting to the service %s" % (str(boto_ex)))

        return keyname_list

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
        ec2conn = EC2Connection(self.iaas_key, self.iaas_secret, host=uparts.hostname,
            port=uparts.port, is_secure=is_secure, validate_certs=False)
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

        ec2conn = EC2Connection(self.iaas_key, self.iaas_secret, host=uparts.hostname,
            port=uparts.port, is_secure=is_secure, validate_certs=False, **kwargs)
        ec2conn.host = uparts.hostname
        return ec2conn


class UserObject(object):
    pass


class UserObjectMySQL(UserObject):
    def __init__(self, username):
        self.username = username

        phantom_user = PhantomUser.objects.get(username=username)
        if phantom_user is None:
            msg = 'The user %s is not associated with an access key ID. Please contact your sysadmin' % (username)
            raise PhantomWebException(msg)
        self.access_key = phantom_user.access_key_id

        rabbit_info_objects = RabbitInfoDB.objects.all()
        if not rabbit_info_objects:
            raise PhantomWebException('The service is mis-configured.  Please contact your sysadmin')
        self.rabbit_info = rabbit_info_objects[0]

        ssl = self.rabbit_info.rabbitssl
        self._dashi_conn = DashiCeiConnection(
            self.rabbit_info.rabbithost, self.rabbit_info.rabbituser, self.rabbit_info.rabbitpassword,
            exchange=self.rabbit_info.rabbitexchange, timeout=60, port=self.rabbit_info.rabbitport,
            ssl=ssl)
        self.epum = EPUMClient(self._dashi_conn)
        self.dtrs = DTRSClient(self._dashi_conn)

    def describe_domain(self, username, domain):
        describe = self.epum.describe_domain(domain, caller=self.access_key)
        return describe

    def remove_domain(self, username, domain):
        removed = self.epum.remove_domain(domain, caller=self.access_key)
        return removed

    def _api_parameters_to_general_opts(self, parameters):
        general_opts = {}
        if 'chef_credential' in parameters:
            general_opts['chef_credential'] = parameters['chef_credential']
        return general_opts

    def _api_parameters_to_domain_opts(self, parameters):
        domain_opts = {}
        de_name = parameters.get('de_name')
        domain_opts['phantom_de_name'] = de_name
        domain_opts['clouds'] = parameters.get('clouds', [])

        if de_name == 'sensor':
            try:
                domain_opts['dtname'] = parameters['lc_name']
                domain_opts['cooldown_period'] = parameters['sensor_cooldown']
                domain_opts['maximum_vms'] = parameters['sensor_maximum_vms']
                domain_opts['minimum_vms'] = parameters['sensor_minimum_vms']
                domain_opts['metric'] = parameters['sensor_metric']
                domain_opts['monitor_domain_sensors'] = parameters.get('monitor_domain_sensors', '').split(',')
                domain_opts['monitor_sensors'] = parameters.get('monitor_sensors', '').split(',')
                domain_opts['scale_down_n_vms'] = parameters['sensor_scale_down_vms']
                domain_opts['scale_down_threshold'] = parameters['sensor_scale_down_threshold']
                domain_opts['scale_up_n_vms'] = parameters['sensor_scale_up_vms']
                domain_opts['scale_up_threshold'] = parameters['sensor_scale_up_threshold']
                domain_opts['sample_function'] = 'Average'  # TODO: make configurable
                domain_opts['sensor_type'] = 'opentsdb'  # TODO: make configurable
                domain_opts['opentsdb_port'] = 4242  # TODO: make configurable
                domain_opts['opentsdb_host'] = 'localhost'  # TODO: make configurable
            except KeyError as k:
                raise PhantomWebException("Mandatory parameter '%s' is missing" % k.args[0])

        elif de_name == 'multicloud':
            try:
                domain_opts['dtname'] = parameters['lc_name']
                domain_opts['maximum_vms'] = parameters['vm_count']
                domain_opts['minimum_vms'] = parameters['vm_count']
                domain_opts['monitor_domain_sensors'] = parameters.get('monitor_domain_sensors', '').split(',')
                domain_opts['monitor_sensors'] = parameters.get('monitor_sensors', '').split(',')

                domain_opts['sample_function'] = 'Average'  # TODO: make configurable
                domain_opts['sensor_type'] = 'opentsdb'  # TODO: make configurable
                domain_opts['opentsdb_port'] = 4242  # TODO: make configurable
                domain_opts['opentsdb_host'] = 'localhost'  # TODO: make configurable
            except KeyError as k:
                raise PhantomWebException("Mandatory parameter '%s' is missing" % k.args[0])
        else:
            raise PhantomWebException("de_name '%s' is not supported" % de_name)

        return domain_opts

    def add_domain(self, username, name, parameters):

        domain_opts = self._api_parameters_to_domain_opts(parameters)
        general_opts = self._api_parameters_to_general_opts(parameters)
        id = str(uuid4())
        parameters['id'] = id
        domain_opts['name'] = id
        domain_opts['phantom_name'] = name

        conf = {'engine_conf': domain_opts, 'general': general_opts}

        try:
            self.epum.add_domain(id, PHANTOM_DOMAIN_DEFINITION, conf, caller=self.access_key)
            return parameters
        except Exception:
            log.exception("Problem creating domain: %s" % name)
            raise

    def reconfigure_domain(self, username, id, parameters):

        name = parameters.get('name')
        domain_opts = self._api_parameters_to_domain_opts(parameters)
        general_opts = self._api_parameters_to_general_opts(parameters)
        parameters['id'] = id
        domain_opts['name'] = id
        domain_opts['phantom_name'] = name

        conf = {'engine_conf': domain_opts, 'general': general_opts}

        try:
            self.epum.reconfigure_domain(id, conf, caller=self.access_key)
            return parameters
        except Exception:
            log.exception("Problem modifying domain: %s" % name)
            raise

    def get_all_domains(self, username):
        domain_names = self.epum.list_domains(caller=self.access_key)
        return domain_names

    def _sanitize_sensor_data(self, sensor_data):
        cleaned_sensor_data = {}
        for key, item in sensor_data.iteritems():
            key = key.lower()
            cleaned_item = {}
            for k, v in item.iteritems():
                k = k.lower()
                cleaned_item[k] = v
            cleaned_sensor_data[key] = cleaned_item

        return cleaned_sensor_data

    def get_domain(self, username, id):
        try:
            domain_description = self.epum.describe_domain(id, caller=self.access_key)
        except DashiError:
            return None
        engine_conf = domain_description.get('config', {}).get('engine_conf', {})
        general_conf = domain_description.get('config', {}).get('general', {})

        ent = {}
        ent['id'] = domain_description['name']
        ent['de_name'] = engine_conf.get('phantom_de_name')
        ent['name'] = engine_conf.get('phantom_name')
        ent['sensor_data'] = self._sanitize_sensor_data(domain_description.get('sensor_data', {}))
        ent['monitor_sensors'] = ",".join(engine_conf.get('monitor_sensors', []))
        ent['monitor_domain_sensors'] = ",".join(engine_conf.get('monitor_domain_sensors', []))
        if 'chef_credential' in general_conf:
            ent['chef_credential'] = general_conf['chef_credential']

        if ent['de_name'] == 'multicloud':
            ent['vm_count'] = engine_conf.get('minimum_vms')
            ent['lc_name'] = engine_conf.get('dtname')
        elif ent['de_name'] == 'sensor':
            ent['lc_name'] = engine_conf.get('dtname')
            ent['sensor_minimum_vms'] = engine_conf.get('minimum_vms')
            ent['sensor_maximum_vms'] = engine_conf.get('maximum_vms')
            ent['sensor_metric'] = engine_conf.get('metric')
            ent['sensor_scale_down_threshold'] = engine_conf.get('scale_down_threshold')
            ent['sensor_scale_down_vms'] = engine_conf.get('scale_down_n_vms')
            ent['sensor_scale_up_threshold'] = engine_conf.get('scale_up_threshold')
            ent['sensor_scale_up_vms'] = engine_conf.get('scale_up_n_vms')
            ent['sensor_cooldown'] = engine_conf.get('cooldown_period')
        return ent

    def get_domain_instances(self, username, id):
        try:
            domain_description = self.epum.describe_domain(id, caller=self.access_key)
        except DashiError:
            return None
        instances = domain_description.get('instances', [])
        parsed_instances = []

        for i in instances:
            instance = {
                'id': i.get('instance_id', ''),
                'iaas_instance_id': i.get('iaas_id', ''),
                'lifecycle_state': i.get('state', ''),
                'hostname': i.get('hostname', ''),
                'cloud': i.get('site', ''),
                'image_id': i.get('iaas_image', ''),
                'instance_type': i.get('iaas_allocation', ''),
                'sensor_data': self._sanitize_sensor_data(i.get('sensor_data', {})),
                'keyname': i.get('iaas_sshkeyname', ''),
            }
            parsed_instances.append(instance)

        return parsed_instances

    def get_all_groups(self):
        domain_names = self.epum.list_domains(caller=self.access_key)
        domains = []
        for domain in domain_names:
            domain_description = self.epum.describe_domain(domain, caller=self.access_key)
            domains.append(domain_description)
        return domains

    def create_dt(self, dt_name, cloud_params, context_params):
        dt = self.get_dt(dt_name)
        if dt is None:
            dt = {}
            dt['mappings'] = {}
            create = True
        else:
            create = False

        cloud_credentials = self.get_clouds()

        for cloud_name, parameters in cloud_params.iteritems():
            mapping = dt['mappings'].get(cloud_name)
            if mapping is None:
                mapping = dt['mappings'][cloud_name] = {}
            credentials = cloud_credentials.get(cloud_name, None)

            # Required by EPUM
            mapping['iaas_allocation'] = parameters.get('instance_type')
            mapping['iaas_image'] = parameters.get('image_id')
            if credentials is not None:
                mapping['key_name'] = credentials.keyname
            else:
                # TODO: raise error?
                mapping['key_name'] = ''

            # Phantom stuff
            mapping['common'] = parameters.get('common')
            mapping['rank'] = parameters.get('rank')
            mapping['max_vms'] = parameters.get('max_vms')

        # Contextualization
        if context_params.get('contextualization_method') == 'user_data' or context_params.get('user_data'):
            contextualization = dt.get('contextualization')
            if contextualization is None:
                contextualization = dt['contextualization'] = {}
            contextualization['method'] = 'userdata'
            contextualization['userdata'] = context_params['user_data']
        elif context_params.get('contextualization_method') == 'chef':
            contextualization = dt.get('contextualization')
            if contextualization is None:
                contextualization = dt['contextualization'] = {}
            if contextualization.get('userdata') is not None:
                del contextualization['userdata']
            contextualization['method'] = 'chef'
            try:
                contextualization['run_list'] = json.loads(context_params.get('chef_runlist', '[]'))
            except Exception:
                log.exception("Problem parsing LC content")
                raise PhantomWebException("Problem parsing runlist when creating LC: %s" % context_params.get('chef_runlist'))
            try:
                contextualization['attributes'] = json.loads(context_params.get('chef_attributes', '{}'))
            except Exception:
                log.exception("Problem parsing LC content")
                raise PhantomWebException("Problem parsing chef attributes when creating LC: %s" % context_params.get('chef_attributes'))
        elif parameters.get('contextualization_method') == 'none':
            contextualization = dt['contextualization'] = {}
            contextualization['method'] = None

        if create:
            return self.dtrs.add_dt(self.access_key, dt_name, dt)
        else:
            return self.dtrs.update_dt(self.access_key, dt_name, dt)

    def get_dt(self, dt_name):
        return self.dtrs.describe_dt(self.access_key, dt_name)

    def remove_dt(self, dt_name):
        return self.dtrs.remove_dt(self.access_key, dt_name)

    def get_all_lcs(self):
        dt_names = self.dtrs.list_dts(self.access_key)
        dts = []
        for dt_name in dt_names:
            dt = self.dtrs.describe_dt(self.access_key, dt_name)
            dts.append(dt)
        return dts

    def _load_clouds(self):
        sites = self.dtrs.list_credentials(self.access_key)
        self.iaasclouds = {}
        for site_name in sites:
            try:
                site_desc = self.dtrs.describe_site(self.access_key, site_name)
                desc = self.dtrs.describe_credentials(self.access_key, site_name)
                uci = UserCloudInfo(site_name, self.username, desc['access_key'],
                    desc['secret_key'], desc['key_name'], site_desc)
                self.iaasclouds[site_name] = uci
            except Exception, ex:
                log.error("Failed trying to add the site %s to the user %s | %s" % (site_name, self.username, str(ex)))

    def get_cloud(self, name):
        self._load_clouds()
        if name not in self.iaasclouds:
            raise PhantomWebException("No cloud named %s associated with the user" % (name))
        return self.iaasclouds[name]

    def get_clouds(self):
        self._load_clouds()
        return self.iaasclouds

    def get_chef_credentials(self):
        # TODO: this needs to actually be implemented in ceictl
        credential_names = self.dtrs.list_credentials(self.access_key, credential_type="chef")
        credentials = {}
        for credential_name in credential_names:
            credential = self.dtrs.describe_credentials(self.access_key, credential_name, credential_type="chef")
            credentials[credential_name] = credential
        return credentials

    def add_chef_credentials(self, name, url, client_name, client_key, validator_key):
        credential_names = self.dtrs.list_credentials(self.access_key, credential_type="chef")
        if name in credential_names:
            create = False
        else:
            create = True

        credential = {
            'url': url,
            'client_name': client_name,
            'client_key': client_key,
            'validator_key': validator_key
        }

        if create:
            return self.dtrs.add_credentials(self.access_key, name, credential, credential_type='chef')
        else:
            return self.dtrs.update_credentials(self.access_key, name, credential, credential_type='chef')

    def delete_chef_credentials(self, name):
        credential_names = self.dtrs.list_credentials(self.access_key, credential_type="chef")
        if name not in credential_names:
            raise PhantomWebException("Unknown credentials %s" % name)

        return self.dtrs.remove_credentials(self.access_key, name, credential_type='chef')

    def get_possible_sites(self, details=False):
        site_client = DTRSClient(self._dashi_conn)
        site_names = site_client.list_sites(self.access_key)
        all_sites = {}
        for site in site_names:
            all_sites[site] = {'id': site, 'instance_types': INSTANCE_TYPES}

        if details is True:
            pool = Pool()

            public_results = {}
            user_results = {}
            clouds = self.get_clouds()
            for cloud_name, cloud in clouds.iteritems():
                result = pool.apply_async(cloud.get_user_images)
                user_results[cloud_name] = result

                if cloud.site_desc["type"] != "ec2":
                    result = pool.apply_async(cloud.get_public_images)
                    public_results[cloud_name] = result

            pool.close()

            for cloud_name, result in user_results.iteritems():
                try:
                    all_sites[cloud_name]['user_images'] = result.get(IAAS_TIMEOUT)
                except TimeoutError:
                    log.exception("Timed out getting images from %s" % cloud_name)
                    all_sites[cloud_name]['user_images'] = []
                except Exception:
                    log.exception("Unexpected error getting images from %s" % cloud_name)
                    all_sites[cloud_name]['user_images'] = []

            for cloud_name, result in public_results.iteritems():
                try:
                    all_sites[cloud_name]['public_images'] = result.get(IAAS_TIMEOUT)
                except TimeoutError:
                    log.exception("Timed out getting images from %s" % cloud_name)
                    all_sites[cloud_name]['public_images'] = []
                except Exception:
                    log.exception("Unexpected error getting images from %s" % cloud_name)
                    all_sites[cloud_name]['public_images'] = []

        return all_sites

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


def str_to_bool(st):
    if st.lower() == 'true':
        return True
    else:
        return False


def get_user_object(username):
    return UserObjectMySQL(username)
