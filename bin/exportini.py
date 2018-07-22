#!/usr/bin/env python3
import configparser
import sys

section = 'general'

if len(sys.argv) == 2:
    fn = sys.argv[1]

    config = configparser.ConfigParser()
    config.read(fn)

    if 'general' in config:
        for key in config[section]:
            print('export {}="{}"'.format(key.upper(),config[section][key]))

