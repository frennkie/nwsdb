from django.contrib import admin

# Import then Register your models here.
from .models import Contact

class ContactAdmin(admin.ModelAdmin):
    pass
    #list_display = ('Name',)
    #fields = ['comment', 'email']

admin.site.register(Contact, ContactAdmin)
