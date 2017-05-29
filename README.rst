Nomenclate: A toolset for automating and generating strings based on arbitrary user-defined naming conventions
###################################################################################################
`Online Documentation (ReadTheDocs) <http://nomenclate.readthedocs.io/en/latest/>`_

.. image:: https://readthedocs.org/projects/nomenclate/badge/?version=latest
    :target: http://nomenclate.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://badge.fury.io/py/nomenclate.svg
    :target: https://badge.fury.io/py/nomenclate

.. image:: https://travis-ci.org/AndresMWeber/Nomenclate.svg?branch=master
    :target: https://travis-ci.org/AndresMWeber/Nomenclate

.. image:: https://coveralls.io/repos/github/AndresMWeber/Nomenclate/badge.svg?branch=master
    :target: https://coveralls.io/github/AndresMWeber/Nomenclate?branch=master

.. image:: https://landscape.io/github/AndresMWeber/Nomenclate/master/landscape.svg?style=flat
   :target: https://landscape.io/github/AndresMWeber/Nomenclate/master
   :alt: Code Health

.. contents::

.. section-numbering::

Synopsis
=============

Nomenclate is a tool which creates persistent objects that can be used to generate strings that follow naming
conventions that you designate.  There are sets of current naming conventions that can be replaced or extended following
certain rules for creation.  You can add arbitrary tokens as needed and register token filtering of your own designation.

To start off there is a full set of yaml defined suffix/side substitution strings as found in env.yml.  If you want you
can create your own yml file that you will pass to a Nomenclate instance to have your own configuration.


Features
--------
-  Persistent state object instances
-  Up to date with online help docs
-  User-customizable YAML/human-readable config file
-  Easy object property or dictionary state manipulation

Installation
============
Windows, etc.
-------------
A universal installation method (that works on Windows, Mac OS X, Linux, …, and always provides the latest version) is to use `pip`:

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

    # Create a name object with initialized kwargs
    nomenclate_init_kwargs = nomenclate.Nom(name='test', type='group')

    # Your Nomenclate object has now been initialized and all of the default token set have been added based on
    # The default format_string property from the env.yml config file
    # default: side_location_nameDecoratorVar_childtype_purpose_type
    >>> nomenclate_empty.state
    {'name': '', 'childtype': '', 'location': '', 'var': '', 'type': '', 'side': '', 'decorator': '', 'purpose': ''}
    >>> nomenclate_init_kwargs.state
    {'name': 'test', 'childtype': '', 'location': '', 'var': '', 'type': 'group', 'side': '', 'decorator': '', 'purpose': ''}

    # The format string will automate the process of hot swapping naming formats allows any string to be input.
    >>> nomenclate_init_kwargs.format
    'side_location_nameDecoratorVar_childtype_purpose_type'
    >>> nomenclate_init_kwargs.format = 'name_type'
    >>> nomenclate_init_kwargs.state
    {name:'test', type='group'}

    # At any time you can query the state of the nomenclate object through the .state property

    # This is the detailed explanation of how to manipulate env.yml from the file header itself:
    # List of configurations written in YAML
    #
    # So far the suffixes is a look up dictionary for Maya objects, however I will be adding support for more later.
    # To properly enter a naming format string:
    #
    # Enter all fields you want to look for with a special look up word you want to use
    # as a descriptor for that naming token e.g. -
    #                                       name
    # and place it where you want it in order in the formatting string you set.
    # If you want something to space out or separate the names just input whatever separator
    # you want to use like _ or . and it will keep those for usage.
    #
    # Name the format whatever sub-section name you think is appropriate with an appropriate header
    #
    # If you want them camel cased for example name and type:
    #                                       nameType
    # and it will do the camelcasing for whatever you input.
    #
    # If you want a static string to always be present in a format string just
    # enclose it with parenthesis, for example a version:
    #                                       (v)version
    # if version is 3 and your version padding config is set to 2
    # will evaluate to
    #                                       v02
    #
    #
    #  There are 3 naming tokens with specific formatting functions that will give you customized results
    #  You can designate multiple fields for added granularity by adding a number after e.g. var1, var2
    #       <var> - this depends on var in the config being set to upper or lower
    #             a -returns a character based on position in alphabet, if you go over it starts aa -> az -> ba -> bz etc.
    #             A - returns a character based on position in alphabet, if you go over it starts AA -> AZ -> BA -> BZ etc.
    #       <version> - will return a string number based on the version_padding config setting
    #       <date> - will return a date as a string based on a datetime module formatted string
    #              that the user will input or default to YYYY-MM-DD
    #              full list of options can be found here:
    #              https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    #              please specify whichever separators (or lack of) you want to override the default behavior
    #              just modify the config
    #
    #  If you need any custom token conversion functions you can specify them by extending the nomenclate class with methods
    #  with the following naming structure: convert_<token>(self, token_data) which should return a string
    #
    #  Otherwise, unless you specify an options list for a specific naming token
    #  it will just replace the text with whatever you set that naming token to
    #  on the nomenclate object.  The options lists will be used as a filter for the
    #  naming token validity or as a look up table for UIs and if you specify
    #  different lengths after it, it will use the first in the list unless
    #  otherwise specified in the overall_config section under "<naming_token>_length"
    #  If there is no abbreviation list afterwards then just write it as a list with -


Version Support
===============
This package supports the Maya 2015, 2016 and 2017 so far so please be aware.
