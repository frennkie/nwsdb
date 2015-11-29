from __future__ import unicode_literals
from __future__ import print_function

from django.db import models
from django.core.validators import MaxValueValidator, ValidationError
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey

from django.db import transaction
import reversion as revisions

import idna
import uuid
import re
import iptools


def dns_name_validator(dns_name):
    """IDN compatible domain validator
    https://stackoverflow.com/questions/2532053/validate-a-hostname-string
    """

    if len(dns_name) > 255:
        raise ValidationError(_("The DNS name can not have more than 255 characters."))
    dns_name = dns_name.encode("idna").lower()
    # TODO what is this doing?! And why the _re name?!
    if not hasattr(dns_name_validator, '_re'):
        dns_name_validator._re = re.compile(r'^([0-9a-z][-\w]*[0-9a-z]\.)+[a-z0-9\-]{2,15}$')
    if not bool(dns_name_validator._re.match(dns_name)):
        raise ValidationError(_("The DNS name id invalid."))
    else:
        return True


def network_address_validator(address, obj_range):
    """validate that given ip address and netmask is really the network address of the range
    e.g. 10.11.12.0/24 is valid;
    Args:
        address (unicode): a give address (e.g. "127.0.0.1")
        obj_range (iptools.IpRange): an object instance; e.g. created by: IpRange("::1/128")

    Returns:
        True or Raises ValidationError

    Examples:
        >>> network_address_validator(u'10.11.12.0', iptools.IpRange('10.11.12.0/24'))
        True

        >>> network_address_validator(u'10.11.12.5', iptools.IpRange('10.11.12.0/24'))
        Traceback (most recent call last):
          ...
        ValidationError: [u'Wrong network address for given mask, should be 10.11.12.0']

    """

    if not iptools.IpRange(address).startIp == obj_range.startIp:
        raise ValidationError(_(
            "Wrong network address for given mask, should be " + unicode(obj_range[0])))
    return True


class RangeV4(MPTTModel):
    """IPv4 specific Range model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)

    comment = models.CharField(max_length=255, default="", blank=True)

    duplicates_allowed = models.BooleanField(default=False)
    is_duplicate = models.BooleanField(default=False, editable=False)

    membershipprorange = models.ForeignKey("MembershipPRORange", verbose_name="Relation")

    class Meta:
        ordering = ["address_integer", "mask"]

    class MPTTMeta:
        order_insertion_by = ["address", "mask"]

    address = models.GenericIPAddressField(verbose_name="Network Address (IPv4)",
                                           protocol='IPv4', unpack_ipv4=False)

    address_integer = models.BigIntegerField(verbose_name="IPv4 as Integer", editable=False)

    mask = models.PositiveSmallIntegerField(verbose_name="Mask in Bits (e.g. /24)",
                                            validators=[MaxValueValidator(32)])

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    def __repr__(self):
        return "<{0}: {1}>".format(
                self.__class__.__name__,
                self.cidr)

    def __unicode__(self):  # __str__ on Python 3
        return self.cidr

    # properties
    def cidr(self):
        if self.address and self.mask:
            return self.address + "/" + unicode(self.mask)
        elif self.address == "0.0.0.0" and self.mask == 0:
            return "0.0.0.0/0"
        else:
            return ""
    cidr = property(cidr)

    def ip_range(self):
        try:
            return iptools.IpRange(self.cidr)
        except:
            # 2015-11-23 (RH): TODO when and how can parsing the IpRange fail?!
            print("warning.. unable to create an ip_range from input!")
            return None
    ip_range = property(ip_range)

    def address_int(self):
        return iptools.IpRange(self.address).startIp
    address_int = property(address_int)

    def clean(self):
        """validate fields
        https://docs.djangoproject.com/en/1.8/ref/models/instances/#django.db.models.Model.clean
        This method should be used to provide custom model validation,
        and to modify attributes on your model if desired.
        Note that a model's clean() method is not invoked when you call your model's save()
        method. But it is called when is_valid is invoked.

        """

        if self.ip_range:
            network_address_validator(self.address, iptools.IpRange(self.ip_range))

        self.check_is_duplicate()

        if self.parent:
            if self.address not in self.parent.ip_range:
                raise ValidationError(_(
                    self.cidr + " is not a subnet of " + self.parent.cidr))

        if not self.address_integer == self.address_int:
            self.address_integer = self.address_int

        if not RangeV4.objects.filter(id=self.id):
            self.insert_into_tree()
        else:
            print("well, ok.. but is position still correct?!")

        """
        existing = self.check_is_subnet_of_existing()
        if existing:
            if not self.subnet_of == existing:
                raise ValidationError(_(
                    self.cidr + " is a subnet of existing range " + existing.cidr))
        """

        return self

    ''' well.. seems a bit dangerous to override save() .. easily get's you into a loop
    def save(self, *args, **kwargs):
        pass
    '''

    def delete(self, *args, **kwargs):
        """ Override built in delete method to update the "is_duplicate" flag"""

        if self.is_duplicate:
            all_dupes = RangeV4.objects.filter(address=self.address).exclude(id=self.id)
            if len(all_dupes) == 1:
                with transaction.atomic(), revisions.create_revision():
                    revisions.set_comment("set is_duplicate to False while deleting")
                    all_dupes[0].is_duplicate = False
                    all_dupes[0].save()

        # only needed if both rangev4 (child) and subnet_of (parent) are set
        try:
            isinstance(self.rangev4, RangeV4)
            isinstance(self.subnet_of, RangeV4)

            print("need to move relation")
            # 2015-11-28 (RH): TODO move relation

        except:
            print("no need to move relation")
            pass

        super(RangeV4, self).delete(*args, **kwargs)  # Call the "real" save() method.

    def insert_into_tree(self):
        """insert into tree at correct position"""

        # find tree that range belongs to; if none found create new tree
        r_nodes = RangeV4.objects.root_nodes()
        for r_node in r_nodes:
            if self.address in r_node.ip_range:
                break
        else:  # this belongs to the for r_node in r_nodes!
            # range is not part of an existing tree
            print("Not in any range! Will create new tree.")
            self.insert_at(None)

        # 2015-11-29 (RH): TODO is self.parent = None needed here?!
        self.parent = None
        self.find_parent(r_node)
        self.save()

        for child in self.parent.get_children():
            # as we are saving self above we appear as child of parent.. just skip
            if child.cidr == self.cidr:
                pass
            elif child.address in self.ip_range:
                # print("need to set self as parent for: " + str(child))
                child.parent = self
                child.save()
        return

    def find_parent(self, node=None):
        """find the parent of self in tree starting from top/root
            Assumes that the tree exists.
            Runs recursively.
            Initial run should pass in the tree root as "node".

        Args:
            node (RangeV4): When calling should be the root of a tree that contains self

        Returns:
            True when done
                parent value is stored in self.parent
                All cases where a parent can't be found are covered in Exceptions

        Raises:
            Generic Exception:
                when node is not set
                when node is the exact same object as self
                when node and self have the same values for address AND mask
                when node does not contain self

            TODO <RH 2015-11-28>: Create more specific Exceptions?!

        """

        if not node:
            raise Exception(_("Error: Can not find position without node?!"))

        if node is self:
            raise Exception(_("Error: That's me! That shouldn't happen!"))

        if node.cidr == self.cidr:
            # TODO <RH 2015-11-28>: Duplicate handling?!
            # I'd say checking duplicate should be done before calling this (recursive method)!
            raise Exception(_("Error: same Network AND same Mask!"))

        if self.address not in node.ip_range:
            raise Exception(_("Error: I'm not a child of supposed parent!"))

        if not self.parent:
            self.parent = node

        for child in node.get_children():
            # print("checking: " + str(child.cidr))
            if self.address in child.ip_range:
                # print("Yepp, could be: " + str(child.cidr))
                if self.mask < child.mask:
                    # print("no no .. you might be my child!")
                    pass
                else:
                    self.parent = child
                    self.find_parent(child)
                    break
        else:
            return False
        return True

    def check_is_subnet_of_existing(self):
        """try to find out whether there already is range of which is range is a subnet

        Returns
        """

        all_ranges = RangeV4.objects.all().exclude(id=self.id)

        candidate_list = list()
        for _range in all_ranges:
            if self.address in _range.ip_range:
                candidate_list.append(_range)

        if not candidate_list:
            return False

        longest_parent_range = False
        for candidate in candidate_list:
            if not longest_parent_range:
                if 0 < candidate.mask < self.mask:
                    longest_parent_range = candidate
            else:
                if longest_parent_range.mask < candidate.mask < self.mask:
                    longest_parent_range = candidate

        return longest_parent_range

    def check_is_duplicate(self):
        """Method to check whether there already is a Range object defined with the exact
        same "cidr" value. If so also check for duplicates_allowed flag and act on it."""

        all_dupes_same_mask = RangeV4.objects.filter(address=self.address, mask=self.mask).exclude(id=self.id)

        if not all_dupes_same_mask:
            return False
        print("made it past here!")

        all_dupes = RangeV4.objects.filter(address=self.address, mask=self.mask).exclude(id=self.id)

        if not all_dupes:
            return False

        print("and here!")

        if not self.duplicates_allowed:
            raise ValidationError(_(
                "Range already exists but duplicates_allowed is set to False on this Range."))

        duplicates_allowed_list = list()
        duplicates_forbidden_id_list = list()

        for dupe in all_dupes:
            if self.id == dupe.id:
                pass
            else:
                if dupe.duplicates_allowed:
                    duplicates_allowed_list.append(dupe)
                else:
                    duplicates_forbidden_id_list.append(dupe.id)

        if duplicates_forbidden_id_list:
            raise ValidationError(_(
                """Range already exists and at least one existing entry does not allow
                duplicates. Check: """ + unicode(duplicates_forbidden_id_list)))

        with transaction.atomic(), revisions.create_revision():
            revisions.set_comment("set is_duplicate to True while adding")
            self.is_duplicate = True
            self.save()

        for dupe in all_dupes:
            if not dupe.is_duplicate:
                with transaction.atomic(), revisions.create_revision():
                    revisions.set_comment("set is_duplicate to True while adding " + unicode(self.id))
                    dupe.is_duplicate = True
                    dupe.save()

        return True


class RangeV6(models.Model):
    """IPv6 specific Range model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)

    comment = models.CharField(max_length=255, default="", blank=True)

    duplicates_allowed = models.BooleanField(default=False)
    is_duplicate = models.BooleanField(default=False, editable=False)

    membershipprorange = models.ForeignKey("MembershipPRORange", verbose_name="Relation")

    class Meta:
        ordering = ["address"]

    address = models.GenericIPAddressField(verbose_name="IPv6 Address",
                                           protocol='IPv6', unpack_ipv4=False)
    mask = models.PositiveSmallIntegerField(verbose_name="CIDR Bits",
                                            validators=[MaxValueValidator(128)])

    subnet_of = models.OneToOneField('self', null=True, blank=True, on_delete=models.SET_NULL)

    def cidr(self):
        if self.address and self.mask:
            return self.address + "/" + unicode(self.mask)
        else:
            return ""
    cidr = property(cidr)

    def ip_range(self):
        return iptools.IpRange(self.cidr)
    ip_range = property(ip_range)

    def __repr__(self):
        return "<{0}: {1}>".format(
                self.__class__.__name__,
                self.address)

    def __unicode__(self):  # __str__ on Python 3
        return self.address

    def clean(self, exclude=None):
        """validate fields"""
        self.check_is_duplicate()
        return self

    def delete(self, *args, **kwargs):
        """ Override built in delete to update the "is_duplicate" flag"""

        if self.is_duplicate:
            all_dupes = RangeV6.objects.filter(address=self.address).exclude(id=self.id)
            if len(all_dupes) == 1:
                with transaction.atomic(), revisions.create_revision():
                    revisions.set_comment("set is_duplicate to False while deleting")
                    all_dupes[0].is_duplicate = False
                    all_dupes[0].save()

            super(RangeV6, self).delete(*args, **kwargs)
            return  # just return
        else:
            super(RangeV6, self).delete(*args, **kwargs)  # Call the "real" save() method.
            return

    def check_is_duplicate(self):
        """Method to check whether there already is a Range object defined with the exact
        same "address" value. If so also check for duplicates_allowed flag and act on it."""

        all_dupes = RangeV6.objects.filter(address=self.address).exclude(id=self.id)

        if not all_dupes:
            return False

        if not self.duplicates_allowed:
            raise ValidationError(_(
                "Range already exists but allow duplicates is set to False on this Range."))

        duplicates_allowed_list = list()
        duplicates_forbidden_id_list = list()

        for dupe in all_dupes:
            if self.id == dupe.id:
                pass
            else:
                if dupe.duplicates_allowed:
                    duplicates_allowed_list.append(dupe)
                else:
                    duplicates_forbidden_id_list.append(dupe.id)

        if duplicates_forbidden_id_list:
            raise ValidationError(_(
                """Range already exists and at least one existing entry does not allow
                duplicates. Check: """ + unicode(duplicates_forbidden_id_list)))

        with transaction.atomic(), revisions.create_revision():
            revisions.set_comment("set is_duplicate to True while adding")
            self.is_duplicate = True
            self.save()

        for dupe in all_dupes:
            if not dupe.is_duplicate:
                with transaction.atomic(), revisions.create_revision():
                    revisions.set_comment("set is_duplicate to True while adding " +
                                          unicode(self.id))
                    dupe.is_duplicate = True
                    dupe.save()

        return True


class RangeDNS(models.Model):
    """DNS specific Range model"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)

    comment = models.CharField(max_length=255, default="", blank=True)

    duplicates_allowed = models.BooleanField(default=False)
    is_duplicate = models.BooleanField(default=False, editable=False)

    membershipprorange = models.ForeignKey("MembershipPRORange", verbose_name="Relation")

    class Meta:
        ordering = ["address"]

    address = models.CharField(max_length=255)

    def clean_fields(self, exclude=None):
        """first validate, then lower case and IDN convert dns_name"""
        dns_name_validator(self.address)
        self.address = self.address.encode("idna").lower()
        return self

    # is a @property done without the @ shortcut + a label for django admin
    def idna_decoded(self):
        return idna.decode(self.address)
    idna_decoded.short_description = "DNS as IDN"
    idna_decoded = property(idna_decoded)

    def __repr__(self):
        return "<{0}: {1}>".format(
                self.__class__.__name__,
                self.address)

    def __unicode__(self):  # __str__ on Python 3
        return self.address

    def clean(self, exclude=None):
        """validate fields"""
        self.check_is_duplicate()
        return self

    def delete(self, *args, **kwargs):
        """ Override built in delete to update the "is_duplicate" flag"""

        if self.is_duplicate:
            all_dupes = RangeDNS.objects.filter(address=self.address).exclude(id=self.id)
            if len(all_dupes) == 1:
                with transaction.atomic(), revisions.create_revision():
                    revisions.set_comment("set is_duplicate to False while deleting")
                    all_dupes[0].is_duplicate = False
                    all_dupes[0].save()

        super(RangeDNS, self).delete(*args, **kwargs)  # Call the "real" save() method.

    def check_is_duplicate(self):
        """Method to check whether there already is a Range object defined with the exact
        same "address" value. If so also check for duplicates_allowed flag and act on it."""

        all_dupes = RangeDNS.objects.filter(address=self.address).exclude(id=self.id)

        if not all_dupes:
            return False

        if not self.duplicates_allowed:
            raise ValidationError(_("Range already exists but allow duplicates is set to False on this Range."))

        duplicates_allowed_list = list()
        duplicates_forbidden_id_list = list()

        for dupe in all_dupes:
            if self.id == dupe.id:
                pass
            else:
                if dupe.duplicates_allowed:
                    duplicates_allowed_list.append(dupe)
                else:
                    duplicates_forbidden_id_list.append(dupe.id)

        if duplicates_forbidden_id_list:
            raise ValidationError(_("""Range already exists and at least one existing entry does not allow duplicates. Check: """ + unicode(duplicates_forbidden_id_list)))

        with transaction.atomic(), revisions.create_revision():
            revisions.set_comment("set is_duplicate to True while adding")
            self.is_duplicate = True
            self.save()

        for dupe in all_dupes:
            if not dupe.is_duplicate:
                with transaction.atomic(), revisions.create_revision():
                    revisions.set_comment("set is_duplicate to True while adding " + unicode(self.id))
                    dupe.is_duplicate = True
                    dupe.save()

        return True


class Person(models.Model):
    """Person Range model"""

    class Meta:
        ordering = ["email"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)

    comment = models.CharField(max_length=255, default="", blank=True)

    email = models.EmailField()
    last_name = models.CharField(max_length=80, default="")
    first_names = models.CharField(max_length=80, default="", blank=True)

    # salutation
    SALUTATION_CHOICES = (
        ('MR', 'Mr.'),
        ('MRS', 'Mrs.'),
        ('MS', 'Ms.'),
        ('OTHER', 'Other'),
    )
    salutation = models.CharField(max_length=5, choices=SALUTATION_CHOICES)

    def display_name(self):
        if len(self.last_name) and len(self.first_names):
            return self.last_name + ", " + self.first_names
        elif not len(self.last_name) and not len(self.first_names):
            return "Doe, John"
        elif len(self.last_name):
            return self.last_name
        else:
            return self.first_names
    display_name = property(display_name)

    def __repr__(self):
        return "<{0}: {1}>".format(
                self.__class__.__name__,
                self.email)

    def __unicode__(self):  # __str__ on Python 3
        return self.display_name + " (" + self.email + ")"


class Organization(models.Model):
    """Organization model"""

    class Meta:
        ordering = ["name"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)

    comment = models.CharField(max_length=255, default="", blank=True)

    name = models.CharField(max_length=80)

    def __repr__(self):
        return "<{0}: {1}>".format(
                self.__class__.__name__,
                self.name)

    def __unicode__(self):  # __str__ on Python 3
        return self.name


class Role(models.Model):
    """Organization model"""

    class Meta:
        ordering = ["name"]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)

    comment = models.CharField(max_length=255, default="", blank=True)

    name = models.CharField(max_length=80)

    def __repr__(self):
        return "<{0}: {1}>".format(
                self.__class__.__name__,
                self.name)

    def __unicode__(self):  # __str__ on Python 3
        return self.name


class MembershipPRORange(models.Model):
    """Membership Person Organization having a Role"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        unique_together = (("person", "organization"),)

    person = models.ForeignKey(Person)
    organization = models.ForeignKey(Organization)
    role = models.ForeignKey(Role)

    def ranges_total(self):
        return self.rangev4_set.count() + self.rangev6_set.count() + self.rangedns_set.count()
    ranges_total = property(ranges_total)

    def __repr__(self):
        return "<{0}: {1}>".format(
                self.__class__.__name__,
                self.person.email)

    def __unicode__(self):  # __str__ on Python 3
        return ("User: \"" + self.person.display_name +
                "\" Role: \"" + self.role.name +
                "\" at Org: \"" + self.organization.name +
                "\" (" + unicode(self.ranges_total) + " Ranges)")
