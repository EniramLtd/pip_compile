=============
 pip_compile
=============

This is a prototype for a Git subcommand which compiles a complete set of
depended packages and versions from requirements and constraints.

Basically this does exactly the same thing as ``pip install``, but skips
actually installing the packages and outputs a list of packages and versions
instead.


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
