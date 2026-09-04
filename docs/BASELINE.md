# Original target and evidence

`lab/original` is a byte-for-byte snapshot of `repo/project/starter-app` at course revision `6996818be46cfb3f26b9b9d88e7c95af7ae32176`. Its application SHA-256 is recorded in `evidence/baseline.json`. Do not run its original Compose file: the historical target binds all interfaces, enables debugging and resets its database.

Use the isolated test-client harness instead. It creates a temporary database, initializes the correct team's marker, runs harmless local probes, writes actual JSON responses, and removes the temporary database. It never opens a network listener.

```sh
uv venv .lab-venv --python 3.11
uv pip install --python .lab-venv/bin/python -r lab/original/requirements.txt itsdangerous==2.0.1 MarkupSafe==2.0.1
.lab-venv/bin/python scripts/reproduce_baseline.py
```

The two extra pins preserve compatibility with this old Flask/Jinja stack; none of the provided direct dependency pins or application code are changed. This environment intentionally contains vulnerable packages and is excluded from the runtime image and release package. Never use it to serve real data.

The CSRF probe establishes that the server accepts an authenticated foreign-origin POST without a token. It does not claim that every modern browser sends the starter's cookie in all cross-site situations. The XSS probe proves executable HTML reaches the response; the SSTI probe proves `{{7*7}}` evaluates to `49`. Neither is described as a browser screenshot or a demonstrated remote shell.
