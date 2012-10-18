import boto
from boto.ec2.autoscale import Tag
from boto.exception import EC2ResponseError
from boto.regioninfo import RegionInfo
import logging
import urlparse
import boto.ec2.autoscale
from phantomweb.models import LaunchConfigurationDB, HostMaxPairDB
from phantomweb.phantom_web_exceptions import PhantomWebException
from phantomweb.util import PhantomWebDecorator, LogEntryDecorator
from phantomsql import phantom_get_default_key_name

import logging   # import the required logging module

g_general_log = logging.getLogger('phantomweb.general')

# at some point this should come from some sort of DB
g_instance_types = ["m1.small", "m1.large", "m1.xlarge"]

#
# we are only dealing with launch configurations that were made with the web app
#
def _get_launch_configuration(phantom_con, lc_db_object):
    lc_name = lc_db_object.name
    site_dict = {}
    host_vm_db_objs_a = HostMaxPairDB.objects.filter(launch_config=lc_db_object)
    for host_vm_db_obj in host_vm_db_objs_a:
        site_name = host_vm_db_obj.cloud_name
        shoe_horn_lc_name = "%s@%s" % (lc_name, site_name)
        try:
            lcs = phantom_con.get_all_launch_configurations(names=[shoe_horn_lc_name,])
        except Exception, ex:
            lcs = []
        if len(lcs) != 1:
            raise PhantomWebException("Error communication with Phantom REST.  %s might be misconfigured | %s" % (shoe_horn_lc_name, str(ex)))
        lc = lcs[0]
        site_entry = {
            'cloud': site_name,
            'image_id': lc.image_id,
            'instance_type': lc.instance_type,
            'keyname': lc.key_name,
            'user_data': lc.user_data,
            'common': host_vm_db_obj.common_image,
            'max_vm': host_vm_db_obj.max_vms,
            'rank': host_vm_db_obj.rank
        }
        site_dict[site_name] = site_entry

    return site_dict

def _get_all_launch_configurations(phantom_con):
    all_lc_dict = {}
    lc_db_objects_a = LaunchConfigurationDB.objects.all()
    for lc_db_object in lc_db_objects_a:
        site_dict = _get_launch_configuration(phantom_con, lc_db_object)
        all_lc_dict[lc_db_object.name] = site_dict
    return all_lc_dict

def _get_all_domains(phantom_con):

    asgs = phantom_con.get_all_groups()

    return_asgs = {}
    for a in asgs:
        ent = {}
        ent['name'] = a.name
        ent['vm_size'] = a.desired_capacity
        ent['lc_name'] = a.launch_config_name # .replace("[LaunchConfiguration:", "")
        return_asgs[a.name] = ent

    return return_asgs

@LogEntryDecorator
def _get_phantom_con(userobj):
    url = userobj.phantom_info.phantom_url
    g_general_log.debug("Getting phantom can at %s" % (url))
    uparts = urlparse.urlparse(url)
    is_secure = uparts.scheme == 'https'
    region = RegionInfo(endpoint=uparts.hostname)
    con = boto.ec2.autoscale.AutoScaleConnection(aws_access_key_id=userobj._user_dbobject.access_key, aws_secret_access_key=userobj._user_dbobject.access_secret, is_secure=is_secure, port=uparts.port, region=region, validate_certs=False)
    con.host = uparts.hostname
    return con

@LogEntryDecorator
def _start_domain(phantom_con, domain_name, lc_name, vm_count, host_list_str, a_cloudname):

    shoe_horn = "%s@%s" % (lc_name, a_cloudname)
    try:
        lc = phantom_con.get_all_launch_configurations(names=[shoe_horn,])
    except EC2ResponseError, ec2re:
        lc = None
    if not lc:
        raise PhantomWebException("The LC %s no longer exists." % (lc_name))

    lc = lc[0]

    policy_name_key = 'PHANTOM_DEFINTION'
    policy_name = 'error_overflow_n_preserving'
    ordered_clouds_key = 'clouds'
    n_preserve_key = 'n_preserve'
    n_preserve = vm_count

    policy_tag = Tag(connection=phantom_con, key=policy_name_key, value=policy_name, resource_id=domain_name)
    clouds_tag = Tag(connection=phantom_con, key=ordered_clouds_key, value=host_list_str, resource_id=domain_name)
    npreserve_tag = Tag(connection=phantom_con, key=n_preserve_key, value=n_preserve, resource_id=domain_name)

    tags = [policy_tag, clouds_tag, npreserve_tag]

    asg = boto.ec2.autoscale.group.AutoScalingGroup(launch_config=lc, connection=phantom_con, group_name=domain_name, availability_zones=["us-east-1"], min_size=vm_count, max_size=vm_count, tags=tags)
    phantom_con.create_auto_scaling_group(asg)


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
def terminate_iaas_instance(request_params, userobj):

    params = ['cloud','instance']
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))

    cloud_name = request_params['cloud']
    iaas_cloud = userobj.get_cloud(cloud_name)
    instance = request_params['instance']

    ec2conn = iaas_cloud.get_iaas_compute_con()
    g_general_log.debug("User %s terminating the instance %s on %s" % (userobj._user_dbobject.access_key, instance, cloud_name))
    ec2conn.terminate_instances(instance_ids=[instance,])

    response_dict = {
        'name': 'terminating',
        'success': 'success',
        'instance': instance,
        'cloud': cloud_name
    }
    return response_dict

#
#  cloud site management pages
#
@PhantomWebDecorator
@LogEntryDecorator
def phantom_sites_delete(request_params, userobj):
    params = ['cloud',]
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))

    site_name = request_params['cloud']

    userobj.delete_site(site_name)
    userobj._load_clouds()
    response_dict = {
    }
    return response_dict


@PhantomWebDecorator
@LogEntryDecorator
def phantom_sites_add(request_params, userobj):
    params = ['cloud', "access", "secret", "keyname"]
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))

    site_name = request_params['cloud']
    keyname = request_params['keyname']
    access = request_params['access']
    secret = request_params['secret']

    userobj.add_site(site_name, access, secret, keyname)
    response_dict = {
    }
    return response_dict


@PhantomWebDecorator
@LogEntryDecorator
def phantom_sites_load(request_params, userobj):
    sites = userobj.get_clouds()
    all_sites = userobj.get_possible_sites()

    out_info = {}
    for site_name in sites:
        ci = sites[site_name]
        ci_dict = {
            'username': ci.username,
            'access_key': ci.iaas_key,
            'secret_key': ci.iaas_secret,
            'keyname': ci.keyname,
            'status': 0,
            'status_msg': ""
        }

        ec2conn = ci.get_iaas_compute_con()
        try:
            keypairs = ec2conn.get_all_key_pairs()
            keyname_list = [k.name for k in keypairs]
            ci_dict['keyname_list'] = keyname_list
            ci_dict['status_msg'] = ""
        except Exception, boto_ex:
            g_general_log.error("Error connecting to the service %s" % (str(boto_ex)))
            ci_dict['keyname_list'] = []
            ci_dict['status_msg'] = "Error communication with the specific cloud %s.  Please check your credentials." % (site_name)
            ci_dict['status'] = 1

        out_info[site_name] = ci_dict

    response_dict = {
        'sites': out_info,
        'all_sites': all_sites
    }
    return response_dict

def _parse_param_name(needle, haystack, request_params, lc_dict):
    ndx = haystack.find("." + needle)
    if ndx < 0:
        return lc_dict
    site_name = haystack[:ndx]
    val = request_params[haystack]

    if site_name in lc_dict:
        entry = lc_dict[site_name]
    else:
        entry = {}
    entry[needle] = val
    lc_dict[site_name] = entry

    return lc_dict

#
#  cloud launch config functions
#
@PhantomWebDecorator
@LogEntryDecorator
def phantom_lc_load(request_params, userobj):
    global g_instance_types

    clouds_d = userobj.get_clouds()

    phantom_con = _get_phantom_con(userobj)

    all_lc_dict = _get_all_launch_configurations(phantom_con)
    iaas_info = {}
    for cloud_name in clouds_d:
        try:
            cloud_info = {}
            cloud = clouds_d[cloud_name]
            ec2conn = cloud.get_iaas_compute_con()
            g_general_log.debug("Looking up images for user %s on %s" % (userobj._user_dbobject.access_key, cloud_name))
            # This does not seem to be working l = ec2conn.get_all_images(filters={'is-public': False})
            l = ec2conn.get_all_images(filters={'is-public': False})
            user_images = [u.id for u in l if not u.is_public]
            keypairs = ec2conn.get_all_key_pairs()
            keynames = [k.name for k in keypairs]
            cloud_info['personal_images'] = user_images
            cloud_info['keynames'] = keynames
            cloud_info['instances'] = g_instance_types
            cloud_info['status'] = 0
        except Exception, ex:
            g_general_log.warn("Error communication with %s for user %s | %s" % (cloud_name, userobj._user_dbobject.access_key, str(ex)))
            cloud_info = {'error': str(ex)}
            cloud_info['status'] = 1
        iaas_info[cloud_name] = cloud_info

    response_dict = {
        'cloud_info': iaas_info,
        'lc_info': all_lc_dict
    }
    return response_dict


@PhantomWebDecorator
@LogEntryDecorator
def phantom_lc_save(request_params, userobj):
    lc_name = request_params['name']

    lc_dict = {}
    # we need to convert params to a usable dict
    for param_name in request_params:
        _parse_param_name("cloud", param_name, request_params, lc_dict)
        _parse_param_name("keyname", param_name, request_params, lc_dict)
        _parse_param_name("image_id", param_name, request_params, lc_dict)
        _parse_param_name("instance_type", param_name, request_params, lc_dict)
        _parse_param_name("max_vm", param_name, request_params, lc_dict)
        _parse_param_name("common", param_name, request_params, lc_dict)
        _parse_param_name("rank", param_name, request_params, lc_dict)

    lc_db_object = LaunchConfigurationDB.objects.filter(name=lc_name)
    if not lc_db_object:
        lc_db_object = LaunchConfigurationDB.objects.create(name=lc_name)
    else:
        lc_db_object = lc_db_object[0]
    lc_db_object.save()

    phantom_con = _get_phantom_con(userobj)

    try:
        for site_name in lc_dict:
            lc_conf_name = "%s@%s" % (lc_name, site_name)
            entry = lc_dict[site_name]

            # check for valid image
            cloud_object = userobj.get_cloud(site_name)
            ec2conn = cloud_object.get_iaas_compute_con()
            try:
                tmp_img = ec2conn.get_all_images(image_ids=[entry['image_id']])
            except EC2ResponseError, boto_image_ex:
                tmp_img = None
            if not tmp_img:
                raise PhantomWebException("No such image %s for cloud %s" % (entry['image_id'], site_name))

            try:
                # we probably need to list everything with the base name and delete it
                    phantom_con.delete_launch_configuration(lc_conf_name)
            except Exception, boto_del_ex:
                # delete in case this is an update
                pass
            lc = boto.ec2.autoscale.launchconfig.LaunchConfiguration(phantom_con, name=lc_conf_name, image_id=entry['image_id'], key_name=entry['keyname'], security_groups=['default'], instance_type=entry['instance_type'])
            phantom_con.create_launch_configuration(lc)

            is_common = entry['common'].lower() == "true"
            host_max_db_a = HostMaxPairDB.objects.filter(cloud_name=site_name, launch_config=lc_db_object)
            if host_max_db_a:
                host_max_db = host_max_db_a[0]
            else:
                host_max_db = HostMaxPairDB.objects.create(cloud_name=site_name, max_vms=entry['max_vm'], launch_config=lc_db_object, rank=int(entry['rank']), common_image=is_common)
            host_max_db.save()
    except Exception, boto_ex:
        g_general_log.error("Error adding the launch configuration %s | %s" % (lc_name, str(boto_ex)))
        raise PhantomWebException(str(boto_ex))

    response_dict = {}
    
    return response_dict

@PhantomWebDecorator
@LogEntryDecorator
def phantom_lc_delete(request_params, userobj):
    params = ["name",]
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))

    lc_name = request_params['name']

    phantom_con = _get_phantom_con(userobj)
    try:
        lcs = phantom_con.get_all_launch_configurations()
    except Exception, ex:
        raise PhantomWebException("Error communication with Phantom REST: %s" % (str(ex)))


    lc_db_object = LaunchConfigurationDB.objects.filter(name=lc_name)
    if not lc_db_object or len(lc_db_object) < 1:
        raise PhantomWebException("No such launch configuration %s. Misconfigured service" % (lc.name))
    lc_db_object = lc_db_object[0]
    host_vm_db_a = HostMaxPairDB.objects.filter(launch_config=lc_db_object)
    if not host_vm_db_a:
        raise PhantomWebException("No such launch configuration %s. Misconfigured service" % (lc_name))

    for lc in lcs:
        ndx = lc.name.find(lc_name)
        if ndx == 0:
            lc.delete()
    for host_vm_db in host_vm_db_a:
        host_vm_db.delete()
    lc_db_object.delete()

    response_dict = {}

    return response_dict



@PhantomWebDecorator
@LogEntryDecorator
def phantom_domain_load(request_params, userobj):
    phantom_con = _get_phantom_con(userobj)

    domains = _get_all_domains(phantom_con)
    all_lc_dict = _get_all_launch_configurations(phantom_con)

    lc_names = []
    for name in all_lc_dict.keys():
        lc_names.append(name)

    response_dict = {
        'launchconfigs': lc_names,
        'domains': domains
        }

    return response_dict

@PhantomWebDecorator
@LogEntryDecorator
def phantom_domain_start(request_params, userobj):
    params = ['name', "lc_name", "vm_count", ]
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))
    domain_name = request_params["name"]
    lc_name = request_params["lc_name"]
    vm_count = request_params["vm_count"]


    lc_db_object = LaunchConfigurationDB.objects.filter(name=lc_name)
    if not lc_db_object or len(lc_db_object) < 1:
        raise PhantomWebException("The launch configuration %s is not known to the web application." % (lc_name))

    lc_db_object = lc_db_object[0]
    host_vm_dbs = HostMaxPairDB.objects.filter(launch_config=lc_db_object)

    sorted_by_rank = sorted(host_vm_dbs, key=lambda hm: hm.rank)

    # we need just any cloud name from the list to properly fake the AWS lc name
    a_cloudname = None
    ordered_hosts = ""
    delim = ""
    for hm in sorted_by_rank:
        ordered_hosts = ordered_hosts + delim + "%s:%d" % (hm.cloud_name, hm.max_vms)
        a_cloudname = hm.cloud_name
        delim = ","


    phantom_con = _get_phantom_con(userobj)
    _start_domain(phantom_con, domain_name, lc_name, vm_count, ordered_hosts, a_cloudname)

    response_dict = {}
    return response_dict

@PhantomWebDecorator
@LogEntryDecorator
def phantom_domain_resize(request_params, userobj):
    params = ['name', "vm_count"]
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))

    domain_name = request_params["name"]
    new_size = request_params["vm_count"]

    try:
        phantom_con = _get_phantom_con(userobj)
        asg = phantom_con.get_all_groups(names=[domain_name,])
        if not asg:
            raise PhantomWebException("domain %s not found" % (domain_name))
        asg = asg[0]
        asg.set_capacity(new_size)
    except PhantomWebException:
        raise
    except Exception, ex:
        raise PhantomWebException(str(ex))
    response_dict = {}
    return response_dict


@PhantomWebDecorator
@LogEntryDecorator
def phantom_domain_terminate(request_params, userobj):
    params = ['name',]
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))

    domain_name = request_params["name"]

    g_general_log.debug("deleting %s" % (domain_name))
    phantom_con = _get_phantom_con(userobj)
    phantom_con.delete_auto_scaling_group(domain_name)

    response_dict = {}
    return response_dict

@PhantomWebDecorator
@LogEntryDecorator
def phantom_instance_terminate(request_params, userobj):
    params = ['instance', "adjust"]
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))

    instance_id = request_params["instance"]
    adjust = request_params["adjust"]
    adjust = adjust.lower() == "true"

    g_general_log.debug("deleting %s" % (instance_id))
    phantom_con = _get_phantom_con(userobj)

    phantom_con.terminate_instance(instance_id, decrement_capacity=adjust)

    response_dict = {}
    return response_dict

@PhantomWebDecorator
@LogEntryDecorator
def phantom_domain_details(request_params, userobj):
    params = ['name',]
    for p in params:
        if p not in request_params:
            raise PhantomWebException('Missing parameter %s' % (p))

    domain_name = request_params["name"]

    phantom_con = _get_phantom_con(userobj)

    g_general_log.debug("Looking up domain name %s for user %s" % (str(domain_name), userobj._user_dbobject.access_key))

    try:
        asgs = phantom_con.get_all_groups(names=[domain_name,])
    except Exception, ex:
        raise PhantomWebException("There was a problem finding the domain %s: %s" % (domain_name, str(ex)))
    if not asgs:
        raise PhantomWebException("No domain named %s was found" % (domain_name))

    asg = asgs[0]

    lc_name = asg.launch_config_name
    lc_db_objects_a = LaunchConfigurationDB.objects.filter(name=lc_name)
    if not lc_db_objects_a:
        msg = "Could not find the launch configuration '%s' associated with the domain '%s'" % (lc_name, domain_name)
        g_general_log.error(msg)
        raise PhantomWebException(msg)

    lc_db_object = lc_db_objects_a[0]
    site_dict = _get_launch_configuration(phantom_con, lc_db_object)

    inst_list = []
    for instance in asg.instances:
        i_d = {}
        i_d['health_status'] = instance.health_status
        i_d['instance_id'] = instance.instance_id.strip()
        i_d['lifecycle_state'] = instance.lifecycle_state
        i_d['hostname'] = "unknown"
        if not instance.availability_zone or instance.availability_zone not in site_dict.keys():
            error_msg = "No availabilty zone for %s in domain %s" % (str(instance), domain_name)
            g_general_log.error(error_msg)
            raise PhantomWebException(error_msg)
        cloud_name = instance.availability_zone
        i_d['cloud'] = cloud_name

        site = site_dict[cloud_name]
        i_d['image_id'] = site['image_id']
        i_d['instance_type'] = site['instance_type']
        i_d['keyname'] = site['keyname']
        i_d['user_data'] = site['user_data']

        if i_d['instance_id']:
            # look up more info with boto. this could be optimized for network communication
            iaas_cloud = userobj.get_cloud(cloud_name)
            if not iaas_cloud:
                error_msg = "The user %s does not have a cloud configured %s.  They must have deleted it after starting the domain." % (userobj._user_dbobject.access_key, cloud_name)
                g_general_log.error(error_msg)
                raise PhantomWebException(error_msg)
            
            iaas_con = iaas_cloud.get_iaas_compute_con()
            boto_insts = iaas_con.get_all_instances(instance_ids=[i_d['instance_id'],])
            if boto_insts and boto_insts[0].instances:
                boto_i = boto_insts[0].instances[0]
                i_d['hostname'] = boto_i.dns_name
        inst_list.append(i_d)

    response_dict = {
        'instances': inst_list,
        'lc_name': asg.launch_config_name,
        'domain_size': asg.desired_capacity
    }
    return response_dict


