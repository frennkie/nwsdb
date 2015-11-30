from __future__ import unicode_literals
from __future__ import print_function

from django.db import models, IntegrityError
from django.core.validators import MaxValueValidator, ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _

from mptt.models import MPTTModel, TreeForeignKey

from django.db import transaction
import reversion as revisions

import idna
import uuid
import re
import iptools

import logging
logger = logging.getLogger(__name__)


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
                                           protocol='IPv4',
                                           unpack_ipv4=False)

    address_integer = models.BigIntegerField(verbose_name="IPv4 as Integer",
                                             editable=False,
                                             db_index=True)

    mask = models.PositiveSmallIntegerField(verbose_name="Mask in Bits (e.g. /24)",
                                            validators=[MaxValueValidator(32)])

    parent = TreeForeignKey('self',
                            null=True,
                            blank=True,
                            related_name='children',
                            db_index=True)

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
        except ValueError:
            # 2015-11-23 (RH): TODO when and how can parsing the IpRange fail?!
            logger.warn("warning.. unable to create an ip_range from input!")
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

        # make sure db field address_integer is set to the correct value
        if not self.address_integer == self.address_int:
            self.address_integer = self.address_int

        # make sure that given address is really the startIp of the range (with given mask)
        if self.ip_range:
            network_address_validator(self.address, iptools.IpRange(self.ip_range))

        # check for duplicates
        # TODO (RH) 2015-11-29: duplicate handling?!
        self.check_is_duplicate()

        # check whether new RangeV4 is really a child of selected parent
        # TODO (RH) 2015-11-29: should user really be allow / required to set parent?!
        if self.parent:
            if self.address not in self.parent.ip_range:
                raise ValidationError(_(
                    self.cidr + " is not a subnet of " + self.parent.cidr))

        # insert into tree at correct position (no matter what user selected as "parent")
        try:
            self.insert_into_tree()
        except IntegrityError:
            logger.debug("Integrity because object is not new.. so that's fine.")

        # TODO (RH) 2015-11-29: does this hurt? Shouldn't really!
        # play it safe.. rebuild on every save
        RangeV4.objects.rebuild()

        return self

    ''' well.. seems a bit dangerous to override save() .. easily get's you into a loop
    def save(self, *args, **kwargs):
        pass
    '''

    def delete(self, *args, **kwargs):
        """Override built in delete method to update the "is_duplicate" flag"""

        # TODO (RH) 2015-11-29: TODO When delete a node the children are also deleted?!

        # update is_duplicate flags
        if self.is_duplicate:
            all_dupes = RangeV4.objects.filter(address=self.address).exclude(id=self.id)
            if len(all_dupes) == 1:
                with transaction.atomic(), revisions.create_revision():
                    revisions.set_comment("set is_duplicate to False while deleting")
                    all_dupes[0].is_duplicate = False
                    all_dupes[0].save()

        # take care of parent/child relations
        self.prepare_delete()
        RangeV4.objects.rebuild()

        super(RangeV4, self).delete(*args, **kwargs)  # Call the "real" save() method.

    def prepare_delete(self, preserve_children=True):
        """Prepare deletion of a node.

        Args:
            preserve_children (bool): If False all children will be deleted with node
                When True will preserve children (might require to promote new root

        Returns:
            True if everything is find, otherwise (e.g. unable to promote new root) False

        """

        if not preserve_children:
            return True

        # TODO (RH) 2015-11-28: move relation .. write some tests! :-)
        # Fixture for tests: 20151129.datadump.json
        if self.is_root_node():
            if self.is_leaf_node():
                logger.debug("Node is both root and leaf.. no need to move anything.")
                return True
            else:
                new_root_candidates = self.get_children()
                if len(new_root_candidates) == 1:
                    new_root = new_root_candidates[0]
                    logger.info("Make this the new tree root: " + str(new_root.cidr))
                    new_root.parent = None
                    new_root.move_to(None, None)
                    new_root.save()

                    return True
                else:
                    logger.info("Root (going to be deleted) has more than one child. Split..")
                    for new_root_candidate in new_root_candidates:
                        logger.debug("New root: " + str(new_root_candidate))
                        new_root_candidate.parent = None
                        new_root_candidate.move_to(None, None)
                        new_root_candidate.save()

                    return False

        else:
            if self.is_leaf_node():
                logger.debug("Node is a leaf.. no need to move anything.")
                return True
            else:
                logger.debug("need to fix parent - child relations...")
                for node in self.get_children():
                    logger.debug("kids: " + node.cidr)
                    node.parent = self.parent
                    node.save()

                return True

    @classmethod
    def validate_trees(cls):
        """validate database (iterate over every root)"""

        root_nodes = RangeV4.objects.root_nodes()

        inconsistent_trees = list()

        for root in root_nodes:
            if not root.validate_tree():
                inconsistent_trees.append(root)

        if inconsistent_trees:
            logger.error("Inconsistent tree(s): " + str(inconsistent_trees))
            raise Exception(_("Error: Inconsistent tree(s)"))
        else:
            logger.info("Tree(s) appear to be consistent!")

    def validate_tree(self):
        """validate one tee

            Iterate every item in tree and check:
                is item cidr contained in parent cidr
                is cidr of every child contained in item cidr

        Returns:
            True or False

        Notes:
            TODO (RH) 2015-11-28: Some cases are missing
                * document implemented cases
                * document missing cases
                * implement missing cases
                * write tests! ;-)

            * Go over every leaf node and check the direct ancestor line (to root)
            * check every sibling.. should not have exact same address

        """

        for item in self.get_family():
            logger.debug("validating on: " + item.cidr)
            # check parent (unless item it's a root_node)
            if not item.is_root_node():
                if item.address not in item.parent.ip_range:
                    logger.error("Range " + item.cidr + " not in " + str(item.parent.ip_range))
                    return False
                if item.mask == item.parent.mask:
                    logger.error("child has same mask as parent on: " + item.cidr)
                    return False
                # store current value of item.parent, run find_parent and then compare
                cur_parent = item.parent
                item.find_parent(item.get_root())
                if cur_parent is not item.parent:
                    logger.error("Range " + item.cidr + " points to wrong parent.")
                    return False

            # check children (unless item is a leaf_node)
            if not item.is_leaf_node():
                for child in item.get_children():
                    if child.address not in item.ip_range:
                        logger.error("Range " + child.cidr + " not in " + str(item.ip_range))
                        return False

        return True

    '''
    def check_is_subnet_of_existing(self):
        # try to find out whether there already is range of which is range is a subnet

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
    '''



    def insert_into_tree(self):
        """Insert into tree at correct position.

        Insert as member method to insert a _new_ object at the right position.
        Parent and Child relations are taken care of

        Raises:
            IntegrityError: if object already exists in DB

        """

        # ensure that object is not already in DB - in that case it would be a move
        if RangeV4.objects.filter(pk=self.pk).exists():
            raise IntegrityError("Object instance already in database.")

        # find tree that range belongs to; if none found create new tree
        all_root_nodes = RangeV4.objects.root_nodes()
        for root_node in all_root_nodes:
            if self.address in root_node.ip_range:
                logger.debug("Need to insert Range " + self.cidr + " below: " + str(root_node))
                break
        else:  # from for loop!
            # range is not part of an existing tree
            # TODO (RH) 2015-11-29: new tree handling! Passt?!
            logger.debug("Range not in any existing tree! Create new tree.")
            self.insert_at(None)
            self.save()
            RangeV4.objects.rebuild()
            return True

        self.parent = self.find_parent(root_node)
        logger.debug("Setting newly created Range as child of: " + str(self.parent))
        self.save()

        # rearranging any items that were children of parent and are now children of self
        for child in self.parent.get_children():
            # as we are saving self above we appear as child of parent.. just skip
            if child.cidr == self.cidr:
                pass
            elif child.address in self.ip_range:
                logger.info("Setting newly created Range as parent for: " + str(child))
                child.parent = self
                child.save()

        return True

    def find_parent(self, node):
        """Find the parent of self in tree starting from top/root.

        Assumes that the tree exists.
        Tree needs to be valid (Ranges reflect IP subnet rules)
        Runs recursively.
        Initial run must pass in the tree root as "node".

        Args:
            node (RangeV4): Must be the root of a tree that contains self

        Returns:
            parent (RangeV4)

        """

        parent = node

        for item in node.get_children():
            if self.address in item.ip_range:
                logger.debug("Yepp: self is part of this branch: " + str(parent.cidr))
                parent = self.find_parent(item)
                break

        return parent

    def check_is_duplicate(self):
        """Method to check whether there already is a Range object defined with the exact
        same "cidr" value. If so also check for duplicates_allowed flag and act on it."""

        all_dupes_same_mask = RangeV4.objects.filter(address=self.address, mask=self.mask).exclude(id=self.id)

        if not all_dupes_same_mask:
            return False
        logger.debug("made it past here!")

        all_dupes = RangeV4.objects.filter(address=self.address, mask=self.mask).exclude(id=self.id)

        if not all_dupes:
            return False

        logger.debug("and here!")

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
