from django.db import models

from django.contrib.auth.models import User


class OrgUnit(models.Model):
    """Class for Org

    """

    name = models.CharField(max_length=200)
    comment = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)
    members = models.ManyToManyField(User, through='Membership')

    # one should not override __init__ in django
    @classmethod
    def create(cls, name, email):
        _org_unit = cls(name=name, email=email)
        _org_unit.comment = "foo.. at"
        return _org_unit

    def __repr__(self):
        return "<{0} {1}> Name: ({3}) Mail: ({4})".format(
                self.__class__.__name__,
                self.id,
                self.created,
                self.name,
                self.email)

    def __unicode__(self): # __str__ on Python 3
        return self.name


class Membership(models.Model):
    """Membership Many-to-Many User to Org (Organization)
    """
    user = models.ForeignKey(User)
    org = models.ForeignKey(OrgUnit)
