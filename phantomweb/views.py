from django.core.context_processors import csrf
from django.conf.urls.defaults import patterns
from django.template import Context, loader
import simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from phantomweb.phantom_web_exceptions import PhantomRedirectException
from phantomweb.util import get_user_object, LogEntryDecorator
from phantomweb.workload import terminate_iaas_instance, phantom_lc_load, phantom_sites_add,\
    phantom_sites_delete, phantom_sites_load, phantom_lc_delete, phantom_lc_save,\
    phantom_domain_load, phantom_domain_terminate, phantom_domain_resize,\
    phantom_domain_start, phantom_domain_details, phantom_instance_terminate, phantom_sensors_load
from django.contrib import admin


@LogEntryDecorator
@login_required
def django_terminate_iaas_instance(request):
    user_obj = get_user_object(request.user.username)
    response_dict = terminate_iaas_instance(request.GET, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_domain_html(request):
    try:
        # no need to talk to the workload app here
        response_dict = {}
        response_dict.update(csrf(request))
        response_dict['user'] = request.user
        t = loader.get_template('phantom_domain.html')
        c = Context(response_dict)
    except PhantomRedirectException, ex:
        return HttpResponseRedirect(ex.redir)
    return HttpResponse(t.render(c))


@LogEntryDecorator
@login_required
def django_sensors_load(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_sensors_load(request.GET, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_domain_load(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_domain_load(request.GET, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_domain_start(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_domain_start(request.POST, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_domain_resize(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_domain_resize(request.POST, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_domain_details(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_domain_details(request.POST, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_domain_terminate(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_domain_terminate(request.POST, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_instance_terminate(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_instance_terminate(request.POST, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_phantom_html(request):
    try:
        # no need to talk to the workload app here
        response_dict = {}
        response_dict.update(csrf(request))
        response_dict['user'] = request.user
        t = loader.get_template('../templates/phantom.html')
        c = Context(response_dict)
    except PhantomRedirectException, ex:
        return HttpResponseRedirect(ex.redir)
    return HttpResponse(t.render(c))


@LogEntryDecorator
@login_required
def django_lc_html(request):
    """
    launch configuration options
    """
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
    response_dict = phantom_lc_load(request.GET, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_lc_delete(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_lc_delete(request.POST, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_lc_save(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_lc_save(request.POST, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


#
#  manage cloud functions
#

@LogEntryDecorator
@login_required
def django_profile_html(request):
    response_dict = {}
    response_dict.update(csrf(request))
    response_dict['user'] = request.user
    t = loader.get_template('../templates/profile.html')
    c = Context(response_dict)

    return HttpResponse(t.render(c))


@LogEntryDecorator
@login_required
def django_publiclc_html(request):
    response_dict = {}
    response_dict.update(csrf(request))
    response_dict['user'] = request.user
    t = loader.get_template('../templates/publiclaunchconfigurations.html')
    c = Context(response_dict)

    return HttpResponse(t.render(c))


@LogEntryDecorator
@login_required
def django_sites_load(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_sites_load(request.GET, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_sites_delete(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_sites_delete(request.GET, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_sites_add(request):
    user_obj = get_user_object(request.user.username)
    response_dict = phantom_sites_add(request.REQUEST, user_obj)
    h = HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
    return h


@LogEntryDecorator
@login_required
def django_change_password(request):

    if request.is_ajax():

        try:
            user = User.objects.get(username=request.user.username)
        except User.DoesNotExist:
            return HttpResponse("USER_NOT_FOUND", status=500)

        old_password = request.POST.get('old_password')

        if not user.check_password(old_password):
            return HttpResponse("BAD_OLD_PASSWORD", status=500)

        new_password = request.POST.get('new_password')
        new_password_confirmation = request.POST.get('new_password_confirmation')

        if new_password != new_password_confirmation:
            return HttpResponse("PASSWORDS_DO_NOT_MATCH", status=500)

        if not new_password:
            return HttpResponse("NEW_PASSWORD_IS_BLANK", status=500)

        if not new_password_confirmation:
            return HttpResponse("NEW_PASSWORD_CONFIRMATION_IS_BLANK", status=500)

        user.set_password(new_password)
        user.save()
        return HttpResponse("{}", status=200)
    else:
        return HttpResponse(status=400)


class MyModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(MyModelAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^my_view/$', self.admin_site.admin_view(self.my_view))
        )
        return my_urls + urls
