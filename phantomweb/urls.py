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
    url(r'^phantom/get_iaas$', 'phantomweb.views.django_get_iaas_info'),
    url(r'^phantom/get_initial$', 'phantomweb.views.django_get_initial_info'),
    url(r'^phantom/domain/list$', 'phantomweb.views.django_list_domain'),
    url(r'^phantom/domain/start$', 'phantomweb.views.django_start_domain'),
    url(r'^phantom/domain/delete$', 'phantomweb.views.django_delete_domain'),
    url(r'^phantom/domain/resize$', 'phantomweb.views.django_update_desired_size'),
    url(r'^phantom/domain/terminate_instance$', 'phantomweb.views.django_terminate_iaas_instance'),
    url(r'^phantom$', 'phantomweb.views.django_phantom'),
    url(r'^phantom/launchconfig$', 'phantomweb.views.django_lc'),
    url(r'^phantom/cloudedit$', 'phantomweb.views.django_cloud_edit'),
    url(r'^phantom/get_sites$', 'phantomweb.views.django_get_sites'),
    url(r'^phantom/get_user_sites$', 'phantomweb.views.django_get_user_site_info'),
    url(r'^phantom/delete_cloud$', 'phantomweb.views.django_delete_site'),
    url(r'^phantom/add_cloud$', 'phantomweb.views.django_add_site'),
    url(r'^phantom/load_lc$', 'phantomweb.views.django_lc_load'),
    url(r'^phantom/phantom2$', 'phantomweb.views.django_phantom2'),
)

