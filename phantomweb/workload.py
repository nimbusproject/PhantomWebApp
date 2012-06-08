import boto
from boto.ec2.connection import EC2Connection
from boto.regioninfo import RegionInfo
import logging
import urlparse
import boto.ec2.autoscale
from phantomweb.phantom_web_exceptions import PhantomWebException
from phantomweb.util import PhantomWebDecorator, LogEntryDecorator
from phantomsql import phantom_get_default_key_name

import logging   # import the required logging module

g_general_log = logging.getLogger('phantomweb.general')

@LogEntryDecorator
def _get_phantom_con(userobj):
    url = userobj.phantom_info.phantom_url
    g_general_log.debug("Getting phantom can at %s" % (url))

    uparts = urlparse.urlparse(url)
    is_secure = uparts.scheme == 'https'
    region = RegionInfo(uparts.hostname)
    con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=userobj._user_dbobject.access_key, aws_secret_access_key=userobj._user_dbobject.access_secret, is_secure=is_secure, port=uparts.port, region=region)
    con.host = uparts.hostname
    return con

@LogEntryDecorator
def _get_iaas_compute_con(iaas_cloud):
    uparts = urlparse.urlparse(iaas_cloud.cloud_url)
    is_secure = uparts.scheme == 'https'
    ec2conn = EC2Connection(iaas_cloud.iaas_key, iaas_cloud.iaas_secret, host=uparts.hostname, port=uparts.port, is_secure=is_secure)
    ec2conn.host = uparts.hostname
    return ec2conn

@LogEntryDecorator
def _get_keys(ec2conn):
    r = ec2conn.get_all_key_pairs()
    rs = [k.name for k in r]
    return rs

@PhantomWebDecorator
@LogEntryDecorator
def get_iaas_info(request_params, userobj):

    params = ['cloud',]
    for p in params:
        if p not in request_params:
            raise PhantomWebDecorator('Missing parameter %s' % (p))

    cloud_name = request_params['cloud']
    iaas_cloud = userobj.get_cloud(cloud_name)

    ec2conn = _get_iaas_compute_con(iaas_cloud)
    g_general_log.debug("Looking up images for user %s on %s" % (userobj._user_dbobject.access_key, cloud_name))
    l = ec2conn.get_all_images()
    common_images = [c.id for c in l if c.is_public]
    user_images = [u.id for u in l if not u.is_public]

    response_dict = {
        'name': 'hello',
        'user_images': user_images,
        'common_images': common_images,
    }
    return response_dict

@PhantomWebDecorator
@LogEntryDecorator
def list_domains(request_params, userobj):
    con = _get_phantom_con(userobj)

    domain_names = None
    if 'domain_name' in request_params:
        domain_name = request_params['domain_name']
        domain_names = [domain_name,]
    g_general_log.debug("Looking up domain names %s for user %s" % (str(domain_names), userobj._user_dbobject.access_key))

    asgs = con.get_all_groups(names=domain_names)
    return_asgs = []

    for a in asgs:
        ent = {}
        ent['name'] = a.name
        ent['desired_capacity'] = a.desired_capacity
        lc_name = a.launch_config_name
        lcs = con.get_all_launch_configurations(names=[lc_name,])
        ent['cloudname'] = a.availability_zones[0]
        if lcs:
            lc = lcs[0]
            ent['lc_name'] = lc.name
            ent['image_id'] = lc.image_id
            ent['key_name'] = lc.key_name
            ent['instance_type'] = lc.instance_type
        inst_list = []
        for instance in a.instances:
            i_d = {}
            i_d['cloud'] = instance.availability_zone
            i_d['health_status'] = instance.health_status
            i_d['instance_id'] = instance.instance_id.strip()
            i_d['lifecycle_state'] = instance.lifecycle_state
            inst_list.append(i_d)
            i_d['hostname'] = "unknown"

            if i_d['instance_id']:
                # look up more info with boto.  this could be optimized for network communication
                iaas_cloud = userobj.get_cloud(i_d['cloud'])
                iaas_con = _get_iaas_compute_con(iaas_cloud)
                boto_insts = iaas_con.get_all_instances(instance_ids=[i_d['instance_id'],])
                if boto_insts and boto_insts[0].instances:
                    boto_i = boto_insts[0].instances[0]
                    i_d['hostname'] = boto_i.dns_name

        ent['instances'] = inst_list

        return_asgs.append(ent)

    response_dict = {
        'name': 'hello',
        'domains': return_asgs,
    }
    return response_dict


@LogEntryDecorator
def _find_or_create_config(con, size, image, keyname, common, lc_name):
    lcs = con.get_all_launch_configurations(names=[lc_name,])
    if not lcs:
        lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(con, name=lc_name, image_id=image, key_name=keyname, security_groups='default', instance_type=size)
        con.create_launch_configuration(lc)
        return lc
    return lcs[0]   


@PhantomWebDecorator
@LogEntryDecorator
def start_domain(request_params, userobj):
    con = _get_phantom_con(userobj)

    params = ['size', 'name', 'image', 'cloud', 'common', 'desired_size']
    for p in params:
        if p not in request_params:
            raise PhantomWebDecorator('Missing parameter %s' % (p))

    image_name = request_params['image']
    size = request_params['size']
    asg_name = request_params['name']
    cloud = request_params['cloud']
    common = request_params['common']

    try:
        desired_size = int(request_params['desired_size'])
    except:
        e_msg = 'Please set the desired size to an integer, not %s' % (str(request_params['desired_size']))
        g_general_log.error(e_msg)
        raise PhantomWebException(e_msg)

    lc_name = "WEB-%s-%s-%s" % (size, image_name, common)
    key_name = phantom_get_default_key_name()

    g_general_log.debug("starting to launch: %s %s %s %s %d" % (image_name, str(size), asg_name, cloud, desired_size))

    iaas_cloud = userobj.get_cloud(cloud)
    ec2con = _get_iaas_compute_con(iaas_cloud)
    kps = _get_keys(ec2con)
    if key_name not in kps:
        e_msg = "The key name %s is not known.  Please provide a public key in the settings section." % (key_name)
        g_general_log.error(e_msg)
        raise PhantomWebException(e_msg)

    lc_name = "%s@%s" % (lc_name, cloud)
    lc = _find_or_create_config(con, size, image_name, key_name, common, lc_name)
    asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=con, group_name=asg_name, availability_zones=[cloud], min_size=desired_size, max_size=desired_size)
    con.create_auto_scaling_group(asg)
    response_dict = {
        'Success': True,
    }
    return response_dict

@PhantomWebDecorator
@LogEntryDecorator
def delete_domain(request_params, userobj):
    con = _get_phantom_con(userobj)

    params = ['name']
    for p in params:
        if p not in request_params:
            return None

    asg_name = request_params['name']
    g_general_log.debug("deleting %s" % (asg_name))
    con.delete_auto_scaling_group(asg_name)
    response_dict = {
        'Success': True,
    }
    return response_dict


@PhantomWebDecorator
@LogEntryDecorator
def update_desired_size(request_params, userobj):
    con = _get_phantom_con(userobj)

    params = ['name', 'new_desired_size']
    for p in params:
        if p not in request_params:
            return None
    asg_name = request_params['name']

    try:
        asg_new_desired_size = int(request_params['new_desired_size'])
    except:
        e_msg = 'Please set the desired size to an integer, not %s' % (str(request_params['new_desired_size']))
        g_general_log.error(e_msg)
        raise PhantomWebException(e_msg)

    g_general_log.debug("updating %s to be size %d" % (asg_name, asg_new_desired_size))

    asgs = con.get_all_groups(names=[asg_name,])
    if not asgs:
        e_msg = "The domain %s does not exist." % (asg_name)
        raise PhantomWebException(e_msg)
    asgs[0].set_capacity(asg_new_desired_size)

    response_dict = {
        'Success': True,
    }
    return response_dict


@PhantomWebDecorator
@LogEntryDecorator
def phantom_main_html(request_params, userobj):
    instance_types = ["m1.small", "m1.large"]
    cloud_locations = userobj.iaasclouds.keys()
    response_dict = {
        'instance_types': instance_types,
        'cloud_locations': cloud_locations,
    }
    return response_dict
