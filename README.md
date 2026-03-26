# easyrecon

```
  ___  ___  ____  _  _  ____  ___  _____  __ _
 | __|/ _ \/ ___|\ \/ /|  _ \| __||  ___||  ` |
 | _|| |_| \___  \  / | |_) | _|  | |    | .  |
 |___|\___/ |___/ \/  |____/|___| |_|    |_|\_|
```

**Fast, automated recon suite for bug bounty hunters and pentesters.**

Run one command. Get subdomains, URLs, live hosts, categorized attack surface, and a full report — automatically.

---

## Features

- **6-Phase Pipeline** — Subdomain enum → URL discovery → Live detection → Categorization → Report
- **3 Tools Per Phase** — Runs subfinder + amass + assetfinder in parallel, merges and deduplicates results
- **Auto-Install** — Missing tools are installed automatically on first run
- **Dynamic Tool Registry** — Disable, timeout, or customize any tool via `easyrecon.yaml`
- **Smart Categorization** — 12 attack surface categories: params, admin, api, sensitive, login, upload, backup, js, json, xml, php, errors
- **Premium Terminal UI** — Rich-powered live spinners, progress bars, tables, color-coded output
- **Graceful Error Handling** — 25+ edge cases handled — never crashes
- **Universal Command** — `easyrecon target.com` from anywhere after install

---

## Requirements

- Python 3.8+
- Go (for tool installation)

---

## Installation

```bash
git clone https://github.com/unrealsrabon/easyrecon
cd easyrecon
chmod +x install.sh
./install.sh
```

`install.sh` will:
1. Check Python and Go versions
2. Install all 7 required tools via `go install`
3. Install Python dependencies
4. Optionally add `easyrecon` to your PATH

After that, just run:

```bash
easyrecon target.com
```

---

## Usage

```bash
# Full recon (all 6 phases)
easyrecon target.com

# Run a specific phase only
easyrecon target.com --phase subdomain
easyrecon target.com --phase urls
easyrecon target.com --phase live
easyrecon target.com --phase categorize
easyrecon target.com --phase report

# Custom options
easyrecon target.com --timeout 60          # Override all tool timeouts
easyrecon target.com --output ~/results    # Custom output folder
easyrecon target.com --config custom.yaml  # Custom config file
easyrecon target.com --no-install          # Skip auto-install check

# Info
easyrecon --version
easyrecon --help
```

---

## Output Structure

```
results/
└── target.com_2026-03-13_04-20/
    ├── raw/                    ← Raw output from each tool
    │   ├── subfinder.txt
    │   ├── amass.txt
    │   ├── assetfinder.txt
    │   ├── gau.txt
    │   ├── waybackurls.txt
    │   └── katana.txt
    ├── processed/              ← Merged, deduplicated results
    │   ├── all_subdomains.txt
    │   ├── live_subdomains.txt
    │   ├── all_urls.txt
    │   └── live_urls.txt
    ├── categorized/            ← Attack surface categories
    │   ├── sensitive.txt
    │   ├── admin.txt
    │   ├── api.txt
    │   ├── params.txt
    │   ├── login.txt
    │   ├── upload.txt
    │   ├── backup.txt
    │   ├── js.txt
    │   ├── json.txt
    │   ├── xml.txt
    │   ├── php.txt
    │   └── errors.txt
    ├── report.md               ← Full recon report
    └── errors.log              ← Any errors during run
```

---

## Categories

| Category | What it finds | Priority |
|---|---|---|
| `sensitive` | `.git`, `.env`, `/backup`, `/config`, `/actuator` | 🔴 HIGH |
| `admin` | `/admin`, `/dashboard`, `/panel`, `/cp` | 🟠 HIGH |
| `login` | `/login`, `/auth`, `/wp-admin`, `/sso` | 🟠 HIGH |
| `upload` | `/upload`, `/file`, `/media`, `/import` | 🟡 MEDIUM |
| `api` | `/api/`, `/v1/`, `/graphql`, `/swagger` | 🟡 MEDIUM |
| `params` | `?id=`, `?redirect=`, `?url=`, `?file=` | 🔵 MEDIUM |
| `backup` | `.bak`, `.sql`, `.zip`, `.old` | 🟡 MEDIUM |
| `errors` | 403, 401, 405 responses | ⚪ INFO |
| `js` | `.js` files | ⚪ INFO |
| `json` | `.json` endpoints | ⚪ INFO |
| `php` | `.php` files | ⚪ INFO |
| `xml` | `.xml` files | ⚪ INFO |

---

## Configuration

Copy `easyrecon.yaml` to `~/.easyrecon.yaml` and customize:

```yaml
tools:
  amass:
    enabled: false        # Disable slow tools
  subfinder:
    timeout: 60           # Custom timeout
    extra_args: "-recursive"  # Extra flags

settings:
  output_dir: "~/results"
  threads: 50
  auto_install: true
```

Config priority: `--config flag` > `./easyrecon.yaml` > `~/.easyrecon.yaml` > defaults

---

## Tools Used

| Tool | Phase | Purpose |
|---|---|---|
| subfinder | Subdomain | Fast passive subdomain enum |
| amass | Subdomain | Deep passive subdomain enum |
| assetfinder | Subdomain | Lightweight subdomain finder |
| gau | URLs | Historical URLs (AlienVault + Wayback) |
| waybackurls | URLs | Wayback Machine URLs |
| katana | URLs | Active web crawler with JS support |
| httpx | Live | HTTP probing and fingerprinting |

---

## Legal

Only use easyrecon on targets you own or have **explicit written permission** to test.
Unauthorized scanning is illegal in most jurisdictions.

---

## Contributing

Pull requests welcome. Please open an issue first to discuss changes.

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Author

Made by [@unrealsrabon](https://github.com/unrealsrabon)  
Part of the [ai-will-replace-developers](https://github.com/ai-will-replace-developers) project
