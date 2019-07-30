ansible-role-security
=========

NetApp security hardening configuration as defined by ELEM-6014

Requirements
------------

None

Role Variables
--------------

None

Dependencies
------------

None

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

```ansible
---
- hosts: testhost01.one.den.solidfire.net
  become: true
  vars:
    ansible_user: solidfire
    gather_facts: true
  roles:
    - { role: 'ansible-role-security', tags: 'ansible-role-security'}
```

Testing
----------------

Testing this module is done via [molecule](https://github.com/ansible/molecule)

1. Download & install virtualenv (to run testing in a virtualized python environment)

```bash
pip install -U virtualenv
echo  'export WORKON_HOME=~/Envs' >> ~/.bash_profile
mkdir -p ~/Envs
echo  'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bash_profile
mkvirtualenv security-testing
```  

2. Now we can install the required pip modules to test this module

```bash
(security-testing)$ pip install ansible
(security-testing)$ pip install git+https://github.com/ansible/molecule
```

2. Run the tests

```bash
(security-testing)$ cd ansible-role-security/
(security-testing)$ molecule test
```

The tests should run and you should see no errors! When developing against this module please run these tests before committing changes to ensure all tests pass.

License
-------

BSD  

Author Information
------------------

Julian Barnett (julianb@netapp.com)
