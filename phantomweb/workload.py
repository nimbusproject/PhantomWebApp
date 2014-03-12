import json
import logging
import urlparse

from boto.ec2.autoscale import Tag
from boto.exception import EC2ResponseError
from boto.regioninfo import RegionInfo
from phantomweb.tevent import Pool, TimeoutError
import boto
import boto.ec2.autoscale
import statsd

from phantomweb.models import LaunchConfiguration, LaunchConfigurationDB, HostMaxPairDB, \
    PublicLaunchConfiguration
from phantomweb.phantom_web_exceptions import PhantomWebException
from phantomweb.util import PhantomWebDecorator, LogEntryDecorator, get_user_object


IAAS_TIMEOUT = 5
log = logging.getLogger('phantomweb.general')

# at some point this should come from some sort of DB
g_instance_types = ["m1.small", "m1.large", "m1.xlarge"]

g_engine_to_phantom_de_map = {
    "epu.decisionengine.impls.phantom_multi_site_overflow.PhantomMultiSiteOverflowEngine": "multicloud",
    "epu.decisionengine.impls.sensor.SensorEngine": "sensor",
}

PHANTOM_REGION = 'phantom'

OPENTSDB_METRICS = [
    "df.1kblocks.free", "df.1kblocks.total", "df.1kblocks.used",
    "df.inodes.free", "df.inodes.total", "df.inodes.used", "iostat.part.ios_in_progress",
    "iostat.part.msec_read", "iostat.part.msec_total", "iostat.part.msec_weighted_total",
    "iostat.part.msec_write", "iostat.part.read_merged", "iostat.part.read_requests",
    "iostat.part.read_sectors", "iostat.part.write_merged", "iostat.part.write_requests",
    "iostat.part.write_sectors", "net.sockstat.ipfragqueues", "net.sockstat.memory",
    "net.sockstat.num_orphans", "net.sockstat.num_sockets", "net.sockstat.num_timewait",
    "net.sockstat.sockets_inuse", "net.stat.tcp.abort", "net.stat.tcp.abort.failed",
    "net.stat.tcp.congestion.recovery", "net.stat.tcp.delayedack",
    "net.stat.tcp.failed_accept", "net.stat.tcp.memory.pressure",
    "net.stat.tcp.memory.prune", "net.stat.tcp.packetloss.recovery",
    "net.stat.tcp.reording", "net.stat.tcp.syncookies", "proc.net.bytes",
    "proc.net.dropped", "proc.net.errs", "proc.net.packets", "proc.net.tcp",
    "proc.kernel.entropy_avail", "proc.loadavg.15min", "proc.loadavg.1min",
    "proc.loadavg.5min", "proc.loadavg.runnable", "proc.loadavg.total_threads",
    "proc.meminfo.active", "proc.meminfo.anonpages", "proc.meminfo.bounce",
    "proc.meminfo.buffers", "proc.meminfo.cached", "proc.meminfo.commitlimit",
    "proc.meminfo.committed_as", "proc.meminfo.dirty", "proc.meminfo.highfree",
    "proc.meminfo.hightotal", "proc.meminfo.inactive", "proc.meminfo.lowfree",
    "proc.meminfo.lowtotal", "proc.meminfo.mapped", "proc.meminfo.memfree",
    "proc.meminfo.memtotal", "proc.meminfo.nfs_unstable", "proc.meminfo.pagetables",
    "proc.meminfo.slab", "tcollector.collector.lines_invalid",
    "tcollector.collector.lines_received", "tcollector.collector.lines_sent",
    "tcollector.reader.lines_collected", "tcollector.reader.lines_dropped"
]


def _get_launch_configuration(phantom_con, lc_db_object):
    """
    we are only dealing with launch configurations that were made with the web app
    """
    lc_name = lc_db_object.name
    site_dict = {}
    host_vm_db_objs_a = HostMaxPairDB.objects.filter(launch_config=lc_db_object)
    for host_vm_db_obj in host_vm_db_objs_a:
        site_name = host_vm_db_obj.cloud_name
        shoe_horn_lc_name = "%s@%s" % (lc_name, site_name)
        try:
            lcs = phantom_con.get_all_launch_configurations(names=[shoe_horn_lc_name, ])
        except Exception, ex:
            raise PhantomWebException(
                "Error communicating with Phantom REST.  %s might be misconfigured | %s" % (
                shoe_horn_lc_name, str(ex)))

        if len(lcs) != 1:
            log.error(
                "Received empty launch configuration list from Phantom REST.  %s might be misconfigured" % (
                shoe_horn_lc_name, ))
            continue
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


########

# New implementation for the Phantom API

def get_all_keys(clouds):
    """get all ssh keys from a dictionary of UserCloudInfo objects
    """
    pool = Pool(processes=10)
    key_dict = {}

    results = {}
    for cloud_name, cloud in clouds.iteritems():
        result = pool.apply_async(cloud.get_keys)
        results[cloud_name] = result

    pool.close()

    for cloud_name, result in results.iteritems():
        try:
            key_dict[cloud_name] = result.get(IAAS_TIMEOUT)
        except TimeoutError:
            log.exception("Timed out getting keys from %s" % cloud_name)
            key_dict[cloud_name] = []
        except Exception:
            log.exception("Unexpected error getting keys from %s" % cloud_name)
            key_dict[cloud_name] = []

    return key_dict


def upload_key(cloud, name, key):
    """upload an ssh key to iaas
    """

    cloud.upload_key(name, key)


def create_launch_configuration(username, name, cloud_params, context_params, appliance=None):
    lc = LaunchConfiguration.objects.create(name=name, username=username)

    user_obj = get_user_object(username)
    user_obj.create_dt(name, cloud_params, context_params, appliance)

    lc.save()

    return lc


def update_launch_configuration(id, cloud_params, context_params, appliance=None):
    lc = get_launch_configuration(id)
    if lc is None:
        raise PhantomWebException("Trying to update lc %s that doesn't exist?" % id)

    username = lc.get('owner')
    name = lc.get('name')
    user_obj = get_user_object(username)
    user_obj.create_dt(name, cloud_params, context_params, appliance)

    return lc


def get_all_launch_configurations(username, public=False):

    if public is True:
        public_lcs = PublicLaunchConfiguration.objects.all()
        lcs = {}
        for public_lc in public_lcs:
            lcs[public_lc.launch_configuration.id] = {
                'id': public_lc.launch_configuration.id,
                'description': public_lc.description,
            }

    else:
        lcs = {}
        all_lcs = LaunchConfiguration.objects.filter(username=username)
        for lc in all_lcs:
            lcs[lc.id] = {
                'id': lc.id,
            }
    return lcs


def get_launch_configuration(id):

    try:
        lc = LaunchConfiguration.objects.get(id=id)
    except LaunchConfiguration.DoesNotExist:
        return None

    lc_dict = {
        "id": lc.id,
        "name": lc.name,
        "owner": lc.username,
        "cloud_params": {}
    }

    user_obj = get_user_object(lc.username)
    dt = user_obj.get_dt(lc.name)
    if dt is None:
        log.error("DT %s doesn't seem to be in DTRS, continuing anyway" % lc.name)
        dt = {}
    contextualization = dt.get('contextualization', {})

    if contextualization:
        userdata = contextualization.get("userdata")
        method = contextualization.get("method")
        run_list = contextualization.get("run_list")
        attributes = contextualization.get("attributes")
        if method == 'userdata' or userdata is not None:
            lc_dict["contextualization_method"] = 'user_data'
            lc_dict["user_data"] = userdata
        elif method == 'chef':
            lc_dict["contextualization_method"] = 'chef'
            lc_dict["chef_runlist"] = run_list
            lc_dict["chef_attributes"] = attributes
        elif method is None:
            lc_dict["contextualization_method"] = 'none'

    appliance = dt.get('appliance')
    if appliance:
        lc_dict['appliance'] = appliance

    for cloud, mapping in dt.get('mappings', {}).iteritems():

        lc_dict["cloud_params"][cloud] = {
            "max_vms": mapping.get('max_vms'),
            "common": mapping.get('common'),
            "rank": mapping.get('rank'),
            "image_id": mapping.get("iaas_image"),
            "instance_type": mapping.get("iaas_allocation")
        }

    return lc_dict


def get_launch_configuration_object(id):
    try:
        lc = LaunchConfiguration.objects.get(id=id)
    except LaunchConfiguration.DoesNotExist:
        return None
    return lc


def get_launch_configuration_by_name(username, name):
    lcs = LaunchConfiguration.objects.filter(name=name, username=username)
    if len(lcs) == 0:
        return None
    else:
        return lcs[0]


def remove_launch_configuration(username, lc_id):
    try:
        lc = LaunchConfiguration.objects.get(id=lc_id)
    except LaunchConfiguration.DoesNotExist:
        raise PhantomWebException("Could not delete launch configuration %s. Doesn't exist." % lc_id)

    user_obj = get_user_object(lc.username)
    try:
        user_obj.remove_dt(lc.name)
    except Exception:
        log.exception("Couldn't delete dt %s" % lc.name)

    lc.delete()


def get_host_max_pair(launch_config, cloud_name):
    hmp = HostMaxPairDB.objects.filter(cloud_name=cloud_name, launch_config=launch_config)
    if len(hmp) == 0:
        return None
    else:
        return hmp[0]


def set_host_max_pair(launch_config, cloud_name, max_vms=-1, rank=0, common_image=False):
    host_max_pairs = HostMaxPairDB.objects.filter(cloud_name=cloud_name, launch_config=launch_config)
    if len(host_max_pairs) == 0:
        host_max_pair = HostMaxPairDB.objects.create(cloud_name=cloud_name,
            launch_config=launch_config, max_vms=max_vms, rank=rank, common_image=common_image)
    else:
        host_max_pair = host_max_pairs[0]
        host_max_pair.update(cloud_name=cloud_name,
            launch_config=launch_config, max_vms=max_vms, rank=rank, common_image=common_image)

    host_max_pair.save()
    return host_max_pair


def get_all_domains(username):
    user_obj = get_user_object(username)
    domains = user_obj.get_all_domains(username)

    return_domains = []
    for d in domains:
        ent = user_obj.get_domain(username, d)
        return_domains.append(ent)

    return return_domains


def get_domain(username, id):
    user_obj = get_user_object(username)
    return user_obj.get_domain(username, id)


def get_domain_instances(username, id):
    user_obj = get_user_object(username)
    return user_obj.get_domain_instances(username, id)


def get_domain_instance(username, id, instance_id):
    user_obj = get_user_object(username)
    instances = user_obj.get_domain_instances(username, id)
    wanted_instance = None
    for instance in instances:
        if instance.get('id') == instance_id:
            wanted_instance = instance
            break
    return wanted_instance


def get_domain_by_name(username, name):
    domains = get_all_domains(username)
    for domain in domains:
        if domain.get('name') == name:
            return domain
    return None


def terminate_domain_instance(username, domain_id, instance_id):
    user_obj = get_user_object(username)
    instance_to_terminate = get_domain_instance(username, domain_id, instance_id)
    if instance_to_terminate is None:
        raise PhantomWebException("No instance %s available to terminate" % instance_id)

    instance_iaas_id = instance_to_terminate.get('iaas_instance_id')
    if instance_iaas_id is None:
        raise PhantomWebException("Instance %s has no iaas ID" % instance_id)

    cloud_name = instance_to_terminate.get('cloud')
    cloud_name = cloud_name.split("/")[-1]

    iaas_cloud = user_obj.get_cloud(cloud_name)
    iaas_connection = iaas_cloud.get_iaas_compute_con()

    log.debug("User %s terminating the instance %s on %s" % (username, instance_iaas_id, cloud_name))

    timer = statsd.Timer('phantomweb')
    timer.start()

    timer_cloud = statsd.Timer('phantomweb')
    timer_cloud.start()

    try:
        iaas_connection.terminate_instances(instance_ids=[instance_iaas_id, ])
    except Exception:
        log.exception("Couldn't terminate %s" % instance_iaas_id)
    timer.stop('terminate_instances.timing')
    timer_cloud.stop('terminate_instances.%s.timing' % cloud_name)

    return


def remove_domain(username, id):
    user_obj = get_user_object(username)
    return user_obj.remove_domain(username, id)


def create_domain(username, name, parameters):
    user_obj = get_user_object(username)
    lc_name = parameters.get('lc_name')
    lc = get_launch_configuration_by_name(username, lc_name)
    if lc is None:
        raise PhantomWebException("No launch configuration named %s. Can't make domain" % lc_name)
    lc_dict = get_launch_configuration(lc.id)
    clouds = []
    for cloud_name, cloud in lc_dict.get('cloud_params', {}).iteritems():
        cloud = {
            'site_name': cloud_name,
            'rank': cloud.get('rank'),
            'size': cloud.get('max_vms'),
        }
        clouds.append(cloud)

    parameters['clouds'] = clouds
    return user_obj.add_domain(username, name, parameters)


def modify_domain(username, id, parameters):
    user_obj = get_user_object(username)
    return user_obj.reconfigure_domain(username, id, parameters)


def get_sensors(username):
    return OPENTSDB_METRICS

#
#  cloud site management pages
#

@PhantomWebDecorator
@LogEntryDecorator
def phantom_get_sites(request_params, userobj, details=False):
    return userobj.get_possible_sites(details=details)
