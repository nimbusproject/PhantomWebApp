from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import password_reset

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^accounts/password/reset$', 'django.contrib.auth.views.password_change'),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^phantom/get_iaas$', 'phantomweb.views.django_get_iaas_info'),
    url(r'^phantom/get_initial$', 'phantomweb.views.django_get_initial_info'),
    url(r'^phantom/domain/list$', 'phantomweb.views.django_list_domain'),
    url(r'^phantom/domain/start$', 'phantomweb.views.django_start_domain'),
    url(r'^phantom/domain/delete$', 'phantomweb.views.django_delete_domain'),
    url(r'^phantom$', 'phantomweb.views.django_phantom'),
)
