Nomenclate: A tool set for automating and generating strings based on arbitrary user-defined naming conventions
###############################################################################################################

`Online Documentation (ReadTheDocs) <http://nomenclate.readthedocs.io/en/latest/>`_

.. image:: https://readthedocs.org/projects/nomenclate/badge/?version=latest
    :target: http://nomenclate.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://badge.fury.io/py/nomenclate.svg
    :target: https://badge.fury.io/py/nomenclate

.. image:: https://circleci.com/gh/AndresMWeber/Nomenclate.svg?style=svg
    :target: https://circleci.com/gh/AndresMWeber/Nomenclate

.. image:: https://coveralls.io/repos/github/AndresMWeber/Nomenclate/badge.svg?branch=master
    :target: https://coveralls.io/github/AndresMWeber/Nomenclate?branch=master

.. image:: https://landscape.io/github/AndresMWeber/Nomenclate/master/landscape.svg?style=flat
   :target: https://landscape.io/github/AndresMWeber/Nomenclate/master
   :alt: Code Health

.. image:: https://img.shields.io/pypi/pyversions/nomenclate.svg
   :target: https://pypi.python.org/pypi/nomenclate

.. contents::

.. section-numbering::

Synopsis
=============

Nomenclate is a tool which creates persistent objects that can be used to generate strings that follow naming
conventions that you designate.
There are sets of current naming conventions (format strings) that can be replaced or extended following certain rules
for creation. You can add arbitrary tokens as needed and register token filtering of your own designation.

There is a full set of YAML defined suffix/side substitution strings as found in ``env.yml``.
If you want you can create your own .yml file that you will pass to a Nomenclate instance to have your own configuration.

Concept Definitions
-------------------
token
    : A component of the format string which is a meaningful symbol/definition pair that will be filtered by
    a grammar of regular expressions.
    A simplified representation could be token=value wherein the token (as found in the format string) will be resolved
    to the value as is adheres to the token's syntax/grammar rules

format string
    : A string that represents a series of tokens separated with arbitrary delimiters.

    e.g. - ``side_location_nameDecoratorVar_childtype_purpose_type``

    Note: Nomenclate automatically supports camelCasing the tokens to separate them as a natural delimiter.

`For a review of parsing/composition look here <https://en.wikipedia.org/wiki/Parsing>`_

Features
--------
-  Applies a naming convention with arbitrary syntax/grammar to the formatting of string tokens
-  Top down parsing of format string given token-specific grammar rule classes that are extensible
-  Persistent state object instances
-  Up to date with online help docs
-  User-customizable YAML/human-readable config file
-  Easy object property or dictionary state manipulation
-  Cross-Python compatible: Tested and working with Python 2.7 and 3.5
-  Cross-Platform compatible: Works under Linux, Mac OS ,Windows environments
-  Full module/class documentation
-  Sensible token value entry/conversion (like ``side='left'`` with automatic token syntax replacement)

Installation
============
Windows, etc.
-------------
A universal installation method (that works on Windows, Mac OS X, Linux, ..., and always provides the latest version) is to use `pip`:

.. code-block:: bash

    # Make sure we have an up-to-date version of pip and setuptools:
    $ pip install --upgrade pip setuptools
    $ pip install Nomenclate


(If ``pip`` installation fails for some reason, you can try ``easy_install nomenclate`` as a fallback.)

Usage
=============

Python Package Usage
---------------------
Use this tool via package level functions

.. code-block:: python

    import nomenclate
    # Create empty name object
    nomenclate_empty = nomenclate.Nom()

    # At any time you can query the state of the nomenclate object through the state property
    >>> nomenclate_empty.state
    {'name': '', 'childtype': '', 'location': '', 'var': '', 'type': '', 'side': '', 'decorator': '', 'purpose': ''}

    # You can also create a nomenclate with initialized kwargs
    nomenclate_init_kwargs = nomenclate.Nom(name='test', type='group')

    # Your Nomenclate object has now been initialized and all of the default token set have been added based on
    # The default format_string property from the env.yml config file
    # default: side_location_nameDecoratorVar_childtype_purpose_type
    >>> nomenclate_init_kwargs.state
    {'name': 'test', 'childtype': '', 'location': '', 'var': '', 'type': 'group', 'side': '', 'decorator': '', 'purpose': ''}

    # Feel free to manipulate each token's value on a property basis
    >>> nomenclate_init_kwargs.location = 'rear'

    # Now that you're all set up you can use the get method to obtain a string representation of your conventionalized output:
    >>> nomenclate_init_kwargs.get()
    'rr_test_GRP'

    # As you'll notice both tokens group and location have been composed following the replacements that can be found in the config YAML file.  This way things like "left" just need to be entered as "left" and then based on the yaml will replace automatically with anything you want.  Finally you don't need to enter things like "L" and worry about it later on!

    # The format string will automate the process of hot swapping naming formats allows any string to be input.
    >>> nomenclate_init_kwargs.format
    'side_location_nameDecoratorVar_childtype_purpose_type'
    >>> nomenclate_init_kwargs.format = 'name_type'
    >>> nomenclate_init_kwargs.state
    {name:'test', type='group'}

    # You can enter static text that will always be present in the name by surrounding with parenthesis
    # For now they only support alphanumeric characters.

    >>> nomenclate_init_kwargs.format = 'side_location_nameDecoratorVar_(static.text)childtype_purpose_type'
    >>> nomenclate_init_kwargs.name = 'test'
    >>> nomenclate_init_kwargs.location = 'rear'
    >>> nomenclate_init_kwargs.type = 'group'
    'rr_test_staticText_GRP'

    # Now entering all these values by properties is fun and all, however there is a convenience function that can digest dictionaries
    >>> test_nom = nomenclate.Nom()
    >>> test_nom.merge_serialization({'name':'test', 'location':'rear', 'type':'group'})
    >>> test_nom.get()

    # As you might have guessed, using state and merge_serialization you can pass naming values from instance to instance (as you can see __eq__ has been defined for Nomenclate instances):
    >>> nom_a = nomenclate.Nom(name='test', location='rear')
    >>> nom_b = nomenclate.Nom()
    >>> nom_b == nom_a
    False
    >>> nom_b.merge_serialization(nom_a.state)
    >>> nom_b == nom_a
    True

    # Optionally you can just pass the nomenclate object itself
    >>> nom_b.token_dict.reset() # Internal function to be made into a public method later...
    >>> nom_b == nom_a
    False
    >>> nom_b.merge_serialization(nom_a)
    >>> nom_b == nom_a
    True



YAML Configuration File Rules
-----------------------------

So far the suffixes is a look up dictionary for Maya objects, however I will be adding support for more later.

To properly enter a naming format string:

    Enter all tokens you want to use with descriptive value that naming token's label e.g:
        ``name``

    and place it where you want it in order in the formatting string you set.
    If you want something to space out or separate the names just input whatever separator
    you want to use like ``_`` or ``.`` and it will keep those as delimiters.
    ``name_side_type``

    Additionall if you want them camel cased for example name and type:
    ``side_nameType``
    and it will automatically camelcase your for whatever you input for the given token values.

    In the config YAML file ``(default is nomenclate/core/env.yml)`` define your format under the header ``naming_formats`` with a sub-section name you think is appropriate (the following example is optionally nested under "node"):

    .. code-block:: yaml

        naming_formats:
            node:
                your_format: name_sidePurpose_type


    If you want a static string to always be present in a format string just enclose it with parenthesis (for now only alphanumeric characters are accepted), for example a version:
        ``(v)version``
        in format string:
        ``side_name_(v)version_(static_text_example)``

        Example:
            If version is 3 and your version padding config is set to 2
            will evaluate to:
            ``v02``

Further version/var/date specific token notes:
    There are 3 naming tokens with specific formatting functions that will give you customized results.  You can designate multiple fields for added granularity by adding a number after e.g. var1, var2

      :var:
        this depends on var in the config being set to upper or lower

        ``a``: returns a character based on position in alphabet, if you go over it starts aa -> az -> ba -> bz etc.

        ``A``: returns a character based on position in alphabet, if you go over it starts AA -> AZ -> BA -> BZ etc.

      :version:
        Will return a string number based on the version_padding config setting

      :date:
        Will return a date as a string based on a datetime module formatted string
        that the user will input or default to YYYY-MM-DD

        Please specify whichever separators (or lack of) you want to override the default behavior just modify the config

        The full list of options can be found here:
        `Datetime Documentation <https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior>`_

 If you need any custom token value conversion functions you can specify them by inheriting from ``nomenclate.core.rendering.RenderBase`` and implementing its render function like so:

    .. code-block:: python

        import nomenclate

        class RenderCustom(nomenclate.core.rendering.RenderBase):
            token = 'custom'
            def render(cls, value, token, nomenclate_object, **kwargs):
                """ Always prepend "meh"

                :param value: str, the un-parsed/formatted token value
                :param token: str, the name of the token in question
                :param nomenclate_object: nomenclate.Nom, the nomenclate instance (for checking attribute values/config settings)
                :return: str, the final syntax adhering token value
                """
                return 'meh' + value

    Otherwise, unless you specify an options list for a specific naming token in the custom renderer
    it will just replace the text with whatever you set that naming token to
    on the nomenclate object.  The options lists will be used as a filter for the
    naming token validity or as a look up table for UIs and if you specify
    different lengths after it. It will use the first in the list unless
    otherwise specified in the overall_config section under "<naming_token>_length"
    If there is no abbreviation list afterwards then just write it as a list with -


Version Support
===============
Currently this package supports Python 2.7, 3.5 and 3.6

Attribution
===========
WPZOOM Developer Icon Set by WPZOOM License_ Source_ - Designed by David Ferreira.
    .. _License: http://creativecommons.org/licenses/by-sa/3.0/
    .. _Source: http://www.wpzoom.com

Icon made by iconauth_ from www.flaticon.com
    .. _iconauth: https://www.flaticon.com/authors/freepik