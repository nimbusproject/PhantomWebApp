from django.core.context_processors import csrf
from django.conf.urls.defaults import patterns
from django.core.urlresolvers import reverse
from django.template import Context, loader
import simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from phantomweb.phantom_web_exceptions import PhantomWebException, PhantomRedirectException
from phantomweb.util import PhantomWebDecorator, get_user_object, LogEntryDecorator
from phantomweb.workload import delete_domain, phantom_main_html, start_domain, list_domains, get_iaas_info, update_desired_size, terminate_iaas_instance, phantom_lc_load, phantom_cloud_edit_html, phantom_get_sites, phantom_get_user_site_info, phantom_delete_site, phantom_add_site
from django.contrib import admin

@LogEntryDecorator
@login_required
def django_get_initial_info(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = get_iaas_info(request.GET, user_obj)
        domain_dict = list_domains(request.GET, user_obj)
        response_dict.update(domain_dict)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h


@LogEntryDecorator
@login_required
def django_update_desired_size(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = update_desired_size(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h


@LogEntryDecorator
@login_required
def django_get_iaas_info(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = get_iaas_info(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_terminate_iaas_instance(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = terminate_iaas_instance(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_list_domain(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = list_domains(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_start_domain(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = start_domain(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_delete_domain(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = delete_domain(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_get_user_site_info(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_get_user_site_info(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_phantom(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_main_html(request.GET, user_obj)
        t = loader.get_template('../templates/phantom.html')
        c = Context(response_dict)
    except PhantomRedirectException, ex:
        return HttpResponseRedirect(ex.redir)
    finally:
        user_obj.close()
    return HttpResponse(t.render(c))

@LogEntryDecorator
@login_required
def django_lc(request):
    try:
        # no need to talk to the workload app here
        response_dict = {}
        response_dict.update(csrf(request))
        t = loader.get_template('../templates/launchconfig.html')
        c = Context(response_dict)
    except PhantomRedirectException, ex:
        return HttpResponseRedirect(ex.redir)
    return HttpResponse(t.render(c))


@LogEntryDecorator
@login_required
def django_lc_load(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_lc_load(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h


@LogEntryDecorator
@login_required
def django_cloud_edit(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_cloud_edit_html(request.GET, user_obj)
        response_dict.update(csrf(request))
        t = loader.get_template('../templates/cloudedit.html')
        c = Context(response_dict)
    except PhantomRedirectException, ex:
        return HttpResponseRedirect(ex.redir)
    finally:
        user_obj.close()
    return HttpResponse(t.render(c))


@LogEntryDecorator
@login_required
def django_get_sites(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_get_sites(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_delete_site(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_delete_site(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_add_site(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_add_site(request.REQUEST, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h



class MyModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(MyModelAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^my_view/$', self.admin_site.admin_view(self.my_view))
        )
        return my_urls + urls
