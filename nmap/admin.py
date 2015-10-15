from django.contrib import admin

# Import then Register your models here.
from .models import Contact, NmapTask, OrgUnit, Membership


class MembershipInline(admin.TabularInline):
    model = Membership


class OrgUnitAdmin(admin.ModelAdmin):
    inlines = (MembershipInline,)
    #ordering = ("name", )
    #list_display = ('Name',)
    #fields = ['comment', 'email']


class ContactAdmin(admin.ModelAdmin):
    pass
    #list_display = ('Name',)
    #fields = ['comment', 'email']


class NmapTaskAdmin(admin.ModelAdmin):
    pass

admin.site.register(Contact, ContactAdmin)
admin.site.register(NmapTask, NmapTaskAdmin)
admin.site.register(OrgUnit, OrgUnitAdmin)
