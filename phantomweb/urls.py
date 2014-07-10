from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.contrib.auth.views import password_reset, password_change, password_change_done, \
    password_reset_confirm, password_reset_done, password_reset_complete
from django.views.generic import RedirectView
from password_policies.views import PasswordChangeFormView, PasswordChangeDoneView

admin.autodiscover()

DEV_VERSION = "dev"
ACCEPTED_RESOURCE_PATTERN = "[-_.0-9A-Za-z ]"

urlpatterns = patterns('',

    url(r'^accounts/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico')),
    url(r'^accounts/ajax_change_password/$', 'phantomweb.views.django_change_password'),
    url(r'^accounts/change_password/$', PasswordChangeFormView.as_view(), name='password_change'),
    url(r'^accounts/change_password/done/$', PasswordChangeDoneView.as_view(), name='password_change_done'),
    url(r'^accounts/reset_password/$', password_reset),
    url(r'^accounts/reset_password/done$', password_reset_done),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/password/rest_complete/$', password_reset_complete),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^accounts/signup/$', 'phantomweb.views.django_sign_up'),

    url(r'^phantom/appliances/?$', 'phantomweb.views.django_publiclc_html'),

    url(r'^phantom/imagegenerators$', 'phantomweb.views.django_imagegenerators_html'),

    url(r'^phantom/profile/?$', 'phantomweb.views.django_profile_html'),

    url(r'^phantom/?$', 'phantomweb.views.django_phantom_html'),
    url(r'^$', 'phantomweb.views.django_phantom_html'),

    url(r'^phantom/launchconfig/?$', 'phantomweb.views.django_lc_html'),

    url(r'^phantom/domain/?$', 'phantomweb.views.django_domain_html'),

    # API dev version
    url(r'^api/%s/token$' % DEV_VERSION, 'tokenapi.views.token_new', name='api_token_new'),
    url(r'^api/%s/token/(?P<token>.{24})/(?P<user>\d+).json$' % DEV_VERSION, 'tokenapi.views.token', name='api_token'),

    url(r'^api/%s/sites$' % DEV_VERSION, 'phantomweb.api.dev.sites'),
    url(r'^api/%s/sites(?P<details>\w+)$' % DEV_VERSION, 'phantomweb.api.dev.sites'),
    url(r'^api/%s/sites/(%s+)$' % (DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.site_resource'),
    url(r'^api/%s/sites/(%s+)(?P<details>\w+)$' % (
        DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.site_resource'),
    url(r'^api/%s/sites/(%s+)/sshkeys$' % (
        DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.site_ssh_key_resource'),
    url(r'^api/%s/credentials/sites$' % DEV_VERSION, 'phantomweb.api.dev.credentials'),
    url(r'^api/%s/credentials/sites(?P<details>\w+)$' % DEV_VERSION, 'phantomweb.api.dev.credentials'),
    url(r'^api/%s/credentials/sites/(%s+)$' % (
        DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.credentials_resource'),
    url(r'^api/%s/credentials/sites/(%s+)(?P<details>\w+)$' % (
        DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.credentials'),
    url(r'^api/%s/credentials/chef$' % DEV_VERSION, 'phantomweb.api.dev.chef_credentials'),
    url(r'^api/%s/credentials/chef/(%s+)$' % (
        DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.chef_credentials_resource'),
    url(r'^api/%s/launchconfigurations$' % DEV_VERSION, 'phantomweb.api.dev.launchconfigurations'),
    url(r'^api/%s/launchconfigurations(?P<public>\w+)$' % DEV_VERSION, 'phantomweb.api.dev.launchconfigurations'),
    url(r'^api/%s/launchconfigurations/(%s+)$' % (DEV_VERSION, ACCEPTED_RESOURCE_PATTERN),
        'phantomweb.api.dev.launchconfiguration_resource'),
    url(r'^api/%s/domains$' % DEV_VERSION, 'phantomweb.api.dev.domains'),
    url(r'^api/%s/domains/([-0-9A-Za-z]+)$' % DEV_VERSION, 'phantomweb.api.dev.domain_resource'),
    url(r'^api/%s/domains/([-0-9A-Za-z]+)/instances$' % DEV_VERSION, 'phantomweb.api.dev.instances'),
    url(r'^api/%s/domains/([-0-9A-Za-z]+)/instances/([-0-9A-Za-z]+)$' % DEV_VERSION,
            'phantomweb.api.dev.instance_resource'),
    url(r'^api/%s/domains/([-0-9A-Za-z]+)/instances/([-0-9A-Za-z]+)(?P<details>\w+)$' % DEV_VERSION,
            'phantomweb.api.dev.instance_resource'),
    url(r'^api/%s/sensors$' % DEV_VERSION, 'phantomweb.api.dev.sensors'),
    url(r'^api/%s/sensors/(%s+)$' % (DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.sensor_resource'),

    url(r'^api/%s/imagegenerators$' % DEV_VERSION, 'phantomweb.api.dev.imagegenerators'),
    url(r'^api/%s/imagegenerators/(%s+)$' % (DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.imagegenerator_resource'),
    url(r'^api/%s/imagegenerators/(%s+)/builds$' % (DEV_VERSION, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.image_builds'),
    url(r'^api/%s/imagegenerators/(%s+)/builds/(%s+)$' % (DEV_VERSION, ACCEPTED_RESOURCE_PATTERN, ACCEPTED_RESOURCE_PATTERN), 'phantomweb.api.dev.image_build_resource'),
)
