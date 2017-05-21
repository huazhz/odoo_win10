##########################################################################
#
# pgAdmin 4 - PostgreSQL Tools
#
# Copyright (C) 2013 - 2017, The pgAdmin Development Team
# This software is released under the PostgreSQL Licence
#
##########################################################################

"""Server helper utilities"""


def parse_priv_from_db(db_privileges):
    """
    Common utility function to parse privileges retrieved from database.
    """
    acl = {
        'grantor': db_privileges['grantor'],
        'grantee': db_privileges['grantee'],
        'privileges': []
    }

    privileges = []
    for idx, priv in enumerate(db_privileges['privileges']):
        privileges.append({
            "privilege_type": priv,
            "privilege": True,
            "with_grant": db_privileges['grantable'][idx]
        })

    acl['privileges'] = privileges

    return acl


def parse_priv_to_db(str_privileges, allowed_acls=[]):
    """
    Common utility function to parse privileges before sending to database.
    """
    from pgadmin.utils.driver import get_driver
    from config import PG_DEFAULT_DRIVER
    driver = get_driver(PG_DEFAULT_DRIVER)

    db_privileges = {
        'c': 'CONNECT',
        'C': 'CREATE',
        'T': 'TEMPORARY',
        'a': 'INSERT',
        'r': 'SELECT',
        'w': 'UPDATE',
        'd': 'DELETE',
        'D': 'TRUNCATE',
        'x': 'REFERENCES',
        't': 'TRIGGER',
        'U': 'USAGE',
        'X': 'EXECUTE'
    }

    privileges = []
    allowed_acls_len = len(allowed_acls)

    for priv in str_privileges:
        priv_with_grant = []
        priv_without_grant = []

        if isinstance(priv['privileges'], dict) and 'changed' in priv['privileges']:
            tmp = []
            for p in priv['privileges']['changed']:
                tmp_p = {'privilege_type': p['privilege_type'],
                         'privilege': False,
                         'with_grant': False}

                if 'with_grant' in p:
                    tmp_p['privilege'] = True
                    tmp_p['with_grant'] = p['with_grant']

                if 'privilege' in p:
                    tmp_p['privilege'] = p['privilege']

                tmp.append(tmp_p)

            priv['privileges'] = tmp

        for privilege in priv['privileges']:

            if privilege['privilege_type'] not in db_privileges:
                continue

            if privilege['privilege_type'] not in allowed_acls:
                continue

            if privilege['with_grant']:
                priv_with_grant.append(
                    db_privileges[privilege['privilege_type']]
                )
            elif privilege['privilege']:
                priv_without_grant.append(
                    db_privileges[privilege['privilege_type']]
                )
        # If we have all acl then just return all
        if len(priv_with_grant) == allowed_acls_len > 1:
            priv_with_grant = ['ALL']
        if len(priv_without_grant) == allowed_acls_len > 1:
            priv_without_grant = ['ALL']
        # Appending and returning all ACL
        privileges.append({
            'grantee': driver.qtIdent(None, priv['grantee'])
            if priv['grantee'] != 'PUBLIC' else 'PUBLIC',
            'with_grant': priv_with_grant,
            'without_grant': priv_without_grant
        })

    return privileges


def tokenize_options(options_from_db, option_name, option_value):
    """
    This function will tokenize the string stored in database
    e.g. database store the value as below
    key1=value1, key2=value2, key3=value3, ....
    This function will extract key and value from above string

    Args:
        options_from_db: Options from database
        option_name: Option Name
        option_value: Option Value

    Returns:
        Tokenized options
    """
    options = []
    if options_from_db is not None:
        option_str = options_from_db.split(',')
        for fdw_option in option_str:
            k, v = fdw_option.split('=', 1)
            options.append({option_name: k, option_value: v})
    return options


def validate_options(options, option_name, option_value):
    """
    This function will filter validated options
    and sets flag to use in sql template if there are any
    valid options

    Args:
        options: List of options
        option_name: Option Name
        option_value: Option Value

    Returns:
        Flag, Filtered options
    """
    valid_options = []
    is_valid_options = False

    for option in options:
        # If option name is valid
        if option_name in option and \
            option[option_name] is not None and \
                option[option_name] != '' and \
                len(option[option_name].strip()) > 0:
            # If option value is valid
            if option_value in option and \
                            option[option_value] is not None and \
                            option[option_value] != '' and \
                            len(option[option_value].strip()) > 0:
                # Do nothing here
                pass
            else:
                # Set empty string if no value provided
                option[option_value] = ''
            valid_options.append(option)

    if len(valid_options) > 0:
        is_valid_options = True

    return is_valid_options, valid_options
