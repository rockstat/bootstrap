from __future__ import (unicode_literals, absolute_import, division, print_function)
# from builtins import str
import netaddr

def ip_pattern_to_net(pattern):
    bits = 32 - pattern.count('*') * 8
    network = str.replace(pattern, '*', '0')
    return "%s/%s" % (network, bits)

def net_gateway(netstr):
    net = netaddr.IPNetwork(netstr)
    return "%s" % (net[1])


class FilterModule (object):
    def filters(self):
        return {
            "ip_p2n": ip_pattern_to_net,
            "net_gw": net_gateway
        }
