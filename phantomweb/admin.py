from django.contrib import admin

from phantomweb.models import RabbitInfoDB, LaunchConfigurationDB,\
    HostMaxPairDB, PhantomUser, LaunchConfiguration, PublicLaunchConfiguration


class RabbitInfoAdmin(admin.ModelAdmin):
    pass

admin.site.register(RabbitInfoDB, RabbitInfoAdmin)


class AutoScaleLaunchConfigurationAdmin(admin.ModelAdmin):
    pass

admin.site.register(LaunchConfigurationDB, AutoScaleLaunchConfigurationAdmin)


class LaunchConfigurationAdmin(admin.ModelAdmin):
    pass

admin.site.register(LaunchConfiguration, LaunchConfigurationAdmin)


class PublicLaunchConfigurationAdmin(admin.ModelAdmin):
    pass

admin.site.register(PublicLaunchConfiguration, LaunchConfigurationAdmin)


class HostMaxPairAdmin(admin.ModelAdmin):
    pass

admin.site.register(HostMaxPairDB, HostMaxPairAdmin)


class PhantomUserAdmin(admin.ModelAdmin):
    pass

admin.site.register(PhantomUser, PhantomUserAdmin)
