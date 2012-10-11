from django.contrib import admin
from phantomweb.models import PhantomInfoDB

class PhantomInfoAdmin(admin.ModelAdmin):
    pass
admin.site.register(PhantomInfoDB, PhantomInfoAdmin)

