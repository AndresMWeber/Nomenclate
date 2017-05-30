import codecs
from os.path import abspath, dirname, join
from distutils.util import convert_path
from setuptools import setup, find_packages

__author__ = 'Andres Weber'
__author_email__ = 'andresmweber@gmail.com'
__package__ = 'nomenclate'

main_ns = {}
with open(convert_path('%s/version.py' % __package__)) as ver_file:
    exec (ver_file.read(), main_ns)

with codecs.open(join(abspath(dirname(__file__)), 'README.rst'), encoding='utf-8') as readme_file:
    long_description = readme_file.read()

description = 'A tool for generating strings based on a preset naming convention.',

tests_requires = [
    'python-mimeparse',
    'pbr',
    'mox3',
    'virtualenv',
    'traceback2',
    'coverage',
    'extras',
    'funcsigs',
    'linecache2',
    'pluggy',
    'py',
    'fixtures',
    'unittest2',
    'mock',
    'nose',
    'pyfakefs',
    'tox >= 1.9, < 3',
    'testtools',
    'tox',
    'coveralls'
]

dev_requires = ['twine', 'sphinx', 'docutils', 'docopt']

install_requires = [
    'configparser',
    'future',
    'python-dateutil',
    'PyYAML',
    'six'
]

setup(
    name=__package__,
    version=main_ns['__version__'],
    packages=find_packages(),
    package_data={'configYML': ['nomenclate/core/*.yml']},
    include_package_data=True,
    url='https://github.com/andresmweber/nomenclate',
    license='MIT',
    author=__author__,
    author_email=__author_email__,
    description=description,
    long_description=long_description,
    keywords='naming conventions labels config convention name parsing parse',
    entry_points={
        'console_scripts': [
            'nomenclate = nomenclate.app:run',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Multimedia :: Graphics :: 3D Modeling',
    ],
    install_requires=install_requires,
    extras_require={
        'tests': tests_requires,
        'dev': dev_requires
    }
)
