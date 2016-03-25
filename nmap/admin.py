from django.contrib import admin

from reversion.admin import VersionAdmin


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


class NetworkServiceAdmin(VersionAdmin):
    # "normal" declaration of readonly (ro) fields (never editable)
    readonly_fields = ("name", )

    list_display = ('name',
                    "protocol",
                    "address",
                    "port",
                    'service',
                    'state',
                    'reason',
                    'banner',
                    "nmap_report_meta")

    # fields (and order) in detail/edit view  - TODO - actually no service should be editable
    fields = ["name",              # add: ro - view: ro
              "protocol",          # add: rw - view: rw
              "address",           # add: rw - view: rw
              "port",              # add: rw - view: rw
              "service",           # add: rw - view: rw
              "state",             # add: rw - view: rw
              "reason",            # add: rw - view: rw
              "banner",            # add: rw - view: rw
              "nmap_report_meta"]  # add: rw - view: rw


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

