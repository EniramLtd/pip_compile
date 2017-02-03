"""pip_compile setup information

Copyright 2015-2017 The pip_compile developers. See the LICENSE.txt file at the
top-level directory of this distribution and at
https://github.com/akaihola/pip_compile/blob/master/LICENSE.txt

"""

import warnings

from setuptools import setup

# show deprecation warnings
warnings.simplefilter('default')

PACKAGE_NAME = 'pip_compile'

with open('{}/version.py'.format(PACKAGE_NAME)) as f:
    exec(f.read(), globals())

TEST_REQUIREMENTS = ['pytest']

setup(name=PACKAGE_NAME,
      version=__version__,
      description=('Prototype Pip subcommand for compiling a complete set of '
                   'depended packages and versions from requirements and '
                   'constraints'),
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Topic :: Software Development :: Build Tools",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: Implementation :: PyPy"
      ],
      keywords='pip easy_install distutils setuptools egg virtualenv',
      author='The pip_compile developers',
      author_email='antti.kaihola@eniram.fi',
      url='https://github.com/EniramLtd/pip_compile',
      license='MIT',
      packages=['pip_compile'],
      entry_points={'console_scripts': ['pip-compile = pip_compile:main']},
      setup_requires=['pytest-runner'],
      install_requires=['pip'],
      tests_require=[TEST_REQUIREMENTS],
      extras_require={'testing': [TEST_REQUIREMENTS],
                      'documentation': [],
                      'development': [TEST_REQUIREMENTS]})
