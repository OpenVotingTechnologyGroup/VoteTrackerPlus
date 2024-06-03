## Testing Strategy

#### Work in Progress

Some initial thoughts on a test triangle so to speak:

1) Unit Testing (pytest)
   - requires a VTP-dev-end environment
   - simple basic sanity tests
     - tests/test_versions.py
   - test the CLI entrypoints can print help
     - tests/test_cli_help.py

2) Integration Testing (pytest)
   - requires a VTP-dev-end environment
   - test blank ballot creation
     -  tests/test_blank_ballot.py
   - test voting
     - tests/test_voting.py
   - test inspecting CVRs
     - tests/test_cvrs.py
   - test tallying
     - tests/test_tallies.py
   - test setup-vtp-demo
     - tests/test_setupdemo.py

3) End-to-End Testing (pytest)
   Requires a demo environment (post setup-vtp-demo)
   - test demo voting
   - test running VTP scanner app
   - test running VTP tabulation app
   - test running demo ballot inspection
   - test running demo tallying
