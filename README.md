# envdiff

Compare `.env` files across environments and surface missing or mismatched keys.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/yourname/envdiff.git
cd envdiff && pip install -e .
```

---

## Usage

```bash
# Compare two .env files
envdiff .env.development .env.production

# Compare multiple files against a base
envdiff .env.example .env.staging .env.production
```

**Example output:**

```
Missing in .env.production:
  - DATABASE_URL
  - REDIS_HOST

Mismatched keys between .env.development and .env.production:
  - DEBUG: "true" vs "false"
  - LOG_LEVEL: "debug" vs "error"
```

You can also use it as a Python library:

```python
from envdiff import compare

results = compare(".env.development", ".env.production")
for issue in results:
    print(issue)
```

---

## Options

| Flag | Description |
|------|-------------|
| `--missing` | Show only missing keys |
| `--mismatch` | Show only mismatched values |
| `--quiet` | Exit with code 1 if differences found (useful in CI) |

---

## License

MIT © [yourname](https://github.com/yourname)