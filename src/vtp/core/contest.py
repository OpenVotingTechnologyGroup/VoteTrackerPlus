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

"""How to manage a VTP specific contest"""

import json

# local
from .common import Globals


class Contest:
    """
    A class to handle the rules of engagement regarding a specific
    contest.  A contest is a dict.

    Some historical design notes.  A ballot originally had contests
    being a funky dict in version 0.1.0. However, in version 0.2.0
    contests was changed to an ordered list, greatly simplifying some
    low level logic.  The git log entry in 0.1.0 also ended up having
    an analogous dictionary with an outer "CVR" key.  This has also
    become OBE and so in 0.2.0 the git log entry is now just a simple
    one level dictionary.

    At the same time in an effort to simplify things, the contest
    selection logic was moved from the Ballot class to this class
    while changing the Ballot class to _always_ create Contest objects
    when it encounters a contest.

    Note - the contest is a dict with the following set-able keys:
    - choices: a list of choices, each choice is either a string or a dict
      with the keys 'name' and optionally 'party' and 'ticket_names'
    - tally: the tally type, either 'plurality', 'rcv', 'pwc', or 'stv'
      For multiseat, rcv is a sequential rcv while stv is proportional rcv
    - win_by: currently defunct though it started out being setable to support
      non simple majority plurality contests.  For sequential rcv it is statically
      set to '> 50%'.  For proportional rcv it is set to the Droop quota:
      (1 / 1 + open_positions) + 1.
    - max_selections: the maximum number of selections a voter may select.  Defaults
      to 1 for plurality and the number of choices for RCV.
    - open_positions: number of open positions.  Defaults to 1 for both plurality and RCV.
      This is basically the number of open seats.
    - write_in: a boolean indicating if write-in votes are allowed, defaults to False
    - description: a optional string describing the contest
    - contest_type: the type of contest, either 'candidate', 'ticket', or 'question'
    - ticket_titles: a list of titles for the tickets, only used in ticket contests
    - election_upstream_remote: a string indicating the upstream remote for the election,
      used for voter UX
    - contest_name: a string indicating the name of the contest
    - ggo: a string indicating the GGO (General Governmental Organization) for the contest

    The contest also has the following keys that are not part of the
    contest dict but are used for internal tracking and management:
    - uid: a unique identifier for the contest, automatically generated.
    - selection: a list of selections made by the voter, can be empty.
    - cast_branch: a string indicating the branch of the cast vote, used for tracking.
    - name: a string indicating the name of the contest.
    """

    # Legitimate Contest keys.  Note 'selection', 'uid', 'cloak', and
    # 'name' are not legitimate keys for blank ballots.  Unless
    # otherwise explicitly stated, all the fields coming from the yaml
    # data are strings and not integers.
    _config_keys = [
        "choices",
        "tally",
        "win_by",  # when auto generated a float
        "max_selections",
        "open_positions",
        "write_in",
        "description",
        "contest_type",
        "ticket_titles",
        "election_upstream_remote",
        "contest_name",
        "ggo",
    ]
    _blank_ballot_keys = _config_keys + ["uid"]
    _cast_keys = _blank_ballot_keys + ["selection", "cast_branch"]
    _choice_keys = ["name", "party", "ticket_names"]

    # A simple numerical n digit uid
    _uids = {}
    _nextuid = 0

    @staticmethod
    def set_uid(a_contest_blob: dict, ggo: str):
        """Will add a globally unique contest uid (only good within
        the context of this specific election) to the supplied contest
        while caching the contest_name and ggo.
        """
        if "uid" in a_contest_blob:
            raise IndexError(
                f"The uid of contest {a_contest_blob['contest_name']} is already set"
            )
        a_contest_blob["uid"] = str(Contest._nextuid).rjust(4, "0")
        if Contest._nextuid not in Contest._uids:
            Contest._uids[Contest._nextuid] = {}
        Contest._uids[Contest._nextuid]["contest_name"] = a_contest_blob["contest_name"]
        Contest._uids[Contest._nextuid]["ggo"] = ggo
        Contest._nextuid += 1

    @staticmethod
    def get_uid_pp_name(uid: str):
        """Will return the contest pretty-print name of the global contest uid"""
        return uid + " - " + Contest._uids[int(uid)]["contest_name"]

    @staticmethod
    # pylint: disable=too-many-branches
    def check_contest_choices(choices: list, a_contest_blob: dict):
        """
        Will validate the syntax of the contest choices.  To validate
        a ticket contest, the outer context node now contains the
        ticket_titles while the inner node choice contains the paired
        ticket_names.  A a_contest_blob can be either a_contest_blob or
        a_cvr_blob.
        """
        # if this is a ticket contest, need to validate uber ticket syntax
        check_ticket = (
            "contest_type" in a_contest_blob
            and a_contest_blob["contest_type"] == "ticket"
        )
        for choice in choices:
            if isinstance(choice, str):
                continue
            if isinstance(choice, dict):
                bad_keys = [key for key in choice if key not in Contest._choice_keys]
                if bad_keys:
                    raise KeyError(
                        "the following keys are not valid Contest choice keys: "
                        f"{','.join(bad_keys)}"
                    )
                if check_ticket:
                    if "ticket_names" not in choice:
                        raise KeyError(
                            "Contest type is a ticket contest but does not contain ticket_names"
                        )
                    if len(choice["ticket_names"]) != len(
                        a_contest_blob["ticket_titles"]
                    ):
                        raise KeyError(
                            "when either 'ticket_names' or 'ticket_titles' are specified"
                            "the length of each array mush match - "
                            f"{len(choice['ticket_names'])} != {len(choice['ticket_names'])}"
                        )
                    if not isinstance(choice["ticket_names"], list):
                        raise KeyError("the key 'ticket_names' can only be a list")
                    if not isinstance(a_contest_blob["ticket_titles"], list):
                        raise KeyError("the key 'ticket_names' can only be a list")
                elif "ticket_names" in choice:
                    raise KeyError(
                        "contest_type is not a ticket contest but contains ticket_names"
                    )
                continue
            if isinstance(choice, bool):
                continue

    @staticmethod
    def check_contest_type(a_contest_blob: dict):
        """Will validate the value of contest_type"""
        if "contest_type" not in a_contest_blob or a_contest_blob[
            "contest_type"
        ] not in [
            "candidate",
            "ticket",
            "question",
        ]:
            raise KeyError(
                f"contest_type ({a_contest_blob['contest_type']}) must be specified "
                "as either: candidate, ticket, or question"
            )

    @staticmethod
    def check_selection(a_contest_blob: dict):
        """Will check the syntaz of the selection array"""

    @staticmethod
    # pylint: disable=too-many-branches
    def check_contest_blob_syntax(
        a_contest_blob: dict,
        filename: str = "",
        digest: str = "",
        set_defaults: bool = False,
    ):
        """
        Will check the syntax of a contest.

        Note - the filename and digest parameters only adjust
        potential error messages.

        If set_defaults is set, missing default values will be set.
        Four default adjustments can be made: max_selections, win_by,
        the "name" key for each choice, and election_upstream_remote
        """
        legal_fields = Contest._cast_keys
        bad_keys = [key for key in a_contest_blob if key not in legal_fields]
        if bad_keys:
            if filename:
                raise KeyError(
                    f"File ({filename}): "
                    f"the following keys are not valid Contest keys: "
                    f"{','.join(bad_keys)}"
                )
            if digest:
                raise KeyError(
                    f"Commit digest ({digest}): "
                    f"the following keys are not valid Contest keys: "
                    f"{','.join(bad_keys)}"
                )
            raise KeyError(
                f"the following keys are not valid Contest keys: "
                f"{','.join(bad_keys)}"
            )
        # Need to validate choices sub data structure as well
        Contest.check_contest_choices(a_contest_blob["choices"], a_contest_blob)
        Contest.check_contest_type(a_contest_blob)
        if "selection" in a_contest_blob:
            Contest.check_selection(a_contest_blob)
        if set_defaults:
            # If max_selections is not set, set it
            # import pdb; pdb.set_trace()
            if "max_selections" not in a_contest_blob:
                if a_contest_blob["tally"] == "plurality":
                    a_contest_blob["max_selections"] = 1
                else:
                    a_contest_blob["max_selections"] = len(a_contest_blob["choices"])
            # open_positions cannot be 0 and must be defined
            if "open_positions" not in a_contest_blob:
                raise KeyError(
                    "open_positions must be defined as a non zero postive integer - "
                    "it is not defined"
                )
            if not a_contest_blob["open_positions"].isdigit():
                raise KeyError(
                    "open_positions must be a non zero postive integer "
                    f"({a_contest_blob['open_positions']})"
                )
            open_positions = int(a_contest_blob["open_positions"])
            if open_positions < 1:
                raise KeyError(
                    "open_positions must be an integer greater than zero "
                    f"({a_contest_blob['open_positions']})"
                )
            # If win_by is not set
            if "win_by" not in a_contest_blob:
                # Note1: it is possible to set win_by in the
                # electionData when the contest is a simple contest
                # (non RCV).  When plurality it is a majority
                # regardless.  For RCV it is derived as a Droop quota:
                # GREATER than total votes/(k +1) where k =
                # open_positions.  win_by is just the percentage, not
                # the actual necessary vote count to be a winner.
                a_contest_blob["win_by"] = 1.0 / (open_positions + 1.0)
            elif "plurality" != a_contest_blob["tally"]:
                raise KeyError(
                    "setting win_by in a non plurality contest is not supported - "
                    "it does make sense"
                )
            # Add an empty selection if it does not exist
            if "selection" not in a_contest_blob:
                a_contest_blob["selection"] = []
            # If the contest choice is a string, convert it to dict (name)
            for index, choice in enumerate(a_contest_blob["choices"]):
                if isinstance(choice, str):
                    a_contest_blob["choices"][index] = {"name": choice}
            # For voter UX, add ELECTION_UPSTREAM_REMOTE
            a_contest_blob["election_upstream_remote"] = Globals.get(
                "ELECTION_UPSTREAM_REMOTE"
            )

    @staticmethod
    def get_choices_from_contest(choices: list):
        """Will smartly return just the pure list of choices sans all
        values and sub dictionaries.  An individual choice can either
        be a simple string, a regulare 1D dictionary, or it turns out
        a bool.  Returns a copy!
        """
        # Returns a pure list of choices sans any other values or sub dictionaries
        if isinstance(choices[0], str):
            return list(choices)
        if isinstance(choices[0], dict):
            return [entry["name"] for entry in choices]
        if isinstance(choices[0], bool):
            return ["True", "False"] if choices[0] else ["False", "True"]
        raise ValueError(
            f"unknown/unsupported contest choices data structure ({choices})"
        )

    def __init__(
        self,
        a_contest_blob: dict,
        set_defaults: bool = False,
    ):
        """Construct the object placing the contest info in an attribute
        while recording the meta data
        """
        # ZZZ import pdb; pdb.set_trace()
        # Note - Contest.check_contest_blob_syntax will set missing defaults
        Contest.check_contest_blob_syntax(
            a_contest_blob,
            set_defaults=set_defaults,
        )
        self.contest = a_contest_blob
        self.cloak = False

    def __str__(self):
        """Return the contest contents as a print-able json string - careful ..."""
        # Note - keep cloak out of it until proven safe to include
        contest_dict = {
            key: self.contest[key] for key in Contest._cast_keys if key in self.contest
        }
        return json.dumps(contest_dict, sort_keys=True, indent=4, ensure_ascii=False)

    def pretty_print_a_ticket(self, choice: str):
        """Will pretty print a ticket"""
        details = []
        for choice_index, ticket in enumerate(self.contest["choices"]):
            if ticket["name"] == choice:
                for name_index, title in enumerate(self.contest["ticket_titles"]):
                    # import pdb; pdb.set_trace()
                    details.append(
                        f"{title}: "
                        f"{self.contest['choices'][choice_index]['ticket_names'][name_index]}"
                    )
                return f"{choice} ({'; '.join(details)})"
        raise ValueError(
            f"pretty_print_a_ticket: supplied choice {choice} does not match "
            f"any of the possible choices ({self.get('choices')})"
        )

    def get(self, thing: str):
        """
        Generic getter - can raise KeyError.  When the parameter is
        'dict', will return an aggregated dictionary similar to when
        the object is printed.  If the parameter is 'contest', it
        returns the contest.

        Note - get'ing the choices will return the choice 'name's regardless
        of contest type.

        Note - 'contest' does NOT create/return a copy while 'dict'
        does not copy any deeper data structures.
        """
        if thing == "dict":
            # return the combined psuedo dictionary similar to __str__ above
            contest_dict = {
                key: self.contest[key]
                for key in Contest._cast_keys
                if key in self.contest
            }
            return contest_dict
        if thing == "contest":
            return self.contest
        if thing == "choices":
            return Contest.get_choices_from_contest(self.contest["choices"])
        # Return contest 'meta' data
        if thing in ["cloak"]:
            return getattr(self, thing)
        # Else return contest data itself indexed by thing
        return getattr(self, "contest")[thing]

    def set(self, thing: str, value: str):
        """Generic setter - need to be able to set things outside of contest dict"""
        if thing in ["cloak"]:
            setattr(self, thing, value)
            return
        # At the moment cast_branch is the only thing that needs to be set-able
        # after the constructor/initiator
        if thing in ["cast_branch"]:
            self.contest["cast_branch"] = value
            return
        raise ValueError(f"Illegal value for Contest attribute ({thing})")

    def clear_selection(self):
        """Clear the selection (as when self adjudicating)"""
        self.contest["selection"] = []

    def delete_contest_field(self, thing: str):
        """Generic deleter - need to be able to delete nodes"""
        if thing in Contest._cast_keys:
            if thing in self.contest:
                del self.contest[thing]
            return
        raise ValueError(f"Illegal value for Contest attribute ({thing})")

    def add_selection(self, selection: str = "", offset: int = -1):
        """Will add the specified contest choice as defined by the
        unique name string.  This is an 'add' since in plurality one
        may be voting for more than one choice, or in RCV one needs to
        rank the choices.  In both the order is the rank but in
        plurality rank does not matter.
        """
        choices = Contest.get_choices_from_contest(self.contest["choices"])
        # Some minimal sanity checking
        if offset != -1 and selection != "":
            raise ValueError("add_selection: cannot specify both selection and offset")
        if offset == -1 and selection == "":
            raise ValueError("add_selection: no selection or offset was supplied")
        if offset != -1:
            if offset > len(choices):
                raise ValueError(
                    f"The choice offset ({offset}) is greater "
                    f"than the number of choices ({len(choices)})"
                )
            if offset < 0:
                raise ValueError(f"Only positive offsets are supported ({offset})")
            selection = choices[offset]
        if selection not in choices:
            raise ValueError(
                f"The specified selection ({selection}) is not one of "
                f"the available/legitimate choices: {choices}"
            )
        if "selection" not in self.contest:
            self.contest["selection"] = [selection]
            return
        if selection in self.contest["selection"]:
            raise ValueError(
                (
                    f"The selection ({selection}) has already been "
                    f"selected for contest ({self.contest['contest_name']}) "
                    f"for GGO ({self.contest['ggo']})"
                )
            )
        # Note - prior to 2024/05/09, the selection was an offset + " : "
        # + "name".  That was inherently a bad idea.  It also resulted in
        # confusion of what the offset was.  So as of now, just use the
        # unique name of the contest.
        self.contest["selection"].append(selection)


# EOF
