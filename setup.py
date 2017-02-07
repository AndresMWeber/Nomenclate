import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


# ref: https://tox.readthedocs.org/en/latest/example/basic.html#integration-with-setuptools-distribute-test-commands
class Tox(TestCommand):
    user_options = [('tox-args=', 'a', "Arguments to pass to tox")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = ''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import tox
        import shlex
        errno = tox.cmdline(args=shlex.split(self.tox_args))
        sys.exit(errno)


class ToxWithRecreate(Tox):
    description = ('Run tests, but recreate the testing environments first. '
                   '(Useful if the test dependencies change.)')

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.tox_args = '-r'


setup(
    name='nomenclate',
    version='0.2.8',
    packages=['nomenclate'],
    url='https://github.com/andresmweber/nomenclate',
    license='MIT',
    author='Andres Weber',
    description='Naming Convention Generator ',
    long_description='Tool for generating string-based labels based on a preset convention configuration.',
    keywords='naming conventions labels config convention name',
    
    entry_points={
        'console_scripts':[
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

    install_requires=[
        'configparser',
        'future',
        'python-dateutil',
        'PyYAML',
        'six'
    ],

    # tox is responsible for setting up the test runner and its dependencies
    # (e.g., code coverage tools) -- see the tox.ini file
    tests_require=[
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
        'tox'
    ],

    cmdclass={
        'test': Tox,
        'clean_test': ToxWithRecreate,
    },
)
