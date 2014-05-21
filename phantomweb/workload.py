from __future__ import absolute_import

import json
import logging
import urlparse
import celery

from boto.ec2.autoscale import Tag
from boto.exception import EC2ResponseError
from boto.regioninfo import RegionInfo
from celery.result import AsyncResult
from phantomweb.tevent import Pool, TimeoutError
import boto
import boto.ec2.autoscale
import statsd

from phantomweb.celery import packer_build
from phantomweb.models import LaunchConfiguration, LaunchConfigurationDB, HostMaxPairDB, \
    PublicLaunchConfiguration, ImageGenerator, ImageGeneratorCloudConfig, ImageGeneratorScript, \
    ImageBuild, ImageBuildArtifact, PackerCredential
from phantomweb.phantom_web_exceptions import PhantomWebException
from phantomweb.util import PhantomWebDecorator, LogEntryDecorator, get_user_object


IAAS_TIMEOUT = 5
log = logging.getLogger('phantomweb.general')

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
def get_all_packer_credentials(username, clouds):
    """get all packer credentials"""
    packer_credentials_dict = {}
    for cloud_name, cloud in clouds.iteritems():
        packer_credentials_dict[cloud_name] = {}
        try:
            packer_credentials = PackerCredential.objects.get(username=username, cloud=cloud_name)
            packer_credentials_dict[cloud_name]["canonical_id"] = packer_credentials.canonical_id
            packer_credentials_dict[cloud_name]["usercert"] = packer_credentials.certificate
            packer_credentials_dict[cloud_name]["userkey"] = packer_credentials.key
            packer_credentials_dict[cloud_name]["openstack_username"] = packer_credentials.openstack_login
            packer_credentials_dict[cloud_name]["openstack_password"] = packer_credentials.openstack_password
            packer_credentials_dict[cloud_name]["openstack_project"] = packer_credentials.openstack_project
        except PackerCredential.DoesNotExist:
            pass

    return packer_credentials_dict


def add_packer_credentials(username, cloud, nimbus_user_cert=None, nimbus_user_key=None, nimbus_canonical_id=None):
    try:
        pc = PackerCredential.objects.get(username=username, cloud=cloud)
        pc.certificate = nimbus_user_cert
        pc.key = nimbus_user_key
        pc.canonical_id = nimbus_canonical_id
    except PackerCredential.DoesNotExist:
        pc = PackerCredential.objects.create(username=username, cloud=cloud, certificate=nimbus_user_cert,
                key=nimbus_user_key, canonical_id=nimbus_canonical_id, openstack_login=" ", openstack_password=" ",
                openstack_project=" ")

    pc.save()
    return pc


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

def get_all_image_generators(username):
    image_generators = []
    all_image_generators = ImageGenerator.objects.filter(username=username)
    for ig in all_image_generators:
        image_generators.append(ig.id)
    return image_generators


def create_image_generator(username, name, cloud_params, script):
    image_generator = ImageGenerator.objects.create(name=name, username=username)
    image_generator.save()
    for cloud_name in cloud_params:
        params = cloud_params[cloud_name]
        image_name = params.get("image_id")
        instance_type = params.get("instance_type")
        ssh_username = params.get("ssh_username")
        common_image = params.get("common")
        new_image_name = params.get("new_image_name")

        if image_name is None:
            raise PhantomWebException("You must provide an image_id in the cloud parameters")
        if instance_type is None:
            raise PhantomWebException("You must provide an instance_type in the cloud parameters")
        if ssh_username is None:
            raise PhantomWebException("You must provide an ssh_username in the cloud parameters")
        if common_image is None:
            raise PhantomWebException("You must provide a common boolean in the cloud parameters")
        if new_image_name is None:
            raise PhantomWebException("You must provide a new_image_name in the cloud parameters")

        igcc = ImageGeneratorCloudConfig.objects.create(
            image_generator=image_generator,
            cloud_name=cloud_name,
            image_name=image_name,
            ssh_username=ssh_username,
            instance_type=instance_type,
            common_image=common_image,
            new_image_name=new_image_name)
        igcc.save()

        igs = ImageGeneratorScript.objects.create(
            image_generator=image_generator,
            script_content=script)
        igs.save()

    return image_generator


def get_image_generator(id):
    try:
        image_generator = ImageGenerator.objects.get(id=id)
    except ImageGenerator.DoesNotExist:
        return None

    image_generator_dict = {
        "id": image_generator.id,
        "name": image_generator.name,
        "owner": image_generator.username,
        "cloud_params": {},
        "script": None,
    }

    cloud_configs = image_generator.imagegeneratorcloudconfig_set.all()
    for cc in cloud_configs:
        cloud_name = cc.cloud_name
        image_generator_dict["cloud_params"][cloud_name] = {
            "image_id": cc.image_name,
            "ssh_username": cc.ssh_username,
            "instance_type": cc.instance_type,
            "common": cc.common_image,
            "new_image_name": cc.new_image_name
        }

    scripts = image_generator.imagegeneratorscript_set.all()
    if len(scripts) != 1:
        raise PhantomWebException("There should be only 1 script, not %d" % len(scripts))

    image_generator_dict["script"] = scripts[0].script_content

    return image_generator_dict


def get_image_generator_by_name(username, name):
    image_generators = ImageGenerator.objects.filter(name=name, username=username)
    if len(image_generators) == 0:
        return None
    else:
        return image_generators[0]


def modify_image_generator(id, image_generator_params):
    try:
        image_generator = ImageGenerator.objects.get(id=id)
    except ImageGenerator.DoesNotExist:
        raise PhantomWebException("Trying to update image generator %s that doesn't exist?" % id)

    # Required params: name, script, cloud_params
    name = image_generator_params.get("name")
    if name is None:
        raise PhantomWebException("Must provide 'name' element to update an image generator")

    script = image_generator_params.get("script")
    if script is None:
        raise PhantomWebException("Must provide 'script' element to update an image generator")

    cloud_params = image_generator_params.get("cloud_params")
    if cloud_params is None:
        raise PhantomWebException("Must provide 'cloud_params' element to update an image generator")

    image_generator.name = name
    image_generator.save()

    scripts = image_generator.imagegeneratorscript_set.all()
    if len(scripts) != 1:
        raise PhantomWebException("There should be only 1 script, not %d" % len(scripts))
    scripts[0].script_content = script
    scripts[0].save()

    cloud_configs = image_generator.imagegeneratorcloudconfig_set.all()
    for cc in cloud_configs:
        cc.delete()

    for cloud_name in cloud_params:
        params = cloud_params[cloud_name]
        image_name = params.get("image_id")
        instance_type = params.get("instance_type")
        ssh_username = params.get("ssh_username")
        common_image = params.get("common")
        new_image_name = params.get("new_image_name")

        if image_name is None:
            raise PhantomWebException("You must provide an image_id in the cloud parameters")
        if instance_type is None:
            raise PhantomWebException("You must provide an instance_type in the cloud parameters")
        if ssh_username is None:
            raise PhantomWebException("You must provide an ssh_username in the cloud parameters")
        if common_image is None:
            raise PhantomWebException("You must provide a common boolean in the cloud parameters")
        if new_image_name is None:
            raise PhantomWebException("You must provide a new_image_name in the cloud parameters")

        igcc = ImageGeneratorCloudConfig.objects.create(
            image_generator=image_generator,
            cloud_name=cloud_name,
            image_name=image_name,
            ssh_username=ssh_username,
            instance_type=instance_type,
            common_image=common_image,
            new_image_name=new_image_name)
        igcc.save()

    return get_image_generator(id)


def remove_image_generator(id):
    try:
        image_generator = ImageGenerator.objects.get(id=id)
    except ImageGenerator.DoesNotExist:
        raise PhantomWebException("Could not delete image generator %s. Doesn't exist." % id)

    image_generator.delete()


def create_image_build(username, image_generator):
    user_obj = get_user_object(username)
    all_clouds = user_obj.get_clouds()
    sites = {}
    credentials = {}
    for site in image_generator["cloud_params"]:
        try:
            cloud = all_clouds[site]
            sites[site] = cloud.site_desc
            credentials[site] = {
                "access_key": cloud.iaas_key,
                "secret_key": cloud.iaas_secret,
            }

            if sites[site]["type"] == "nimbus":
                try:
                    packer_credentials = PackerCredential.objects.get(username=username, cloud=site)
                    credentials[site]["canonical_id"] = packer_credentials.canonical_id
                    credentials[site]["usercert"] = packer_credentials.certificate
                    credentials[site]["userkey"] = packer_credentials.key
                except PackerCredential.DoesNotExist:
                    raise PhantomWebException("Could not find extra Nimbus credentials for image generation.")
            elif sites[site]["type"] == "openstack":
                try:
                    packer_credentials = PackerCredential.objects.get(username=username, cloud=site)
                    credentials[site]["openstack_username"] = packer_credentials.openstack_login
                    credentials[site]["openstack_password"] = packer_credentials.openstack_password
                    credentials[site]["openstack_project"] = packer_credentials.openstack_project
                except PackerCredential.DoesNotExist:
                    raise PhantomWebException("Could not find extra OpenStack credentials for image generation.")
        except KeyError:
            raise PhantomWebException("Could not get cloud %s" % site)

    result = packer_build.delay(image_generator, sites, credentials)

    image_build = ImageBuild.objects.create(
        image_generator_id=image_generator["id"],
        celery_task_id=result.id,
        status='submitted',
        returncode=-1,
        full_output="",
        cloud_name=site,
        owner=username)
    image_build.save()

    return {"id": image_build.id, "ready": result.ready(), "owner": username}


def get_all_image_builds(username, image_generator_id):
    image_builds = []
    all_image_builds = ImageBuild.objects.filter(owner=username, image_generator_id=image_generator_id)
    for ib in all_image_builds:
        image_builds.append(ib.id)
    return image_builds


def get_image_build(username, image_build_id):
    try:
        image_build = ImageBuild.objects.get(id=image_build_id, owner=username)
    except ImageBuild.DoesNotExist:
        raise PhantomWebException("Could not find image build %s. Doesn't exist." % image_build_id)

    ret = {"id": image_build.id, "owner": username, "cloud_name": image_build.cloud_name}
    if image_build.status == "successful":
        ret["ready"] = True
    elif image_build.status == "submitted":
        result = AsyncResult(image_build.celery_task_id)
        ready = result.ready()
        ret["ready"] = ready
        if ready:
            if result.successful():
                image_build.returncode = result.result["returncode"]
                if image_build.returncode == 0:
                    image_build.status = "successful"
                else:
                    image_build.status = "failed"

                for cloud_name in result.result["artifacts"]:
                    image_build_artifact = ImageBuildArtifact.objects.create(
                        image_build_id=image_build.id,
                        cloud_name=cloud_name,
                        image_name=result.result["artifacts"][cloud_name])
                    image_build_artifact.save()

                image_build.full_output = result.result["full_output"]
                image_build.save()
            else:
                image_build.status = "failed"
                image_build.returncode = -1
                image_build.full_output = str(result.result)
                image_build.save()

    ret["status"] = image_build.status
    if image_build.status != "submitted":
        ret["returncode"] = image_build.returncode
        ret["full_output"] = image_build.full_output
        ret["artifacts"] = {}
        try:
            artifacts = ImageBuildArtifact.objects.filter(image_build_id=image_build_id)
            for artifact in artifacts:
                ret["artifacts"][artifact.cloud_name] = artifact.image_name
        except ImageBuildArtifact.DoesNotExist:
            raise PhantomWebException("Could not find image build artifact for image build id %s. Doesn't exist." % image_build_id)

    return ret


def remove_image_build(username, image_build_id):
    try:
        image_build = ImageBuild.objects.get(id=image_build_id, owner=username)
    except ImageBuild.DoesNotExist:
        raise PhantomWebException("Could not find image build %s. Doesn't exist." % image_build_id)

    image_build.delete()

#
#  cloud site management pages
#

@PhantomWebDecorator
@LogEntryDecorator
def phantom_get_sites(request_params, userobj, details=False):
    return userobj.get_possible_sites(details=details)
