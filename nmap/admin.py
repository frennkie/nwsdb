from django.contrib import admin

# Import then Register your models here.
from .models import Contact, NmapTask

class ContactAdmin(admin.ModelAdmin):
    pass
    #list_display = ('Name',)
    #fields = ['comment', 'email']

class NmapTaskAdmin(admin.ModelAdmin):
    pass

admin.site.register(Contact, ContactAdmin)
admin.site.register(NmapTask, NmapTaskAdmin)
