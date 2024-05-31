#!/usr/bin/env python

#  VoteTrackerPlus
#   Copyright (C) 2022 Sandy Currier
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Will test versions of stuff - a TBD"""


import os
import sys

import pytest

# Project imports
from vtp.core.address import Address
from vtp.core.election_config import ElectionConfig
from vtp.ops.vote_operation import VoteOperation


################
# Fixtures
################
# https://stackoverflow.com/questions/46089480/pytest-fixtures-redefining-name-from-outer-scope-pylint
@pytest.fixture(name="main_street_address")
def fixture_main_street_address():
    """Returns a main street address in csv form"""
    return "123, Main Street, Concord, Massachusetts"


@pytest.fixture(name="election_data_dir")
def fixture_election_data_dir():
    """Returns the local (to this VoteTrackerPlus repo) ElectionData dir"""
    return "../VTP-mock-election.US.17"


################
# test points
################


# save the user from themselves
def test_python_version():
    """Test python version - needs to run in older versions ..."""
    assert sys.version_info.major == 3 and sys.version_info.minor >= 10


def test_address(main_street_address):
    """Test that an address object can be created and accessed"""
    an_address = Address(csv=main_street_address)
    assert an_address.get("number") == "123"
    assert an_address.get("street") == "Main Street"
    assert an_address.get("town") == "Concord"
    assert an_address.get("state") == "Massachusetts"


def test_electiondata(election_data_dir, verbosity=3, printonly=False):
    """The test fixtures are more or less based on the specific
    ElectionData repo - tests that it exists
    """
    # Note - need an ops instance.  The vote ops constructor does not
    # write to disk and if it does not error, will be inspectable
    vote_operation = VoteOperation(
        election_data_dir=election_data_dir,
        verbosity=verbosity,
        printonly=printonly,
    )
    # with the ops instance get the ElectionConfig
    the_election_config = ElectionConfig.configure_election(
        vote_operation,
        vote_operation.election_data_dir,
    )
    # just making sure
    assert os.path.basename(the_election_config.get("git_rootdir")) == os.path.basename(
        election_data_dir
    )
    # in VTP-mock-election.US.17 there are 6 config files to parse
    assert len(the_election_config.parsed_configs) == 6
    # ... the third node has the same uid
    assert (
        the_election_config.get_node(the_election_config.get_dag("topo")[3], "uid")
        == "003"
    )
    # ... and is a town
    assert (
        the_election_config.get_node(the_election_config.get_dag("topo")[3], "kind")
        == "towns"
    )
