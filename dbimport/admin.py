from __future__ import unicode_literals
from __future__ import print_function

from django.contrib import admin


# Import then Register your models here.
from .models import RangeV4
from .models import RangeV6
from .models import RangeDNS


class RangeV4Admin(admin.ModelAdmin):

    fields = ["address", "mask", "subnet_of", "comment"]
    list_display = ("address", "mask", "subnet_of", "comment")
    ordering = ["address"]


class RangeV6Admin(admin.ModelAdmin):

    fields = ["address", "mask", "subnet_of", "comment"]
    list_display = ("address", "mask", "subnet_of", "comment")
    ordering = ["address"]


class RangeDNSAdmin(admin.ModelAdmin):

    fields = ["address", "comment"]
    list_display = ["address", "idna_decoded", "comment"]
    ordering = ["address"]


# registers
admin.site.register(RangeV4, RangeV4Admin)
admin.site.register(RangeV6, RangeV6Admin)
admin.site.register(RangeDNS, RangeDNSAdmin)

