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
merge_contests.py - command line level script to merge CVR contest
branches into the master branch

See './merge_contests.py -h' for usage information.

See ../docs/tech/merge_contests.md for the context in which this
file was created.
"""

# Standard imports
# pylint: disable=wrong-import-position   # import statements not top of file
import sys
import os
import re
import random
import argparse
import logging
from logging import debug

# Local import
from common import Globals, Shellout
from election_config import ElectionConfig

# Functions
def randomly_merge_contests(uid, batch):
    """
    Will randomingly select (len(batch) - BALLOT_RECEIPT_ROWS) contest
    branches from the supplied list of branch and merge them to the
    master branch.

    This is the git merge-to-master sequence.
    """
    rows = Globals.get('BALLOT_RECEIPT_ROWS')
    if len(batch) <= rows:
        if args.flush:
            count = len(batch)
        else:
            debug(f"Contest {uid} not merged - only {len(batch)} available")
            return 0
    else:
        count = len(batch) - rows
    loop = count
    while loop:
        pick = random.randrange(len(batch))
        branch = batch[pick]
        # If the VTP server is processing contests from different
        # voting centers, then the contest.json could be in different
        # locations on different branches.
        contest_file = Shellout.run(
            ['git', 'diff-tree', '--no-commit-id', '-r', '--name-only', branch],
            capture_output=True, text=True).stdout.strip()
        Shellout.run(
            ['git', 'merge', '--no-ff', '--no-commit', branch],
            args.printonly)
        # ZZZ - replace this with an run-time cryptographic value
        # derived from the run-time election private key (diffent from
        # the git commit run-time value).  This will basically slam
        # the contents of the contest file to a second runtime digest
        # (the first one being contained in the commit itself).
        result = Shellout.run(
            ['openssl',  'rand', '-base64',  '48'], capture_output=True, text=True)
        if result.stdout == '':
            raise ValueError("'openssl rand' should never return an empty string")
        if not args.printonly:
            # ZZZ need to convert the digest to json format ...
            with open(contest_file, 'w', encoding="utf8") as outfile:
                # Write a runtime digest as the actual contents of the
                # merge
                outfile.write(str(result.stdout))
        # Force the git add just in case
        Shellout.run(['git', 'add', contest_file], args.printonly)
        # Use the default merge message as is
        Shellout.run(['git', 'commit'], args.printonly)
        Shellout.run(['git', 'push', 'origin', 'master'], args.printonly)
        # Delete both the local and remote branch
        Shellout.run(['git', 'branch', '-d', batch[pick]], args.printonly)
        Shellout.run(['git', 'push', 'origin', ':' + batch[pick]], args.printonly)
        # End of loop maintenance
        del batch[pick]
        loop -= 1
    debug(f"Merged {count} {uid} contests")
    return count

################
# arg parsing
################
# pylint: disable=duplicate-code
def parse_arguments():
    """Parse arguments from a command line"""

    parser = argparse.ArgumentParser(description=
    """merge_contests.py will run the git based workflow on a VTP
    server node so to merge pending CVR contest branches into the
    master git branch.

    If there are less then the prerequisite number of already cast
    contests, a warning will be printed/logged but no error will be
    raised.  Supplying -f will flush all remaining contests to the
    master branch.
    """,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("-f", "--flush", action='store_true',
                            help="will flush the remaining unmerged contest branches")
    parser.add_argument("-v", "--verbosity", type=int, default=3,
                            help="0 critical, 1 error, 2 warning, 3 info, 4 debug (def=3)")
    parser.add_argument("-n", "--printonly", action="store_true",
                            help="will printonly and not write to disk (def=True)")

    parsed_args = parser.parse_args()
    verbose = {0: logging.CRITICAL, 1: logging.ERROR, 2: logging.WARNING,
                   3: logging.INFO, 4: logging.DEBUG}
    logging.basicConfig(format="%(message)s", level=verbose[parsed_args.verbosity],
                            stream=sys.stdout)

    # Validate required args
    return parsed_args

################
# main
################
# pylint: disable=duplicate-code
def main():
    """Main function - see -h for more info"""

    # Create an VTP election config object
    the_election_config = ElectionConfig()
    the_election_config.parse_configs()

    # Set the three EV's
    os.environ['GIT_AUTHOR_DATE'] = '2022-01-01T12:00:00'
    os.environ['GIT_COMMITTER_DATE'] = '2022-01-01T12:00:00'
    os.environ['GIT_EDITOR'] = 'true'

    # For best results (so to use the 'correct' git submodule or
    # tranverse the correct symlink or not), use the CWD as when
    # accepting the ballot (accept_ballot.py).
    with Shellout.changed_cwd(os.path.join(
        the_election_config.get('git_rootdir'),
        Globals.get('ROOT_ELECTION_DATA_SUBDIR'))):
        # So, the CWD in this block is the state/town subfolder
        # Pull the remote
        Shellout.run(["git", "pull"], args.printonly, check=True)
        # Get the pending CVR branches
        cvr_branches = [branch.strip() for branch in Shellout.run(
            ['git', 'branch'],
            check=True, capture_output=True,
            text=True).stdout.splitlines() if re.search(
                f"^{Globals.get('CONTEST_FILE_SUBDIR')}/", branch.strip())]
        # Note - sorted alphanumerically on contest UID. Loop over
        # contests and randomly merge extras
        batch = []
        current_uid = None
        for branch in cvr_branches:
#            import pdb; pdb.set_trace()
            uid = re.search(f"^{Globals.get('CONTEST_FILE_SUBDIR')}/([^/]+?)/",
                                branch).group(1)
            if current_uid == uid:
                batch.append(branch)
                continue
            if current_uid:
                # see if previous batch can be merged
                if args.flush or len(batch) >= Globals.get('BALLOT_RECEIPT_ROWS'):
                    randomly_merge_contests(uid, batch)
            # Start a new next batch
            current_uid = uid
            batch = [branch]

if __name__ == '__main__':
    args = parse_arguments()
    main()

# EOF
