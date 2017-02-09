0.1.2 / 2017-02-09
==================
- Relaxed the requirement for pinning to a specific version in constraints. If a
  requirement is pinned to a version or downloaded from a link, it doesn't need
  to exist in constraints.

0.1.1 / 2017-02-08
==================
- Raise an exception if requirement and constraint links don't match for a
  package, or if requirement is ``--editable`` but the constraint isn't.
  Fixes #2.

0.1.0 / 2017-02-04
==================
- Added the ``--allow-double`` command line option.

0.0.1 / 2017-01-30
==================
- First release.