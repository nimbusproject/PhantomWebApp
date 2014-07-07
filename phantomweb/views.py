from django.core.mail import send_mail
from django.core.context_processors import csrf
from django.conf.urls import patterns, url, include
from django.template import Context, loader
import json
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from phantomweb.phantom_web_exceptions import PhantomRedirectException
from phantomweb.util import get_user_object, LogEntryDecorator
from phantomweb.models import PhantomUser
from django.contrib import admin

ACTIVATE_ON_REGISTER = False
ACTIVATION_EMAIL = ["nimbus@mcs.anl.gov", ]


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
        response_dict['user'] = request.user
        t = loader.get_template('../templates/launchconfig.html')
        c = Context(response_dict)
    except PhantomRedirectException, ex:
        return HttpResponseRedirect(ex.redir)
    return HttpResponse(t.render(c))


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
def django_imagegenerators_html(request):
    response_dict = {}
    response_dict.update(csrf(request))
    response_dict['user'] = request.user
    t = loader.get_template('../templates/imagegenerators.html')
    c = Context(response_dict)

    return HttpResponse(t.render(c))


def django_sign_up(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            if not request.POST['email']:
                form.errors['email'] = ['You must provide an email address']
                return

            new_user = form.save()

            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = request.POST['email']

            phantom_user = PhantomUser.objects.create(username=username, access_key_id=username)
            phantom_user.save()

            if ACTIVATE_ON_REGISTER:
                new_user.email = email
                new_user.save()
                new_user = authenticate(username=username, password=password)
                login(request, new_user)
                return HttpResponseRedirect("/phantom/")
            else:
                new_user.is_active = False
                new_user.email = email
                new_user.save()

                send_mail('New Phantom User Needs Activation',
                    'New user %s (%s) needs activation.' % (username, email),
                    'nimbus@mcs.anl.gov', ACTIVATION_EMAIL, fail_silently=False)

                t = loader.get_template('../templates/registration/activation.html')
                c = Context({'user': username, 'email': email})
                return HttpResponse(t.render(c))

    else:
        form = UserCreationForm()
    return render(request, "../templates/registration/signup.html", {
        'form': form,
    })


@LogEntryDecorator
@login_required
def django_change_password(request):

    if request.is_ajax():

        try:
            user = User.objects.get(username=request.user.username)
        except User.DoesNotExist:
            return HttpResponse("USER_NOT_FOUND", status=500)

        request_json = json.loads(request.body)

        old_password = request_json.get('old_password')
        if not user.check_password(old_password):
            return HttpResponse("BAD_OLD_PASSWORD", status=500)

        new_password = request_json.get('new_password')
        new_password_confirmation = request_json.get('new_password_confirmation')

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
