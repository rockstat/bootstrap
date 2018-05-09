def flatten_dict_values(dictionary):
    result = []
    result = reduce(list.__add__, dictionary,[])
    return result

class FilterModule (object):
    def filters(self):
        return {
            "flatten_dict_values": flatten_dict_values
        }
