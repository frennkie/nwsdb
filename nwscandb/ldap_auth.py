
import re, binascii

from django.contrib.auth.hashers import make_password
from django.utils.encoding import force_text
from django.utils.module_loading import import_string
from django.utils import six

from django_python3_ldap.conf import settings


def import_func(func):
    if callable(func):
        return func
    elif isinstance(func, six.string_types):
        return import_string(func)
    raise AttributeError("Expected a function {0!r}".format(func))


def convert_model_fields_to_ldap_fields(model_fields):
    """
    Converts a set of model fields into a set of corresponding
    LDAP fields.
    """
    return {
        settings.LDAP_AUTH_USER_FIELDS[field_name]: field_value
        for field_name, field_value
        in model_fields.items()
    }


def format_search_filter(model_fields):
    """
    Creates an LDAP search filter for the given set of model
    fields.
    """
    ldap_fields = convert_model_fields_to_ldap_fields(model_fields);
    ldap_fields["objectClass"] = settings.LDAP_AUTH_OBJECT_CLASS
    search_filters = import_func(settings.LDAP_AUTH_FORMAT_SEARCH_FILTERS)(ldap_fields)
    return "(&{})".format("".join(search_filters));


def sync_user_relations(user, ldap_attributes):
    # do nothing by default
    pass
