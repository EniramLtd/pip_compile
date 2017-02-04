"""Compile requirements files against pin files"""
import json

import os
import pip
import sys
from pip import cmdoptions, logger
from pip.basecommand import RequirementCommand
from pip.exceptions import InstallationError
from pip.req import RequirementSet, parse_requirements
from pip.utils.build import BuildDirectory
from pip.utils.filesystem import check_path_owner
from pip.wheel import WheelCache, WheelBuilder

try:
    import wheel
except ImportError:
    wheel = None

PIP_MAJOR_VERSION = int(pip.__version__.split('.')[0])


class PipCompileRequirementSet(RequirementSet):
    """A RequirementSet with support for the compile subcommand

    Adds support for allowing double requirements when a constraint file is
    used.

    """
    def __init__(self, *args, **kwargs):
        self._allow_double = kwargs.pop('allow_double', False)
        super(PipCompileRequirementSet, self).__init__(*args, **kwargs)

    def add_requirement(self, install_req, parent_req_name=None,
                        **kwargs):
        """Add install_req as a requirement to install.

        :param parent_req_name: The name of the requirement that needed this
            added. The name is used because when multiple unnamed requirements
            resolve to the same name, we could otherwise end up with dependency
            links that point outside the Requirements set. parent_req must
            already be added. Note that None implies that this is a user
            supplied requirement, vs an inferred one.
        :param extras_requested: an iterable of extras used to evaluate the
            environement markers (only pip>=9.0.0).
        :return: Additional requirements to scan. That is either [] if
            the requirement is not applicable, or [install_req] if the
            requirement is applicable and has just been added.

        *pip_compile modifications:*

        This implementation has been copied verbatim from pip 7.1.2, and the
        only modification is the new else clause which handles duplicate
        constraints.

        The signature contains ``**kwargs`` instead of ``extras_requested=``
        since that keyword argument only appeared in 9.0.0 and we still want to
        support pip 8.1.2.

        """
        name = install_req.name
        if not install_req.match_markers(**kwargs):
            logger.warning("Ignoring %s: markers %r don't match your "
                           "environment", install_req.name,
                           install_req.markers)
            return []

        install_req.as_egg = self.as_egg
        install_req.use_user_site = self.use_user_site
        install_req.target_dir = self.target_dir
        install_req.pycompile = self.pycompile
        if not name:
            # url or path requirement w/o an egg fragment
            self.unnamed_requirements.append(install_req)
            return [install_req]
        else:
            try:
                existing_req = self.get_requirement(name)
            except KeyError:
                existing_req = None
            if (parent_req_name is None and existing_req and not
                    existing_req.constraint):
                if self._allow_double:
                    logger.warn('Allowing double requirement: {} (already in '
                                '{}, name={!r}).'
                                .format(install_req, existing_req, name))
                else:
                    raise InstallationError(
                        'Double requirement given: %s (already in %s, name=%r)'
                        % (install_req, existing_req, name))
            if not existing_req:
                # Add requirement
                self.requirements[name] = install_req
                # FIXME: what about other normalizations?  E.g., _ vs. -?
                if name.lower() != name:
                    self.requirement_aliases[name.lower()] = name
                result = [install_req]
                # FIXME: Should result be empty if install_req is a constraint?
            else:
                if not existing_req.constraint:
                    # No need to scan, we've already encountered this for
                    # scanning.
                    result = []
                elif not install_req.constraint:
                    # If we're now installing a constraint, mark the existing
                    # object for real installation.
                    existing_req.constraint = False
                    # Bugfix for pip 7.1.2: Report the origin of the actual
                    # package for installation (i.e. the -r file) instead of a
                    # constraint file.
                    existing_req.comes_from = install_req.comes_from
                    # And now we need to scan this.
                    result = [existing_req]
                else:  # both existing_req and install_req are constraints
                    # This else clause is an extension to pip 7.1.12:
                    # VCS links override plain package specifiers
                    # if there are duplicates in constraints.
                    if install_req.link and not existing_req.link:
                        # Our assumption is that dependencies are populated only
                        # later. Is this correct?
                        assert not self._dependencies
                        if name != existing_req.name:
                            # The Requirement class has no __delitem__()
                            del self.requirements._dict[existing_req.name]
                            self.requirements._keys.remove(existing_req.name)
                        self.requirements[name] = install_req
                        if name.lower() != name:
                            self.requirement_aliases[name.lower()] = name
                    elif not install_req.link and existing_req.link:
                        # Only the existing constraint was a link, so abandon
                        # the new looser constraint
                        pass
                    else:
                        # All other constraint conflicts are unresolved for the
                        # time being.
                        raise InstallationError(
                                'Duplicate constraint {}, existing {}'
                                .format(install_req, existing_req))
                    result = []
                # Canonicalise to the already-added object for the backref
                # check below.
                install_req = existing_req
            if parent_req_name:
                parent_req = self.get_requirement(parent_req_name)
                self._dependencies[parent_req].append(install_req)
            return result

    def to_dict(self):
        return {str(package.req): [str(dependency.req)
                                   for dependency in dependencies]
                for package, dependencies in self._dependencies.items()}


class CompileCommand(RequirementCommand):
    """
    Compile a list of required packages and versions which are pinned to
    a list of constraints. Packages are retrieved from:

    - PyPI (and other indexes) using requirement specifiers.
    - VCS project urls.
    - Local project directories.
    - Local or remote source archives.

    pip_compile also supports compiling the list from "requirements files",
    which provide an easy way to specify a whole environment to be installed.

    This command was modelled after the built-in "install" command in Pip 7.1.2,
    with several options and steps removed which are only relevant for actually
    installing the packages, and are not needed when only compiling a list of
    requirements.

    """
    name = 'compile'

    usage = """
      pip_compile.py [options] -c <constraints file> <requirement specifier> [package-index-options] ...
      pip_compile.py [options] -c <constraints file> -r <requirements file> [package-index-options] ...
      pip_compile.py [options] -c <constraints file> [-e] <vcs project url> ...
      pip_compile.py [options] -c <constraints file> <archive url/path> ..."""

    summary = 'Compile pinned packages.'

    def __init__(self, *args, **kw):
        super(RequirementCommand, self).__init__(*args, **kw)

        cmd_opts = self.cmd_opts

        cmd_opts.add_option(cmdoptions.constraints())
        cmd_opts.add_option(cmdoptions.editable())
        cmd_opts.add_option(cmdoptions.requirements())
        cmd_opts.add_option(cmdoptions.build_dir())

        # pip_compile omits the following 'pip install' command line options:
        #     '-t', '--target'
        #     dest='target_dir'
        #     '-d', '--download', '--download-dir', '--download-directory'
        #     dest='download_dir'
        # cmd_opts.add_option(cmdoptions.download_cache())

        cmd_opts.add_option(cmdoptions.src())

        # pip_compile omits the following 'pip install' command line options:
        #     '-U', '--upgrade'
        #     '--force-reinstall'
        #     '-I', '--ignore-installed'

        cmd_opts.add_option(cmdoptions.no_deps())

        cmd_opts.add_option(cmdoptions.install_options())
        cmd_opts.add_option(cmdoptions.global_options())

        # pip_compile omits the following 'pip install' command line options:
        #     '--user'
        #     dest='use_user_site'
        #     '--egg'
        #     dest='as_egg'
        #     '--root'
        #     dest='root_path'
        #     '--prefix'
        #     dest='prefix_path'
        #     "--compile"
        #     "--no-compile"
        #     dest="compile"

        cmd_opts.add_option(cmdoptions.use_wheel())
        cmd_opts.add_option(cmdoptions.no_use_wheel())
        cmd_opts.add_option(cmdoptions.no_binary())
        cmd_opts.add_option(cmdoptions.only_binary())
        cmd_opts.add_option(cmdoptions.pre())
        cmd_opts.add_option(cmdoptions.no_clean())
        cmd_opts.add_option(cmdoptions.require_hashes())

        # pip_compile adds the --flat, --output, --json-output and
        # --allow-double command line options:
        cmd_opts.add_option(
            '--flat',
            action='store_true',
            default=False,
            help='Do not recurse into dependencies.')
        cmd_opts.add_option(
            '-o',
            '--output',
            action='store',
            default=None,
            help='Output the list of pinned packages to the given path.')
        cmd_opts.add_option(
            '-j',
            '--json-output',
            action='store',
            default=None,
            help='Output a dependency graph of pinned packages as JSON to the '
                 'given path.')
        cmd_opts.add_option(
            '--allow-double',
            action='store_true',
            default=False,
            help="Allow double requirements.")

        index_opts = cmdoptions.make_option_group(
            cmdoptions.index_group,
            self.parser,
        )

        self.parser.insert_option_group(0, index_opts)
        self.parser.insert_option_group(0, cmd_opts)

    def run(self, options, args):
        if options.allow_double and not options.constraints:
            raise Exception('--allow-double can only be used together with -c /'
                            '--constraint')
        cmdoptions.resolve_wheel_no_use_binary(options)
        cmdoptions.check_install_build_global(options)

        # Removed handling for the following options which are not included in
        # pip_compile:
        # options.allow_external
        # options.allow_all_external
        # options.allow_unverified
        # options.download_dir
        # options.ignore_installed

        if options.build_dir:
            options.build_dir = os.path.abspath(options.build_dir)

        options.src_dir = os.path.abspath(options.src_dir)

        # pip_compile skips building of install_options since it doesn't install
        # anything:
        # options.use_user_site:
        #   --user
        #   --prefix=
        # options.target_dir:
        #   options.ignore_installed
        #   --home=
        # options.global_options

        with self._build_session(options) as session:

            finder = self._build_package_finder(options, session)
            build_delete = (not (options.no_clean or options.build_dir))
            wheel_cache = WheelCache(options.cache_dir, options.format_control)
            if options.cache_dir and not check_path_owner(options.cache_dir):
                logger.warning(
                    "The directory '%s' or its parent directory is not owned "
                    "by the current user and caching wheels has been "
                    "disabled. check the permissions and owner of that "
                    "directory. If executing pip with sudo, you may want "
                    "sudo's -H flag.",
                    options.cache_dir,
                )
                options.cache_dir = None

            with BuildDirectory(options.build_dir,
                                delete=build_delete) as build_dir:
                requirement_set = PipCompileRequirementSet(
                    build_dir=build_dir,
                    src_dir=options.src_dir,
                    download_dir=None,  # not needed
                    # upgrade - option not needed
                    # as_egg - option not needed
                    ignore_installed=True,  # always ignore installed
                    ignore_dependencies=options.ignore_dependencies,
                    # force_reinstall - option not needed
                    # use_user_site - option not needed
                    # target_dir - option not needed
                    session=session,
                    # pycompile - option not needed
                    isolated=options.isolated_mode,
                    wheel_cache=wheel_cache,
                    # require_hashes - option not needed?
                    allow_double=options.allow_double
                )

                self.populate_requirement_set(
                    requirement_set, args, options, finder, session, self.name,
                    wheel_cache
                )

                # Additional pip_compile functionality: constraints
                constraints = set()
                for filename in options.constraints:
                    for req in parse_requirements(
                            filename,
                            constraint=True, finder=finder, options=options,
                            session=session, wheel_cache=wheel_cache):
                        constraints.add(req.name)
                missing_constraints = [
                    req.name for req in requirement_set._to_install()
                    if req.name not in constraints]
                if missing_constraints:
                    raise Exception(
                        'Package(s) missing from constraints {}:\n{}'
                        .format(options.constraints,
                                ', '.join(missing_constraints)))

                # Conditions for whether to build wheels differ in pip_compile
                # from original pip:
                if not options.flat and requirement_set.has_requirements:
                    if not wheel or not options.cache_dir:

                        # on -d don't do complex things like building
                        # wheels, and don't try to build wheels when wheel is
                        # not installed.
                        requirement_set.prepare_files(finder)
                    else:
                        # build wheels before install.
                        wb = WheelBuilder(
                            requirement_set,
                            finder,
                            build_options=[],
                            global_options=[],
                        )
                        # Ignore the result: a failed wheel will be
                        # installed from the sdist/vcs whatever.
                        wb.build(autobuilding=True)

        # pip_compile adds printing out the compiled requirements:
        if options.output == '-':
            print_requirements(requirement_set)
        elif options.output:
            with open(options.output, 'w') as output:
                print_requirements(requirement_set, output)

        if options.json_output == '-':
            json.dump(requirement_set.to_dict(), sys.stdout, indent=4)
        elif options.json_output:
            with open(options.json_output, 'w') as output:
                json.dump(requirement_set.to_dict(), output, indent=4)

        # pip_compile skips package installation

        return requirement_set


def print_requirements(requirement_set, output=sys.stdout):
    for req in requirement_set._to_install():
        if req.link and req.link.url.startswith('git+'):
            output.write('{editable}{link}\n'
                         .format(editable='-e ' if req.editable else '',
                                 link=req.link))
        else:
            output.write('{editable}{name}{specifier}\n'
                         .format(editable='-e ' if req.editable else '',
                                 name=req.name,
                                 specifier=req.specifier))


def main():
    CompileCommand().main(sys.argv[1:])


if __name__ == '__main__':
   main()
