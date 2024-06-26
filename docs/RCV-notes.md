## Rank Choice Voting

VoteTrackerPlus (VTP) provides unique insight and transparency to Rank Choice Vote (RCV) contests.  Since VTP provides an anonymous way for every voter to track their individual contest votes in an unencrypted data-at-rest manner, the end voter can witness - replay in a repeatable manner - the tally of their specific vote.

It is one thing to see a plurality contest tally of a few thousand votes (a local election) or a few million votes (a national election) and witness one's vote being adding to the tally on ones own smart device.  And then to additionally have that tally match the same VTP tally that election officials report.  But in the case of RCV contests, such transparency is important for a few additional reasons: namely, though RCV contests provide better and more fair and representative elections, RCV contests are more complicated to implement, understand, and hence be trusted by the general public.  RCV contests are more prone to misinformation and malinformation attacks.

With VTP and its inherent transparency, every end voter can witness each run-off round of a RCV contest and potentially witness their specific vote get re-cast if they have voted for a losing-round candidate.  Not only does this transparency increase trust in RCV tallies but it also helps explain how RCV tallies work.

Consider the following output from a RCV contest in the [VTP-mock-election.US.17](https://github.com/OpenVotingTechnologyGroup/VTP-mock-election.US.17/) repository:

```bash
Scanned 170 contests for contest (U.S. Senate) uid=0001, tally=rcv, max_selections=6, win_by>0.5

--------------------------------
RCV: round 0
Counted 374ce87855270169b3fe7007249ab67eb599a6dd as vote 15: selection=Francis Foxtrot
Total vote count: 134
  ('Anthony Alpha', 29)
  ('Betty Beta', 25)
  ('Francis Foxtrot', 24)
  ('David Delta', 23)
  ('Emily Echo', 21)
  ('Gloria Gamma', 12)

--------------------------------
RCV: round 1
INSPECTING: 374ce87855270169b3fe7007249ab67eb599a6dd (contest=U.S. Senate) as vote 15
Total vote count: 134
  ('Anthony Alpha', 32)
  ('Betty Beta', 28)
  ('Francis Foxtrot', 26)
  ('David Delta', 25)
  ('Emily Echo', 23)
  ('Gloria Gamma', 0)

--------------------------------
RCV: round 2
INSPECTING: 374ce87855270169b3fe7007249ab67eb599a6dd (contest=U.S. Senate) as vote 15
Total vote count: 134
  ('Anthony Alpha', 38)
  ('Francis Foxtrot', 34)
  ('Betty Beta', 33)
  ('David Delta', 29)
  ('Emily Echo', 0)
  ('Gloria Gamma', 0)

--------------------------------
RCV: round 3
INSPECTING: 374ce87855270169b3fe7007249ab67eb599a6dd (contest=U.S. Senate) as vote 15
Total vote count: 133
  ('Anthony Alpha', 45)
  ('Betty Beta', 45)
  ('Francis Foxtrot', 43)
  ('David Delta', 0)
  ('Emily Echo', 0)
  ('Gloria Gamma', 0)

--------------------------------
RCV: round 4
INSPECTING: 374ce87855270169b3fe7007249ab67eb599a6dd (contest=U.S. Senate) as vote 15
RCV: 374ce87855270169b3fe7007249ab67eb599a6dd (contest=U.S. Senate) last place pop and count (Francis Foxtrot -> Anthony Alpha)
Total vote count: 131
Final results for contest U.S. Senate (uid=0001):
  ('Betty Beta', 66)
  ('Anthony Alpha', 65)
  ('Francis Foxtrot', 0)
  ('David Delta', 0)
  ('Emily Echo', 0)
  ('Gloria Gamma', 0)
```
In the above, any voter who tallies the U.S. Senate contest and supplies the 374ce87855270169b3fe7007249ab67eb599a6dd as a contest check (digest) to track will observe that in round 4, that vote was recast from Francis Foxtrot to Anthony Alpha, and it was done so as vote 15 out of 170 votes.

Though VTP can print all the round recastings, being able to show the specific recasting of a voter's specific vote (who remembers their ballot receipt's secret row number) so that they can verify that their vote has been correctly cast, counted, and tallied, adds extra resilience to RCV in the face of misinformation and malinformation attacks.

Note that all the software to execute the tally is included in the VTP [Merkle Tree](https://en.wikipedia.org/wiki/Merkle_tree), so that when downloading the VTP repos for the election, the voter also gets all the software to run the tallies locally on their smart devices.
