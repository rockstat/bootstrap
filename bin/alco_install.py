#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
Установщик alcolytics.

==================================================================
Что умеет делать:
* Выкачиывать или обновлять git репозиторий alco-bootstrap
* Готовить inventory файл для anbisble (диалог с пользователем, чтобы получить параметры)
* Готовить файл htpasswd с логинами и паролями для nginx (тоже диалог с пользователем)
* Собственно главная задача - запускать ansible
* Если запускается не первый раз - забирает текущие параметры из inventory и htpasswd, с опциональной возможностью
    их поменять. Если пользователь откажется менять, просто перезапустит ansible
* Собирать факты из ansible
* Отправлять лог работы и ansible факты на http сервер в случае ошибки


==================================================================
Логика работы:
В случае первой установки:
* Создаётся /srv/alco и ставится туда git репозиторий
* Спрашиваем у юзера параметры - имя хоста, домен и email
* Показываем общий список параметров + файл инвентаря, и куда он запишется.
    Спрашиваем ОК? Если не ок, возвращаемся на пред. пункт.
* Создаём инвентарь, собираем факты
* Спрашиваем, хотиле ли настроить пользоателей?
    Если да, запускаем диалог настройки пользователей, сохраняем htpasswd
* Запускаем ansible
* Пишем в /etc/openap/config.yml стейт, что установка прошла
* Если где-то упали - отправляем лог и факты на сервер
* Если всё нормально - подчищаем за собой файл лога


В случае повторной установки (если есть уже стейт в конфиге /etc/openap/config.yml и есть /src/alco)
* Обновляется git репозиторий
* Говорим юзеру "уже установлено, хотите поменять инвентарь?"
* Если хочет:
    * Проверяем наличие текущего инвентаря, кол. хостов в ansible (должно быть 1).
         Если проверка не прошла, говорим, что не можем поменять конфигурацию, т.к. вы что-то там правили
    * Загружаем из текущего инвентаря параметры
    * Показываем параметры пользовалелю с возможностью что-то поменять
* Загружаем из текущего htpasswd пользователей, показываем их и говорим "хотели изменить что-то?"
    * Если да - вызываем диалог добавления/удаления пользователей
* Запускаем ansible


==================================================================
Что на текущий момент остаётся в баше:
* Setting language params - если локали кривые, сам питон может не запуститься
* sudo apt-get -q -y update
* sudo apt-get -q -y install python-minimal python-pip python-netaddr git openssl
* sudo -H pip install setuptools
* sudo -H pip install ansible (надо особую версию 2.4 поставить)
* sudo -H pip install prompt_toolkit
"""


import prompt_toolkit
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from prompt_toolkit.shortcuts import print_tokens

import argparse
import os
from collections import namedtuple
import subprocess
import logging
import sys

import tempfile

import requests
import socket
import datetime
import yaml
import re
from collections import OrderedDict

from ConfigParser import ConfigParser
import fnmatch
import getpass


class HardcodedData:
    INSTALL_DIR = '/srv/alco'
    REPO_SRC = 'https://github.com/alcolytics/alco-bootstrap'
    # TODO поменять адрес FAIL_REPORT_URL на реальный, добавить логин-пароль
    FAIL_REPORT_URL = 'https://x1.vtest.alcolytics.ru/install_fails_reports'
    STATIC_STATE_PATH = '/etc/openap/config.yml'
    ROOT_PLAYBOOK_NAME = 'alcolytics.yml'
    RELATIVE_BOOTSTRAP_PATH = 'alco-bootstrap'
    RELATIVE_DEFAULT_INVENTORY_PATH = os.path.join(RELATIVE_BOOTSTRAP_PATH, 'inventory', 'private')
    RELATIVE_GIT_PATH = os.path.join(RELATIVE_BOOTSTRAP_PATH, '.git')
    RELATIVE_HTPASSWD_PATH = os.path.join(RELATIVE_BOOTSTRAP_PATH, 'files', '.htpasswd.tools')
    PARAM_COLOR = '#88EE88'

    def __init__(self):
        pass


class Helpers:
    ProcessOutput = namedtuple('ProcessOutput', ['retcode', 'output'])
    RootPassword = ''

    def __init__(self):
        pass

    @staticmethod
    def setup_log(output_filename):
        class CustomLogHandler(logging.Handler):
            def __init__(self, outfile):
                logging.Handler.__init__(self)

                self.console_handler = logging.StreamHandler(sys.stdout)
                self.file_handler = logging.FileHandler(outfile)

                self.console_handler.setFormatter(logging.Formatter('%(message)s'))
                self.file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"))

            def emit(self, record):
                self.file_handler.emit(record)
                if record.name != 'quiet':
                    self.console_handler.emit(record)

            def flush(self):
                self.console_handler.flush()
                self.file_handler.flush()

        logging.basicConfig(level=logging.INFO)
        handler = CustomLogHandler(output_filename)
        logging.getLogger().handlers = [handler]

    @staticmethod
    def flush_log():
        for h in logging.getLogger().handlers:
            h.flush()

    @classmethod
    def ask_root_password(cls):
        def validate_root_password(p):
            return bool(Helpers.run_process(cmd='echo test',
                                            as_root=True,
                                            root_password=p,
                                            throwing=False).retcode == 0)

        log = logging.getLogger()
        need_root_password = bool(Helpers.run_process('sudo -k -n echo test', throwing=False).retcode != 0)
        if not need_root_password:
            log.info('root password is not required')
            cls.RootPassword = ''
            return

        cls.RootPassword = Prompter().prompt_password('Enter root password', validate_func=validate_root_password)

    @classmethod
    def get_root_password(cls):
        return cls.RootPassword

    @staticmethod
    def run_process(cmd,
                    workdir='.',
                    throwing=True,
                    store_output=False,
                    as_root=False,
                    root_password=None,
                    log_output=True):
        main_log = logging.getLogger()
        output_log = logging.getLogger('PROCESS OUT')

        execstyle = 'EXECUTING' if not as_root else 'EXECUTING AS ROOT'
        if log_output:
            main_log.info("{execstyle}: '{cmd}' in '{wd}'".format(execstyle=execstyle,
                                                                  cmd=cmd,
                                                                  wd=os.path.realpath(workdir)))
        if not as_root:
            actual_cmd = cmd
        else:
            password = root_password or Helpers.get_root_password()
            actual_cmd = 'echo "{password}" | sudo -p "" -S {cmd}'.format(password=password, cmd=cmd)

        proc = subprocess.Popen(actual_cmd, shell=True, cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        output_lines = []
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            if log_output:
                output_log.info(line.strip())
            if store_output:
                output_lines.append(line)

        rc = proc.wait()
        if throwing and rc:
            raise RuntimeError("error of command '{}': returncode = {}".format(cmd, rc))
        return Helpers.ProcessOutput(retcode=rc, output=''.join(output_lines))

    @staticmethod
    def send_report(temp_files):
        def upload_file(input_filename, upload_filename):
            if not os.path.exists(input_filename):
                print 'could not send file {} to report server: file does not exist'.format(input_filename)
                return

            with open(input_filename) as f:
                resp = requests.put(url=os.path.join(HardcodedData.FAIL_REPORT_URL, upload_filename), data=f)
                if resp.status_code != 201:
                    raise RuntimeError('bad status_code from upload server: {}'.format(resp.status_code))

        try:
            prefix = '{}_{}'.format(socket.gethostname(), datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
            upload_file(temp_files.log, '{}_alco_install_log'.format(prefix))
            upload_file(temp_files.facts, '{}_alco_install_facts'.format(prefix))

        except Exception as e:
            print '\n\ncould not upload error report: {}'.format(e)

    @staticmethod
    def strip_lines(s):
        return '\n'.join((line.strip() for line in str(s).split('\n')))

    @staticmethod
    def sudo_touch_and_chown(filename):
        Helpers.run_process('touch "{}"'.format(filename))
        Helpers.run_process('chown {} "{}"'.format(getpass.getuser(), filename))

    @staticmethod
    def sudo_mkdir_and_chown(dirname):
        Helpers.run_process('mkdir -p "{}"'.format(dirname), as_root=True)
        Helpers.run_process('chown -R {} "{}"'.format(getpass.getuser(), dirname), as_root=True)

    @staticmethod
    def assert_root():
        return getpass.getuser() == 'root'

    @staticmethod
    def mkdir_if_not_exists(dirname):
        if not os.path.isdir(dirname):
            os.makedirs(dirname)


class Ansible:
    def __init__(self, homedir):
        self.log = logging.getLogger()
        self.homedir = homedir
        self.bootstrap_dir = os.path.join(homedir, HardcodedData.RELATIVE_BOOTSTRAP_PATH)

    def _has_the_only_host(self):
        res = Helpers.run_process(cmd='ansible-playbook {} --list-hosts'.format(HardcodedData.ROOT_PLAYBOOK_NAME),
                                  workdir=self.bootstrap_dir,
                                  store_output=True,
                                  throwing=False)
        if res.retcode:
            self.log.warn('could not determine ansible hosts count: bad retcode from ansible: {}'.format(res.retcode))
            return False

        matches = 0
        for line in res.output.split('\n'):
            if bool(re.match(r'.*hosts\s*\(1\).*', line)):
                matches += 1
            if matches > 1:
                break

        if matches != 1:
            self.log.warn('ansible has more than 1 host')
            return False

        return True

    def default_inventory_path(self):
        return os.path.join(self.homedir, HardcodedData.RELATIVE_DEFAULT_INVENTORY_PATH)

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

        if not self._has_the_only_host():
            self.log.warn('could not load default ansible inventory: ansible hosts count is undefined')
            return

        if not os.path.exists(self.default_inventory_path()):
            self.log.warn('could not load default ansible inventory: inventory does not exist')
            return

        conf = ConfigParser()
        conf.read(self.default_inventory_path())
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
               {hostname} ansible_host={domain}

               [private:vars]
               tracker_domain={domain}
               contact_email={email}

            """
        )
        return inventory_template.format(
            hostname=args.hostname,
            domain=args.domain,
            email=args.email,
        )

    def write_default_inventory(self, args):
        out_path = self.default_inventory_path()
        Helpers.mkdir_if_not_exists(os.path.dirname(out_path))
        self.log.info('writing default ansible inventory to {}'.format(out_path))
        data = self.generate_default_inventory(args)
        with open(out_path, 'w') as f:
            f.write(data)

    def gather_facts(self, hostname, output_file):
        logging.getLogger().info('Gathering facts about your system')
        Helpers.run_process(
            cmd='ansible {hostname} -m debug --connection=local '
                '-a "var=hostvars|to_nice_yaml" > "{output_file}"'.format(hostname=hostname, output_file=output_file),
            workdir=self.bootstrap_dir
        )

    def run(self):
        self.log.info('starting ansible')
        Helpers.run_process(cmd='ansible-playbook {} --connection=local'.format(HardcodedData.ROOT_PLAYBOOK_NAME),
                            workdir=self.bootstrap_dir)


class Prompter:
    def __init__(self, postfix=':\n> ', color=HardcodedData.PARAM_COLOR):
        self.postfix = unicode(postfix)
        self.quietlog = logging.getLogger('quiet')
        self.log = logging.getLogger()
        self.style = style_from_dict({
            Token: color,
        }) if color else None

    def prompt_string(self, msg, default=None, validate_func=None):
        self.quietlog.info('Ask user: {}'.format(msg))
        all_msg = unicode(msg) + self.postfix
        while True:
            res = prompt_toolkit.prompt(message=all_msg,
                                        default=unicode(default) if default else u'',
                                        style=self.style)

            if not res or (validate_func and not validate_func(res)):
                self.log.info('invalid choice')
                continue

            break

        self.quietlog.info('User answer: {}'.format(res))
        print
        return res

    def prompt_yes_no(self, msg, default=True):
        yn_str = 'Y/n' if default else 'y/N'
        all_msg = u'{}({}){}'.format(unicode(msg), unicode(yn_str), self.postfix)
        self.quietlog.info('Ask user (y/n): {}'.format(msg))
        while True:
            res = prompt_toolkit.prompt(message=all_msg, style=self.style).lower()

            if not res:
                res = 'y' if default else 'n'

            if res in ('y', 'n'):
                break

        self.quietlog.info('User answer: {}'.format(res))
        print
        return res == 'y'

    def prompt_password(self, msg, validate_func=None, need_confirm=False):
        self.quietlog.info('Ask user for password: {}'.format(msg))
        while True:
            all_msg1 = unicode(msg) + self.postfix
            res1 = prompt_toolkit.prompt(message=all_msg1, style=self.style, is_password=True)

            if need_confirm:
                all_msg2 = unicode(msg + '(confirm)') + self.postfix
                res2 = prompt_toolkit.prompt(message=all_msg2, style=self.style, is_password=True)
                if res1 != res2:
                    self.log.info('passwords dont match')
                    continue

            if validate_func and not validate_func(res1):
                self.log.info('invalid password, try again')
                continue
            break
        self.quietlog.info('The user has entered password (not logged because it is private data!)')
        print
        return res1


class UserParamsGetter:
    UserParam = namedtuple('UserParam', ['shortname', 'fullname', 'descr', 'default'])
    AllParams = [
        UserParam(shortname='-n', fullname='hostname',
                  descr='short hostname (installer will change system hostname)',
                  default=''),

        UserParam(shortname='-t', fullname='domain',
                  descr='your tracking domain name (for example alco.txxx.com)',
                  default=''),

        UserParam(shortname='-e', fullname='email',
                  descr='email to receive notifications about SSL certificate expiration',
                  default=''),
    ]

    def __init__(self):
        self.args = self._get_cli_args()
        self.prompter = Prompter()
        self.log = logging.getLogger()
        self.quietlog = logging.getLogger('quiet')

    def _get_cli_args(self):
        parser = argparse.ArgumentParser(description='Alcolytics bootstrap installer')
        for p in self.AllParams:
            parser.add_argument(p.shortname, '--' + p.fullname.replace('_', '-'), help=p.descr, default=p.default)
        return parser.parse_args()

    def _show_params(self):
        style = style_from_dict({
            Token.Param: HardcodedData.PARAM_COLOR,
        })

        data = OrderedDict()
        for p in self.AllParams:
            data[p.descr] = getattr(self.args, p.fullname)

        ansible = Ansible(HardcodedData.INSTALL_DIR)
        data['Ansible inventory'] = 'Will be written to {path}:\n{data}'.format(
            path=ansible.default_inventory_path(),
            data='------------\n{}\n------------'.format(ansible.generate_default_inventory(self.args)),
        )

        self.log.info('Alcolytics will be installed with following options:')
        for key, value in data.iteritems():
            tokens = [
                (Token.Param, '* {}: '.format(key)),
                (Token.Value, value)
            ]
            print_tokens(tokens, style=style)
            print
            self.quietlog.info('* {}: {}'.format(key, value))

    def _prompt_params(self, only_missing):
        for p in self.AllParams:
            current_val = getattr(self.args, p.fullname)
            if not current_val or not only_missing:
                val = self.prompter.prompt_string('Enter {}'.format(p.descr), default=current_val)
                setattr(self.args, p.fullname, val)

    def _restore_missing_params(self, static_state):
        ansible = Ansible(static_state.install_dir())
        params = ansible.try_load_default_inventory()
        if not params:
            return

        for name in ('hostname', 'domain', 'email'):
            if not getattr(self.args, name):
                setattr(self.args, name, params[name])
                self.log.info('{} was loaded from {}'.format(name, ansible.default_inventory_path()))

        return True

    def _confirm_or_correct_dialog(self):
        while True:
            self.log.info('\n\n\n=============================================')
            self._show_params()
            self.log.info('=============================================\n\n\n')

            if not self.prompter.prompt_yes_no('Do you want to continue?', default=True):
                self.log.info("Ok, let's enter all parameters again\n")
                self._prompt_params(only_missing=False)
                continue
            return

    def get_from_user(self):
        self._prompt_params(only_missing=True)
        self._confirm_or_correct_dialog()
        return self.args

    def restore_from_installed(self, static_state):
        if not self._restore_missing_params(static_state):
            return

        # just in case: ask user if ansible ok, but some parameter was not restored
        self._prompt_params(only_missing=True)
        self._confirm_or_correct_dialog()
        return self.args


class Git:
    def __init__(self, reposrc, homedir):
        self.homedir = homedir
        self.reposrc = reposrc
        self.log = logging.getLogger()

    def install_repo(self, ask_to_confirm=False):
        git_path = os.path.join(self.homedir, HardcodedData.RELATIVE_GIT_PATH)
        bootstrap_path = os.path.join(self.homedir, HardcodedData.RELATIVE_BOOTSTRAP_PATH)

        if not os.path.isdir(git_path):
            self.log.info('cloning git repo from scratch')
            Helpers.run_process('git clone "{}" "{}"'.format(self.reposrc, bootstrap_path))
            Helpers.run_process('git submodule init', workdir=bootstrap_path)
            Helpers.run_process('git submodule update', workdir=bootstrap_path)
        else:
            if ask_to_confirm:
                if not Prompter().prompt_yes_no('Found existing git bootstrap repository in {src}.\n'
                                                'Do you want to update it from {dst}?\n'.format(src=self.reposrc,
                                                                                                dst=bootstrap_path)):
                    self.log.info('OK, skip updating git repository')
                    return True

            self.log.info('updating existing git repo')
            Helpers.run_process('git pull --rebase', workdir=bootstrap_path)
            Helpers.run_process('git submodule init', workdir=bootstrap_path)
            Helpers.run_process('git submodule update --rebase --remote', workdir=bootstrap_path)
        return True


class TempFiles:
    def __init__(self):
        self.log = self._create_empty_tempfile('alco_install_log_')
        self.facts = self._create_empty_tempfile('alco_install_facts_')
        self.clean_on_exit = True

    @staticmethod
    def _create_empty_tempfile(prefix):
        with tempfile.NamedTemporaryFile(delete=False, prefix=prefix) as f:
            return f.name

    def clean(self):
        os.remove(self.log)
        os.remove(self.facts)

    def dont_clean(self):
        self.clean_on_exit = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.clean_on_exit:
            self.clean()


class StaticState:
    def __init__(self):
        self.data = dict()
        self._load()

    def _load(self):
        if not os.path.exists(HardcodedData.STATIC_STATE_PATH):
            return
        res = yaml.load(open(HardcodedData.STATIC_STATE_PATH)) or dict()
        install_dir = res.get('install_homedir')
        if not install_dir or not os.path.isdir(install_dir):
            return
        self.data = res

    def _save(self):
        # Helpers.sudo_touch_and_chown(HardcodedData.STATIC_STATE_PATH) пока не нужно, всегда работаем от рута
        Helpers.mkdir_if_not_exists(os.path.dirname(HardcodedData.STATIC_STATE_PATH))
        with open(HardcodedData.STATIC_STATE_PATH, 'w') as f:
            yaml.dump(self.data, f, default_flow_style=False)

    def is_installed(self):
        if not self.data:
            return
        return str(self.data.get('install_success', '0')) == '1'

    def set_installed(self, homedir):
        self.data['install_success'] = 1
        self.data['install_homedir'] = homedir
        self.data['install_time'] = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._save()

    def install_dir(self):
        return self.data['install_homedir']


class UserAccounts:
    # TODO ALLOWED_USER_SYMBOLS это костылик, см _validate_username
    ALLOWED_USER_SYMBOLS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'

    def __init__(self, homedir):
        self.log = logging.getLogger()
        self.data = OrderedDict()
        self.htpasswd_path = os.path.join(homedir, HardcodedData.RELATIVE_HTPASSWD_PATH)
        self.load_htpasswd()
        self.prompter = Prompter()

    def load_htpasswd(self):
        if not os.path.exists(self.htpasswd_path):
            return

        self.log.info('loading htpasswd from {}'.format(self.htpasswd_path))

        with open(self.htpasswd_path) as f:
            for line in f:
                line = line.strip()
                fields = line.split(':')
                if len(fields) < 2:
                    self.log.warn('bad record in htpasswd, skip: {}'.format(line))
                    continue
                user_name = fields[0]
                self.data[user_name] = line

    def save_htpasswd(self):
        Helpers.mkdir_if_not_exists(os.path.dirname(self.htpasswd_path))
        with open(self.htpasswd_path, 'w') as f:
            f.write('\n'.join(self.data.values()))

    @staticmethod
    def _make_htpasswd_string(user_name):
        res = Helpers.run_process('openssl passwd -apr1 2>/dev/null'.format(user_name),
                                  throwing=False,
                                  store_output=True,
                                  log_output=False)
        if res.retcode:
            return
        return '{}:{}'.format(user_name, res.output.strip())

    def _validate_username(self, user_name):
        # TODO как-то некрасиво делать это руками, поискать где-нибудь готовое решение для этого.
        # например https://github.com/theskumar/python-usernames
        for c in user_name:
            if c not in self.ALLOWED_USER_SYMBOLS:
                return False
        return True

    def _dialog_step(self):
        ans = self.prompter.prompt_string('select your action')
        fields = [x for x in ans.split(' ') if x]
        if not fields:
            self.log.info('empty value')
            return

        action = fields[0].lower()

        if action == 'ok':
            return True

        if len(fields) < 2:
            self.log.info('invalid value')
            return

        user_name = fields[1]

        if action == 'add':
            if not self._validate_username(user_name):
                self.log.info('invalid user name')
                return

            if user_name in self.data:
                self.log.info('user {} already exists'.format(user_name))
                return

            self.log.info('input password for user {}'.format(user_name))
            htpasswd_string = self._make_htpasswd_string(user_name)
            if not htpasswd_string:
                self.log.info('could not get password for user {}'.format(user_name))
                return

            self.data[user_name] = htpasswd_string
            self.log.info('user {} added'.format(user_name))
            return

        if action == 'del':
            to_delete = fnmatch.filter(self.data.keys(), user_name)
            if not to_delete:
                self.log.info('there is not such user: {}'.format(user_name))
                return

            if not self.prompter.prompt_yes_no('Delete user(s): {}?'.format(','.join(to_delete))):
                return

            for user in to_delete:
                del self.data[user]

            self.log.info('user(s) {} deleted'.format(','.join(to_delete)))
            return

    def dialog(self):
        if self.data:
            users_msg = 'User accounts found:\n{}'.format('\n'.join(['* {}'.format(x) for x in self.data.keys()]))
        else:
            users_msg = 'No user accounts found'

        if not self.prompter.prompt_yes_no('{}\nDo you want to configure user accounts?'.format(users_msg),
                                           default=False):
            return

        self.log.info("============================================")
        self.log.info("Configuring user accounts")
        while True:
            # TODO это тоже цветом
            self.log.info('\nActions available:\n'
                          'add <user_name>:     add new user and set his password\n'
                          'del <user_name>:     delete user (wildcard symbols like "*", "?" is supported)\n'
                          'ok:                  exit from user accounts configuration'
                          '\n')

            while not self._dialog_step():
                pass

            self.log.info('User accounts: {}'.format(', '.join(self.data.keys())))
            if not self.prompter.prompt_yes_no('Do you confirm it?'):
                self.log.info("OK, let's configure users again")
                continue

            break

        self.log.info("User accounts configured")
        self.log.info("============================================")


class Main:
    def __init__(self):
        self.temp_files = TempFiles()
        Helpers.setup_log(self.temp_files.log)
        self.log = logging.getLogger()

    def _init_stage(self):
        # Helpers.ask_root_password() пока не нужно, всегда работаем от рута
        self.log.info('initializing install dir: {}'.format(HardcodedData.INSTALL_DIR))
        Helpers.mkdir_if_not_exists(HardcodedData.INSTALL_DIR)
        # Helpers.sudo_mkdir_and_chown(homedir) пока не нужно, всегда работаем от рута

    @staticmethod
    def _git_stage():
        return Git(HardcodedData.REPO_SRC, HardcodedData.INSTALL_DIR).install_repo(ask_to_confirm=False)

    def _configuration_stage(self, static_state):
        if static_state.is_installed():
            if not Prompter().prompt_yes_no(
                    'System is already installed to your server.\n'
                    'Configuration stage (generating ansible inventory with params) is not necessary.\n'
                    'Do you want to change parameters and force reconfigure ansible inventory?\n',
                    default=False
            ):
                self.log.info('OK, skip configuration stage')
                return True

            args = UserParamsGetter().restore_from_installed(static_state)

            if not args:
                if Prompter().prompt_yes_no(
                        'Configuration stage cannot be done because program could not get ansible options.\n'
                        'It is normal if you have already installed system and changed your ansible inventories.\n'
                        'Do you want to continue?',
                        default=True
                ):
                    self.log.info('OK, skip configuration stage')
                    return True
                else:
                    self.log.info('OK, then exit')
                    return False

        else:
            args = UserParamsGetter().get_from_user()

        self.log.info('Starting configuration')
        ansible = Ansible(HardcodedData.INSTALL_DIR)
        ansible.write_default_inventory(args)
        ansible.gather_facts(args.hostname, self.temp_files.facts)
        return True

    @staticmethod
    def _users_accounts_stage():
        accounts = UserAccounts(HardcodedData.INSTALL_DIR)
        accounts.dialog()
        accounts.save_htpasswd()

    def _install_stage(self):
        self.log.info('Starting installation')
        ansible = Ansible(HardcodedData.INSTALL_DIR)
        ansible.run()

    def run(self):
        with self.temp_files:
            try:
                self.log.info('Welcome to alcolytics installation tool')
                self.log.info('Temporary log file: {}\n'.format(self.temp_files.log))

                static_state = StaticState()
                self._init_stage()

                if not self._git_stage():
                    return 1

                if not self._configuration_stage(static_state):
                    return 1

                self._users_accounts_stage()

                self._install_stage()

                static_state.set_installed(HardcodedData.INSTALL_DIR)
                self.log.info('Installation finished successfully')

            except (KeyboardInterrupt, EOFError):
                print 'Installation cancelled'
                return 1

            except (Exception, OSError):
                self.temp_files.dont_clean()
                print "\n\n\n\n"
                # TODO красным написать это
                self.log.exception('*********Install error!********* log saved to {} '
                                   'and report will be sent'.format(self.temp_files.log))
                Helpers.flush_log()
                Helpers.send_report(self.temp_files)
                return 1

        return 0


if __name__ == "__main__":
    if not Helpers.assert_root():
        print 'installation cannot be launched only by root'
        sys.exit(1)

    sys.exit(int(Main().run() or 0))
