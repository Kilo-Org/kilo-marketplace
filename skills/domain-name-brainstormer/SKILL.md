---
name: domain-name-brainstormer
description: "Generates creative, brandable domain name candidates from a project description using compound words, portmanteaus, and invented names, then checks availability across TLDs (.com, .io, .dev, .ai, .app) and ranks results by memorability, brand fit, and price. Use when launching a new project or company, rebranding, registering a side project domain, brainstorming startup names, or finding available alternatives when a preferred domain is taken."
metadata:
  category: business-marketing
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: domain-name-brainstormer
---

## Workflow

### Step 1: Gather Requirements

Collect from the user: project description and target audience, preferred keywords or word roots, TLD preferences (.com, .io, .dev, .ai, .app), naming style (descriptive, abstract, compound, invented), and maximum length.

### Step 2: Generate Domain Name Candidates

Create 10-15 candidates across strategies: compound words, portmanteaus, descriptive names, abstract/invented words, and TLD hacks. Mix at least 3 strategies to give the user variety.

### Step 3: Check Availability

Use WHOIS lookups or DNS queries to verify each candidate:

```bash
# Quick DNS check — NXDOMAIN means likely available
for domain in snippetbox.com codeclip.com snippet.dev codebox.io; do
  if dig +short "$domain" | grep -q '.'; then
    echo "✗ $domain — TAKEN (has DNS records)"
  else
    echo "✓ $domain — likely available (no DNS records)"
  fi
done
```

```python
# Programmatic WHOIS check (more reliable)
import subprocess

def check_domain(domain):
    result = subprocess.run(["whois", domain], capture_output=True, text=True)
    if "No match" in result.stdout or "NOT FOUND" in result.stdout:
        return "available"
    return "taken"

domains = ["snippetbox.com", "codeclip.com", "snippet.dev"]
for d in domains:
    status = check_domain(d)
    print(f"{'✓' if status == 'available' else '✗'} {d} — {status}")
```

For bulk checks, use the Domainr API: `curl -s "https://domainr.p.rapidapi.com/v2/status?domain=snippetbox.com"`.

Present results grouped by availability:

```
## Available (.com)
1. ✓ snippetbox.com — Clear, memorable, standard pricing (~$12/yr)
2. ✓ codeclip.com — Short (8 chars), standard pricing

## Available (Alternative TLDs)
3. ✓ snippet.dev — .dev signals developer tool (~$14/yr)
4. ✓ codebox.io — Tech-forward (~$35/yr)

## Taken / Premium
- codeshare.com (Taken, aftermarket est. $2,500)
```

### Step 4: Rank and Recommend

Rank the top available candidates with reasoning:

- **Top pick**: Best blend of availability, memorability, and brand fit
- **Runner-up**: Strong alternative with different trade-offs
- **Budget option**: Available at standard registration price (~$10-15/yr)

### Step 5: Next Steps

After the user picks a domain: register it promptly (good names sell fast), check social media handle availability (`@username`) on key platforms, register the .com variant if primary TLD is different, and search trademark databases (USPTO TESS: `https://tmsearch.uspto.gov`).

## Example

**Prompt**: "I'm building a tool for developers to share code snippets. Suggest creative domain names."

**Process**: Analyzes project (target: developers, code sharing). Generates 12 candidates using compound and portmanteau strategies. Runs WHOIS checks across .com, .dev, .io.

**Output**: snippet.dev (top pick — short, memorable, .dev signals developer tool, $14/yr), snippetbox.com (runner-up — .com universally trusted, descriptive, $12/yr), codeclip.io (budget option — available at standard .io pricing).

**Inspired by:** Ben Aiad's use case from Lenny's Newsletter
