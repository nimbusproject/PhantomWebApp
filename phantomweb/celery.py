from __future__ import absolute_import

import json
import os
import re
import subprocess
import tempfile

from celery import Celery

from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phantomweb.settings')

cloud_client_path = settings.NIMBUS_CLOUD_CLIENT_PATH

broker = 'amqp://%s:%s@%s:%s//' % (settings.RABBITMQ_USERNAME, settings.RABBITMQ_PASSWORD, settings.RABBITMQ_HOSTNAME, settings.RABBITMQ_PORT)
app = Celery('phantomweb', backend='amqp', broker=broker)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

def ec2_builder_config(cloud_name, site, site_credentials, config):
    return {
        "name": "amazon-ebs-%s" % cloud_name,
        "type": "amazon-ebs",
        "region": site["region"],
        "source_ami": config["image_id"],
        "instance_type": config["instance_type"],
        "ssh_username": config["ssh_username"],
        "ami_name": config["new_image_name"],
        "access_key": site_credentials["access_key"],
        "secret_key": site_credentials["secret_key"]
    }


def openstack_builder_config(cloud_name, site, site_credentials, config):
    packer_config = {
        "name": "openstack-%s" % cloud_name,
        "type": "openstack",
        "username": site_credentials["openstack_username"],
        "password": site_credentials["openstack_password"],
        "provider": site["provider_url"],
        "ssh_username": config["ssh_username"],
        "image_name": config["new_image_name"],
        "source_image": config["image_id"],
        "flavor": "1", # FIXME
        "project": site_credentials["openstack_project"],
        "region": site["region"]
    }

    if site.get("ip_pool_name"):
        packer_config["ip_pool_name"] = site["ip_pool_name"]

    if site.get("packer_insecure"):
        packer_config["insecure"] = site["packer_insecure"]

    if site.get("use_floating_ip"):
        packer_config["use_floating_ip"] = site["use_floating_ip"]

    if site.get("floating_ip_pool"):
        packer_config["floating_ip_pool"] = site["floating_ip_pool"]

    return packer_config


def nimbus_builder_config(cloud_name, site, site_credentials, config):
    usercert_file, usercert_file_path = tempfile.mkstemp()
    with os.fdopen(usercert_file, 'w') as f:
        f.write(site_credentials["usercert"])

    userkey_file, userkey_file_path = tempfile.mkstemp()
    with os.fdopen(userkey_file, 'w') as f:
        f.write(site_credentials["userkey"])

    builder_config = {
        "name": "nimbus-%s" % cloud_name,
        "type": "nimbus",
        "factory": "%s:%d" % (site["host"], site["factory_port"]),
        "repository": "%s:%d" % (site["host"], site["repository_port"]),
        "factory_identity": site["factory_identity"],
        "s3id": site_credentials["access_key"],
        "s3key": site_credentials["secret_key"],
        "canonicalid": site_credentials["canonical_id"],
        "cert": usercert_file_path,
        "key": userkey_file_path,
        "ssh_username": config["ssh_username"],
        "image_name": config["new_image_name"],
        "source_image": config["image_id"],
        "cloud_client_path": cloud_client_path
    }

    mount_as = site.get("mount_as")
    if mount_as is not None:
        builder_config["mount_as"] = mount_as

    public_image = config.get("public_image")
    if public_image is not None:
        builder_config["public_image"] = public_image

    return builder_config


@app.task(bind=True)
def packer_build(self, params, sites, credentials):
    builders = []
    try:
        template_file, template_file_path = tempfile.mkstemp()
        script_file, script_file_path = tempfile.mkstemp()

        for cloud in params["cloud_params"]:
            site = sites[cloud]
            site_credentials = credentials[cloud]
            config = params["cloud_params"][cloud]

            if not site.get("image_generation"):
                raise ValueError("The cloud %s is not supported yet" % cloud)

            if site["type"] == "ec2":
                builder_config = ec2_builder_config(cloud, site, site_credentials, config)
            elif site["type"] == "openstack":
                builder_config = openstack_builder_config(cloud, site, site_credentials, config)
            elif site["type"] == "nimbus":
                builder_config = nimbus_builder_config(cloud, site, site_credentials, config)
            else:
                raise ValueError("The cloud %s is not supported yet" % cloud)

            builders.append(builder_config)

        template = {
            "builders": builders,
            "provisioners": []
        }

        with os.fdopen(script_file, 'w') as f:
            f.write(params.get("script"))
        template["provisioners"].append({"type": "shell", "script": script_file_path})

        with os.fdopen(template_file, 'w') as f:
            f.write(json.dumps(template))

        with open(template_file_path) as f:
            print f.read()

        cmd = "packer build -machine-readable %s" % template_file_path
        try:
            full_output = subprocess.check_output(cmd, shell=True)
            returncode = 0
        except subprocess.CalledProcessError as e:
            returncode = e.returncode
            full_output = e.output.rstrip()

    finally:
        os.remove(script_file_path)
        os.remove(template_file_path)

    artifacts = {}

    for line in full_output.splitlines():
        m = re.search(r',nimbus-(.*),artifact,0,id,(.*)', line)
        if m is not None:
            cloud = m.group(1)
            artifacts[cloud] = m.group(2)

        m = re.search(r',amazon-ebs-(.*),artifact,0,id,.*:(.*)', line)
        if m is not None:
            cloud = m.group(1)
            artifacts[cloud] = m.group(2)

        m = re.search(r',openstack-(.*),artifact,0,id,(.*)', line)
        if m is not None:
            cloud = m.group(1)
            artifacts[cloud] = m.group(2)

    return {
        "returncode": returncode,
        "artifacts": artifacts,
        "full_output": full_output
    }
