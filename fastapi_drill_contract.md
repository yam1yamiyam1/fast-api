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
- Requirements and tests must be consistent — every signature, parameter, and behavior in the tests must match exactly what the requirements describe
- Requirements must be ordered by dependency — if X is used inside Y, X must be defined before Y in the requirements list
- Every argument and variable in the Requirements block must include: name, type, and one plain-English sentence explaining what it represents in the scenario domain — not just its technical type. Example: manifest: dict — the cargo document being validated, passed as-is to the inspector. Never leave a domain variable unnamed or unexplained.
- For Real FastAPI concepts (drills 91–130): if the concept maps to something built in pure Python drills, show a translation block — "Pure Python:" then "FastAPI:" side by side. Only use patterns actually drilled, never invented. If no pure Python equivalent exists, skip the block and explain from scratch.
