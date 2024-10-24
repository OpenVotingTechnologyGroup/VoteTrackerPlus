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

"""
Logic of operation for running a mock election.  See the --help output
or the README.md file in the src/vtp directory for details.
"""

# Standard imports
import os
import time

# Project imports
from vtp.core.address import Address
from vtp.core.ballot import Ballot
from vtp.core.election_config import ElectionConfig
from vtp.ops.accept_ballot_operation import AcceptBallotOperation
from vtp.ops.cast_ballot_operation import CastBallotOperation
from vtp.ops.merge_contests_operation import MergeContestsOperation
from vtp.ops.tally_contests_operation import TallyContestsOperation

# Local imports
from .operation import Operation


class RunMockElectionOperation(Operation):
    """
    A class to implememt the run-mock-election operation.  See the
    run-mock-election help output or read the parse_argument argparse
    description (immediately below this) in the source file.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # problem child
    def scanner_mockup(
        self,
        the_election_config: ElectionConfig,
        ballot: str,
        iterations: int,
        device: str,
        flush_mode: int,
        minimum_cast_cache: int,
        duration: int,
        version_receipts: bool,
    ):
        """Simulate a VTP scanner"""

        # Get list of available blank ballots
        blank_ballots = []
        if ballot:
            # a blank ballot location was specified (either directly or via an address)
            blank_ballots.append(ballot)
        else:
            with self.changed_cwd(the_election_config.get("git_rootdir")):
                for dirpath, _, files in os.walk("."):
                    for filename in [
                        f
                        for f in files
                        if f.endswith(",ballot.json")
                        and dirpath.endswith("blank-ballots/json")
                    ]:
                        blank_ballots.append(os.path.join(dirpath, filename))
        # Loop over the list N times
        if not blank_ballots:
            raise ValueError("found no blank ballots to cast")
        start_time = time.time()
        seconds = 60 * duration
        count = 0
        while True:
            count += 1
            for blank_ballot in blank_ballots:
                if duration:
                    self.imprimir(
                        f"Iteration {count} - processing {blank_ballot}",
                        3,
                    )
                else:
                    self.imprimir(
                        f"Iteration {count} of {iterations} - processing {blank_ballot}",
                        3,
                    )
                # - cast a ballot
                with self.changed_cwd(the_election_config.get("git_rootdir")):
                    self.shell_out(
                        ["git", "pull"],
                        timeout=None,
                        check=True,
                        incoming_printlevel=4,
                    )
                # import pdb; pdb.set_trace()
                cast_ballot = CastBallotOperation(
                    election_data_dir=self.election_data_dir,
                    verbosity=self.verbosity,
                    printonly=self.printonly,
                )
                cast_ballot.run(
                    blank_ballot=blank_ballot,
                    demo_mode=True,
                )
                # - accept the ballot
                accept_ballot = AcceptBallotOperation(
                    election_data_dir=self.election_data_dir,
                    verbosity=self.verbosity,
                    printonly=self.printonly,
                )
                accept_ballot.run(
                    cast_ballot=Ballot.get_cast_from_blank(blank_ballot),
                    version_receipts=version_receipts,
                )
                if device == "both":
                    # - merge the ballot's contests
                    if flush_mode == 2:
                        # Since casting and merging is basically
                        # synchronous, no need for an extra large timeout
                        merge_contests = MergeContestsOperation(
                            election_data_dir=self.election_data_dir,
                            verbosity=self.verbosity,
                            printonly=self.printonly,
                        )
                        merge_contests.run(
                            flush=True,
                        )
                    else:
                        # Should only need to merge one ballot worth of
                        # contests - also no need for an extra large
                        # timeout
                        merge_contests = MergeContestsOperation(
                            election_data_dir=self.election_data_dir,
                            verbosity=self.verbosity,
                            printonly=self.printonly,
                        )
                        merge_contests.run(
                            minimum_cast_cache=minimum_cast_cache,
                        )
                    # don't let too much garbage build up
                    if count % 10 == 9:
                        self.shell_out(
                            ["git", "gc"],
                            timeout=None,
                            check=True,
                            incoming_printlevel=4,
                        )
            if iterations and count >= iterations:
                break
            if seconds:
                elapsed_time = time.time() - start_time
                if elapsed_time > seconds:
                    break
        if device == "both":
            # merge the remaining contests
            # Note - this needs a longer timeout as it can take many seconds
            merge_contests = MergeContestsOperation(
                election_data_dir=self.election_data_dir,
                verbosity=self.verbosity,
                printonly=self.printonly,
            )
            merge_contests.run(
                flush=True,
            )
            # tally the contests
            tally_contests = TallyContestsOperation(
                election_data_dir=self.election_data_dir,
                verbosity=self.verbosity,
                printonly=self.printonly,
            )
            tally_contests.run()
        # clean up git just in case
        self.shell_out(
            ["git", "remote", "prune", "origin"],
            timeout=None,
            check=True,
            incoming_printlevel=4,
        )
        self.shell_out(
            ["git", "gc"],
            timeout=None,
            check=True,
            incoming_printlevel=4,
        )

    # pylint: disable=too-many-positional-arguments
    def tabulator_mockup(
        self,
        the_election_config: ElectionConfig,
        flush_mode: int,
        duration: int,
        minimum_cast_cache: int,
        iterations: int,
    ):
        """Simulate a VTP tabulator"""
        # This is the VTP tabulator simulation code.  In this case, the VTP
        # scanners are pushing to an ElectionData remote and this (tabulator)
        # needs to pull from the ElectionData remote.  And, in this case
        # the branches to be merged are remote and not local.
        start_time = time.time()
        # Loop for a day and sleep for 10 seconds
        seconds = 60 * duration
        count = 0

        while True:
            count += 1
            with self.changed_cwd(the_election_config.get("git_rootdir")):
                self.shell_out(
                    ["git", "pull"],
                    timeout=None,
                    check=True,
                    incoming_printlevel=4,
                )
            if flush_mode == 2:
                merge_contests = MergeContestsOperation(
                    election_data_dir=self.election_data_dir,
                    verbosity=self.verbosity,
                    printonly=self.printonly,
                )
                merge_contests.run(
                    remote=True,
                    flush=True,
                )
                tally_contests = TallyContestsOperation(
                    election_data_dir=self.election_data_dir,
                    verbosity=self.verbosity,
                    printonly=self.printonly,
                )
                tally_contests.run()
                return
            merge_contests = MergeContestsOperation(
                election_data_dir=self.election_data_dir,
                verbosity=self.verbosity,
                printonly=self.printonly,
            )
            merge_contests.run(
                remote=True,
                minimum_cast_cache=minimum_cast_cache,
            )
            if iterations and count >= iterations:
                break
            self.imprimir(f"Sleeping for 10 (iteration={count})", 3)
            time.sleep(10)
            elapsed_time = time.time() - start_time
            if not iterations and elapsed_time > seconds:
                break
        if flush_mode in [1, 2]:
            print("Cleaning up remaining unmerged ballots")
            merge_contests = MergeContestsOperation(
                election_data_dir=self.election_data_dir,
                verbosity=self.verbosity,
                printonly=self.printonly,
            )
            merge_contests.run(
                remote=True,
                flush=True,
            )
        # tally the contests
        # tally_contests = TallyContestsOperation(
        #     election_data_dir=self.election_data_dir,
        #     verbosity=self.verbosity,
        #     printonly=self.printonly,
        # )
        # tally_contests.run()

    # pylint: disable=duplicate-code
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def run(
        self,
        an_address: Address = None,
        blank_ballot: str = "",
        device: str = "",
        minimum_cast_cache: int = 100,
        flush_mode: int = 0,
        iterations: int = 10,
        duration: int = 0,
        version_receipts: bool = False,
    ):
        """Main function - see -h for more info

        Note - this is a serial synchronous mock election loop.  A
        parallel loop would have one VTP tabulator git workspace somewhere
        and N VTP scanner workspaces someplace else.  Depending on the
        network topology, it is also possible to start up VTP scanner
        workspaces on other machines as long as the git remotes and clones
        are properly configured (with access etc).

        While a mock election is running, it is also possible to use yet
        another VTP scanner workspace to personally cast/insert individual
        ballots for interactive purposes.

        Assumes that each supplied town already has the blank ballots
        generated and/or already committed.
        """

        # Create a VTP ElectionData object if one does not already exist
        the_election_config = ElectionConfig.configure_election(
            self,
            self.election_data_dir,
        )

        # If an address was used, use that
        if an_address is not None:
            an_address.map_ggos(the_election_config)
            blank_ballot = the_election_config.gen_blank_ballot_location(
                an_address.active_ggos, an_address.ballot_subdir
            )

        # the VTP scanner mock simulation
        if device in ["scanner", "both"]:
            self.scanner_mockup(
                the_election_config=the_election_config,
                ballot=blank_ballot,
                iterations=iterations,
                device=device,
                flush_mode=flush_mode,
                minimum_cast_cache=minimum_cast_cache,
                duration=duration,
                version_receipts=version_receipts,
            )
        elif device == "tabulator":
            self.tabulator_mockup(
                the_election_config=the_election_config,
                flush_mode=flush_mode,
                duration=duration,
                minimum_cast_cache=minimum_cast_cache,
                iterations=iterations,
            )
        else:
            raise ValueError(f"an illegal value was supplied for device ({device})")


# EOF
