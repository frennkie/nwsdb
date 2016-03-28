# ldap_auth.py (custom methods for django_python3_ldap)
from django_python3_ldap.utils import format_search_filters

from nwscandb.settings_prod import LDAP_AUTH_MEMBER_OF_ATTRIBUTE
from nwscandb.settings_prod import LDAP_AUTH_GROUP_MEMBER_OF
from nwscandb.settings_prod import LDAP_AUTH_SYNC_USER_RELATIONS_GROUPS


import logging
logger = logging.getLogger(__name__)


def custom_format_search_filters(ldap_fields):
    # Add in simple filters.
    ldap_fields[LDAP_AUTH_MEMBER_OF_ATTRIBUTE] = LDAP_AUTH_GROUP_MEMBER_OF
    # Call the base format callable.
    search_filters = format_search_filters(ldap_fields)
    # All done!
    return search_filters


def custom_sync_user_relations(user, ldap_attributes):
    # do nothing by default

    group_memberships = ldap_attributes[LDAP_AUTH_MEMBER_OF_ATTRIBUTE]

    if LDAP_AUTH_SYNC_USER_RELATIONS_GROUPS["staff"] in group_memberships:
        user.is_staff = True
        user.save()

    if LDAP_AUTH_SYNC_USER_RELATIONS_GROUPS["superuser"] in group_memberships:
        user.is_superuser = True
        user.save()
    # All done!
    return



