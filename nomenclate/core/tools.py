from future.utils import iteritems
import collections
from pprint import pformat
from nlog import (
    getLogger,
    DEBUG,
    INFO,
    CRITICAL
)

LOG = getLogger(__name__, level=DEBUG)


def combine_dicts(*args, **kwargs):
    dicts = [arg for arg in args if isinstance(arg, dict)]
    LOG.info('dicts are %s' % pformat(dicts))
    dicts.append(kwargs)
    super_dict = collections.defaultdict(dict)

    for d in dicts:
        for k, v in iteritems(d):
            if k:
                super_dict[k] = v
    LOG.info('super dict is %s' % pformat(dict(super_dict)))
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


def gen_dict_key_matches(key, dictionary, path=None, full_path=False):
    if path is None:
        path = []
    LOG.info('\nThe main input to the function is:\n %s\n' % pformat(dict(dictionary)))
    for k, v in iteritems(dictionary):
        path.append(k)
        if k == key:
            LOG.debug('\n\t\tkey %s matches query string %s, yielding!' % (k, key))
            yield (path, v) if full_path else v
        elif isinstance(v, dict):
            LOG.debug('\n\t\tvalue is a dictionary, iterating through %s!' % pformat(v))
            for result in gen_dict_key_matches(key, v, path):
                yield result


def flatten(it):
    """ From:
    http://stackoverflow.com/questions/11503065/python-function-to-flatten-generator-containing-another-generator
    """
    for x in it:
        if isinstance(x, collections.Iterable) and not isinstance(x, str):
            for y in flatten(x):
                yield y
        else:
            yield x
