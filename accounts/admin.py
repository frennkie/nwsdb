from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin

# Import then Register your models here.
from .models import OrgUnit, Membership


class MembershipInline(admin.TabularInline):
    model = Membership


class OrgUniAdmin(admin.ModelAdmin):
    inlines = (MembershipInline,)
    #ordering = ("name", )
    #list_display = ('Name',)
    #fields = ['comment', 'email']


"""
class UserAdmin(admin.ModelAdmin):
    inlines = (MembershipInline, )
"""

admin.site.register(OrgUnit, OrgUniAdmin)

# Re-register UserAdmin
#admin.site.unregister(User)
#admin.site.register(User, UserAdmin)
