# An Informal Description of the Security Model of VoteTrackerPlus

__UNDER CONSTRUCTION__

## 1) Terminology

For definitions and technical terms, please refer to the [NIST Glossary](https://pages.nist.gov/ElectionGlossary/)

## 2) What does this page cover?

This page describes a high-level summary of the security model, [cryptographic protocols](https://en.wikipedia.org/wiki/Cryptographic_protocol), [attack surfaces](https://en.wikipedia.org/wiki/Attack_surface), and [zero trust aspects](https://en.wikipedia.org/wiki/Zero_trust_security_model) of VTP.  For ease of understanding, this information is divided three domains:

1) Data-at-Rest
2) Data-in-Motion-Local
3) Data-in-Motion-Remote

Since the planning as well as the execution of a public election occurs over many months, the above dichotomy is overlayed with four more or less chronological time slices:

1) Election Data creation and deployment
2) Pre-election day ballot distribution and potential early voting ballot scanning
3) Election day activities
4) Post election day activities

There is a (Threat Model MindMap)[https://mm.tt/app/map/3063357845?t=DuNY3bTVbg] that might be of interest.

The primary driver for the first three domains is due to VoteTrackerPlus's primary design tenet is that since both the recorded per contest CVRs and ballot receipts are already anonymous when they are added to the underlying Git Merkle Tree, there is no need or desire to encrypt the data at rest.  However, since the all the election data (software, election definition, cast contest CVRs etc) is also stored in the same underlying Git Merkle Tree, attack surface wise this results in the integrity of the Merkle Tree itself as a primary target and hence attack surface.

Thus a major benefit as well as an attack surface of VTP is the data at rest itself, protected by the natural Git Merkle Tree.  Thus Data-at_rest is called out as the first domain of interest.

The Data-in-Motion-Local domain refers to contest level CVRs and ballot receipts moving in the local polling location (call it LAN local motion, though actual VTP deployments may not have a LAN).  The polling location may support in-person voting or it may be an election official (and public watchers) only location.

The Data-in-Motion-Remote domains refers to when the local Git repos are being transferred/pushed/pulled to/from the upstream remote or when upstream remote changes are being pulled down to the polling location.  This includes updating git submodule references.

A primary driver for the second four time partitions of a election is due to VoteTrackerPlus's primary design that all the software and blank ballot definitions are also part of the underlying Git Merkle Tree.  As such, as the election is defined, deployed, and tested, VoteTrackerPlus brings modern (software development processes)[https://en.wikipedia.org/wiki/Software_development_process] to this pre election day time period by incorporating modern (agile project management)[https://en.wikipedia.org/wiki/Agile_software_development] and (DecSecOps automation)[https://en.wikipedia.org/wiki/DevOps#DevSecOps,_shifting_security_left].

## 3) What does this page not cover?

Lots.  This page is just an overview of VTP workflows from a security point of view.  In addition, election officials in different precincts will chose different VTP deployment models with different election equipment.  Such choices will directly effect the scope of various attack surfaces.  For example, one precinct may decide to have one VTP tabulator per polling center while another may wish to place a VTP tabulator in each ballot scanner while yet another may simply use dedicated touch screens resulting in effectively one VTP scanner and one VTP tabulator.

Also, election officials can decide how to push and pull VTP data to/from the remote.  The push'es and pulls could occur by sneaker, wire, or radio frequencies.

Note - regardless of mode the data should always be encrypted and follow solid industrial/military grade encryption standards regarding data movement.

## 4) VTP is not introducing a new cryptographic protocol

VTP is __not__ introducing a new cryptographic protocol, such as for example [ElectionGuard](https://www.electionguard.vote/) by introducing homomorphic encryption.  New cryptographic protocols need not to be designed, vetted, and built.  VTP leverages already in-play and existing cryptographic protocols for all three security domains across all four time slices, such as [PKI](https://en.wikipedia.org/wiki/Public_key_infrastructure) and [PGP](https://en.wikipedia.org/wiki/Pretty_Good_Privacy), additional security features such as [2FA](https://en.wikipedia.org/wiki/Multi-factor_authentication) as a way to increase tamper-resistance and to add greater resistance to accidental corruption and adversarial attacks.

However, one aspect of VTP that is new and does require security review is that the ballot receipt containing 100 contest level [cast vote record](https://pages.nist.gov/ElectionGlossary/#cast-vote-record) [SHA-256](https://en.wikipedia.org/wiki/SHA-2) digests, whether it is printed on paper at in-person voting scenarios or returned to the user's smart device in internet based voting scenarios.  The ballot receipt contains 99 randomly selected contest CVR's from other ballots.  VTP also records the cast vote records into the Git based [Merkle Tree](https://en.wikipedia.org/wiki/Merkle_tree) in random order.  Both instances of this randomization neet to be cryptographically vetted by cryptographic and security experts.

Note that there are no private keys associate with the public digests contained in the ballot receipt.  The only private keys contained or active in a VTP election are those public and private keys employed to secure the data in motion and to secure the running of the election itself.  The former are used for TLS communication and the latter are used to prevent insertion of fraudulent ballots and CVRs as each election has it's own CA/ICA trust store and private/public keys.

## 5) The VTP Attack Surfaces - a Decomposition into Three Spatial Domains

### 5a) Data-at-Rest

VTP leverages [Git](https://git-scm.com/) as the [Merkle Tree](https://en.wikipedia.org/wiki/Merkle_tree) engine in which to store both the VTP software applications, blank ballot information, as well as the [cast vote records](https://pages.nist.gov/ElectionGlossary/#cast-vote-record).  VTP accomplishes this by storing the individual precinct data in precinct *owned* repos that are configured as [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) via the parent git repo that is effectively *administering the election*.  In all repos Git is configured to only use [SHA-265 commit digests](https://github.com/git/git/blob/main/Documentation/technical/hash-function-transition.txt).  In addition the Git hosting service is configured to require all commits to have valid  [GPG](https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/about-commit-signature-verification) signatures, etc.

At rest, the git repositories are protected from tampering both via the nature of the SHA-256 Merkle Tree as well as the git hosting service protecting the git repositories at rest.  Since the repositories are publicly available, each voter can have their own complete copy as well and independently secure their clone as desired.  Note that VTP repositories contain both the VTP software apps source, such as those used to tally the ballots for the specific associated election as well as the cast vote records for that election.  All VTP software programs are written in Python as source code and include all testing and CI/CD pipeline infrastructure code as well such that every voter can inspect, test, and comment on all aspects of the VTP programs.

### 5b) Data-in-Motion-Remote

Data-in-Motion-Remote refers to that part of the attack surface in play when someone is either legitimately trying to update/download a remote VTP repo or when VTP is being independently attacked via false update attempts.

#### Prior to ballots being scanned

Regarding the git hosting service and using GitHub as an example (any sufficiently robust git hosting service can be used), the election is initially setup via a [GitHub Organization](https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/about-organizations) representing the actual real organization that is running the overall election.  The parent VTP repo for the election is forked from the latest official release of the VTP open source project.  The organization is set up with the industry/military best practices regarding security.  For purposes of this description, will assume this is for the 2024 US election and that the election is being run by some thin federal agency.

The parent VTP repo is configured for the next level of the Geopolitical Geographical Overlay (GGO - note, NIST refers to a GGO as a [Geopolitical Unit](https://pages.nist.gov/ElectionGlossary/#geopolitical-unit)) that comprise the first GGO overlay of the physical geographical geopolitical locations on the territory over which the election is being held.  The parent VTP organizations works with official representatives of each of the GGO's to create and verify election officials as GitHub users with the proper security settings (GPG keys etc) and proper forks of the release VTP repos.

Again using the 2024 US election as an example, if there is no such parent organization running the election at a federal level, then each state acts as an independent parent organization.  It is possible that some states will decide to share a single parent, facilitating the overall election process, while other state will opt out of such sharing while other state will not even be employing a VTP solution.

Regardless, the root election owning organization establishes the chain-of-trust with downstream repo owners.  From a [SDLC](https://en.wikipedia.org/wiki/Systems_development_life_cycle) point of view, prior to the start of ballot scanning, the various GGO's follow standard Git/GitHub best software agile development methods to update all the GGO VTP repos with the correct ballot races and questions as well as the GIS information.  The GIS information allows VTP to print address correct ballots.

There is a natural and automated CI pipeline that is followed prior to [pull requests](https://en.wikipedia.org/wiki/Distributed_version_control) being merged into the root VTP repo main branch, helping to validate changes even at this stage of the election.  Note that all submodules main branch updates also adhere to such a policy.

#### During Ballot Scanning and Cast Vote Record Creation

Once the election enters the phase of scanning ballots and creating cast vote records, in theory no additional non cast vote records changes are allowed by the controlling organization.  This would nominally be enforced at pull request time if not earlier in the [SDLC](https://en.wikipedia.org/wiki/Systems_development_life_cycle) process.

Regardless if any such changes are made, every change, included the authenticated author, will be seen by every voter when the VTP repos are downloaded.

During this phase of cast vote record creation, the live VTP repos are not publicly available.  Note that operationally the **real** VTP repos are highly armored with only limited and official access.  These repos are technically never publicly available.  What is publicly available are direct downstream mirrors of these.  Once scanning of the ballots begins, the mirrors are **NOT** updated until all the polls close.

However, the security of the previous section still applies.  In addition, all pull requests have an additional non internet based 2FA between the root organization and individual on-the-ground election official(s) for each distributed local VTP repo.  Nominally there is one local VTP repo per voting center such that any single or set of voting centers can go offline and still process local ballots.  When the centers come back on line and push cast vote records, the 2FA is executed at that time.

After all the polls close, any un-pushed cast vote records are continued to be pushed and other ballots such as mail-in, absentee, etc., are also continued to be scanned and pushed.

Independent of the continued scanning of yet-to-be scanned ballots, once all the polls close and the election is considered *closed* for any additional unqueued ballots, the mirrors of the real VTP repos can be updated so that the electorate can see how the election is unfolding in real time.  This real-time transparency allows the electorate to inspect their ballots as well as inspect the VTP voter rolls.

Note that in this manner, every member of the electorate is on equal footing with election officials.

#### Post Ballot Scanning and Cast Vote Record Creation

After all the polls close, the VTP repos for the election can be made publicly available.  Voters can continually update their clones as the queues of un-scanned, un-pushed cast vote records are pushed.  Each voter and each election official can tally the votes on their devices as well as inspecting the voter id repos.  The voter id repos are separate repos that solely contain the voter names and addresses and no other data.  This allows all voters to search for local and non local fraudulent voter names or addresses.

Note - it is not covered here, but when subsequent elections are held via VTP technology solution, depending on the state configuration of VTP it is possible for VTP to track a specific voter across addresses, greatly reducing the ability of an individual to vote in multiple times via different addresses.  Similar to risk limiting audits of the ballot counting/scanning process, risk limiting audits can be executed against voters with the same name but with different addresses within a single election but also across multiple elections.

Since the voter id registration process itself can be either erroneous or attacked, which is completely separate from VTP itself, it is quite possible that legal cases will be filed to throw out certain ballots or sets of ballots, perhaps at specific voting center.  Technically this can be done by selecting the physically ballots to be revoked and revoking the specific SHA-256 commits for the associated cast vote records.

If fraudulent cast vote records are found, they can be revoked in a similar manner.

Note that since every cast vote records nominally has a voter behind it, a voter will know when their cast vote record is revoked.  This would theoretically enable a counter legal challenge to be brought if the voter so chose.

### In the General Case

This section primarily covers the general security of when there is data in motion from one spot on the planet / internet to another, for example when a local voting center with its local VTP repo goes to push their repo(s) to the election root VTP server.

At the https layer, all election official connections will employ [mutual authentication](https://en.wikipedia.org/wiki/Mutual_authentication) ssl leveraging a root certificate authority chain created and managed by the root level parent GGO running the election.  Note - the CI pipeline testing of this operational part of VTP will include cert revocation - all end points in the operational footprint of a VTP election must be able to adequately and properly handle cert revocation and new/renew cert allocation.  The CI test plan includes this type of adversarial attack.

On top of this military/industrial grade https/ssl layer will reside the GitHub app level security model at the highest grade configuration and implementation.  For example, all commits will be GPG signed and during the cast vote record creation phase, all pull requests require out-of-band 2FA.

Regarding reading/cloning repositories from the VTP Git service, there will be a mirror of the actual live repos to several different git service end-points.  This will allow the voters at large as well as election officials who only need to read/clone the VTP repos to access services built to handle the traffic (perhaps many millions of connections per second) as well as the adversarial assaults on large capacity servers without effecting the uploading of commits to the real root servers.  The real VTP upstream servers will be hardened in a manner consistent with limited read/write access and hidden to extent possible from the internet at large.

### 5c) Data-in-Motion-Local

Data in local motion refers to the security models and attack surfaces in play within a specific LAN where either cast vote records are being created/processed or prior to the start of an election when the various GGO's are configuring VTP and the blank ballots as well as testing VTP in various test scenarios.

Prior to when the first ballots are scanned, the various VTP repos are undergoing normal [SDLC](https://en.wikipedia.org/wiki/Systems_development_life_cycle) agile development methodologies.  As Git is a well understood [distributed version control](https://en.wikipedia.org/wiki/Distributed_version_control) system, standard Git based agile development practices will apply.  Basically, within a LAN, each developer is interacting with the live remote repos - there is no special LAN specific cryptographic protocols in play beyond the well understood military/industrial best practices.

Once a LAN at a voting center starts scanning / processing cast vote records, the LAN needs to be protected against run-time adversarial attacks at disrupting active voters.  This is no different then other non-VTP implementations.  Best practices should be used - wired connections if possible, WiFi encryption, etc.

Ballot scanning and tabulating is the time and place where new [GUIDs](https://en.wikipedia.org/wiki/Universally_unique_identifier) and SHA-256 Git digests are being generated.  The generation of both are completely local as the salt's for the GUIDs include the various private and public keys already shared between the local VTP submodule repo and the root parent VTP repo and git service.

At a high level, each ballot is separated into each [contest](https://pages.nist.gov/ElectionGlossary/#contest).  The voter's ballot will receive a different git commit for each contest.  The main purpose of this is to minimize the revelation of perhaps nefarious patterns to the multiple perhaps *uninteresting* contests on a ballot.  There is no way in VTP to re-assemble the individual ballot contests into the original single (paper) ballot with the sole exception being the private information returned to the voter - their specific row offset in their specific voter sheet.

Once the voter has personally and privately blessed the cast vote record or decided to pass on that verification step entirely, the physical ballot is printed with a GUID that is both random and based on a unique local election repo private key as well as a root election private key passed from the root repo/organization to the local via a private key exchange.  An adversary will not be able to generate a valid GUID against the public election keys without these keys.

This ballot GUID is also added to the digital scan of the ballot by the ballot scanning device.  This simply associates the physical ballot with the actual digital scan, both of which are never made public.  This association aids audits and recounts by limiting the ability to alter either the physical or digital scans in isolation.  Election officials control the physical ballot while the contractual agreement between the election officials and the ballot scanning hardware supplies determines the ownership of the actual ballot scans.
