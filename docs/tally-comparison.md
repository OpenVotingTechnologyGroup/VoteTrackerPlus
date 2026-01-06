## A Quick Comparison of Plurality, sequential & proportional RCV, and Condorcet Election Contest Tallies

What follows is the printout (what terminal applications such as [MacOS Terminal](https://en.wikipedia.org/wiki/PowerShell) or [Windows PowerShell](https://en.wikipedia.org/wiki/PowerShell) will display) of four different election contest tallies over the same data.  The data is a multi-seat contest selecting <u>three winners from six contestants</u>.  For plurality the ranking is effectively ignored - there is only one tally round that considers only the first three choices as equal choices.

The first tally below is [plurality](https://en.wikipedia.org/wiki/Plurality_(voting)); the second is a [sequential implementation](https://fairvote.org/proportional-ranked-choice-voting-vs-sequential-ranked-choice-voting/) of [Ranked Choice Voting](https://en.wikipedia.org/wiki/Ranked_voting); the third is a proportional RCV (a.k.a. STV) implementation, specifically a [Weighted Inclusive Gregory Method](https://prfound.org/resources/reference/) as used for example by the city of Minneapolis (for more info on multi seat RCV in the US, consult internet searches or [this link](https://www.rcvresources.org/types-of-rcv)); and the fourth is [pairwise Condorcet](https://en.wikipedia.org/wiki/Condorcet_method) contest tally.

VoteTrackerPlus is a [Merkle Tree](https://en.wikipedia.org/wiki/Merkle_tree) election system implementation similar to blockchain and cryptocurrencies but also fundementally different as there are no private keys of ownership - the ballot contest cryptographic signatures are completely anonymous, each contest on a voter's ballot receiving its own unique and anonymous digital signature.  In this way each contest vote can be referenced by its signature.  When tallying a contest, to be able to support election transparency, signatures can be supplied to the tally which will then track all the tally events associated with that specific vote.

In the below example, the first contest digital signature, [e92c62931cedfe0607865c624c178ecfc64cfd97](https://github.com/OpenVotingTechnologyGroup/VTP-mock-election.sRCV.1/commit/e92c62931cedfe0607865c624c178ecfc64cfd97), is for a ballot where the voter ranked all 6 candidates.  The ballot is counted as the 210 vote in the election.  With the second digest, [08e29630567c00e2e8887c089072d1edf3a92215](https://github.com/OpenVotingTechnologyGroup/VTP-mock-election.sRCV.1/commit/08e29630567c00e2e8887c089072d1edf3a92215), the voter only selected a single candidate and did not supply any further ranking information.  That ballot is counted as the 224th vote in the election.

For the plurality tally, only the first three rankings are used and are interpreted as equal rankings - they are all considered the same.  The last three rankings are ignored.

For the RCV and Condorcet tallies, all the ranking data supplied by the voter is taken into account.

## Plurality
```bash
% tally-contests -c 0001 -t e92c62931cedfe0607865c624c178ecfc64cfd97,08e29630567c00e2e8887c089072d1edf3a92215 --tally_override plurality
Scanned 224 votes for contest (Select Board) uid=0001, tally=rcv, open_positions=3, max_selections=6 
Running a plurality tally
Counted vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) seat 1 selection=Gloria Gamma
Counted vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) seat 2 selection=Anthony Alpha
Counted vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) seat 3 selection=Betty Beta
Counted vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) seat 1 selection=Francis Foxtrot
Counted vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) seat 2 as no vote - BLANK
Counted vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) seat 3 as no vote - BLANK
Final plurality round results for contest Select Board (uid=0001):
  ('Anthony Alpha', 121)
  ('David Delta', 114)
  ('Betty Beta', 110)
  ('Gloria Gamma', 108)
  ('Emily Echo', 106)
  ('Francis Foxtrot', 106)
Winner(s): Anthony Alpha, David Delta, Betty Beta
```

## Ranked Choice Vote (sequential)
```bash
% tally-contests -c 0001 -t e92c62931cedfe0607865c624c178ecfc64cfd97,08e29630567c00e2e8887c089072d1edf3a92215 --tally_override rcv
Scanned 224 votes for contest (Select Board) uid=0001, tally=rcv, open_positions=3, max_selections=6 
--------------------------------
RCV: initial tally, 1st seat
Counted vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) for Gloria Gamma
Counted vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) for Francis Foxtrot
Total non-blank vote count: 223 (out of 224)
Running sequential RCV for the 1st open seat
  ('Anthony Alpha', 45)
  ('Betty Beta', 40)
  ('Emily Echo', 38)
  ('Gloria Gamma', 34)
  ('David Delta', 34)
  ('Francis Foxtrot', 32)

--------------------------------
RCV: round 1, 1st seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
RCV: vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) last place pop and drop (Francis Foxtrot -> BLANK)
Total non-blank vote count: 222 (out of 224)
  ('Anthony Alpha', 50)
  ('Betty Beta', 45)
  ('Emily Echo', 44)
  ('David Delta', 43)
  ('Gloria Gamma', 40)
  ('Francis Foxtrot', 0)

--------------------------------
RCV: round 2, 1st seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
RCV: vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) last place pop and count: Gloria Gamma (vote 210) -> Anthony Alpha (vote 60)
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
RCV: vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) no vote - BLANK 
Total non-blank vote count: 222 (out of 224)
  ('Anthony Alpha', 61)
  ('Betty Beta', 55)
  ('Emily Echo', 54)
  ('David Delta', 52)
  ('Gloria Gamma', 0)
  ('Francis Foxtrot', 0)

--------------------------------
RCV: round 3, 1st seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
RCV: vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) no vote - BLANK 
Total non-blank vote count: 222 (out of 224)
  ('Betty Beta', 78)
  ('Anthony Alpha', 77)
  ('Emily Echo', 67)
  ('David Delta', 0)
  ('Gloria Gamma', 0)
  ('Francis Foxtrot', 0)

--------------------------------
RCV: round 4, 1st seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
RCV: vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) no vote - BLANK 
Total non-blank vote count: 222 (out of 224)
Results for the 1st open seat of contest Select Board (uid=0001):
  ('Betty Beta', 115)
  ('Anthony Alpha', 107)
  ('Emily Echo', 0)
  ('David Delta', 0)
  ('Gloria Gamma', 0)
  ('Francis Foxtrot', 0)
Removing the winner(s), Betty Beta, from consideration for the next open seat (seat 2 of 3)
Running next open seat tally ...

--------------------------------
RCV: initial tally, 2nd seat
RCV: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) note - Betty Beta, rank=3, is already a winner
Counted vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) for Gloria Gamma
Counted vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) for Francis Foxtrot
Total non-blank vote count: 222 (out of 224)
Running sequential RCV for the 2nd open seat
  ('Anthony Alpha', 57)
  ('Emily Echo', 46)
  ('Gloria Gamma', 40)
  ('Francis Foxtrot', 40)
  ('David Delta', 39)

--------------------------------
RCV: round 1, 2nd seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
Total non-blank vote count: 222 (out of 224)
  ('Anthony Alpha', 64)
  ('Emily Echo', 54)
  ('Francis Foxtrot', 53)
  ('Gloria Gamma', 51)
  ('David Delta', 0)

--------------------------------
RCV: round 2, 2nd seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
RCV: vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) last place pop and count: Gloria Gamma (vote 210) -> Anthony Alpha (vote 85)
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
Total non-blank vote count: 222 (out of 224)
  ('Anthony Alpha', 86)
  ('Emily Echo', 73)
  ('Francis Foxtrot', 63)
  ('Gloria Gamma', 0)
  ('David Delta', 0)

--------------------------------
RCV: round 3, 2nd seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
RCV: vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) last place pop and drop (Francis Foxtrot -> BLANK)
Total non-blank vote count: 221 (out of 224)
Results for the 2nd open seat of contest Select Board (uid=0001):
  ('Anthony Alpha', 115)
  ('Emily Echo', 106)
  ('Francis Foxtrot', 0)
  ('Gloria Gamma', 0)
  ('David Delta', 0)
Removing the winner(s), Anthony Alpha, from consideration for the next open seat (seat 3 of 3)
Running next open seat tally ...

--------------------------------
RCV: initial tally, 3rd seat
RCV: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) note - Anthony Alpha, rank=2, is already a winner
RCV: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) note - Betty Beta, rank=3, is already a winner
Counted vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) for Gloria Gamma
Counted vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) for Francis Foxtrot
Total non-blank vote count: 222 (out of 224)
Running sequential RCV for the 3rd open seat
  ('Emily Echo', 61)
  ('Gloria Gamma', 54)
  ('David Delta', 54)
  ('Francis Foxtrot', 53)

--------------------------------
RCV: round 1, 3rd seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
RCV: vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) last place pop and drop (Francis Foxtrot -> BLANK)
Total non-blank vote count: 221 (out of 224)
  ('David Delta', 76)
  ('Emily Echo', 73)
  ('Gloria Gamma', 72)
  ('Francis Foxtrot', 0)

--------------------------------
RCV: round 2, 3rd seat
INSPECTING: e92c62931cedfe0607865c624c178ecfc64cfd97 (contest=Select Board) as vote 210
RCV: vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97) last place pop and count: Gloria Gamma (vote 210) -> David Delta (vote 110)
INSPECTING: 08e29630567c00e2e8887c089072d1edf3a92215 (contest=Select Board) as vote 224
RCV: vote 224 (08e29630567c00e2e8887c089072d1edf3a92215) no vote - BLANK 
Total non-blank vote count: 221 (out of 224)
Final rcv round results for contest Select Board (uid=0001):
  ('David Delta', 112)
  ('Emily Echo', 109)
  ('Gloria Gamma', 0)
  ('Francis Foxtrot', 0)
Winner(s): Betty Beta, Anthony Alpha, David Delta
```

## Proportional RCV (a.k.a STV, a Weighted Inclusive Gregory Method implementation)
```
% tally-contests -c 0001 -t d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb --tally_override stv
Scanned 224 votes for contest (Select Board) uid=0001, tally=rcv, open_positions=3, max_selections=6 
Running a proportinal STV tally
STV: quota set to 57
  ballot 4 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) counted for Anthony Alpha (weight=1)
  found 1 blank ballot(s) (weight=1) marking as exhausted
STV: Round 1: ballot weight state — locked=1, active=223, total=224
  eliminating Francis Foxtrot with 32 votes
  ballot 4 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) counted for Anthony Alpha (weight=1)
  exhaustion detected — 2 ballots, total exhausted weight=2
STV: Round 2: ballot weight state — locked=1, active=223, total=224
  eliminating Gloria Gamma with 40 votes
  ballot 4 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) counted for Anthony Alpha (weight=1)
  exhaustion detected — 2 ballots, total exhausted weight=2
STV: Round 3: ballot weight state — locked=1, active=223, total=224
  Anthony Alpha elected with 61 votes
  transferring surplus of 4 (fraction=4/61) from Anthony Alpha
  total ballot weight BEFORE transfer = 224
  ballot d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb surplus transfer from Anthony Alpha (weight=4/61)
  post-transfer ballot weights — locked=58, active=166, total=224
  total ballot weight AFTER transfer = 224
  surplus accounting for Anthony Alpha — locked_to_quota=57, transferable_surplus=166
  removing winner Anthony Alpha from further consideration
  ballot 4 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) EXHAUSTED (weight=57/61)
  ballot 5 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) Anthony Alpha is no longer continuing - skipping
  ballot 5 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) Gloria Gamma is no longer continuing - skipping
  ballot 5 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) counted for David Delta (weight=4/61)
  exhaustion detected — 63 ballots, total exhausted weight=59
STV: Round 4: ballot weight state — locked=58, active=166, total=224
  eliminating David Delta with 53 31/61 votes
  ballot 4 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) EXHAUSTED (weight=57/61)
  ballot 5 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) Anthony Alpha is no longer continuing - skipping
  ballot 5 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) Gloria Gamma is no longer continuing - skipping
  ballot 5 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) David Delta is no longer continuing - skipping
  ballot 5 (d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb) counted for Emily Echo (weight=4/61)
  exhaustion detected — 63 ballots, total exhausted weight=59
STV: Round 5: ballot weight state — locked=58, active=166, total=224
  Betty Beta elected with 89 6/61 votes
  transferring surplus of 32 6/61 (fraction=1958/5435) from Betty Beta
  total ballot weight BEFORE transfer = 224
  post-transfer ballot weights — locked=115, active=109, total=224
  total ballot weight AFTER transfer = 224
  surplus accounting for Betty Beta — locked_to_quota=57, transferable_surplus=109
  removing winner Betty Beta from further consideration
  Emily Echo elected with 75 55/61 votes
  transferring surplus of 18 55/61 (fraction=1153/4630) from Emily Echo
  total ballot weight BEFORE transfer = 224
  ballot d9350e1f7287aaecd0460db12a5d7c2f6bb0e8bb surplus transfer from Emily Echo (weight=2306/141215)
  post-transfer ballot weights — locked=195 10498747/12582025, active=28 2083278/12582025, total=224
  total ballot weight AFTER transfer = 224
  surplus accounting for Emily Echo — locked_to_quota=1017060747/12582025, transferable_surplus=354379978/12582025
  removing winner Emily Echo from further consideration

STV summary:
Total Votes = 224; Quota = 57
Elected = ['Anthony Alpha', 'Betty Beta', 'Emily Echo']

Round Details:
Round 1:
  Elected: []
  Continuing: ['Anthony Alpha', 'Betty Beta', 'David Delta', 'Emily Echo', 'Francis Foxtrot', 'Gloria Gamma']
  Totals:
    Anthony Alpha: 45
    Betty Beta: 40
    Gloria Gamma: 34
    David Delta: 34
    Emily Echo: 38
    Francis Foxtrot: 32
Round 2:
  Elected: []
  Continuing: ['Anthony Alpha', 'Betty Beta', 'David Delta', 'Emily Echo', 'Gloria Gamma']
  Totals:
    Anthony Alpha: 50
    Betty Beta: 45
    Gloria Gamma: 40
    David Delta: 43
    Emily Echo: 44
Round 3:
  Elected: []
  Continuing: ['Anthony Alpha', 'Betty Beta', 'David Delta', 'Emily Echo']
  Totals:
    Anthony Alpha: 61
    Betty Beta: 55
    David Delta: 52
    Emily Echo: 54
Round 4:
  Elected: ['Anthony Alpha']
  Continuing: ['Betty Beta', 'David Delta', 'Emily Echo']
  Totals:
    Betty Beta: 56 19/61
    David Delta: 53 31/61
    Emily Echo: 55 11/61
Round 5:
  Elected: ['Anthony Alpha']
  Continuing: ['Betty Beta', 'Emily Echo']
  Totals:
    Betty Beta: 89 6/61
    Emily Echo: 75 55/61
Election Final: ['Anthony Alpha', 'Betty Beta', 'Emily Echo']
```

## Pairwise Condorcet
```
% tally-contests -c 0001 -t e92c62931cedfe0607865c624c178ecfc64cfd97,08e29630567c00e2e8887c089072d1edf3a92215 --tally_override pwc
Scanned 224 votes for contest (Select Board) uid=0001, tally=rcv, open_positions=3, max_selections=6 
Running a pairwise Condorcet tally
Pairwise ranking for ballot vote 210 (e92c62931cedfe0607865c624c178ecfc64cfd97): {'Gloria Gamma': 0, 'Anthony Alpha': 1, 'Betty Beta': 2, 'David Delta': 3, 'Emily Echo': 4, 'Francis Foxtrot': 5}
Pairwise vote 101 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Anthony Alpha', 'Betty Beta')
Pairwise vote 113 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Anthony Alpha', 'David Delta')
Pairwise vote 109 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Anthony Alpha', 'Emily Echo')
Pairwise vote 112 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Anthony Alpha', 'Francis Foxtrot')
Pairwise vote 108 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Betty Beta', 'David Delta')
Pairwise vote 112 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Betty Beta', 'Emily Echo')
Pairwise vote 110 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Betty Beta', 'Francis Foxtrot')
Pairwise vote 101 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Gloria Gamma', 'Anthony Alpha')
Pairwise vote 107 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Gloria Gamma', 'Betty Beta')
Pairwise vote 114 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Gloria Gamma', 'David Delta')
Pairwise vote 108 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Gloria Gamma', 'Emily Echo')
Pairwise vote 105 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Gloria Gamma', 'Francis Foxtrot')
Pairwise vote 107 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('David Delta', 'Emily Echo')
Pairwise vote 111 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('David Delta', 'Francis Foxtrot')
Pairwise vote 114 (e92c62931cedfe0607865c624c178ecfc64cfd97) for ('Emily Echo', 'Francis Foxtrot')
Pairwise ranking for ballot vote 224 (08e29630567c00e2e8887c089072d1edf3a92215): {'Francis Foxtrot': 0}
Pairwise vote 105 (08e29630567c00e2e8887c089072d1edf3a92215) for ('Francis Foxtrot', 'Anthony Alpha')
Pairwise vote 107 (08e29630567c00e2e8887c089072d1edf3a92215) for ('Francis Foxtrot', 'Betty Beta')
Pairwise vote 111 (08e29630567c00e2e8887c089072d1edf3a92215) for ('Francis Foxtrot', 'Gloria Gamma')
Pairwise vote 106 (08e29630567c00e2e8887c089072d1edf3a92215) for ('Francis Foxtrot', 'David Delta')
Pairwise vote 101 (08e29630567c00e2e8887c089072d1edf3a92215) for ('Francis Foxtrot', 'Emily Echo')
Creating 6 node Condorcet directed acyclic graph to determine winners:
Adding edge Emily Echo -> Francis Foxtrot (margin=20, 121-101)
Adding edge Anthony Alpha -> David Delta (margin=17, 119-102)
Adding edge Gloria Gamma -> David Delta (margin=17, 119-102)
Adding edge Betty Beta -> Emily Echo (margin=16, 119-103)
Adding edge Anthony Alpha -> Francis Foxtrot (margin=12, 117-105)
Adding edge David Delta -> Francis Foxtrot (margin=10, 116-106)
Adding edge Betty Beta -> Francis Foxtrot (margin=9, 116-107)
Adding edge Anthony Alpha -> Gloria Gamma (margin=9, 115-106)
Adding edge Anthony Alpha -> Emily Echo (margin=9, 115-106)
Adding edge Betty Beta -> Anthony Alpha (margin=8, 115-107)
Adding edge Gloria Gamma -> Emily Echo (margin=5, 113-108)
Adding edge Betty Beta -> David Delta (margin=4, 113-109)
Skipping edge Gloria Gamma -> Betty Beta (margin=4, 113-109) to avoid cycle
Adding edge David Delta -> Emily Echo (margin=3, 112-109)
Condorcet topological order: Betty Beta, Anthony Alpha, Gloria Gamma, David Delta, Emily Echo, Francis Foxtrot
Condorcet winner(s): ['Betty Beta', 'Anthony Alpha', 'Gloria Gamma']
```
