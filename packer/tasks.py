import json
import os
import re
import subprocess
import tempfile

from celery import Celery

celery = Celery('tasks', backend='amqp', broker='amqp://guest@localhost//')


@celery.task
def packer_build(params, credentials):
    if "ec2" not in params["cloud_params"]:
        raise ValueError("You must provide an EC2 cloud in parameters")

    template_file, template_file_path = tempfile.mkstemp()
    script_file, script_file_path = tempfile.mkstemp()

    template = {
        "builders": [
            {
                "type": "amazon-ebs",
                "region": "us-east-1",
                "source_ami": params["cloud_params"]["ec2"]["image_id"],
                "instance_type": params["cloud_params"]["ec2"]["instance_type"],
                "ssh_username": params["cloud_params"]["ec2"]["ssh_username"],
                "ami_name": params["cloud_params"]["ec2"]["new_image_name"],
                "access_key": credentials["ec2"]["access_key"],
                "secret_key": credentials["ec2"]["secret_key"]
            }
        ],
        "provisioners": [],
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

    os.remove(script_file_path)
    os.remove(template_file_path)

    # Look for a line such as "1377624261,amazon-ebs,artifact,0,string,AMIs were created:\n\nus-east-1: ami-ef034e86"
    ami_name = ""
    for line in full_output.splitlines():
        m = re.search(r',amazon-ebs,artifact,0,id,.*:(.*)', line)
        if m is not None:
            ami_name = m.group(1)
            break

    return {
        "returncode": returncode,
        "ami_name": ami_name,
        "full_output": full_output
    }
