import base64
import json
import logging

from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseNotFound, HttpResponseServerError, HttpResponseRedirect
from django.views.decorators.http import require_http_methods

from phantomweb.util import get_user_object
from phantomweb.phantom_web_exceptions import PhantomWebException
from phantomweb.workload import phantom_get_sites, get_all_launch_configurations, \
    get_launch_configuration, get_launch_configuration_by_name, create_launch_configuration, \
    set_host_max_pair, get_all_domains, create_domain, get_domain_by_name, get_domain, \
    remove_domain, modify_domain, get_domain_instances, get_domain_instance, \
    terminate_domain_instance, get_sensors, remove_launch_configuration, \
    get_launch_configuration_object

log = logging.getLogger('phantomweb.api.dev')

DOC_URI = "http://www.nimbusproject.org/doc/phantom/latest/api.html"
API_VERSION = 'dev'


def basic_http_auth(f):
    def wrap(request, *args, **kwargs):
        if request.user:
            if request.user.is_authenticated():
                # Already logged in, just return the result of the view
                return f(request, *args, **kwargs)

        if request.META.get('HTTP_AUTHORIZATION', False):
            authtype, auth = request.META['HTTP_AUTHORIZATION'].split(' ')
            auth = base64.b64decode(auth)
            username, password = auth.split(':')

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return f(request, *args, **kwargs)
                else:
                    r = HttpResponse("Your account has been disabled", status=401, mimetype='application/javascript')
                    r['WWW-Authenticate'] = 'Basic realm="api"'
                    return r
            else:
                r = HttpResponse("Your username and password were incorrect", status=401,
                        mimetype='application/javascript')
                r['WWW-Authenticate'] = 'Basic realm="api"'
                return r
        else:
            r = HttpResponse("Auth Required", status=401, mimetype='application/javascript')
            r['WWW-Authenticate'] = 'Basic realm="api"'
            return r

    return wrap


def has_all_required_params(params, content):
    for param in params:
        if param not in content:
            return False

    return True


@basic_http_auth
@require_http_methods(["GET"])
def sites(request):
    user_obj = get_user_object(request.user.username)

    all_sites = phantom_get_sites(request.GET, user_obj)
    response_list = []
    for site in all_sites:
        site_name = str(site)
        site_dict = {
            "id": site_name,
            "credentials": "/api/%s/credentials/%s" % (API_VERSION, site_name),
            "uri": "/api/%s/sites/%s" % (API_VERSION, site_name)
        }
        response_list.append(site_dict)
    h = HttpResponse(json.dumps(response_list), mimetype='application/javascript')
    return h


@basic_http_auth
@require_http_methods(["GET"])
def site_resource(request, site):
    user_obj = get_user_object(request.user.username)
    all_sites = phantom_get_sites(request.GET, user_obj)
    if site in all_sites:
        response_dict = {
            "id": site,
            "credentials": "/api/%s/credentials/%s" % (API_VERSION, site),
            "uri": "/api/%s/sites/%s" % (API_VERSION, site)
        }
        h = HttpResponse(json.dumps(response_dict), mimetype='application/javascript')
    else:
        h = HttpResponseNotFound('Site %s not found' % site, mimetype='application/javascript')
    return h


@basic_http_auth
@require_http_methods(["GET", "POST"])
def credentials(request):
    user_obj = get_user_object(request.user.username)

    if request.method == "GET":
        all_clouds = user_obj.get_clouds()
        response_list = []
        for cloud in all_clouds.values():
            credentials_name = cloud.cloudname
            credentials_dict = {
                "id": credentials_name,
                "access_key": cloud.iaas_key,
                "secret_key": cloud.iaas_secret,
                "key_name": cloud.keyname,
                "uri": "/api/%s/credentials/%s" % (API_VERSION, credentials_name)
            }
            response_list.append(credentials_dict)
        h = HttpResponse(json.dumps(response_list), mimetype='application/javascript')
    elif request.method == "POST":
        try:
            content = json.loads(request.body)
        except:
            msg = "Bad request. No JSON. See API docs: %s" % DOC_URI
            return HttpResponseBadRequest(msg)

        required_params = ["id", "access_key", "secret_key", "key_name"]
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest()

        site = content["id"]
        access_key = content["access_key"]
        secret_key = content["secret_key"]
        key_name = content["key_name"]

        # Check that the site exists
        all_sites = phantom_get_sites(request.POST, user_obj)
        if site not in all_sites:
            return HttpResponseBadRequest()

        response_dict = {
            "id": site,
            "access_key": access_key,
            "secret_key": secret_key,
            "key_name": key_name,
            "uri": "/api/%s/credentials/%s" % (API_VERSION, site)
        }

        # Add credentials to DTRS
        try:
            user_obj.add_site(site, access_key, secret_key, key_name)
        except:
            log.exception("Failed to add credentials for site %s" % site)
            return HttpResponseServerError()

        h = HttpResponse(json.dumps(response_dict), status=201, mimetype='application/javascript')

    return h


@basic_http_auth
@require_http_methods(["GET", "PUT", "DELETE"])
def credentials_resource(request, site):
    user_obj = get_user_object(request.user.username)

    if request.method == "GET":
        all_clouds = user_obj.get_clouds()
        cloud = all_clouds.get(site)

        if cloud is not None:
            response_dict = {
                "id": cloud.cloudname,
                "access_key": cloud.iaas_key,
                "secret_key": cloud.iaas_secret,
                "key_name": cloud.keyname,
                "uri": "/api/%s/credentials/%s" % (API_VERSION, cloud.cloudname)
            }
            h = HttpResponse(json.dumps(response_dict), mimetype='application/javascript')
        else:
            h = HttpResponseNotFound('Credentials for site %s not found' % site, mimetype='application/javascript')
    elif request.method == "PUT":
        try:
            content = json.loads(request.body)
        except:
            return HttpResponseBadRequest()

        required_params = ["id", "access_key", "secret_key", "key_name"]
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest()

        if site != content["id"]:
            return HttpResponseBadRequest()

        access_key = content["access_key"]
        secret_key = content["secret_key"]
        key_name = content["key_name"]

        # Check that the site exists
        all_sites = phantom_get_sites(request.REQUEST, user_obj)
        if site not in all_sites:
            return HttpResponseBadRequest()

        # Check that credentials exist
        if site not in user_obj.get_clouds():
            return HttpResponseBadRequest()

        response_dict = {
            "id": site,
            "access_key": access_key,
            "secret_key": secret_key,
            "key_name": key_name,
            "uri": "/api/%s/credentials/%s" % (API_VERSION, site)
        }

        # Add credentials to DTRS
        try:
            user_obj.add_site(site, access_key, secret_key, key_name)
        except:
            log.exception("Failed to add credentials for site %s" % site)
            return HttpResponseServerError()

        h = HttpResponse(json.dumps(response_dict), status=201, mimetype='application/javascript')
    elif request.method == "DELETE":
        # Check that credentials exist
        if site not in user_obj.get_clouds():
            return HttpResponseBadRequest()

        # Remove credentials from DTRS
        try:
            user_obj.delete_site(site)
        except:
            log.exception("Failed to remove credentials for site %s" % site)
            return HttpResponseServerError()

        h = HttpResponse(status=204)

    return h


@basic_http_auth
@require_http_methods(["GET", "POST"])
def launchconfigurations(request):
    if request.method == "GET":
        all_launch_configurations = get_all_launch_configurations(request.user.username)
        response_list = []
        for lc_id in all_launch_configurations:
            lc_dict = get_launch_configuration(lc_id)
            lc_dict['uri'] = "/api/%s/launchconfigurations/%s" % (API_VERSION, lc_dict.get('id'))
            response_list.append(lc_dict)

        h = HttpResponse(json.dumps(response_list), mimetype='application/javascript')

    elif request.method == "POST":
        try:
            content = json.loads(request.body)
        except:
            return HttpResponseBadRequest()

        required_params = ["name", "cloud_params"]
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest()
        name = content['name']
        cloud_params = content['cloud_params']
        username = request.user.username
        user_obj = get_user_object(username)

        lc = get_launch_configuration_by_name(username, name)
        if lc is not None:
            # LC already exists, redirect to existing one
            return HttpResponseRedirect("/api/%s/launchconfigurations/%s" % (API_VERSION, lc.id))

        lc = create_launch_configuration(username, name)
        lc.save()
        configured_clouds = user_obj.get_clouds()

        # TODO: validate these values

        for cloud_name, cloud in cloud_params.iteritems():

            if cloud_name not in configured_clouds.keys():
                msg = "%s is not configured. Check your profile" % cloud_name
                return HttpResponseBadRequest(msg)

            set_host_max_pair(cloud_name=cloud_name, max_vms=cloud['max_vms'],
                launch_config=lc, rank=int(cloud['rank']), common_image=cloud["common"])

        response_dict = {
            "id": lc.id,
            "name": name,
            "owner": username,
            "cloud_params": cloud_params,
            "uri": "/api/%s/launchconfigurations/%s" % (API_VERSION, lc.id),
        }

        h = HttpResponse(json.dumps(response_dict), status=201, mimetype='application/javascript')
    return h


@basic_http_auth
@require_http_methods(["GET", "PUT", "DELETE"])
def launchconfiguration_resource(request, id):
    if request.method == "GET":
        lc_dict = get_launch_configuration(id)
        if lc_dict is not None and lc_dict.get('owner') == request.user.username:

            lc_dict['uri'] = "/api/%s/launchconfigurations/%s" % (API_VERSION, lc_dict.get('id'))

            h = HttpResponse(json.dumps(lc_dict), mimetype='application/javascript')
        else:
            h = HttpResponseNotFound('Launch configuration %s not found' % id, mimetype='application/javascript')
        return h
    elif request.method == "PUT":

        lc = get_launch_configuration_object(id)
        if lc is None:
            msg = "Launch configuration %s not found" % id
            return HttpResponseNotFound(msg, mimetype='application/javascript')

        try:
            content = json.loads(request.body)
        except:
            return HttpResponseBadRequest()

        required_params = ["name", "cloud_params"]
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest()

        name = content['name']
        cloud_params = content['cloud_params']
        username = request.user.username
        user_obj = get_user_object(username)

        required_cloud_params = ['image_id', 'instance_type', 'max_vms', 'common', 'rank', 'user_data']
        configured_clouds = user_obj.get_clouds()

        # TODO: validate these values

        for cloud_name, cloud in cloud_params.iteritems():

            if cloud_name not in configured_clouds.keys():
                msg = "%s is not configured. Check your profile" % cloud_name
                return HttpResponseBadRequest(msg)

            if not has_all_required_params(required_cloud_params, cloud):
                msg = "%s does not have all of the required parameters" % cloud_name
                return HttpResponseBadRequest(msg)

            set_host_max_pair(cloud_name=cloud_name, max_vms=cloud['max_vms'],
                launch_config=lc, rank=int(cloud['rank']), common_image=cloud["common"])

        response_dict = {
            "id": lc.id,
            "name": name,
            "owner": username,
            "cloud_params": cloud_params,
            "uri": "/api/%s/launchconfigurations/%s" % (API_VERSION, lc.id),
        }

        h = HttpResponse(json.dumps(response_dict), status=200, mimetype='application/javascript')
        return h

    elif request.method == "DELETE":
        lc = get_launch_configuration(id)
        if lc is not None and lc.get('owner') == request.user.username:
            remove_launch_configuration(request.user.username, id)

            h = HttpResponse(status=204)
        else:
            h = HttpResponseNotFound('Launch configuration %s not found' % id, mimetype='application/javascript')
        return h


@basic_http_auth
@require_http_methods(["GET", "POST"])
def domains(request):
    if request.method == "GET":
        username = request.user.username
        domains = get_all_domains(username)
        response = domains
        h = HttpResponse(json.dumps(response), status=200, mimetype='application/javascript')
        return h
    elif request.method == "POST":

        try:
            content = json.loads(request.body)
        except:
            return HttpResponseBadRequest()
        username = request.user.username
        name = content.get('name')
        if name is None:
            return HttpResponseBadRequest("You must provide a name for your domain")

        domain = get_domain_by_name(username, name)
        if domain is not None:
            # Domain already exists, redirect to existing one
            return HttpResponseRedirect("/api/%s/domains/%s" % (API_VERSION, domain['id']))

        try:
            response = create_domain(username, name, content)
        except PhantomWebException as p:
            return HttpResponseBadRequest(p.message)

        response['owner'] = username
        response['uri'] = "/api/%s/domains/%s" % (API_VERSION, response['id'])

        h = HttpResponse(json.dumps(response), status=201, mimetype='application/javascript')
        return h


@basic_http_auth
@require_http_methods(["GET", "PUT", "DELETE"])
def domain_resource(request, id):
    if request.method == "GET":
        username = request.user.username

        response = get_domain(username, id)
        if response is None:
            return HttpResponseNotFound('Domain %s not found' % id, mimetype='application/javascript')

        response['owner'] = username
        response['uri'] = "/api/%s/domains/%s" % (API_VERSION, id)
        return HttpResponse(json.dumps(response), mimetype='application/javascript')
    elif request.method == "PUT":
        username = request.user.username

        response = get_domain(username, id)
        if response is None:
            return HttpResponseNotFound('Domain %s not found' % id, mimetype='application/javascript')

        try:
            content = json.loads(request.body)
        except:
            return HttpResponseBadRequest()

        try:
            response = modify_domain(username, id, content)
        except PhantomWebException as p:
            return HttpResponseBadRequest(p.message)

        response['owner'] = username
        response['uri'] = "/api/%s/domains/%s" % (API_VERSION, response['id'])

        h = HttpResponse(json.dumps(response), status=200, mimetype='application/javascript')
        return h

    elif request.method == "DELETE":
        username = request.user.username
        response = get_domain(username, id)
        if response is None:
            return HttpResponseNotFound('Domain %s not found' % id, mimetype='application/javascript')
        response = remove_domain(username, id)

        h = HttpResponse(status=204)
        return h


@basic_http_auth
@require_http_methods(["GET"])
def instances(request, domain_id):
    if request.method == "GET":
        username = request.user.username
        response = get_domain_instances(username, domain_id)
        if response is None:
            return HttpResponseNotFound('domain %s not found' % domain_id, mimetype='application/javascript')

        for instance in response:
            instance['owner'] = username
            instance['cloud'] = "/api/%s/sites/%s" % (API_VERSION, instance.get('cloud'))
            instance['uri'] = "/api/%s/domains/%s/instances/%s" % (
                API_VERSION, domain_id, instance.get('id'))

        return HttpResponse(json.dumps(response), mimetype='application/javascript')


@basic_http_auth
@require_http_methods(["GET", "DELETE"])
def instance_resource(request, domain_id, instance_id):
    if request.method == "GET":
        username = request.user.username
        response = get_domain_instances(username, domain_id)
        if response is None:
            return HttpResponseNotFound('domain %s not found' % domain_id, mimetype='application/javascript')

        wanted_instance = None
        for instance in response:
            if instance.get('id') == instance_id:
                wanted_instance = instance
                break

        if wanted_instance is None:
            return HttpResponseNotFound('instance %s not found' % instance_id, mimetype='application/javascript')

        wanted_instance['owner'] = username
        wanted_instance['cloud'] = "/api/%s/sites/%s" % (API_VERSION, wanted_instance.get('cloud'))
        wanted_instance['uri'] = "/api/%s/domains/%s/instances/%s" % (
            API_VERSION, domain_id, wanted_instance.get('id'))

        return HttpResponse(json.dumps(wanted_instance), mimetype='application/javascript')

    elif request.method == "DELETE":
        username = request.user.username
        instance = get_domain_instance(username, domain_id, instance_id)
        if instance is None:
            return HttpResponseNotFound('instance %s not found' % domain_id, mimetype='application/javascript')

        try:
            terminate_domain_instance(username, domain_id, instance_id)
        except PhantomWebException as p:
            return HttpResponseServerError("Couldn't remove instance %s" % instance_id)

        h = HttpResponse(status=204)
        return h


@basic_http_auth
@require_http_methods(["GET"])
def sensors(request):
    if request.method == "GET":
        username = request.user.username
        sensors_list = get_sensors(username)
        sensors = []

        for sensor in sensors_list:
            s = {
                'id': sensor,
                'uri': '/api/%s/sensors/%s' % (API_VERSION, sensor)
            }
            sensors.append(s)

        return HttpResponse(json.dumps(sensors), mimetype='application/javascript')


@basic_http_auth
@require_http_methods(["GET"])
def sensor_resource(request, sensor_id):
    if request.method == "GET":
        username = request.user.username
        sensors_list = get_sensors(username)

        if sensor_id not in sensors_list:
            return HttpResponseNotFound("Sensor '%s' does not exist" % sensor_id)

        sensor = {
            'id': sensor_id,
            'uri': '/api/%s/sensors/%s' % (API_VERSION, sensor_id)
        }

        return HttpResponse(json.dumps(sensor), mimetype='application/javascript')
