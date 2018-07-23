#!/usr/bin/env python3
import configparser
import argparse
import sys
import json

from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.application.current import get_app
from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.widgets import ProgressBar, Dialog, Button, Label, Box, TextArea, RadioList
from prompt_toolkit.layout.containers import HSplit


section = 'general'
config = configparser.ConfigParser()
users: list = []

OK_TEXT = 'Ok'
NEW_TEXT = 'New'
CANCEL_TEXT = 'Cancel'

def readini(fn):
    config.read(fn)


def writeini(fn):
    with open(fn, 'w') as f:
        config.write(f)


def ok_handler():
    get_app().exit(result=radio_list.current_value)


def users_list():
    values = list([(user.split(":")[0], user.split(":")[0]) for user in users])
    title = 'Users management'
    text = 'Choose user to update:'

    style = None
    async_ = False

    radio_list = RadioList(values)
    
    dialog = Dialog(
        title=title,
        body=HSplit(
            [
                Label(text=text, dont_extend_height=True),
                radio_list,
            ],
            padding=1),
        buttons=[
            Button(text=OK_TEXT, handler=ok_handler),
            Button(text=NEW_TEXT, handler=ok_handler),
            Button(text=CANCEL_TEXT, handler=_return_none),
        ],
        with_background=True)

    application = _create_app(dialog, style)
    return application.run()


def _return_none():
    " Button handler that returns None. "
    get_app().exit()


def _create_app(dialog, style):
    # Key bindings.
    bindings = KeyBindings()
    bindings.add('tab')(focus_next)
    bindings.add('s-tab')(focus_previous)

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([
            load_key_bindings(),
            bindings,
        ]),
        mouse_support=True,
        style=style,
        full_screen=True)


def new_user_input_dialog(title='', text='', ok_text='OK', cancel_text='Cancel',
                 completer=None, password=False, style=None, async_=False):
    """
    Display a text input box.
    Return the given text, or None when cancelled.
    """
    def accept(buf):
        get_app().layout.focus(ok_button)

    def ok_handler():
        get_app().exit(result=textfield.text)

    ok_button = Button(text=ok_text, handler=ok_handler)
    cancel_button = Button(text=cancel_text, handler=_return_none)

    textfield = TextArea(
        multiline=False,
        password=password,
        completer=completer,
        accept_handler=accept)

    dialog = Dialog(
        title=title,
        body=HSplit([
            Label(text=text, dont_extend_height=True),
            textfield,
        ], padding=D(preferred=1, max=1)),
        buttons=[ok_button, cancel_button],
        with_background=True)

    return _run_dialog(dialog, style, async_=async_)


def add_user():
    name = input_dialog(
        title='New user',
        text='New user name:')

    print('Result = {}'.format(result))



if __name__ == '__main__':

    if len(sys.argv) >= 2:
        readini(sys.argv[1])
        if 'general' in config:
            if 'users' in config[section]:
                users = json.loads(config[section]['users'])

    users_list()
