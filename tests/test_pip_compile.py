from io import StringIO
from unittest import TestCase

import pytest
from pip import InstallationError
from pip.index import Link
from pip.req import InstallRequirement, RequirementSet

import pip_compile


class PipCompileRequirementSetTestCase(TestCase):
    def setUp(self):
        self.requirement_set = pip_compile.PipCompileRequirementSet(
                None, None, None, session='dummy')
        self.expected = None  # exception expected

    def tearDown(self):
        if self.expected is not None:
            assert [str(req)
                    for req in self.requirement_set.requirements.values()] \
                   == self.expected

    def test_conflicting_constraint(self):
        """Currently, conflicts ignore versions of actual requirements"""
        self.requirement_set.add_requirement(
                InstallRequirement('pkg==1.0.1', None, constraint=True))
        self.requirement_set.add_requirement(
                InstallRequirement('pkg==1.0.2', None))
        self.expected = ['pkg==1.0.1']

    def test_mutually_conflicting_constraints(self):
        """Currently, conflicts ignore versions of actual requirements"""
        self.requirement_set.add_requirement(
                InstallRequirement('pkg==1.0.1', None, constraint=True))
        with pytest.raises(InstallationError):
            self.requirement_set.add_requirement(
                InstallRequirement('pkg==1.0.2', None, constraint=True))

    def test_mutually_conflicting_link_constraints(self):
        """Currently, constraint link conflicts are unresolved"""
        self.requirement_set.add_requirement(
            InstallRequirement(
                'pkg', None,
                link=Link('git+ssh://git@server/pkg.git@1.0'),
                constraint=True))
        with pytest.raises(InstallationError):
            self.requirement_set.add_requirement(
                InstallRequirement(
                    'pkg', None,
                    link=Link('git+ssh://git@server/pkg.git@2.0'),
                    constraint=True))

    def test_link_constraint_overrides_version_constraint(self):
        """Currently, constraints with links override other versions"""
        self.requirement_set.add_requirement(
            InstallRequirement('pkg==1.0', None, constraint=True))
        self.requirement_set.add_requirement(
            InstallRequirement(
                'pkg', None,
                link=Link('git+ssh://git@server/pkg.git@2.0'),
                constraint=True))
        self.expected = ['pkg from git+ssh://git@server/pkg.git@2.0']

    def test_version_constraint_ignored_after_link_constraint(self):
        """Currently, constraints with versions ignored after ones with links"""
        self.requirement_set.add_requirement(
            InstallRequirement(
                'pkg', None,
                link=Link('git+ssh://git@server/pkg.git@2.0'),
                constraint=True))
        self.requirement_set.add_requirement(
            InstallRequirement('pkg==1.0', None, constraint=True))
        self.expected = ['pkg from git+ssh://git@server/pkg.git@2.0']


class PrintRequirementsTestCase(TestCase):
    def setUp(self):
        self.requirement_set = RequirementSet(None, None, None,
                                              session='dummy')

    def tearDown(self):
        output = StringIO()
        pip_compile.print_requirements(self.requirement_set, output=output)
        assert output.getvalue() == self.expected

    def test_no_requirements(self):
        self.expected = ''

    def test_one_requirement_no_version(self):
        self.requirement_set.add_requirement(
            InstallRequirement('pkg', None))
        self.expected = 'pkg\n'

    def test_one_requirement_with_version(self):
        self.requirement_set.add_requirement(
            InstallRequirement('pkg==1.0.1', None))
        self.expected = 'pkg==1.0.1\n'

    def test_one_requirement_with_constraint(self):
        self.requirement_set.add_requirement(
            InstallRequirement('pkg==1.0.1', None, constraint=True))
        self.requirement_set.add_requirement(
            InstallRequirement('pkg==1.0.2-ignored', None))
        self.expected = 'pkg==1.0.1\n'
