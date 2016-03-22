from django.contrib import admin

# Import then Register your models here.
from .models import Membership, OrgUnit
from .models import Contact
from .models import NmapTask, NmapReportMeta
from .models import NetworkService

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

class NetworkServiceAdmin(admin.ModelAdmin):
    pass

class NmapTaskAdmin(admin.ModelAdmin):
    pass


class NmapReportMetaAdmin(admin.ModelAdmin):
    pass

# registers
admin.site.register(OrgUnit, OrgUnitAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(NetworkService, NetworkServiceAdmin)
admin.site.register(NmapTask, NmapTaskAdmin)
admin.site.register(NmapReportMeta, NmapReportMetaAdmin)

