from __future__ import (unicode_literals, absolute_import, division, print_function)
import six
from passlib.apache import HtpasswdFile, CryptContext

myctx = CryptContext(schemes=["apr_md5_crypt"])

def apr1pass(orig):
    return myctx.hash(orig)


class FilterModule (object):
    def filters(self):
        return {
            "apr1pass": apr1pass
        }
