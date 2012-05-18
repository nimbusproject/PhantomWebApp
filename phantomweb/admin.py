from django.contrib import admin
from phantomweb.models import PhantomInfoDB, DefaultCloudsDB

class PhantomInfoAdmin(admin.ModelAdmin):
    pass
admin.site.register(PhantomInfoDB, PhantomInfoAdmin)

class DefaultCloudsDBAdmin(admin.ModelAdmin):
   pass
admin.site.register(DefaultCloudsDB, DefaultCloudsDBAdmin)

