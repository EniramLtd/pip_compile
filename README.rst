=============
 pip_compile
=============

This is a prototype for a pip subcommand which compiles a complete set of
depended packages and versions from requirements and constraints.

Basically this does exactly the same thing as ``pip install``, but skips
actually installing the packages and outputs a list of packages and versions
instead.

Furthermore, when ``-c / --constraint`` is given, the tool checks that all requirements
are actually specified in the constraint list. This gives the user the confirmation
that all versions are explicitly specified. One can use constraints without version specifiers
to accept any version.

A few extra command line options have been added:

* ``--flat``: Do not recurse into dependencies. This is useful for pinning an
  explicit list of packages to versions in a constraints file, without resolving
  any dependencies of packages in the list.
* ``-o / --output``: Path to write a list of pinned dependencies into. Use ``-``
  for standard output. The list is in a similar format as what ``pip freeze``
  outputs.
* ``-j / --json-output``: Path to write the JSON format dependency graph of
  pinned packages into.
* ``--allow-double``: Allow double requirements. This option is only valid
  together with ``-c / --constraint``. It disregards any version specifiers in
  given requirements, and allows the same package to be listed multiple times.
  This is useful when pinning overlapping requirements of multiple packages in
  one go.

Known caveats and limitations
=============================

- constraints override requirements. In case the constraint is in conflict with the 
  requirement (e.g. ``pkg==1.0`` vs ``pkg>=1.1``), the constraint wins. Similarly, 
  requirement conflicts are ignored with constraint.


Example
=======

Given the following ``constraints.txt`` file::

    werkzeug==0.11.11
    MarkupSafe==0.23
    Jinja2==2.8
    Flask==0.11.1

you can run::

    $ pip-compile -c /tmp/c.txt -o - Jinja2
    Collecting Jinja2==2.8
      Using cached Jinja2-2.8-py2.py3-none-any.whl
    Collecting MarkupSafe==0.23 (from Jinja2==2.8)
    MarkupSafe==0.23
    Jinja2==2.8

or, if you need JSON output::

    $ pip-compile -c /tmp/c.txt -j - Jinja2
    Collecting Jinja2==2.8
      Using cached Jinja2-2.8-py2.py3-none-any.whl
    Collecting MarkupSafe==0.23 (from Jinja2==2.8)
    {
        "Jinja2==2.8": [
            "MarkupSafe==0.23"
        ]
    }

See ``pip-compile --help`` for a full list of command line arguments.
