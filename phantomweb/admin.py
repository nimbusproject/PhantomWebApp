from django.contrib import admin
from phantomweb.models import PhantomInfoDB, RabbitInfoDB, LaunchConfigurationDB, HostMaxPairDB

class PhantomInfoAdmin(admin.ModelAdmin):
    pass
admin.site.register(PhantomInfoDB, PhantomInfoAdmin)

class RabbitInfoAdmin(admin.ModelAdmin):
    pass
admin.site.register(RabbitInfoDB, RabbitInfoAdmin)

class LaunchConfigurationAdmin(admin.ModelAdmin):
    pass
admin.site.register(LaunchConfigurationDB, LaunchConfigurationAdmin)

class HostMaxPairAdmin(admin.ModelAdmin):
    pass
admin.site.register(HostMaxPairDB, HostMaxPairAdmin)
