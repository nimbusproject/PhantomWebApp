from django.contrib import admin
from phantomweb.models import PhantomInfoDB, RabbitInfoDB

class PhantomInfoAdmin(admin.ModelAdmin):
    pass
admin.site.register(PhantomInfoDB, PhantomInfoAdmin)

class RabbitInfoAdmin(admin.ModelAdmin):
    pass
admin.site.register(RabbitInfoDB, RabbitInfoAdmin)
