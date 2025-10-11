## A Quick Comparison of Plurality, sequential RCV, and Condorcet Tallies

What follows is the STDOUT printout (what terminal applications such as [MacOS Terminal](https://en.wikipedia.org/wiki/PowerShell) or [Windows PowerShell](https://en.wikipedia.org/wiki/PowerShell) will display) of three different contest tallies over the same data.  The data is a multi-seat contest selecting <u>three winners from six contestants</u>.

The first tally below is [plurality](https://en.wikipedia.org/wiki/Plurality_(voting)), the second is [Ranked Choice Vote](https://en.wikipedia.org/wiki/Ranked_voting) (a [sequential RCV implementation](https://fairvote.org/proportional-ranked-choice-voting-vs-sequential-ranked-choice-voting/)), and the third is [pairwise Condorcet](https://en.wikipedia.org/wiki/Condorcet_method).  VoteTrackerPlus is a [Merkle Tree](https://en.wikipedia.org/wiki/Merkle_tree) election system implementation similar to blcokchain and cryptocurrencies but also fundementally different as there are no private keys of ownership - the ballot contest cryptographic digital signatures are completely anonymous, each contest on a voter's ballot receiving its own unique and anonymous signature.  In this way each contest vote can be referenced by its signature.  When tallying a contest, to be able to support election transparency, the signatures can be supplied to the tally which will track all the tally events associated with that specific vote.

In the below example, the first contest digital signature, [e92c62931cedfe0607865c624c178ecfc64cfd97](https://github.com/OpenVotingTechnologyGroup/VTP-mock-election.sRCV.1/commit/e92c62931cedfe0607865c624c178ecfc64cfd97), is for a ballot where the voter ranked all 6 candidates.  The ballot is counted as the 210 vote in the election.  With the second digest, [08e29630567c00e2e8887c089072d1edf3a92215](https://github.com/OpenVotingTechnologyGroup/VTP-mock-election.sRCV.1/commit/08e29630567c00e2e8887c089072d1edf3a92215) the voter only selected a single candidate and did not supply any further ranking information.  That ballot is counted as the 224th vote in the election.

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

## Rank Choice Vote (sequential)
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
Skipping edge Gloria Gamma -> Betty Beta (margin=4, 113-109) to avoid cycle
Condorcet topological order: Betty Beta, Anthony Alpha, Gloria Gamma, David Delta, Emily Echo, Francis Foxtrot
Condorcet winner(s): ['Betty Beta', 'Anthony Alpha', 'Gloria Gamma']
```
