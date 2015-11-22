from __future__ import unicode_literals
from __future__ import print_function

from django.contrib import admin
from reversion.admin import VersionAdmin

# Import then Register your models here.
from .models import RangeV4, RangeV6, RangeDNS
from .models import Person, Organization, Role, MembershipPRORange


class CustomDeleteMixin(admin.ModelAdmin):
    """regular bulk delete of django admin does not call Object.delete() which I
    want to override. So adding a Mixin that replaces the bulk delete drop down."""

    actions = ['custom_delete']

    def custom_delete(self, request, queryset):
        for object in queryset:
            object.delete()
    custom_delete.short_description = "Delete selected items"

    def get_actions(self, request):
        actions = super(CustomDeleteMixin, self).get_actions(request)
        del actions['delete_selected']
        return actions


class RangeV4Admin(VersionAdmin, CustomDeleteMixin):

    readonly_fields = ("is_duplicate",)
    fields = ["address", "mask", "subnet_of", "membershipprorange",
              "comment", "is_duplicate", "duplicates_allowed"]
    list_display = ("address", "mask", "subnet_of", "membershipprorange",
                    "comment", "is_duplicate", "duplicates_allowed")


class RangeV6Admin(VersionAdmin, CustomDeleteMixin):

    readonly_fields = ("is_duplicate", )
    fields = ["address", "mask", "subnet_of", "membershipprorange",
              "comment", "is_duplicate", "duplicates_allowed"]
    list_display = ("address", "mask", "subnet_of", "membershipprorange",
                    "comment", "is_duplicate", "duplicates_allowed")


class RangeDNSAdmin(VersionAdmin, CustomDeleteMixin):

    readonly_fields = ("is_duplicate",)
    fields = ["address", "membershipprorange",
              "comment", "is_duplicate", "duplicates_allowed"]
    list_display = ["address", "idna_decoded", "membershipprorange",
                    "comment", "is_duplicate", "duplicates_allowed"]


class RangeV4Inline(admin.TabularInline):

    model = RangeV4
    extra = 1

    readonly_fields = ("is_duplicate",)
    fields = ["address", "mask", "subnet_of",
              "comment", "is_duplicate", "duplicates_allowed"]
    list_display = ("address", "mask", "subnet_of",
                    "comment", "is_duplicate", "duplicates_allowed")


class RangeV6Inline(admin.TabularInline):

    model = RangeV6
    extra = 1

    readonly_fields = ("is_duplicate",)
    fields = ["address", "mask", "subnet_of",
              "comment", "is_duplicate", "duplicates_allowed"]
    list_display = ("address", "mask", "subnet_of",
                    "comment", "is_duplicate", "duplicates_allowed")


class RangeDNSInline(admin.TabularInline):

    model = RangeDNS
    extra = 1

    readonly_fields = ("is_duplicate",)
    fields = ["address",
              "comment", "is_duplicate", "duplicates_allowed", "range_ptr"]
    list_display = ["address", "idna_decoded",
                    "comment", "is_duplicate", "duplicates_allowed"]


class PersonAdmin(VersionAdmin):

    fields = ["salutation", "last_name", "first_names", "email", "comment"]
    list_display = ["salutation", "last_name", "first_names", "email", "comment"]


class RoleAdmin(VersionAdmin):

    fields = ["name", "comment"]
    list_display = ["name", "comment"]


class OrganizationAdmin(VersionAdmin):

    fields = ["name", "comment"]
    list_display = ["name", "comment"]


class MembershipPRORangeAdmin(VersionAdmin):

    inlines = [
        RangeV4Inline,
        RangeV6Inline,
        RangeDNSInline,
    ]

    fields = [("person", "organization", "role"), ]
    list_fields = [("person", "organization", "role"), ]


# registers
admin.site.register(RangeV4, RangeV4Admin)
admin.site.register(RangeV6, RangeV6Admin)
admin.site.register(RangeDNS, RangeDNSAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(MembershipPRORange, MembershipPRORangeAdmin)


