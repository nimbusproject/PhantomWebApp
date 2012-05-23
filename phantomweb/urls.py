from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import password_reset, password_change, password_change_done, password_reset_confirm, password_reset_done

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^accounts/change_password/$', password_change, {
        'post_change_redirect' : '/accounts/change_password/done/'})                                                                            ,
    url(r'^accounts/change_password/done/$', password_change_done),
    (r'^accounts/reset_password/$', password_reset),
    (r'^accounts/reset_password/done$', password_reset_done),
    url(r'^accounts/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm),
    url(r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^phantom/get_iaas$', 'phantomweb.views.django_get_iaas_info'),
    url(r'^phantom/get_initial$', 'phantomweb.views.django_get_initial_info'),
    url(r'^phantom/domain/list$', 'phantomweb.views.django_list_domain'),
    url(r'^phantom/domain/start$', 'phantomweb.views.django_start_domain'),
    url(r'^phantom/domain/delete$', 'phantomweb.views.django_delete_domain'),
    url(r'^phantom$', 'phantomweb.views.django_phantom'),   
)
