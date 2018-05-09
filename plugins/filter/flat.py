from collections import MutableMapping, MutableSequence


def flatten(mylist, levels=None):

    ret = []
    for element in mylist:
        if element in (None, 'None', 'null'):
            # ignore undefined items
            break
        elif isinstance(element, MutableSequence):
            if levels is None:
                ret.extend(flatten(element))
            elif levels >= 1:
                levels = int(levels) - 1
                ret.extend(flatten(element, levels=levels))
            else:
                ret.append(element)
        else:
            ret.append(element)

    return ret


class FilterModule (object):
    def filters(self):
        return {
            "flat": flatten
        }
