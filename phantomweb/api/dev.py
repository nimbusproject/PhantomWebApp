import base64
import json
import logging

from functools import wraps
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseNotFound, HttpResponseServerError, HttpResponseRedirect, \
    HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from phantomweb.util import get_user_object, str_to_bool
from phantomweb.phantom_web_exceptions import PhantomWebException
from phantomweb.workload import phantom_get_sites, get_all_launch_configurations, \
    get_launch_configuration, get_launch_configuration_by_name, create_launch_configuration, \
    update_launch_configuration, get_all_domains, create_domain, get_domain_by_name, get_domain, \
    remove_domain, modify_domain, get_domain_instances, get_domain_instance, \
    terminate_domain_instance, get_sensors, remove_launch_configuration, \
    get_launch_configuration_object, get_all_keys

log = logging.getLogger('phantomweb.api.dev')

DOC_URI = "http://www.nimbusproject.org/doc/phantom/latest/api.html"
API_VERSION = 'dev'


def optional_pretty_print(f):
    def wrap(request, *args, **kwargs):
        response = f(request, *args, **kwargs)
        pretty = str_to_bool(request.GET.get('pretty', 'false'))
        if response.status_code == 200 and pretty:
            try:
                content_json = json.loads(response.content)
                pretty_json = json.dumps(content_json, indent=4, separators=(',', ': '))
                response.content = pretty_json
            except:
                pass
        return response
    return wrap


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


# TODO: this should really be a part of django-tokenapi
def token_or_logged_in_required(view_func):
    """Decorator which ensures the user has provided a correct user and token pair."""

    @csrf_exempt
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user:
            if request.user.is_authenticated():
                # Already logged in, just return the result of the view
                return view_func(request, *args, **kwargs)

        user = None
        token = None
        basic_auth = request.META.get('HTTP_AUTHORIZATION')

        if basic_auth:
            auth_method, auth_string = basic_auth.split(' ', 1)

            if auth_method.lower() == 'basic':
                auth_string = auth_string.strip().decode('base64')
                user, token = auth_string.split(':', 1)

        if not (user and token):
            user = request.REQUEST.get('user')
            token = request.REQUEST.get('token')

        if user and token:
            user = authenticate(pk=user, token=token)
            if user:
                login(request, user)
                return view_func(request, *args, **kwargs)

        return HttpResponseForbidden("Authorization Required")
    return _wrapped_view


def has_all_required_params(params, content):
    for param in params:
        if param not in content:
            return False

    return True


@token_or_logged_in_required
@optional_pretty_print
@require_http_methods(["GET"])
def sites(request):
    user_obj = get_user_object(request.user.username)
    details = str_to_bool(request.GET.get('details', 'false'))
    all_sites = phantom_get_sites(request.GET, user_obj, details=details)
    response_list = []
    for site_name, site_dict in all_sites.iteritems():
        site_dict["credentials"] = "/api/%s/credentials/sites/%s" % (API_VERSION, site_name)
        site_dict["uri"] = "/api/%s/sites/%s" % (API_VERSION, site_name)
        if details:
            if site_dict.get('user_images') is None:
                site_dict['user_images'] = []
            if site_dict.get('public_images') is None:
                site_dict['public_images'] = []
        response_list.append(site_dict)
    h = HttpResponse(json.dumps(response_list), mimetype='application/javascript')
    return h


@token_or_logged_in_required
@optional_pretty_print
@require_http_methods(["GET"])
def site_resource(request, site):
    user_obj = get_user_object(request.user.username)
    details = str_to_bool(request.GET.get('details', 'false'))
    all_sites = phantom_get_sites(request.GET, user_obj, details=details)
    if site in all_sites:
        response_dict = {
            "id": site,
            "credentials": "/api/%s/credentials/sites/%s" % (API_VERSION, site),
            "instance_types": all_sites[site].get('instance_types', []),
            "uri": "/api/%s/sites/%s" % (API_VERSION, site)
        }
        if details:
            if response_dict.get('user_images') is None:
                response_dict['user_images'] = []
            if response_dict.get('public_images') is None:
                response_dict['public_images'] = []
        h = HttpResponse(json.dumps(response_dict), mimetype='application/javascript')
    else:
        h = HttpResponseNotFound('Site %s not found' % site, mimetype='application/javascript')
    return h


@token_or_logged_in_required
@optional_pretty_print
@require_http_methods(["GET", "POST"])
def chef_credentials(request):
    user_obj = get_user_object(request.user.username)

    if request.method == "GET":
        all_credentials = user_obj.get_chef_credentials()

        response_list = []
        for credential_name, credential in all_credentials.iteritems():
            credentials_dict = {
                "id": credential_name,
                "server_url": credential['url'],
                "client_name": credential.get('client_name', 'admin'),
                "validation_client_name": credential.get('validation_client_name', 'chef-validator'),
                "client_key": credential['client_key'],
                "validator_key": credential['validator_key'],
                "uri": "/api/%s/credentials/chef/%s" % (API_VERSION, credential_name)
            }
            response_list.append(credentials_dict)
        h = HttpResponse(json.dumps(response_list), mimetype='application/javascript')
    elif request.method == "POST":
        try:
            content = json.loads(request.body)
        except:
            msg = "Bad request (%s). No JSON. See API docs: %s" % (request.body, DOC_URI)
            return HttpResponseBadRequest(msg)

        required_params = ["id", "server_url", "client_name", "client_key", "validator_key"]
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest("Bad request. Do not have all required parameters (%s)" % required_params)

        name = content["id"]
        url = content["server_url"]
        client_name = content["client_name"]
        validation_client_name = content.get("validation_client_name", "chef-validator")
        client_key = content["client_key"]
        validator_key = content["validator_key"]

        # Check that the site exists
        all_credentials = user_obj.get_chef_credentials()
        if name in all_credentials:
            return HttpResponseRedirect("/api/%s/credentials/chef/%s" % (API_VERSION, name))

        response_dict = {
            "id": name,
            "server_url": url,
            "validation_client_name": validation_client_name,
            "client_name": client_name,
            "client_key": client_key,
            "validator_key": validator_key,
            "uri": "/api/%s/credentials/chef/%s" % (API_VERSION, name)
        }

        # Add credentials to DTRS
        try:
            user_obj.add_chef_credentials(name, url, client_name, client_key, validator_key,
                    validation_client_name=validation_client_name)
        except:
            msg = "Failed to add credentials for %s" % name
            raise
            log.exception(msg)
            return HttpResponseServerError(msg)

        h = HttpResponse(json.dumps(response_dict), status=201, mimetype='application/javascript')

    return h


@token_or_logged_in_required
@optional_pretty_print
@require_http_methods(["GET", "PUT", "DELETE"])
def chef_credentials_resource(request, site):
    user_obj = get_user_object(request.user.username)

    if request.method == "GET":
        all_credentials = user_obj.get_chef_credentials()
        credential = all_credentials.get(site)

        if credential is not None:
            response_dict = {
                "id": site,
                "server_url": credential['url'],
                "client_name": credential['client_name'],
                "client_key": credential['client_key'],
                "validator_key": credential['validator_key'],
                "validation_client_name": credential.get('validation_client_name', 'chef-validator'),
                "uri": "/api/%s/credentials/chef/%s" % (API_VERSION, site)
            }
            h = HttpResponse(json.dumps(response_dict), mimetype='application/javascript')
        else:
            h = HttpResponseNotFound('Credentials for site %s not found' % site, mimetype='application/javascript')
        return h
    elif request.method == "PUT":
        try:
            content = json.loads(request.body)
        except:
            msg = "Bad request (%s). No JSON. See API docs: %s" % (request.body, DOC_URI)
            return HttpResponseBadRequest(msg)

        required_params = ["server_url", "client_key", "client_name", "validator_key"]
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest("Bad request. Do not have all required parameters (%s)" % required_params)

        name = site
        url = content["server_url"]
        client_name = content["client_name"]
        validation_client_name = content.get("validation_client_name", 'chef-validator')
        client_key = content["client_key"]
        validator_key = content["validator_key"]

        # Check that the credentials exist
        all_credentials = user_obj.get_chef_credentials()
        if site not in all_credentials:
            return HttpResponseBadRequest()

        response_dict = {
            "id": name,
            "server_url": url,
            "client_name": client_name,
            "client_key": client_key,
            "validator_key": validator_key,
            "validation_client_name": validation_client_name,
            "uri": "/api/%s/credentials/chef/%s" % (API_VERSION, name)
        }

        # Add credentials to DTRS
        try:
            user_obj.add_chef_credentials(name, url, client_name, client_key, validator_key,
                    validation_client_name=validation_client_name)
        except:
            log.exception("Failed to add credentials for site %s" % site)
            return HttpResponseServerError()

        h = HttpResponse(json.dumps(response_dict), status=201, mimetype='application/javascript')

        return h

    elif request.method == "DELETE":
        # Check that the credentials exist
        all_credentials = user_obj.get_chef_credentials()
        if site not in all_credentials:
            return HttpResponseBadRequest()

        # Remove credentials from DTRS
        try:
            user_obj.delete_chef_credentials(site)
        except:
            msg = "Failed to remove credentials for site %s" % site
            log.exception(msg)
            return HttpResponseServerError(msg)

        h = HttpResponse(status=204)

        return h


@token_or_logged_in_required
@optional_pretty_print
@require_http_methods(["GET", "POST"])
def credentials(request):
    user_obj = get_user_object(request.user.username)

    if request.method == "GET":
        all_clouds = user_obj.get_clouds()
        details = str_to_bool(request.GET.get('details', 'false'))
        if details is True:
            keys = get_all_keys(all_clouds)

        response_list = []
        for cloud in all_clouds.values():
            credentials_name = cloud.cloudname
            credentials_dict = {
                "id": credentials_name,
                "access_key": cloud.iaas_key,
                "secret_key": cloud.iaas_secret,
                "key_name": cloud.keyname,
                "uri": "/api/%s/credentials/sites/%s" % (API_VERSION, credentials_name)
            }
            if details is True:
                credentials_dict["available_keys"] = keys[cloud.cloudname]
            response_list.append(credentials_dict)
        h = HttpResponse(json.dumps(response_list), mimetype='application/javascript')
    elif request.method == "POST":
        try:
            content = json.loads(request.body)
        except:
            msg = "Bad request (%s). No JSON. See API docs: %s" % (request.body, DOC_URI)
            return HttpResponseBadRequest(msg)

        required_params = ["id", "access_key", "secret_key", "key_name"]
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest("Bad request. Do not have all required parameters (%s)" % required_params)

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
            "uri": "/api/%s/credentials/sites/%s" % (API_VERSION, site)
        }

        # Add credentials to DTRS
        try:
            user_obj.add_site(site, access_key, secret_key, key_name)
        except:
            log.exception("Failed to add credentials for site %s" % site)
            return HttpResponseServerError()

        h = HttpResponse(json.dumps(response_dict), status=201, mimetype='application/javascript')

    return h


@token_or_logged_in_required
@optional_pretty_print
@require_http_methods(["GET", "PUT", "DELETE"])
def credentials_resource(request, site):
    user_obj = get_user_object(request.user.username)

    if request.method == "GET":
        all_clouds = user_obj.get_clouds()
        cloud = all_clouds.get(site)
        details = str_to_bool(request.GET.get('details', 'false'))
        if details is True:
            keys = get_all_keys([cloud])

        if cloud is not None:
            response_dict = {
                "id": cloud.cloudname,
                "access_key": cloud.iaas_key,
                "secret_key": cloud.iaas_secret,
                "key_name": cloud.keyname,
                "uri": "/api/%s/credentials/sites/%s" % (API_VERSION, cloud.cloudname)
            }
            if details is True:
                response_dict["available_keys"] = keys[cloud.cloudname]
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
            "uri": "/api/%s/credentials/sites/%s" % (API_VERSION, site)
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
        clouds = user_obj.get_clouds()
        if site not in clouds:
            return HttpResponseBadRequest("Site %s not available. Choose from %s" % (site, clouds.keys()))

        # Remove credentials from DTRS
        try:
            user_obj.delete_site(site)
        except:
            msg = "Failed to remove credentials for site %s" % site
            log.exception(msg)
            return HttpResponseServerError(msg)

        h = HttpResponse(status=204)

    return h


@token_or_logged_in_required
@optional_pretty_print
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
            return HttpResponseBadRequest("Couldn't load json from body")

        required_params = ['name', 'cloud_params', 'contextualization_method']
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest("Request must have %s params" % ", ".join(required_params))
        name = content['name']
        cloud_params = content['cloud_params']
        username = request.user.username

        required_cloud_params = ['image_id', 'instance_type', 'max_vms', 'common', 'rank']
        for cloud_name, cloud_p in cloud_params.iteritems():
            if not has_all_required_params(required_cloud_params, cloud_p):
                missing = list(set(required_params) - set(cloud_p))
                return HttpResponseBadRequest("Missing parameters. %s needs: %s." % (
                    cloud_name, ", ".join(missing)))

        lc = get_launch_configuration_by_name(username, name)
        if lc is not None:
            # LC already exists, redirect to existing one
            return HttpResponseRedirect("/api/%s/launchconfigurations/%s" % (API_VERSION, lc.id))

        contextualization_method = content.get('contextualization_method')
        context_params = {
            'contextualization_method': contextualization_method,
            'user_data': content.get('user_data'),
            'chef_runlist': content.get('chef_runlist'),
            'chef_attributes': content.get('chef_attributes')
        }

        lc = create_launch_configuration(username, name, cloud_params, context_params)

        response_dict = {
            "id": lc.id,
            "name": name,
            "owner": username,
            'contextualization_method': contextualization_method,
            "cloud_params": cloud_params,
            "uri": "/api/%s/launchconfigurations/%s" % (API_VERSION, lc.id),
        }

        if contextualization_method == "user_data":
            response_dict['user_data'] = content.get('user_data')
        elif contextualization_method == "chef":
            response_dict['chef_runlist'] = content.get('chef_runlist')
            response_dict['chef_attributes'] = content.get('chef_attributes')

        h = HttpResponse(json.dumps(response_dict), status=201, mimetype='application/javascript')
    return h


@token_or_logged_in_required
@optional_pretty_print
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

        required_params = ['name', 'cloud_params', 'contextualization_method']
        if not has_all_required_params(required_params, content):
            return HttpResponseBadRequest()

        cloud_params = content['cloud_params']

        required_cloud_params = ['image_id', 'instance_type', 'max_vms', 'common', 'rank']
        for cloud_name, cloud_p in cloud_params.iteritems():
            if not has_all_required_params(required_cloud_params, cloud_p):
                missing = list(set(required_params) - set(cloud_p))
                return HttpResponseBadRequest("Missing parameters. %s needs: %s." % (
                    cloud_name, ", ".join(missing)))

        contextualization_method = content.get('contextualization_method')
        context_params = {
            'contextualization_method': contextualization_method,
            'user_data': content.get('user_data'),
            'chef_runlist': content.get('chef_runlist'),
            'chef_attributes': content.get('chef_attributes')
        }

        response_dict = update_launch_configuration(lc.id, cloud_params, context_params)
        response_dict['uri'] = "/api/%s/launchconfigurations/%s" % (API_VERSION, lc.id)
        response_dict['contextualization_method'] = contextualization_method

        if contextualization_method == "user_data":
            response_dict['user_data'] = content.get('user_data')
        elif contextualization_method == "chef":
            response_dict['chef_runlist'] = content.get('chef_runlist')
            response_dict['chef_attributes'] = content.get('chef_attributes')

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


@token_or_logged_in_required
@optional_pretty_print
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


@token_or_logged_in_required
@optional_pretty_print
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


@token_or_logged_in_required
@optional_pretty_print
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


@token_or_logged_in_required
@optional_pretty_print
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
        adjust_policy = str_to_bool(request.GET.get('adjust_policy', 'false'))
        instance = get_domain_instance(username, domain_id, instance_id)
        if instance is None:
            return HttpResponseNotFound('instance %s not found' % domain_id, mimetype='application/javascript')

        try:
            terminate_domain_instance(username, domain_id, instance_id)
        except PhantomWebException:
            return HttpResponseServerError("Couldn't remove instance %s" % instance_id)

        if adjust_policy:
            domain = get_domain(username, domain_id)
            adjusted_domain = None
            if 'vm_count' in domain:
                if int(domain['vm_count']) >= 1:
                    domain['vm_count'] = int(domain['vm_count']) - 1
                    adjusted_domain = domain
            elif 'sensor_minimum_vms' in domain and 'sensor_maximum_vms' in domain:
                if int(domain['sensor_minimum_vms']) >= 1:
                    domain['sensor_minimum_vms'] = int(domain['sensor_minimum_vms']) - 1
                domain['sensor_maximum_vms'] = domain['sensor_minimum_vms']
                adjusted_domain = domain

            if adjusted_domain:
                response = modify_domain(username, domain_id, adjusted_domain)

        h = HttpResponse(status=204)
        return h


@token_or_logged_in_required
@optional_pretty_print
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


@token_or_logged_in_required
@optional_pretty_print
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
