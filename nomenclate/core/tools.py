import collections


class Serializable(object):
    SERIALIZE_ATTRS = []

    def serialize(self):
        return self.to_json()

    def deserialize(self, blob):
        return self.from_json(blob)

    def merge_serialization(self, blob):
        return self.merge_json(blob)

    def to_json(self):
        return {attr: getattr(self, attr) for attr in self.SERIALIZE_ATTRS}

    def merge_json(self, json_blob):
        for search_attr in [
            attr for attr in self.SERIALIZE_ATTRS if json_blob.get(attr) is not None
        ]:
            json_attr = json_blob[search_attr]
            setattr(self, search_attr, json_attr)
        return True

    @classmethod
    def from_json(cls, json_blob):
        return cls(
            **{
                attr: json_blob[attr]
                for attr in cls.SERIALIZE_ATTRS
                if json_blob.get(attr) is not None
            }
        )


class NomenclateNotifier(object):
    def __init__(self, observer):
        self.observers = []
        self.register_observer(observer)

    def register_observer(self, observer_function):
        self.observers.append(observer_function)

    def notify_observer(self, *args, **kwargs):
        for observer_function in self.observers:
            observer_function(*args, **kwargs)


def get_string_difference(string1, string2):
    last_found_index = 0
    matches = []
    longer_string = max(string1, string2)
    shorter_string = min(string1, string2)

    for char_index, char in enumerate(shorter_string):
        comparison_index = max(char_index, last_found_index)

        while comparison_index < len(longer_string):
            if longer_string[comparison_index] == char:
                last_found_index = comparison_index
                matches.append([char_index, longer_string[comparison_index], comparison_index])
                break
            comparison_index += 1

    return matches


def combine_dicts(*args, **kwargs):
    """ Combines all arguments (if they are dictionaries) and kwargs to a final dict

    :param args: dict, any dictionaries the user wants combined
    :param kwargs: dict, kwargs.
    :return: dict, compiled dictionary
    """
    dicts = [arg for arg in args if isinstance(arg, dict)]
    dicts.append(kwargs)
    super_dict = collections.defaultdict(dict)

    for d in dicts:
        for k, v in d.items():
            if k:
                super_dict[k] = v
    return dict(super_dict)


def get_keys_containing(search_string, input_dict, default=None, first_found=True):
    """ Searches a dictionary for all keys containing the search string (as long as the keys are not functions) and
        returns a filtered dictionary of only those keys
    
    :param search_string: str, string we are looking for
    :param input_dict: dict, dictionary to search through
    :param default: object, if we find nothing, return this as the default
    :param first_found: bool, return the first found key
    :return: dict, dictionary filled with any matching keys
    """
    output = {}
    for k, v in input_dict.items():
        if search_string in k and not callable(k):
            output[k] = v

    if first_found:
        try:
            output = output[next(iter(output))]
        except StopIteration:
            pass
    return output or default


def gen_dict_key_matches(key, dictionary, _path=None, full_path=False):
    """ Generates a list of sets of (path, value) where path is a list of keys to access the given value in the given
        nested dictionary

    :param key: object, given dictionary key we are looking for
    :param dictionary: dict, query dictionary
    :param _path: list(str), internal use for the current path to output in case of match.
    :param full_path: bool, return value or (path, value))
    :return: Generator[object] or Generator[(list(str), object)], generator of (path, value) or just value
    """
    if _path is None:
        _path = []
    for k, v in dictionary.items():
        _path.append(k)
        if k == key:
            yield (_path, v) if full_path else v
        elif isinstance(v, dict):
            for result in gen_dict_key_matches(key, v, _path):
                yield result


def flatten(it):
    """ Flattens any iterable
        From:
        http://stackoverflow.com/questions/11503065/python-function-to-flatten-generator-containing-another-generator

    :param it: Iterator, iterator to flatten
    :return: Generator, A generator of the flattened values
    """
    for x in it:
        if isinstance(x, collections.Iterable) and not isinstance(x, str):
            for y in flatten(x):
                yield y
        else:
            yield x


def flattenDictToLeaves(d, result=None, index=None):
    if result is None:
        result = []
    if isinstance(d, (list, tuple)):
        for indexB, element in enumerate(d):
            flattenDictToLeaves(element, result, index=indexB)
    elif isinstance(d, dict):
        for key in list(d):
            value = d[key]
            flattenDictToLeaves(value, result, index=None)
    else:
        result.append(d)
    return result
