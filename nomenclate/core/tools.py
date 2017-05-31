from six import iteritems
import collections
from pprint import pformat
import nomenclate.settings as settings

MODULE_LOGGER_LEVEL_OVERRIDE = None
LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)


class NomenclateNotifier(object):
    def __init__(self, observer):
        self.observers = []
        self.register_observer(observer)

    def register_observer(self, observer_function):
        LOG.info('Registering observer function %s' % observer_function)
        self.observers.append(observer_function)

    def notify_observer(self, *args, **kwargs):
        for observer_function in self.observers:
            LOG.info('Notifying %s with args %s and kwargs %s' % (observer_function.__name__,
                                                                  args,
                                                                  kwargs))
            observer_function(*args, **kwargs)


def combine_dicts(*args, **kwargs):
    """ Combines all arguments (if they are dictionaries) and kwargs to a final dict

    :param args: dict, any dictionaries the user wants combined
    :param kwargs: dict, kwargs.
    :return: dict, compiled dictionary
    """
    dicts = [arg for arg in args if isinstance(arg, dict)]
    LOG.debug('dicts are %s' % pformat(dicts))
    dicts.append(kwargs)
    super_dict = collections.defaultdict(dict)

    for d in dicts:
        for k, v in iteritems(d):
            if k:
                super_dict[k] = v
    LOG.debug('super dict is %s' % pformat(dict(super_dict)))
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
    LOG.debug('\nThe main input to the function is:\n %s\n' % pformat(dict(dictionary)))
    for k, v in iteritems(dictionary):
        _path.append(k)
        if k == key:
            LOG.debug('\n\t\tkey %s matches query string %s, yielding!' % (k, key))
            yield (_path, v) if full_path else v
        elif isinstance(v, dict):
            LOG.debug('\n\t\tvalue is a dictionary, iterating through %s!' % pformat(v))
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
