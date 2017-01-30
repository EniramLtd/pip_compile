"""pip_compile setup information

Copyright 2013-2017 Eniram Ltd. See the LICENSE file at the top-level directory
of this distribution and at
https://github.com/akaihola/pip_compile/blob/master/LICENSE

"""

import warnings

from setuptools import setup

# show deprecation warnings
warnings.simplefilter('default')

PACKAGE_NAME = 'pip_compile'

with open('{}/version.py'.format(PACKAGE_NAME)) as f:
    exec(f.read(), globals())

setup(name=PACKAGE_NAME,
      version=__version__,
      packages=['pip_compile'],
      author='Antti Kaihola',
      author_email='antti.kaihola@eniram.fi',
      license='BSD',
      description=('Prototype Pip subcommand for compiling a complete set of '
                   'depended packages and versions from requirements and '
                   'constraints'),
      keywords='pip',
      url='https://github.com/EniramLtd/pip_compile',
      install_requires=['pip'],
      extras_require={'testing': [],
                      'documentation': []},
      entry_points = {'console_scripts': ['pip-compile = pip_compile:main']})
