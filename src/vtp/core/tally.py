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
import operator

import networkx as nx

# local
from .common import Globals
from .contest import Contest
from .exceptions import TallyException
from .operation import Operation


# pylint: disable=too-many-instance-attributes # (8/7 - not worth it at this time)
# pylint: disable=too-many-public-methods # 21/20
# pylint: disable=too-many-lines
class Tally:
    """
    A class to tally ballot contests a.k.a. CVRs.  The three primary
    functions of the class are the contructor, a tally function, and a
    print-the-tally function.

    Here is an outline of the basic call tree into this class:
    tallyho()
      parse_and_tally_a_contest()
        tally_a_plurality_contest() or tally_a_rcv_contest()
      loop over all open positions:
        loop over winning choices:    # almost always only one
        handle_another_rcv_round()    # if needed
          next_rcv_round_precheck()
          recast_votes()
          restore_proper_rcv_round_ordering()
          various tests and record keeping
          handle_another_rcv_round()  # iterate until done
        return if done
        tallyho()    # iterate until done (current_winners now non-empty)
    """

    @staticmethod
    def get_choices_from_round(choices, what: str = ""):
        """Will smartly return just the pure list of choices sans all
        values and sub dictionaries from a round
        """
        if what == "count":
            return [choice[1] for choice in choices]
        return [choice[0] for choice in choices]

    def __init__(self, a_git_cvr: dict, operation_self: Operation):
        """Given a contest as parsed from the git log, a.k.a the
        contest digest and CVR json payload, will construct a Tally.
        A tally object can validate and tally a contest.

        Note - the constructor is per specific contest and tally
        results of the contest are stored in an attribute of the
        object.

        The operation_self is how STDOUT is being handled as defined by
        the outer ops class/object.  That object just passes down its
        print function to the Tally constructor so that each (contest)
        tally can handle printing as desired.
        """
        #        import pdb; pdb.set_trace()
        self.operation_self = operation_self
        self.reference_contest = a_git_cvr["contestCVR"]
        self.reference_digest = a_git_cvr["digest"]
        Contest.check_contest_blob_syntax(
            self.reference_contest, digest=self.reference_digest
        )
        # Something to hold the actual tallies.  During RCV rounds these
        # will change with last place finishers being decremented to 0.
        self.init_selection_counts()
        # For sequential RCV tallies the default win_by will always be
        # 0.5. For proportional RCV it is a function of
        # open_positions. The if clause is only here for back
        # compatbility with older mock electionData sets.
        if "win_by" not in self.reference_contest:
            self.reference_contest["win_by"] = 0.5
            # self.reference_contest["win_by"] =
            # 1.0 / (int(self.reference_contest["open_positions"]) + 1.0)
        # Need to keep track of current winners for sequential RCV.
        # This is an aggregating copy of the self.winner_order across
        # all the open seats.
        self.multiseat_winners = []
        # The reset-able stuff - defines more instance variables
        self.multiseat_reset()
        # Need a backup of contest["selection'] to restore when
        # tallying multiseat sequential RCV contests
        self.selection_backup = {}
        # At this point any contest tallied against this contest must
        # match all the fields with the exception of selection and
        # write-in, but that check is done in tallyho below.
        if self.reference_contest["tally"] not in ["plurality", "rcv", "pwc"]:
            raise NotImplementedError(
                f"the specified tally ({self.reference_contest['tally']}) is not yet implemented"
            )
        # Initialize pairwise matrix if not already present - used for
        # Condorcet tallies
        choices = Contest.get_choices_from_contest(self.reference_contest["choices"])
        self.pairwise_matrix = {(a, b): 0 for a in choices for b in choices if a != b}

    def init_selection_counts(self):
        """Will initialize the selection_counts to 0"""
        self.selection_counts = {
            choice: 0
            for choice in Contest.get_choices_from_contest(
                self.reference_contest["choices"]
            )
        }

    def multiseat_reset(self):
        """Will initialize/reinitialize what needs to be when
        executing a multiseat sequential RCV tally
        """
        # Total vote count for this contest.  RCV rounds will not effect
        # this.
        self.vote_count = 0  # int
        # Ordered list of winners - a list of tuples and not dictionaries.
        self.winner_order = []  # simple list of names
        # Used in both plurality and rcv, but only round 0 is used in
        # plurality.  Note - rcv_round's are an ordered list of tuples
        # as is winner_order.  The code below expects the current round
        # (beginning as an empty list) to exist within the list.
        self.rcv_round = []  # ordered list of name:votes tuples
        self.rcv_round.append([])
        # Need to keep track of a selections/choices that are no longer
        # viable - key=choice['name'] value=obe round
        self.obe_choices = {}  # key=name, value=knockout round
        self.init_selection_counts()  # dict of names:votes
        # Something to hold the actual tallies.  During RCV rounds these
        # will change with last place finishers being decremented to 0.
        self.init_selection_counts()
        # And remove winners from selection_counts
        for key in self.multiseat_winners:
            if key[0] in self.selection_counts:
                del self.selection_counts[key[0]]

    def get(self, name: str):
        """Simple limited functionality getter"""
        if name in ["max_selections", "open_positions", "win_by"]:
            return self.reference_contest[name]
        if name == "digest":
            return self.reference_digest
        if name == "contest":
            return self.reference_contest
        if name in [
            "rcv_round",
            "selection_counts",
            "vote_count",
            "winner_order",
        ]:
            return getattr(self, name)
        raise NameError(f"Name {name} not accepted/defined for Tally.get()")

    def __str__(self):
        """Return the Tally in a partially print-able json string - careful ..."""
        # Note - keep cloak out of it until proven safe to include
        tally_dict = {
            "contest_name": self.reference_contest["contest_name"],
            "digest": self.reference_digest,
            "multiseat_winners": self.multiseat_winners,
            "obe_choices": self.obe_choices,
            "rcv_round": self.rcv_round,
            "selection_counts": self.selection_counts,
            "vote_count": self.vote_count,
            "winner_order": self.winner_order,
        }
        return json.dumps(tally_dict, sort_keys=True, indent=4, ensure_ascii=False)

    def determine_plurality_winners(self):
        """Given a completed plurality contest, determine the winners
        caveat any issues such as ties.  self.winner_order has already
        been properly defined.
        """
        # loop over self.winner_order filling the open seats
        open_positions = int(self.reference_contest.get("open_positions", 1))
        winners = []
        idx = 0
        while len(winners) < open_positions and idx < len(self.winner_order[0]):
            current_count = self.winner_order[0][idx][1]
            # Add all choices with this count
            tied_choices = [
                choice
                for choice, count in self.winner_order[0]
                if count == current_count
            ]
            winners.extend(tied_choices)
            idx += len(tied_choices)
            if len(tied_choices) > 1:
                self.operation_self.imprimir(
                    f"There is a tie: {tied_choices} for the {Globals.make_ordinal(idx)} seat",
                    0,
                )
        # If more winners than open_positions due to ties, keep all ties
        return winners

    def tally_a_plurality_contest(
        self,
        contest: dict,
        provenance_digest: str,
        vote_count: int,
        digest: str,
    ):
        """plurality tally"""
        for count in range(int(self.reference_contest["open_positions"])):
            if 0 <= count < len(contest["selection"]):
                # yes this can be one line, but the reader may
                # be interested in verifying the explicit
                # values
                selection = contest["selection"][count]
                self.selection_counts[selection] += 1
                self.vote_count += 1
                if provenance_digest:
                    self.operation_self.imprimir(
                        f"Counted vote {vote_count} ({provenance_digest}) seat {count + 1} "
                        "selection={selection}",
                        0,
                    )
                elif self.operation_self.verbosity == 4:
                    self.operation_self.imprimir(
                        f"counted vote {vote_count} ({digest}) seat {count + 1} "
                        "selection={selection}"
                    )
            else:
                # A blank contest
                if provenance_digest:
                    self.operation_self.imprimir(
                        f"Counted vote {vote_count} ({digest}) seat {count + 1} as no vote - BLANK",
                        0,
                    )
                if self.operation_self.verbosity == 4:
                    self.operation_self.imprimir(
                        f"counted vote {vote_count} ({digest}) seat {count + 1} as no vote - BLANK",
                        0,
                    )

    def tally_a_rcv_contest(
        self,
        contest: dict,
        provenance_digest: str,
        vote_count: int,
        digest: str,
    ):
        """RCV tally"""
        # Note - the voter can still leave a RCV contest blank
        if len(contest["selection"]):
            # ZZZ To support multiseat sequential RCV, need to skip
            # any already elected choices.

            # Get the first selection ([0])
            selection = contest["selection"][0]
            self.selection_counts[selection] += 1
            self.vote_count += 1
            if provenance_digest:
                self.operation_self.imprimir(
                    f"Counted vote {vote_count} ({provenance_digest}) for {selection}",
                    0,
                )
            elif self.operation_self.verbosity == 4:
                self.operation_self.imprimir(
                    f"counted vote {vote_count} ({digest}) for {selection}"
                )
        else:
            # A blank contest
            if provenance_digest:
                self.operation_self.imprimir(
                    f"Counted vote {vote_count} ({digest}) as no vote - BLANK", 0
                )
            if self.operation_self.verbosity == 4:
                self.operation_self.imprimir(
                    f"counted vote {vote_count} ({digest}) as no vote - BLANK", 0
                )

    def tally_a_pwc_contest(
        self,
        contest: dict,
        provenance_digest: str,
        ballot_count: int,
        digest: str,
    ):
        """pairwise Condorcet tally"""
        # Only process ballots with at least one selection
        ranking = contest.get("selection", [])
        if not ranking:
            if provenance_digest or self.operation_self.verbosity == 4:
                self.operation_self.imprimir(f"No vote {digest}: BLANK", 0)
            return

        # Build a rank lookup for this ballot
        rank_index = {name: idx for idx, name in enumerate(ranking)}
        if provenance_digest or self.operation_self.verbosity == 4:
            self.operation_self.imprimir(
                f"Pairwise ranking for ballot vote {ballot_count} ({digest}): {rank_index}",
                0,
            )
        # For unranked candidates, treat as ranked last (after all ranked)
        choices = Contest.get_choices_from_contest(self.reference_contest["choices"])
        for a in choices:
            for b in choices:
                if a == b:
                    continue
                # a is preferred to b if:
                # - a is ranked and b is not, or
                # - both are ranked and a's index < b's index
                if a in rank_index and b not in rank_index:
                    self.pairwise_matrix[(a, b)] += 1
                    if provenance_digest or self.operation_self.verbosity == 4:
                        self.operation_self.imprimir(
                            f"Pairwise vote {self.pairwise_matrix[(a, b)]} ({digest}) for {(a,b)}",
                            0,
                        )
                elif (
                    a in rank_index
                    and b in rank_index
                    and rank_index[a] < rank_index[b]
                ):
                    self.pairwise_matrix[(a, b)] += 1
                    if provenance_digest or self.operation_self.verbosity == 4:
                        self.operation_self.imprimir(
                            f"Pairwise vote {self.pairwise_matrix[(a, b)]} ({digest}) for {(a,b)}",
                            0,
                        )
                # else: b is preferred or tie/no info

    def safely_determine_last_place_names(self, current_round: int) -> list:
        """Safely determine the next set of last_place_names for which
        to re-distribute the next RCV round of voting.  Can raise
        various exceptions.  If possible will return the
        last_place_names (which can be greater than length 1 if there
        is tie amongst the losers of a round).

        Note - it is up to the caller to resolve RCV edge cases such
        as multiple and simultaneous losers, a N-way tie of all
        remaining choices, returning a tie which undercuts the max
        number of votes (as in, pick 3 of 5 and a RCV round tie
        results in 1 or 2 choices instead of 3).
        """
        # Note - self.rcv_round[current_round] is the ordered array of
        # all RCV choice tuples
        for result in self.rcv_round[current_round]:
            self.operation_self.imprimir(f"  {result}")
        # self.operation_self.imprimir(f"{self.rcv_round[current_round]}", 3)

        # Step 1: remove self.obe_choices from current round
        working_copy = []
        # Reminder - a_tuple below is the ('name',<vote count>)
        for a_tuple in self.rcv_round[current_round]:
            if a_tuple[0] not in self.obe_choices:
                working_copy.append(a_tuple)

        # Step 2: walk the list backwards returning the set of counts
        # with the same minimum count.
        last_place_names = []
        previous_count = 0
        for offset, a_tuple in enumerate(reversed(working_copy)):
            # Note - current_round is 0 indexed from left, which means
            # it needs an additional decrement when indexing from the
            # right
            current_count = a_tuple[1]
            if offset == 0 or current_count == previous_count:
                last_place_names.append(a_tuple[0])
                previous_count = current_count
            else:
                break
        return last_place_names

    def safely_remove_obe_selections(self, contest: dict):
        """For the specified contest, will 'pop' the current first place
        selection.  If the next selection is already a loser, will pop
        that as well.  self.reference_contest['selection'] may or may not have any
        choices left (it can be empty, have one choice, or multiple
        choices left).

        Prints nothing - assumes caller handles any info/debug printing.
        """
        a_copy = contest["selection"].copy()
        for selection in a_copy:
            if (
                contest["selection"][0] in self.obe_choices
                and selection in contest["selection"]
            ):
                contest["selection"].remove(selection)

    def safely_remove_previous_winners(
        self, contest: dict, provenance_digest: str, digest: str
    ):
        """For the specified contest, will remove all
        self.multiseat_winners from the selection, potentially printing
        the removal.
        """
        a_copy = contest["selection"].copy()
        winners = [item[0] for item in self.multiseat_winners]
        for rank, selection in enumerate(a_copy):
            if selection in winners and selection in contest["selection"]:
                contest["selection"].remove(selection)
                if provenance_digest == digest or self.operation_self.verbosity >= 4:
                    self.operation_self.imprimir(
                        f"RCV: {digest} (contest={contest['contest_name']}) "
                        f"note - {selection}, rank={rank+1}, "
                        "is already a winner",
                        0,
                    )

    def restore_proper_rcv_round_ordering(self, this_round: int):
        """Restore the 'proper' ordering of the losers in the current
        and previous rcv rounds.  Note: at this point the
        self.rcv_round has been sorted by count with the obe_choices
        effectively randomized.  Also note that new incoming
        last_place_names are not yet in self.obe_choices and will not
        be until post the safely_determine_last_place_names call
        below.
        """
        loser_order = []
        for loser in sorted(
            self.obe_choices.items(), key=operator.itemgetter(1), reverse=True
        ):
            loser_order.append(loser)
        # Replace the effectively improperly unordered losers with a
        # properly ordered list of losers. One way is to replace the
        # last N entries with the properly ordered losers.
        if len(loser_order) > 1:
            for index, item in enumerate(reversed(loser_order)):
                self.rcv_round[this_round][-index - 1] = (item[0], 0)

    def get_total_vote_count(self, this_round: int):
        """
        To get the correct denominator to determine the minimum
        required win amount, all the _current_ candidate counts need
        to be added since some ballots may either be blank OR have
        less then the maximum number of rank choices.  Note -
        """
        return sum(
            self.selection_counts[choice]
            for choice in Tally.get_choices_from_round(self.rcv_round[this_round])
        )

    # pylint: disable=too-many-return-statements # what is a poor man to do
    def next_rcv_round_precheck(self, last_place_names: list, this_round: int) -> int:
        """
        Run the checks against the incoming last_place_names to make
        sure that it is ok to have another RCV round.  Returns non 0
        if no more rounds should be performed.
        """

        # 'this_round' is actually the 'next round' with the very
        # first round being round 0.  So, the first time this can be
        # called is the beginning of the second round (this_round =
        # 1).
        non_zero_count_choices = 0
        for choice in self.rcv_round[this_round - 1]:
            non_zero_count_choices += 1 if choice[1] else 0

        # If len(last_place_names) happens to be zero, raise an error.
        # However, though raising an error 'could be' the best test
        # prior to entering another round (calling this function
        # here), not raising an error and allowing such edge case tp
        # print the condition and simply return might be the better
        # design option.  Doing that.
        if not last_place_names:
            self.operation_self.imprimir(
                "No more choices/candidates to recast - no more RCV rounds", 0
            )
            return 1
        if this_round > 64:
            raise TallyException("RCV rounds exceeded safety limit of 64 rounds")
        if this_round >= len(self.rcv_round[0]):
            self.operation_self.imprimir("There are no more RCV rounds", 0)
            return 1
        if not non_zero_count_choices:
            self.operation_self.imprimir("There are no votes for any choice", 0)
            return 1
        # if non_zero_count_choices:
        #     self.operation_self.imprimir(
        #         f"There are only {non_zero_count_choices} viable choices "
        #         "left which is less than the contest max selections "
        #         f"({self.get('max_selections')})",
        #         0,
        #     )
        #     return 0
        if non_zero_count_choices <= 2:
            self.operation_self.imprimir(
                f"There is only {non_zero_count_choices} remaining choices - "
                "halting more RCV rounds",
                0,
            )
            return 1

        # Note - by the time the execution gets here, this rcv_round have been
        # vote count ordered.  But there could be any number of zero count
        # choices depending on the (edge case) details.

        # If len(last_place_names) leaves the exact number of max
        # choices left, this is a runner-up tie which is still ok -
        # return and print that.
        if non_zero_count_choices - len(last_place_names) == 0:
            self.operation_self.imprimir(
                f"This contest ends in a {non_zero_count_choices} way tie", 0
            )
            return 1

        # If len(last_place_names) leaves less than the max but one or
        # more choices left, this is a tie on losing.  Not sure what
        # to do, so print that and return.
        if len(last_place_names) >= 2:
            self.operation_self.imprimir(
                f"There is a last place {len(last_place_names)} way tie.",
                2,
            )
            if non_zero_count_choices > len(last_place_names):
                # ZZZ is this the right thing to do?
                # allow all the zero counts to go
                return 0
            # else, stop
            return 1

        # And, the recursive stack here should probably be returning a
        # success/failure back out of the Contest.tallyho...
        return 0

    def recast_votes(self, last_place_names: list, contest_batch: list, checks: list):
        """
        Loops over the list of CVRs of interest (a contest worth) and
        recasts a voter's selection if that selection is a loser in
        this RCV round.  If there is no next choice, the there is no
        recast and the vote is dropped.

        For multiseat RCV, skip any already elected choices.
        """

        # Loop over CVRs
        total_votes = 0
        for vote_count, a_git_cvr in enumerate(contest_batch):
            contest = a_git_cvr["contestCVR"]
            digest = a_git_cvr["digest"]
            total_votes += 1
            if digest in checks:
                # Note - to manually inspect a specific RCV vote,
                # add the 'if digest == "...": import pdb; pdb.set_trace()' here
                self.operation_self.imprimir(
                    f"INSPECTING: {digest} (contest={contest['contest_name']}) "
                    f"as vote {vote_count + 1}",
                    3,
                )
            # Note - if there is no selection, there is no selection
            if not contest["selection"]:
                if digest in checks or self.operation_self.verbosity >= 4:
                    self.operation_self.imprimir(
                        f"RCV: vote {total_votes} ({digest}) no vote - BLANK ",
                        0,
                    )
                continue
            for last_place_name in last_place_names:
                # Note - as the rounds go by, the
                # contest["selection"]'s will get trimmed to an empty
                # list.  Once empty, the vote/voter is done.
                if contest["selection"] and contest["selection"][0] == last_place_name:
                    # Safely pop the current first choice and reset
                    # contest['selection'].  Note that
                    # self.obe_choices has _already_ been updated with
                    # this_round's OBE in the caller such that
                    # safely_remove_obe_selections will effectively
                    # remove last_place_name from contest['selection']
                    self.safely_remove_obe_selections(contest)
                    # Regardless of the next choice, the current choice is decremented
                    self.selection_counts[last_place_name] -= 1
                    # Either retarget the vote or let it drop
                    if len(contest["selection"]):
                        # The voter can still leave a RCV contest blank
                        # Note - selection is the new selection for this contest
                        new_selection = contest["selection"][0]
                        self.selection_counts[new_selection] += 1
                        # original variant: if digest in checks or loglevel == "DEBUG":
                        if digest in checks or self.operation_self.verbosity >= 4:
                            self.operation_self.imprimir(
                                f"RCV: vote {total_votes} ({digest}) last place "
                                f"pop and count: {last_place_name} (vote {total_votes}) "
                                f"-> {new_selection} (vote {self.selection_counts[new_selection]})",
                                0,
                            )
                    else:
                        if digest in checks or self.operation_self.verbosity >= 4:
                            self.operation_self.imprimir(
                                f"RCV: vote {total_votes} ({digest}) last place "
                                f"pop and drop ({last_place_name} -> BLANK)",
                                0,
                            )
        return total_votes

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def handle_another_rcv_round(
        self,
        this_round: int,
        last_place_names: list,
        contest_batch: list,
        checks: list,
        seat: int,
    ):
        """For the lowest vote getter, for those CVR's that have that
        as their current first/active-round choice, will slice off
        that choice off and re-count the now first selection choice
        (if there is one).

        Note that muiltiple open_positions is just an another outer
        loop around calling this.  As each position is filled, that
        choice is removed from the valid remaining choices.  As
        obe_choices is per RCV round only (it gets reset)
        """
        self.operation_self.imprimir_formatting("empty_line")
        if len(contest_batch) > 1:
            self.operation_self.imprimir_formatting("horizontal_shortline")
        else:
            self.operation_self.imprimir_formatting("horizontal_line")
        self.operation_self.imprimir(
            f"RCV: round {this_round}, {Globals.make_ordinal(seat)} seat", 0
        )

        # ZZZ - create a function to validate incoming last place
        # names and call that.  Maybe in the furure once more is know
        # support GLOBAL configs to determine how edge cases are
        # handled.  That function can cause a return if the the
        # current RCV tally should not proceed to more rounds.  Or
        # raise an RCV-tally error (which can be handled by the caller
        # when printing - prints a warning).
        if self.next_rcv_round_precheck(last_place_names, this_round):
            return

        # Loop over contest_batch and actually re-cast votes
        total_votes = self.recast_votes(last_place_names, contest_batch, checks)
        # Order the winners of this round.  This is a tuple, not a
        # list or dict.  Note - the rcv round losers should not be
        # re-ordered as there is value to retaining that order
        self.rcv_round[this_round] = sorted(
            self.selection_counts.items(), key=operator.itemgetter(1), reverse=True
        )
        self.restore_proper_rcv_round_ordering(this_round)
        # Create the next round list
        self.rcv_round.append([])
        # Regarding the total vote count, in single open_positions IRV
        # tallies, the total vote count would be just be the total
        # number of ballots/votes cast in the current round. However,
        # it still needs to result in a winner in the case of only one
        # ballot being marked, or if all the ballots have a single
        # ranking. In other words, in single open_positions contests
        # if there is no > 50% majority winner, the last remaining
        # choice with the most votes is the winner.  (yes/no?)

        # Extending this to multiple open_positions contests, for any
        # position iteration that does not make it to > 50%, the
        # majority winner still wins and if more open_positions need
        # to be filled, the tally still proceeds to the next open
        # seat.

        # In this light, for sequential RCV (which is what the 'rcv'
        # tally stands for), the win_by is pegged to 50% for all
        # open_positions iterations with an escape clause that if 50%
        # is not met, the remaining plurality winner winner.

        # For proportional RCV, the tally algorithm is fundementally
        # different as not only does the win_by change per round but
        # also a round winner needs to redistribute the over
        # threshhold votes in a proportional manner. In sequential RCV
        # each round winner is added to the winner_circle, and votes
        # for a choice in a later round that is already in the
        # winner_circle are skipped in a manner similar to if the
        # choice has already been eliminated.

        # And for a pair-wise type of Condorcet tally, a DAG solution
        # is required where a DAG is slowly constructed in an orderly
        # manner (largest pair wise winner first), dropping lower
        # ranked edges that create a cycle.

        #
        total_current_vote_count = self.get_total_vote_count(this_round)
        self.operation_self.imprimir(
            f"Total non-blank vote count: {total_current_vote_count} (out of {total_votes})",
            0,
        )
        for choice in Tally.get_choices_from_round(self.rcv_round[this_round]):
            # Note the test is '>' and NOT '>='
            if (
                float(self.selection_counts[choice]) / float(total_current_vote_count)
            ) > float(self.reference_contest["win_by"]):
                # A winner. Note for sequencial RCV contests, the
                # win_by is always > 0.5, so it is not possible to
                # have multiple winners here. However, this was
                # originally coded to attempt to support proportional
                # RCV where win_by can be smaller and multiple winner
                # are possible (i think).
                self.winner_order.append((choice, self.selection_counts[choice]))
                # Need to also add the current winner(s) to the
                # ignore_choices in case there are multiple open
                # seats
                self.multiseat_winners.append((choice, self.selection_counts[choice]))
        # If there are anough winners, stop and return
        if self.winner_order:
            return
        # If not, safely determine the next set of last_place_names and
        # execute another RCV round.
        last_place_names = self.safely_determine_last_place_names(this_round)
        # Add this loser to the obe record
        for last_place_name in last_place_names:
            self.obe_choices[last_place_name] = this_round
        self.handle_another_rcv_round(
            this_round + 1, last_place_names, contest_batch, checks, seat
        )
        return

    def add_digest_error(self, errors: dict, digest: str, err_message: str):
        """Will create/append a digest error msg"""
        if digest not in errors:
            errors[digest] = [err_message]
        else:
            errors[digest].append(err_message)

    # pylint: disable=too-many-branches
    def parse_and_tally_a_contest(
        self, contest_batch: list, checks: list, tally_override: str = ""
    ):
        """
        Will parse all the contests validating each entry.  Choices
        that are in the self.multiseat_winners dict will be skipped -
        the skipping will be printed depending on verbosity.
        """
        errors = {}
        vote_count = 0
        for a_git_cvr in contest_batch:
            vote_count += 1
            contest = a_git_cvr["contestCVR"]
            digest = a_git_cvr["digest"]
            # Maybe print an provenance log for the tally of this contest
            provenance_digest = digest if digest in checks else ""
            # Either save or restore the original contest for
            # restoration if needed
            if digest in self.selection_backup:
                contest["selection"] = self.selection_backup[digest].copy()
                self.safely_remove_previous_winners(contest, provenance_digest, digest)
            else:
                self.selection_backup[digest] = contest["selection"].copy()
            # Check contest syntax
            Contest.check_contest_blob_syntax(contest, digest=digest)
            # Validate the values that should be the same as
            # self.reference_contest (win_by is optional)
            for field in [
                "choices",
                "tally",
                "win_by",
                "max_selections",
                "ggo",
                "uid",
                "contest_name",
                "contest_type",
                "election_upstream_remote",
            ]:
                if field != "win_by" and not (
                    tally_override != "" and field == "tally"
                ):
                    if field in self.reference_contest:
                        if self.reference_contest[field] != contest[field]:
                            self.add_digest_error(
                                errors,
                                digest,
                                f"{field} field does not match: "
                                f"{self.reference_contest[field]} != {contest[field]}",
                            )
                    elif field in contest:
                        self.add_digest_error(
                            errors,
                            digest,
                            f"{field} field is not present in Tally object but "
                            "is present in digest",
                        )
            # Tally the contest - this is just the first pass of a
            # tally.  It just so happens that with plurality tallies
            # the tally can be completed with a single pass over
            # the CVRs.  And that can be done here.  But with more
            # complicated tallies such as RCV, the additional passes
            # are done outside of this for loop.
            if tally_override == "plurality" or (
                tally_override == "" and contest["tally"] == "plurality"
            ):
                self.tally_a_plurality_contest(
                    contest, provenance_digest, vote_count, digest
                )
            elif tally_override == "rcv" or (
                tally_override == "" and contest["tally"] == "rcv"
            ):
                # parse_and_tally_a_contest will be called once at the
                # beginning of each RCV open seat tally.
                # self.multiseat_winners will be null for the first seat
                # and will be non null for seats after that. So,
                # remove all traces of the previous winners before
                # proceeding with the RCV tally.
                self.safely_remove_previous_winners(contest, provenance_digest, digest)
                # Since this is the first round on a rcv tally, just
                # grap the first selection
                self.tally_a_rcv_contest(contest, provenance_digest, vote_count, digest)
            elif tally_override == "pwc" or (
                tally_override == "" and contest["tally"] == "pwc"
            ):
                self.tally_a_pwc_contest(contest, provenance_digest, vote_count, digest)
            else:
                # This code block should never be executed as the
                # constructor or the Validate values clause above will
                # catch this type of error.  It is here only as a
                # safety check during development time when adding
                # support for more tallies.
                raise NotImplementedError(
                    f"the specified tally ({contest['tally']}) is not yet implemented"
                )

        # Will the potential CVR errors found, report them all
        if errors:
            raise TallyException(
                "The following CVRs have structural errors:" f"{errors}"
            )
        return vote_count

    # pylint: disable=too-many-branches
    def tallyho(
        self,
        contest_batch: list,
        checks: list,
        tally_override: str = "",
    ):
        """
        Will verify and tally the suppllied unique contest across all
        the CVRs.  contest_batch is the list of contest CVRs from git
        and checks is a list of optional CVR digests (from the voter)
        to check.
        """
        # Maybe override the tally
        if tally_override:
            self.reference_contest["tally"] = tally_override

        # Loop over open seats. For plurality, regardless of open
        # seats there is only one iteration - a check will exit the
        # loop. For RCV, all the following rounds are handled by
        # handle_another_rcv_round
        for seat in range(1, int(self.reference_contest["open_positions"]) + 1):
            # Prologue header
            if self.reference_contest["tally"] == "plurality":
                self.operation_self.imprimir("Running a plurality tally", 0)
            elif self.reference_contest["tally"] == "rcv":
                self.operation_self.imprimir_formatting("empty_line")
                if len(contest_batch) > 1:
                    self.operation_self.imprimir_formatting("horizontal_shortline")
                else:
                    self.operation_self.imprimir_formatting("horizontal_line")
                self.operation_self.imprimir(
                    f"RCV: initial tally, {Globals.make_ordinal(seat)} seat", 0
                )
            elif self.reference_contest["tally"] == "pwc":
                self.operation_self.imprimir("Running a pairwise Condorcet tally", 0)
            else:
                raise NotImplementedError(
                    f"the specified tally ({self.reference_contest['tally']}) "
                    "is not yet implemented"
                )

            # parse all the CVRs and create the first round of tallys
            total_votes = self.parse_and_tally_a_contest(
                contest_batch, checks, tally_override
            )
            # If pairwise Condorcet, though contest votes have been
            # counted, the actual tally is fundementally then either
            # plurality or rcv.
            if self.reference_contest["tally"] == "pwc":
                # record the winner order, print, and return for yucks
                # anyway
                self.winner_order.append(self.rcv_round[0])
                self.determine_condorcet_winners()
                return

            # For all tallies order what has been counted so far (a tuple)
            self.rcv_round[0] = sorted(
                self.selection_counts.items(), key=operator.itemgetter(1), reverse=True
            )
            self.rcv_round.append([])
            # If plurality, the tally is done
            if self.reference_contest["tally"] == "plurality":
                # record the winner order, print, and return
                # import pdb; pdb.set_trace()
                self.winner_order.append(self.rcv_round[0])
                # Neeed to determine as best as possible the actual
                # winners (for printing)
                winners = self.determine_plurality_winners()
                self.print_final_results(winners)
                return
            # The rest of this block handles RCV

            # See if another RCV round is necessary.  Note that win_by
            # is a function of open_positions.  If there are more open
            # positions left to fill, then record the currently
            # winning votes in the counted_ranking hash with a value
            # of this round of this open position and the voter's
            # specific ranking for choice X (candidate X).
            # Technically this last piece of info is not needed as
            # once a choice/contestant has filled an open position,
            # any vote for that contestant in following open_positions
            # iteration is skipped over and simply not counted.
            # However, displaying this information to the voter offers
            # important transparency into the voting and tally.

            # Get the correct current total vote count for this round
            total_current_vote_count = self.get_total_vote_count(0)
            self.operation_self.imprimir(
                f"Total non-blank vote count: {total_current_vote_count} (out of {total_votes})",
                0,
            )
            # When multiseat RCV, print multiseat RCV header
            if int(self.reference_contest["open_positions"]) > 1:
                self.operation_self.imprimir(
                    f"Running sequential RCV for the {Globals.make_ordinal(seat)}"
                    " open seat"
                )
            # Determine if there are winners by win_by
            for choice in Tally.get_choices_from_round(self.rcv_round[0]):
                # Note the test is '>' and NOT '>='
                if (
                    float(self.selection_counts[choice])
                    / float(total_current_vote_count)
                ) > float(self.reference_contest["win_by"]):
                    # A winner.  Depending on the win_by (which is a
                    # function of max), there could be multiple
                    # winners in this round.
                    self.winner_order.append((choice, self.selection_counts[choice]))
                    # Need to also add the current winner(s) to the
                    # ignore_choices in case there are multiple open
                    # seats
                    self.multiseat_winners.append(
                        (choice, self.selection_counts[choice])
                    )

            # ZZZ need a check when perhaps due to a tie, there are more
            # winners than remaining open_positions

            # If there is a winner, either go to next open seat or return if done
            if self.winner_order:
                if len(self.winner_order) >= int(
                    self.reference_contest["open_positions"]
                ):
                    # Print final results text
                    winners = [item[0] for item in self.multiseat_winners[0]]
                    self.print_final_results(winners)
                    return
                self.print_seat_results(self.winner_order, seat)
                # Reset state needed for multiseat
                self.multiseat_reset()
                # ... and go to next seat
                continue

            # Safely determine the next set of last_place_names and
            # execute a RCV round. Note that all zero vote choices
            # will already be sorted last in self.rcv_round[0].
            last_place_names = self.safely_determine_last_place_names(0)
            for name in last_place_names:
                self.obe_choices[name] = 0
            # Go. handle_another_rcv_round will return somehow at some
            # point - it is recursive until the seat has been won or
            # there is an error
            self.handle_another_rcv_round(
                1, last_place_names, contest_batch, checks, seat
            )

            # If this is the last open_position, need to exit now.
            if seat >= int(self.reference_contest["open_positions"]):
                # Print final results text
                winners = [item[0] for item in self.multiseat_winners]
                self.print_final_results(winners)
                return

            # The following is the prologue for the next open position.
            # Note that winner_order are the winners of this seat and
            # multiseat_winners are the list of winners for all seats so
            # far.
            self.print_seat_results(self.winner_order, seat)

            # After handle_another_rcv_round returns, the current
            # open_position has been filled. Reset what needs to be
            # reset to fill another position and call tallyho again.

            # Reset state needed for multiseat
            self.multiseat_reset()

        # All open_positions have been filled as best as possible.
        # The above for loop in theory should always return...
        return

    def print_seat_results(self, winners: list, seat: int):
        """
        Will print the results of the current seat winner.  Not called
        when there is only one open seat
        """
        self.operation_self.imprimir(
            f"Results for the {Globals.make_ordinal(seat)} open seat of "
            f"contest {self.reference_contest['contest_name']} "
            f"(uid={self.reference_contest['uid']}):",
            0,
        )
        for result in self.rcv_round[-2]:
            self.operation_self.imprimir(f"  {result}")
        self.operation_self.imprimir(
            f"Removing the winner(s), {', '.join([item[0] for item in winners])}, "
            "from consideration for the next open seat "
            f"(seat {seat + 1} of {self.reference_contest['open_positions']})\n"
            "Running next open seat tally ...",
            0,
        )

    def print_final_results(self, winners: list):
        """Will print the results of the tally"""
        self.operation_self.imprimir(
            f"Final {self.reference_contest['tally']} round results for contest "
            f"{self.reference_contest['contest_name']} "
            f"(uid={self.reference_contest['uid']}):",
            0,
        )
        # Note - better to print the last self.rcv_round than
        # self.winner_order since the former is a full count across all
        # choices while the latter is a partial list
        for result in self.rcv_round[-2]:
            self.operation_self.imprimir(f"  {result}")
        # When there is only one open seat
        self.operation_self.imprimir(
            f"Winner(s): {', '.join(winners)}",
            0,
        )

    def determine_condorcet_winners(self):
        """
        Use networkx to build a directed acyclic graph (DAG) of pairwise victories.
        Edges are added in descending order of margin. If an edge creates a cycle,
        print and skip it. At the end, print the topological sort of the DAG.
        """
        if not hasattr(self, "pairwise_matrix"):
            raise TallyException(
                "Pairwise matrix not computed. Run tally_a_pwc_contest first."
            )

        condorcet_graph = nx.DiGraph()
        candidates = Contest.get_choices_from_contest(self.reference_contest["choices"])
        condorcet_graph.add_nodes_from(candidates)

        # Build a list of all pairwise victories with their margins
        pairwise_results = []
        for (a, b), ab_count in self.pairwise_matrix.items():
            ba_count = self.pairwise_matrix.get((b, a), 0)
            margin = ab_count - ba_count
            if margin > 0:
                pairwise_results.append(((a, b), margin, ab_count, ba_count))
        # Sort by margin descending, then by ab_count descending
        pairwise_results.sort(key=lambda x: (x[1], x[2]), reverse=True)

        for (a, b), margin, ab_count, ba_count in pairwise_results:
            condorcet_graph.add_edge(
                a, b, margin=margin, ab_count=ab_count, ba_count=ba_count
            )
            if not nx.is_directed_acyclic_graph(condorcet_graph):
                condorcet_graph.remove_edge(a, b)
                self.operation_self.imprimir(
                    f"Skipping edge {a} -> {b} (margin={margin}, {ab_count}-{ba_count}) "
                    "to avoid cycle",
                    0,
                )
            else:
                self.operation_self.imprimir(
                    f"Adding edge {a} -> {b} (margin={margin}, {ab_count}-{ba_count})",
                    0,
                )

        # Print the topological sort (Condorcet order)
        # import pdb; pdb.set_trace()
        topo_order = list(nx.topological_sort(condorcet_graph))
        self.operation_self.imprimir(
            f"Condorcet topological order: {', '.join(topo_order)}", 0
        )
        # Return up to open_positions winners
        seats = int(self.reference_contest.get("open_positions", 1))
        self.operation_self.imprimir(f"Condorcet winner(s): {topo_order[:seats]}", 0)


# EOF
