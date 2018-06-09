from __future__ import (unicode_literals, absolute_import, division, print_function)
import six
import netaddr

def ip_pattern_to_net(pattern):
    bits = 32 - str(pattern).count('*') * 8
    lostbits = 24 - str(pattern).count('.') * 8
    network = str.replace(str(pattern), '*', '0') + ('.0' * round(lostbits/8))
    return "%s/%s" % (network, bits - lostbits)

def net_gateway(netstr):
    net = netaddr.IPNetwork(str(netstr))
    return "%s" % (net[1])


class FilterModule (object):
    def filters(self):
        return {
            "ip_p2n": ip_pattern_to_net,
            "net_gw": net_gateway
        }
