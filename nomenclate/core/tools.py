from future.utils import iteritems
import collections


def combine_dicts(*args, **kwargs):
    dicts = [arg for arg in args if isinstance(arg, dict)]
    print('dicts are ', dicts)
    dicts.append(kwargs)
    super_dict = collections.defaultdict(dict)

    for d in dicts:
        for k, v in iteritems(d):
            if k:
                super_dict[k] = v
    print('super dict is ', dict(super_dict))
    return dict(super_dict)


def get_keys_containing(search_string, input_dict, default=None, first_found=True):
        output = {}
        for k, v in iteritems(input_dict):
            if search_string in k and not callable(k):
                output[k] = v

        if first_found:
            try:
                output = output[next(iter(output))]
            except StopIteration:
                pass

        output = output or default

        return output


def gen_dict_key_matches(key, iterable, path=None, full_path=False):
    """ From:
    http://stackoverflow.com/questions/34836777/print-complete-key-path-for-all-the-values-of-a-python-nested-dictionary
    """
    if path is None:
        path = []
    for k, v in iteritems(iterable):
        new_path = path + [k]
        if isinstance(v, dict):
            if v == key:
                yield v
            for u in gen_dict_key_matches(key, v, new_path):
                yield u
        else:
            result = (new_path, v) if full_path else v
            if key == k:
                yield result


def flatten(it):
    """ From:
    http://stackoverflow.com/questions/11503065/python-function-to-flatten-generator-containing-another-generator
    """
    for x in it:
        if (isinstance(x, collections.Iterable) and not isinstance(x, str)):
            for y in flatten(x):
                yield y
        else:
            yield x
