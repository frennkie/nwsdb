from __future__ import unicode_literals
from __future__ import print_function

from django.contrib import admin
from reversion.admin import VersionAdmin

# Import then Register your models here.
from .models import RangeV4, RangeV6, RangeDNS
from .models import Person, Organization, Role, Membership


class RangeV4Admin(VersionAdmin):

    fields = ["address", "mask", "membership", "subnet_of", "comment"]
    list_display = ("address", "mask", "membership", "subnet_of", "comment")
    ordering = ["address"]


class RangeV6Admin(VersionAdmin):

    fields = ["address", "mask", "subnet_of", "comment"]
    list_display = ("address", "mask", "subnet_of", "comment")
    ordering = ["address"]


class RangeDNSAdmin(VersionAdmin):

    fields = ["address", "comment", "membership"]
    list_display = ["address", "idna_decoded", "membership", "comment"]
    ordering = ["address"]


class PersonAdmin(VersionAdmin):

    fields = ["email",  "comment"]
    list_display = ["email", "comment"]
    ordering = ["email"]


class RoleAdmin(VersionAdmin):

    fields = ["name", "comment"]
    list_display = ["name", "comment"]
    ordering = ["name"]


class OrganizationAdmin(VersionAdmin):

    fields = ["name", "comment"]
    list_display = ["name", "comment"]
    ordering = ["name"]


class MembershipAdmin(VersionAdmin):
    fields = ["person", "organization", "role"]
    list_display = ["person", "organization", "role"]


# registers
admin.site.register(RangeV4, RangeV4Admin)
admin.site.register(RangeV6, RangeV6Admin)
admin.site.register(RangeDNS, RangeDNSAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Membership, MembershipAdmin)


