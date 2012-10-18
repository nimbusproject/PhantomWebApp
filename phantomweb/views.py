from django.core.context_processors import csrf
from django.conf.urls.defaults import patterns
from django.core.urlresolvers import reverse
from django.template import Context, loader
import simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from phantomweb.phantom_web_exceptions import PhantomWebException, PhantomRedirectException
from phantomweb.util import PhantomWebDecorator, get_user_object, LogEntryDecorator
from phantomweb.workload import terminate_iaas_instance, phantom_lc_load, phantom_sites_add, phantom_sites_delete, phantom_sites_load, phantom_lc_delete, phantom_lc_save, phantom_domain_load, phantom_domain_terminate, phantom_domain_resize, phantom_domain_start, phantom_domain_details, phantom_instance_terminate
from django.contrib import admin



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
def django_domain_html(request):
    try:
        # no need to talk to the workload app here
        response_dict = {}
        response_dict.update(csrf(request))
        t = loader.get_template('phantom_domain.html')
        c = Context(response_dict)
    except PhantomRedirectException, ex:
        return HttpResponseRedirect(ex.redir)
    return HttpResponse(t.render(c))


@LogEntryDecorator
@login_required
def django_domain_load(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_domain_load(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_domain_start(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_domain_start(request.POST, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_domain_resize(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_domain_resize(request.POST, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_domain_details(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_domain_details(request.POST, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h


@LogEntryDecorator
@login_required
def django_domain_terminate(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_domain_terminate(request.POST, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_instance_terminate(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_instance_terminate(request.POST, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h



#
#  launch configuration options
#
@LogEntryDecorator
@login_required
def django_lc_html(request):
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
def django_lc_delete(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_lc_delete(request.POST, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_lc_save(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_lc_save(request.POST, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h


#
#  manage cloud functions
#
@LogEntryDecorator
@login_required
def django_sites_html(request):
    response_dict = {}
    response_dict.update(csrf(request))
    t = loader.get_template('../templates/cloudedit.html')
    c = Context(response_dict)

    return HttpResponse(t.render(c))

@LogEntryDecorator
@login_required
def django_sites_load(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_sites_load(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_sites_delete(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_sites_delete(request.GET, user_obj)
        h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    finally:
        user_obj.close()
    return h

@LogEntryDecorator
@login_required
def django_sites_add(request):
    user_obj = get_user_object(request.user.username)
    try:
        response_dict = phantom_sites_add(request.REQUEST, user_obj)
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
