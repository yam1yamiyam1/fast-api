## Drill Format Rules

- All logic inside `run_drill_N()` — no module-level state
- Scenario + Requirements inside `run_drill_N()` as a comment block
- `# --- YOUR CODE HERE ---` marks where I write my solution
- Each test: print("Test N: <description>"), assert statements, print the key values being tested, then print(" PASS") on success
- All imports have `# noqa: F401`
- Expected output block always present at the bottom — exact copy of what the terminal should print
- All tests use `assert`, not just print
- One new concept per drill, everything else is revision
- Never reuse a scenario from the Used list
- After generating a drill, go silent — wait for the student's attempt
