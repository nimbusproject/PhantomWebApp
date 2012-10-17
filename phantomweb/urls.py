from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import password_reset, password_change, password_change_done, password_reset_confirm, password_reset_done, password_reset_complete

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^accounts/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', password_reset_confirm),

    url(r'^accounts/change_password/$', password_change, {
        'post_change_redirect' : '/accounts/change_password/done/'})                                                                            ,
    url(r'^accounts/change_password/done/$', password_change_done),
    (r'^accounts/reset_password/$', password_reset),
    (r'^accounts/reset_password/done$', password_reset_done),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/password/rest_complete/$', password_reset_complete),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),

    url(r'^phantom/sites$', 'phantomweb.views.django_sites_html'),
    url(r'^phantom/api/sites/load$', 'phantomweb.views.django_sites_load'),
    url(r'^phantom/api/sites/delete$', 'phantomweb.views.django_sites_delete'),
    url(r'^phantom/api/sites/add$', 'phantomweb.views.django_sites_add'),

    url(r'^phantom/launchconfig$', 'phantomweb.views.django_lc_html'),
    url(r'^phantom/api/launchconfig/load$', 'phantomweb.views.django_lc_load'),
    url(r'^phantom/api/launchconfig/save$', 'phantomweb.views.django_lc_save'),
    url(r'^phantom/api/launchconfig/delete$', 'phantomweb.views.django_lc_delete'),

    url(r'^phantom/domain$', 'phantomweb.views.django_domain_html'),
    url(r'^phantom/api/domain/load$', 'phantomweb.views.django_domain_load'),
    url(r'^phantom/api/domain/start$', 'phantomweb.views.django_domain_start'),
    url(r'^phantom/api/domain/terminate$', 'phantomweb.views.django_domain_terminate'),
    url(r'^phantom/api/domain/resize$', 'phantomweb.views.django_domain_resize'),
    url(r'^phantom/api/domain/update$', 'phantomweb.views.django_domain_update'),
    url(r'^phantom/api/domain/details$', 'phantomweb.views.django_domain_details'),
)



