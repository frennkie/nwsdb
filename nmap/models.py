from django.db import models
# https://docs.djangoproject.com/en/1.8/topics/i18n/timezones/
from django.utils import timezone

# Create your models here.

class Contact(models.Model):
    """Class for Contact

     """

    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    comment = models.CharField(max_length=200)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)
    #address_detail = db.relationship("AddressDetail", secondary=contact_addressdetail_table)

    # one should not override __init__ in django
    @classmethod
    def create(cls, name, email):
        contact = cls(name=name, email=email)
        contact.comment = "foo.. at: " + str(timezone.now()) + "!"
        return contact

    def __repr__(self):
        return "<{0} {1}> Name: ({3}) Mail: ({4})".format(
                self.__class__.__name__,
                self.id,
                self.created,
                self.name,
                self.email)

    def __unicode__(self): # __str__ on Python 3
        return self.name

