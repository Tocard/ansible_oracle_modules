#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: oracle_tnsnames
short_description: Manipulate Oracle's tnsnames.ora and other .ora files
description:
    - Manipulate Oracle's tnsnames.ora and other .ora files
    - Must be run on a remote host
version_added: "3.0.1"
options:
    path:
        description:
        - location of .ora file
        required: true
    backup:
        description:
        - Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.
        type: bool
        default: no

notes:
    - Each stanze is written on single line
    - Comments are not supported (yet)
author: ibre5041@ibrezina.net
'''

EXAMPLES = '''
---
- hosts: localhost
  vars:
    oracle_env:
      ORACLE_HOME: /u01/app/grid/product/12.1.0.2/grid
  tasks:
    - name: Modify tnsnames.ora
      oracle_tnsnames:
        path: "{{ oracle_env.ORACLE_HOME }}/network/admin/tnsnames.ora"
'''

# In this case we do import from local project project sub-directory <project-dir>/module_utils
# While this file is placed in <project-dir>/library
# No colletions are used
#try:
#    from ansible.module_utils.dotora import *
#except:
#    pass

# In this case we do import from collections
try:
    from ansible_collections.ibre5041.ansible_oracle_modules.plugins.module_utils.dotora import *
except:
    pass

from ansible.module_utils.basic import *

import sys
import os
import getopt
import tempfile
import unittest


def write_changes(module, content, dest):
    tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
    with os.fdopen(tmpfd, 'wb') as f:
        f.write(to_bytes(content))

    module.atomic_move(tmpfile,
                       to_native(os.path.realpath(to_bytes(dest, errors='surrogate_or_strict')), errors='surrogate_or_strict'),
                       unsafe_writes=True) #


# Ansible code
def main():
    module = AnsibleModule(
        argument_spec = dict(
            path        = dict(required=True),
            follow      = dict(default=True, required=False),
            backup      = dict(type='bool', default=True), # inherited from add_file_common_args
            state       = dict(default="present", choices=["present", "absent"]),
            alias       = dict(required=True),
            whole_value = dict(required=False),
            attribute_path  = dict(required=False),
            attribute_name  = dict(required=False),
            attribute_value = dict(required=False),
        ),
        #add_file_common_args=True,
        supports_check_mode=True,
        mutually_exclusive=[['whole_value', 'attribute_path', 'attribute_name']]
    )
    
    #if module._verbosity >= 3:
    #    module.exit_json(changed=True, debug=module.params)

    whole_value     = module.params['whole_value']
    attribute_value = module.params['attribute_value']
    attribute_path  = module.params['attribute_path']
    attribute_name  = module.params['attribute_name']

    # Preparation
    facts = {}

    filename = module.params["path"]
    alias = module.params['alias']
    state = module.params['state']

    if module.params["follow"]:
        while os.path.islink(filename):
            filename = os.readlink(filename)

    with open(filename, "r") as file:
        old_content = file.read()
        
    orafile = DotOraFile(filename)

    if state == 'present':
        if whole_value:
            orafile.upsertalias(alias, whole_value)
        elif attribute_name:
            orafile.setparamvalue(alias, attribute_name, attribute_value)
        elif attribute_path:
            orafile.upsertaliasatribute(alias, attribute_path, attribute_value)
    elif state == 'absent':
        if whole_value:
            module.fail_json(msg="Combination state: present and whole_value is not allowed")
        elif attribute_path:
            orafile.deleteparampath(alias, attribute_path)
        elif attribute_name:
            orafile.deleteparam(alias, attribute_name)
        elif not attribute_name and not attribute_path and not whole_value:
            orafile.removealias(alias)
        else:
            module.fail_json(msg="Combination of parameter not allowed")


    try:
        param = next(p for p in orafile.params if p.name and p.name.casefold() == alias.casefold())
        alias_value = param.valuesstr()
    except StopIteration:
        alias_value = ''

    new_content = str(orafile)
    changed = bool(old_content != new_content and orafile.changed)
    if changed:
        if module.params['backup']:
            backup_file = module.backup_local(filename)
        write_changes(module, new_content, filename)
        
    # Output
    for line in orafile.warn:
        module.warn(line)
    module.exit_json(msg="{}={}".format(alias, alias_value), changed=changed, ansible_facts=facts)


if __name__ == '__main__':
    main()
