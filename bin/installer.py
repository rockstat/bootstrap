#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Установщик rockstat.

==================================================================
Что умеет делать:
* Выкачиывать или обновлять git репозиторий Rockstat bootstrap
* Готовить inventory файл для anbisble (диалог с пользователем, чтобы получить параметры)
* Готовить файл htpasswd с логинами и паролями для nginx (тоже диалог с пользователем)
* Собственно главная задача - запускать ansible
* Если запускается не первый раз - забирает текущие параметры из inventory и htpasswd, с опциональной возможностью
    их поменять. Можно не менять, просто ещё раз перезапустить ansible
* Отправлять лог работы на http сервер в случае ошибки

==================================================================

Этот скрипт запускается из баш-скрипта, в котором остаётся:
* Setting language params - если локали кривые, сам питон может не запуститься
* sudo apt-get -q -y update
* sudo apt-get -q -y install python-minimal python-pip python-netaddr git locales openssl
* sudo -H pip install setuptools
* sudo -H pip install ansible==2.4.4.0
* sudo -H pip install prompt_toolkit
* sudo -H pip install validators
* sudo -H pip install requests
"""

import os
import sys
import yaml
import copy
import json
import socket
import logging
import getpass
import datetime
import requests
import tempfile
import itertools
import threading
import validators
import subprocess
from collections import namedtuple, OrderedDict

import prompt_toolkit
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from prompt_toolkit.shortcuts import print_tokens

from ConfigParser import ConfigParser


#  TODO: написать хелп
HelpString = """
Write some help here...
"""


class HardcodedData:
    INSTALL_DIR = '/srv/platform'
    REPO_SRC = 'https://github.com/rockstat/bootstrap'
    FAIL_REPORT_URL = 'https://bolt.rstat.org/upload'
    STATIC_STATE_PATH = '/etc/openap/config.yml'
    ROOT_PLAYBOOK_NAME = 'platform.yml'
    RELATIVE_BOOTSTRAP_PATH = 'bootstrap'
    RELATIVE_DEFAULT_INVENTORY_PATH = os.path.join(RELATIVE_BOOTSTRAP_PATH, 'inventory', 'private')
    RELATIVE_GIT_PATH = os.path.join(RELATIVE_BOOTSTRAP_PATH, '.git')
    RELATIVE_HTPASSWD_PATH = os.path.join(RELATIVE_BOOTSTRAP_PATH, 'files', '.htpasswd.tools')
    RELATIVE_USERSYAML_PATH = os.path.join(RELATIVE_BOOTSTRAP_PATH, 'files', 'users.yml')

    def __init__(self):
        pass


class Styles:
    TextAndColor = namedtuple('TextAndColor', ['text', 'color'])

    Separator = '--------------------------------------------------------'

    MenuKeyColor = '#00EEEE'
    PromptColor = '#00EEEE'
    WarningColor = '#EE00EE'
    ErrorColor = '#EE0000'
    SuccessColor = '#00EE00'
    InfoColor = '#808080'

    AskLongStringPrompt = TextAndColor(text='|> ', color=PromptColor)
    AskPasswordPrompt = TextAndColor(text='|> ', color=PromptColor)
    AskShortStringPrompt = TextAndColor(text='?> ', color=PromptColor)
    AskYesNoPrompt = TextAndColor(text='?> ', color=PromptColor)
    WarningMark = TextAndColor(text='>> ', color=WarningColor)
    InfoMark = TextAndColor(text='>> ', color=InfoColor)
    SuccessMark = TextAndColor(text='>> ', color=SuccessColor)
    SuccessMessage = 'Great Success!'

    def __init__(self):
        pass


class Helpers:
    ProcessOutput = namedtuple('ProcessOutput', ['retcode', 'output'])
    ALLOWED_IDENTIFIER_SYMBOLS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'

    def __init__(self):
        pass

    @staticmethod
    def setup_log(output_filename):
        logging.basicConfig(level=logging.INFO)
        file_handler = logging.FileHandler(output_filename)
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s]: %(message)s'))
        logging.getLogger().handlers = [file_handler]

    @staticmethod
    def flush_log():
        for h in logging.getLogger().handlers:
            h.flush()

    @staticmethod
    def run_process(cmd, workdir='.', throwing=True,
                    store_output=False, log_output=True,
                    stdin=None, output_line_handler=None):
        log = logging.getLogger('subprocess')

        if log_output:
            log.info("EXECUTING: '{cmd}' in '{wd}'".format(cmd=cmd, wd=os.path.realpath(workdir)))

        proc = subprocess.Popen(cmd, shell=True, cwd=workdir,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE if stdin else None)

        def write_stdin():
            proc.stdin.write(stdin)
            proc.stdin.close()

        write_thread = threading.Thread(target=write_stdin) if stdin else None
        if write_thread:
            write_thread.start()

        output_lines = []
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            if log_output:
                log.info(line.strip())
            if store_output:
                output_lines.append(line)
            if output_line_handler:
                output_line_handler(line.strip())

        if write_thread:
            write_thread.join()

        rc = proc.wait()
        if throwing and rc:
            raise RuntimeError("error of command '{}': returncode = {}".format(cmd, rc))

        return Helpers.ProcessOutput(retcode=rc, output=''.join(output_lines))

    @staticmethod
    def send_report(temp_files):
        def upload_file(input_filename):
            if not os.path.exists(input_filename):
                Helpers.colored_print('could not send file {} to report server: '
                                      'file does not exist'.format(input_filename), Styles.ErrorColor)
                return

            with open(input_filename) as f:
                resp = requests.post(url=HardcodedData.FAIL_REPORT_URL, files={'log': f})
                if resp.status_code != 200:
                    raise RuntimeError('bad status_code from upload server: {}'.format(resp.status_code))

        try:
            upload_file(temp_files.log)
            pass

        except Exception as e:
            Helpers.colored_print('\n\ncould not upload error report: {}'.format(e), Styles.ErrorColor)

    @staticmethod
    def strip_lines(s):
        return '\n'.join((line.strip() for line in str(s).split('\n')))

    @staticmethod
    def assert_root():
        return getpass.getuser() == 'root'

    @staticmethod
    def mkdir_if_not_exists(dirname):
        if not os.path.isdir(dirname):
            logging.getLogger().info('creating dir: {}'.format(dirname))
            os.makedirs(dirname)

    @staticmethod
    def validate_identifier(val):
        if val.startswith('_') or val.startswith('-'):
            return False

        for c in val:
            if c not in Helpers.ALLOWED_IDENTIFIER_SYMBOLS:
                return False

        return True

    @staticmethod
    def print_with_mark(mark, text):
        print_tokens(
            tokens=[
                (Token.Mark, mark.text),
                (Token.Text, text + '\n'),
            ],
            style=style_from_dict({Token.Mark: mark.color})
        )

    @staticmethod
    def print_success():
        Helpers.print_with_mark(Styles.SuccessMark, Styles.SuccessMessage)
        print

    @staticmethod
    def colored_print(text, color):
        print_tokens(tokens=[(Token.Text, text + '\n')], style=style_from_dict({Token.Text: color}))

    @staticmethod
    def check_ascii(text):
        try:
            text.encode('ascii')
            return True
        except (Exception, OSError):
            return False


class Prompter:
    def __init__(self):
        pass

    @staticmethod
    def ask_string(msg, default=None, validate_func=None, short_mode=False, force_lower=False):
        while True:
            if short_mode:
                print
                sys.stdout.write(msg + ' ')
                res = prompt_toolkit.prompt(
                    message=unicode(Styles.AskShortStringPrompt.text),
                    style=style_from_dict({Token: Styles.AskShortStringPrompt.color}),
                    default=unicode(default) if default else u'',
                )
                print
            else:
                print '\n' + msg + '\n'
                res = prompt_toolkit.prompt(
                    message=unicode(Styles.AskLongStringPrompt.text),
                    style=style_from_dict({Token: Styles.AskLongStringPrompt.color}),
                    default=unicode(default) if default else u'',
                )
                print

            if force_lower:
                res = res.lower()

            if validate_func:
                validate_res = validate_func(res)
                if not isinstance(validate_res, bool) or not validate_res:
                    Helpers.print_with_mark(Styles.WarningMark, str(validate_res))
                    print
                    continue

            break

        return res

    @staticmethod
    def ask_yes_no(msg, default=True):
        yn = 'Y/n' if default else 'y/N'
        while True:
            print
            sys.stdout.write('{msg} ({yn}) '.format(msg=msg, yn=yn))
            res = prompt_toolkit.prompt(
                message=unicode(Styles.AskYesNoPrompt.text),
                style=style_from_dict({Token: Styles.AskYesNoPrompt.color}),
            ).lower()
            print

            if not res:
                return bool(default)

            if res not in ('y', 'n'):
                continue

            return res == 'y'

    @staticmethod
    def is_it_correct(default=True):
        return Prompter.ask_yes_no('Is it correct?', default=default)

    @staticmethod
    def ask_password(msg):
        while True:
            print '\n' + msg + '\n'
            res1 = prompt_toolkit.prompt(
                message=unicode(Styles.AskPasswordPrompt.text), is_password=True,
                style=style_from_dict({Token: Styles.AskPasswordPrompt.color}),
            )

            if not res1 or not Helpers.check_ascii(res1):
                print
                Helpers.print_with_mark(Styles.WarningMark, 'invalid password: it should be non-empty '
                                                            'with only ascii symbols')
                continue

            print '\n' + 'Confirm it' + '\n'
            res2 = prompt_toolkit.prompt(
                message=unicode(Styles.AskPasswordPrompt.text), is_password=True,
                style=style_from_dict({Token: Styles.AskPasswordPrompt.color}),
            )

            if res1 != res2:
                print
                Helpers.print_with_mark(Styles.WarningMark, 'passwords dont match')
                continue

            print
            return res1


class Menu:
    class Item:
        def __init__(self, key, name, handler):
            self.key = key
            self.name = name
            self.handler = handler

        def __len__(self):
            return len(self.name) + len(self.key) + 2

    class Column:
        def __init__(self, indent):
            self.indent = indent
            self.maxlen = 0

        def add(self, item):
            if len(item) > self.maxlen:
                self.maxlen = len(item)

        def __len__(self):
            return self.maxlen + self.indent

        def __gt__(self, other):
            return len(self) > len(other)

        def __eq__(self, other):
            return len(self) == len(other)

    def __init__(self, name, items, ncolumns=4, indent=5):
        self.name = name
        self.items = items
        self.ncolumns = ncolumns
        self.indent = indent
        self.columns = self.make_columns()

    def make_columns(self):
        columns = [self.Column(self.indent) for _ in xrange(self.ncolumns)]
        for n, item in enumerate(self.items):
            columns[n % self.ncolumns].add(item)
        return columns

    def print_menu(self):
        print self.name
        print Styles.Separator

        for n, item in enumerate(self.items):
            ncol = n % self.ncolumns
            column = self.columns[ncol]
            if ncol != self.ncolumns - 1:
                after = ' ' * (len(column) - len(item))
            else:
                after = '\n'

            print_tokens(
                tokens=[
                    (Token.Key, '({})'.format(item.key)),
                    (Token.Name, item.name + after),
                ],
                style=style_from_dict({Token.Key: Styles.MenuKeyColor})
            )

        if len(self.items) % self.ncolumns != 0:
            print

        sys.stdout.flush()

    def run(self):
        items_dict = {item.key: item for item in self.items}

        def validate_key(val):
            if val in items_dict:
                return True
            return 'invalid key'

        while True:
            self.print_menu()
            key = Prompter().ask_string('Press key:', validate_func=validate_key, short_mode=True, force_lower=True)
            item = items_dict[key]
            if not item.handler():
                break

    @classmethod
    def adjust_menus_columns(cls, menus):
        merged_columns = [
            max(columns)
            for columns in itertools.izip_longest(*[m.columns for m in menus], fillvalue=cls.Column(indent=0))
        ]
        for m in menus:
            m.columns = copy.deepcopy(merged_columns[0:len(m.columns)])


class Ansible:
    def __init__(self, static_state):
        self.log = logging.getLogger('ansible')
        self.homedir = static_state.install_dir()
        self.bootstrap_dir = os.path.join(self.homedir, HardcodedData.RELATIVE_BOOTSTRAP_PATH)
        self.default_inventory_path = os.path.join(self.homedir, HardcodedData.RELATIVE_DEFAULT_INVENTORY_PATH)

    def try_load_default_inventory(self):
        def safe_get(config, sect, opt):
            if not config.has_section(sect):
                return
            if not config.has_option(sect, opt):
                return
            return config.get(sect, opt)

        def validate_inventory_conf(invconf):
            if not invconf.has_section('private') or len(invconf.items('private')) != 1:
                return False
            if len(invconf.items('private')[0][0].split(' ')) < 2:
                return False
            if not safe_get(invconf, 'private:vars', 'tracker_domain'):
                return False
            if not safe_get(invconf, 'private:vars', 'contact_email'):
                return False
            return True

        if not os.path.exists(self.default_inventory_path):
            self.log.warn('could not load default ansible inventory: inventory does not exist')
            return

        conf = ConfigParser(allow_no_value=True)
        conf.read(self.default_inventory_path)
        if not validate_inventory_conf(conf):
            self.log.warn('could not load default ansible inventory: config verification fail, '
                          'probably it was changed manually')
            return

        return {
            'hostname': conf.items('private')[0][0].split(' ')[0],
            'domain': safe_get(conf, 'private:vars', 'tracker_domain'),
            'email': safe_get(conf, 'private:vars', 'contact_email'),
        }
    
    @staticmethod
    def generate_default_inventory(args):
        if not args:
            raise RuntimeError('logic error: trying to generate_default_inventory without necessary args')

        inventory_template = Helpers.strip_lines(
            """[private]
               {hostname} ansible_host={domain} contact_email={email}
               
               [private:vars]
               tracker_domain={domain}
               contact_email={email}

               [rockstat]
               {hostname}

            """
        )
        return inventory_template.format(**args)

    def write_default_inventory(self, args):
        Helpers.mkdir_if_not_exists(os.path.dirname(self.default_inventory_path))
        data = self.generate_default_inventory(args)
        self.log.info('writing default ansible inventory to {}:\n{}'.format(self.default_inventory_path, data))
        with open(self.default_inventory_path, 'w') as f:
            f.write(data)

    def run(self):
        print 'Starting ansible...\n'
        self.log.info('starting ansible')

        def on_line(line):
            try:
                data = json.loads(line)
                name = data['name']
                if name:
                    Helpers.print_with_mark(Styles.InfoMark, name)
                    print

                failed = data['result'].get('failed')
                if failed:
                    print
                    msg = data['result'].get('msg')
                    Helpers.colored_print('{} failed: {}'.format(name, msg), Styles.ErrorColor)
                    print

            except (Exception, OSError):
                print line.strip()

        cmd = 'ANSIBLE_STDOUT_CALLBACK=json_cb ' \
              'ansible-playbook {} --connection=local'.format(HardcodedData.ROOT_PLAYBOOK_NAME)
        Helpers.run_process(cmd=cmd, workdir=self.bootstrap_dir, output_line_handler=on_line)

    def install_roles(self):
        print '>>> Updating ansible roles...\n'
        Helpers.run_process('ansible-galaxy install -r install_roles.yml --force', workdir=self.bootstrap_dir)


class Configurator:
    class Param:
        def __init__(self, descr, validate_func):
            self.descr = descr
            self.validate_func = validate_func
            self.value = None

        def ask(self):
            self.value = Prompter().ask_string(
                msg='Enter {}'.format(self.descr),
                default=str(self.value) if self.value is not None else '',
                validate_func=self.validate_func,
            )

    def __init__(self, static_state, ansible):
        self.log = logging.getLogger('configurator')
        self.ansible = ansible
        self.params = OrderedDict()
        self.init_params()
        self.changed = False
        # were check install is complete
        # if static_state.is_installed():
        self.try_restore_params()

    def init_params(self):
        self.params['domain'] = self.Param('dns name which will be used as tracker domain. Example: stat.yoursite.com',
                                           validate_func=self.validate_domain)
        self.params['hostname'] = self.Param('internal server hostname. Example: mystat',
                                             validate_func=self.validate_hostname)
        self.params['email'] = self.Param('email to receive notifications about SSL certificate expiration. '
                                          'Example: foo@bar.com',
                                          validate_func=self.validate_email)

    def print_params(self):
        print
        for name, p in self.params.iteritems():
            print '{}: {}'.format(name, p.value)
        print

    def ask(self):
        self.log.info('ask user for params')

        print 'Domain configuration'
        print Styles.Separator
        self.changed = True
        while True:
            for p in self.params.values():
                p.ask()

            print 'Your input:'
            self.print_params()

            if Prompter().is_it_correct():
                Helpers.print_success()
                break

    def save_if_changed(self):
        if not self.changed:
            self.log.info('configuration was not changed -> skip saving')
            return

        self.log.info('saving configuration')
        print 'Saving configuration...\n'

        self.ansible.write_default_inventory({
            'hostname': self.hostname,
            'domain': self.domain,
            'email': self.email,
        })

    def has_missed_params(self):
        for p in self.params.values():
            if p.value is None:
                return True
        return False

    def try_restore_params(self):
        existing_params = self.ansible.try_load_default_inventory()
        if not existing_params:
            return False

        for pname in ('domain', 'hostname', 'email'):
            self.params[pname].value = existing_params[pname]

        self.log.info('parameters restored from already installed data')
        return True

    @staticmethod
    def validate_domain(val):
        if val and validators.domain(val):
            return True
        return 'Invalid domain. Example of valid domain: stat.yoursite.com'

    @staticmethod
    def validate_hostname(val):
        if val and Helpers.validate_identifier(val):
            return True
        return 'Invalid hostname. Only letters, digits and symbols "_", "-" (not first) are allowed'

    @staticmethod
    def validate_email(val):
        if val and validators.email(val):
            return True
        return 'Invalid email. Example of valid email: foo@bar.com'

    @property
    def domain(self):
        return self.params['domain'].value or ''

    @property
    def hostname(self):
        return self.params['hostname'].value or ''

    @property
    def email(self):
        return self.params['email'].value or ''


class UserAccounts:
    class User:
        def __init__(self, name, descr, encrypted_password):
            self.name = name
            self.descr = descr
            self.encrypted_password = encrypted_password

        def __repr__(self):
            return '{name}{descr}'.format(
                name=self.name,
                descr=" | {}".format(self.descr) if self.descr else ''
            )

        def make_htpasswd_record(self):
            return '{comment}{name}:{password}\n'.format(
                comment="# {}\n".format(self.descr) if self.descr else '',
                name=self.name,
                password=self.encrypted_password,
            )

        @staticmethod
        def encrypt_password(password):
            return Helpers.run_process(
                cmd='openssl passwd -apr1 -stdin 2>/dev/null',
                stdin=password,
                store_output=True,
                log_output=False,
            ).output

        @classmethod
        def ask_to_create(cls):
            def validate_user_name(val):
                if val and Helpers.validate_identifier(val):
                    return True
                return 'Invalid user name. Only letters, digits and symbols "_", "-" (not first) are allowed'

            def validate_descr(val):
                if Helpers.check_ascii(val):
                    return True
                return 'Invalid description. Only latin allowed'

            name = Prompter().ask_string('Enter new user name. Example: myuser', validate_func=validate_user_name)
            descr = Prompter().ask_string('Enter new user description or leave empty', validate_func=validate_descr)
            encrypted_password = cls.encrypt_password(Prompter().ask_password('Enter new user password'))
            return cls(name=name, descr=descr, encrypted_password=encrypted_password)

    def __init__(self, static_state):
        self.log = logging.getLogger('users')
        self.static_state = static_state
        self.htpasswd_path = os.path.join(static_state.install_dir(), HardcodedData.RELATIVE_HTPASSWD_PATH)
        self.usersyaml_path = os.path.join(static_state.install_dir(), HardcodedData.RELATIVE_USERSYAML_PATH)
        self.data = OrderedDict()
        self.load()
        self.menu = Menu('Users management', [
            Menu.Item(key='l', name='list users', handler=self.handler_list_users),
            Menu.Item(key='c', name='create new user', handler=self.handler_create_user),
            Menu.Item(key='r', name='remove user', handler=self.handler_remove_user),
            Menu.Item(key='m', name='return to the main menu', handler=self.handler_return_back),
        ])
        self.changed = False

    def ask(self):
        self.log.info('ask user for users accounts')
        self.changed = True
        self.menu.run()

    def handler_list_users(self):
        print

        if not self.data:
            Helpers.print_with_mark(Styles.WarningMark, 'No users')
            print
            return True

        for n, user in enumerate(self.data.values()):
            print '{}. {}'.format(n, user)
        print
        return True

    def handler_create_user(self):
        user = self.User.ask_to_create()
        if user.name in self.data:
            Helpers.print_with_mark(Styles.WarningMark, 'user {} already exists'.format(user.name))
            return True

        self.data[user.name] = user
        Helpers.print_success()
        return True

    def handler_remove_user(self):
        if not self.data:
            Helpers.print_with_mark(Styles.WarningMark, 'There are not any users')
            return True

        def validate_user_id(val):
            try:
                if int(val) in range(0, len(self.data)):
                    return True
                raise ValueError
            except (Exception, ValueError):
                return 'invalid user number. Choose between {} - {}'.format(0, len(self.data) - 1)

        self.handler_list_users()
        choosen_id = int(Prompter().ask_string('Which one?', validate_func=validate_user_id, short_mode=True))

        name = self.data.items()[choosen_id][0]
        del self.data[name]

        Helpers.print_success()
        return True

    @staticmethod
    def handler_return_back():
        return False

    def load(self):
        if not os.path.exists(self.htpasswd_path):
            self.log.info('there is no file {} -> skip restoring users accounts'.format(self.htpasswd_path))
            return

        with open(self.htpasswd_path) as f:
            last_descr = None
            for line in f:
                line = line.strip()
                if not line:
                    continue

                fields = line.split(':')
                if len(fields) >= 2:
                    self.data[fields[0]] = self.User(
                        name=fields[0],
                        descr=last_descr,
                        encrypted_password=''.join(fields[1:])
                    )

                if line.startswith('#'):
                    last_descr = line[1:].strip()
                else:
                    last_descr = None

        self.log.info('user accounts restored from {}'.format(self.htpasswd_path))

    def save_if_changed(self):
        if not self.changed:
            self.log.info('User accounts was not changed -> skip saving')
            return

        self.log.info('Saving user accounts to {}'.format(self.htpasswd_path))
        print 'Saving user accounts...\n'

        Helpers.mkdir_if_not_exists(os.path.dirname(self.htpasswd_path))
        with open(self.htpasswd_path, 'w') as f:
            f.write('\n'.join((user.make_htpasswd_record() for user in self.data.values())))
        with open(self.usersyaml_path, 'w') as f:
            pairs = dict()
            for user in self.data.values():
                pairs[user.name] = user.encrypted_password
            f.write(yaml.dump(pairs))
            

class Git:
    def __init__(self, static_state):
        self.log = logging.getLogger('git')
        self.homedir = static_state.install_dir()
        self.bootstrap_path = os.path.join(self.homedir, HardcodedData.RELATIVE_BOOTSTRAP_PATH)
        self.git_path = os.path.join(self.homedir, HardcodedData.RELATIVE_GIT_PATH)
        self.reposrc = HardcodedData.REPO_SRC

    def install_repo(self):
        self.log.info('updating repo from {}'.format(self.reposrc))

        print 'Updating git repository...'
        print

        if not os.path.isdir(self.git_path):
            self.log.info('cloning git repo from scratch')
            Helpers.run_process('git clone "{}" "{}"'.format(self.reposrc, self.bootstrap_path))
        else:
            self.log.info('updating existing git repo')
            Helpers.run_process('git pull --rebase', workdir=self.bootstrap_path)
        
        rev = Helpers.run_process('git rev-parse --short HEAD',
                                  workdir=self.bootstrap_path,
                                  store_output=True).output.strip()
        Helpers.print_with_mark(Styles.InfoMark, 'updated to {}'.format(rev))
        self.log.info('at revision {}'.format(rev))
        print


class StaticState:
    def __init__(self):
        self.log = logging.getLogger('static_state')
        self.data = dict()
        self.load()

    def load(self):
        if not os.path.exists(HardcodedData.STATIC_STATE_PATH):
            self.log.info('there is no file {} -> skip loading static state'.format(HardcodedData.STATIC_STATE_PATH))
            return

        res = yaml.load(open(HardcodedData.STATIC_STATE_PATH)) or dict()
        install_dir = res.get('install_homedir')

        if not install_dir or not os.path.isdir(install_dir):
            self.log.warn('cannot load static state from {}: no install_dir'.format(HardcodedData.STATIC_STATE_PATH))
            return

        self.log.info('loaded from {}'.format(HardcodedData.STATIC_STATE_PATH))
        self.data = res

    def save(self):
        Helpers.mkdir_if_not_exists(os.path.dirname(HardcodedData.STATIC_STATE_PATH))
        with open(HardcodedData.STATIC_STATE_PATH, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)
        self.log.info('static state saved to {}'.format(HardcodedData.STATIC_STATE_PATH))

    def is_installed(self):
        if not self.data:
            return
        return str(self.data.get('install_success', '0')) == '1'

    def set_installed(self):
        self.log.info('set installed')
        self.data['install_success'] = 1
        self.data['install_homedir'] = HardcodedData.INSTALL_DIR
        self.save()

    def install_dir(self):
        return self.data.get('install_homedir', HardcodedData.INSTALL_DIR)


class TempFiles:
    def __init__(self):
        self.log = os.path.join(
            tempfile.gettempdir(),
            'rockstat_install_{hostname}_UTC_{now}.log'.format(
                hostname=socket.gethostname(),
                now=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            )
        )

        with open(self.log, 'w'):
            pass

        self.clean_on_exit = True

    def clean(self):
        os.remove(self.log)

    def dont_clean(self):
        self.clean_on_exit = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.clean_on_exit:
            self.clean()


class Installer:
    def __init__(self, temp_files):
        self.log = logging.getLogger('main')
        self.temp_files = temp_files
        self.static_state = StaticState()
        self.git = Git(self.static_state)
        self.ansible = Ansible(self.static_state)
        self.configurator = Configurator(self.static_state, self.ansible)
        self.users_accounts = UserAccounts(self.static_state)
        self.main_menu = Menu('Main menu', [
            Menu.Item(key='u', name='users management', handler=self.handler_users_management),
            Menu.Item(key='s', name='save configuration', handler=self.handler_save_configuration),
            Menu.Item(key='d', name='domain settings', handler=self.handler_domain_settings),
            Menu.Item(key='h', name='help', handler=self.handler_help),
            Menu.Item(key='i', name='install', handler=self.handler_install),
            Menu.Item(key='q', name='quit', handler=self.handler_quit),
        ])
        Menu.adjust_menus_columns([self.main_menu, self.users_accounts.menu])

    def run(self):
        self.log.info('run')

        print Styles.Separator
        print 'Welcome to Rockstat platform v3 configurator'
        print Styles.Separator

        Helpers.mkdir_if_not_exists(HardcodedData.INSTALL_DIR)
        self.git.install_repo()

        if self.configurator.has_missed_params():
            self.log.info('It seems it is first run -> ask user for params before menu')
            self.handler_domain_settings()

        self.main_menu.run()
        self.log.info('finished.')

    def handler_domain_settings(self):
        self.configurator.ask()
        return True

    def handler_users_management(self):
        self.users_accounts.ask()
        return True

    def handler_save_configuration(self):
        self.configurator.save_if_changed()
        self.users_accounts.save_if_changed()
        return True

    def handler_install(self):
        self.handler_save_configuration()
        self.ansible.install_roles()
        self.ansible.run()
        self.static_state.set_installed()
        print 'Installation completed.\n'
        self.log.info('Installation completed.')
        return False

    @staticmethod
    def handler_help():
        print HelpString
        return True

    @staticmethod
    def handler_quit():
        print 'good bye'
        return False


def main():
    if not Helpers.assert_root():
        print 'installation may be launched only by root'
        sys.exit(1)

    temp_files = TempFiles()
    Helpers.setup_log(temp_files.log)
    log = logging.getLogger()
    with temp_files:
        try:
            Installer(temp_files).run()
            return 0

        except (KeyboardInterrupt, EOFError):
            print 'Installation cancelled'
            return 1

        except (Exception, OSError) as e:
            temp_files.dont_clean()
            print "\n\n\n\n"

            msg = '*********Install error!*********\n' \
                  'What: {what}\n' \
                  'Log saved to {logpath} and report will be sent'.format(what=str(e), logpath=temp_files.log)
            Helpers.colored_print(msg, Styles.ErrorColor)

            log.exception(msg)
            Helpers.flush_log()
            Helpers.send_report(temp_files)
            return 1


if __name__ == "__main__":
    sys.exit(int(main() or 0))
