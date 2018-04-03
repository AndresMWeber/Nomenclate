import codecs
import os
import re
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install

name = 'nomenclate'
__author__ = 'Andres Weber'
__author_email__ = 'andresmweber@gmail.com'
__url__ = 'https://github.com/andresmweber/%s' % __package__
__version__ = '0.0.0'

with codecs.open(os.path.abspath(os.path.join(name, 'version.py'))) as ver_file:
    version_regex = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(version_regex, ver_file.read(), re.M)
    try:
        __version__ = mo.group(1)
    except AttributeError:
        raise IOError('Could not find version in %s' % os.path.join(name, 'version.py'))

with codecs.open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'README.rst'), encoding='utf-8') as readme:
    long_description = readme.read()

description = 'A tool for generating strings based on a preset naming convention.'

install_requires = [
    'python-dateutil',
    'PyYAML',
    'six'
]

tests_requires = [
    'coverage',
    'coveralls',
    'fixtures',
    'unittest2',
    'mock',
    'nose',
    'pyfakefs',
    'tox'
]


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('GIT_TAG')
        if __version__ not in tag:
            info = "Git tag: {0} does not match the version of this app: {1}".format(tag, __version__)
            sys.exit(info)


dev_requires = ['twine', 'Sphinx', 'docutils', 'docopt']

setup(
    name=name,
    version=__version__,
    packages=find_packages(exclude=['tests', '*.tests', '*.tests.*']),
    package_data={'configYML': ['nomenclate/core/*.yml']},
    include_package_data=True,
    url=__url__,
    license='MIT',
    author=__author__,
    author_email=__author_email__,
    description=description,
    long_description="`Online Documentation (ReadTheDocs) <http://nomenclate.readthedocs.io/en/latest/>`_",
    keywords='naming conventions labels config convention name parsing parse',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Multimedia :: Graphics :: 3D Modeling',
    ],
    install_requires=install_requires,
    extras_require={
        'tests': tests_requires,
        'dev': dev_requires
    },
    cmdclass={
        'verify': VerifyVersionCommand,
    }
)
