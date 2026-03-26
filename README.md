<div align="center">

```
███████╗ █████╗ ███████╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
█████╗  ███████║███████╗ ╚████╔╝ ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
██╔══╝  ██╔══██║╚════██║  ╚██╔╝  ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
███████╗██║  ██║███████║   ██║   ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝
```

![PHASES](https://img.shields.io/badge/PHASES-6-black?style=flat-square&labelColor=black&color=111)
![TOOLS](https://img.shields.io/badge/TOOLS-7-black?style=flat-square&labelColor=black&color=111)
![CATEGORIES](https://img.shields.io/badge/CATEGORIES-12-black?style=flat-square&labelColor=black&color=111)
![DIFFICULTY](https://img.shields.io/badge/DIFFICULTY-beginner%20friendly-black?style=flat-square&labelColor=222&color=222)
![TYPE](https://img.shields.io/badge/TYPE-recon%20automation-black?style=flat-square&labelColor=333&color=333)
![PLATFORM](https://img.shields.io/badge/PLATFORM-linux%20%2F%20mac-black?style=flat-square&labelColor=444&color=444)

**The recon pipeline that runs itself.**  
Subdomain enum → URL discovery → Live detection → Attack surface → Report — one command.

</div>

---

## What is easyrecon?

Recon is the most time-consuming phase of any bug bounty or pentest engagement. Most hunters still chain tools manually — run subfinder, merge with amass, feed into gau, probe with httpx, grep through thousands of URLs looking for `/admin` or `?redirect=`. That's hours of setup before you've touched a single vulnerability.

easyrecon eliminates that entirely.

It orchestrates **7 industry-standard tools** across **6 phases**, runs them in parallel, merges and deduplicates results, categorizes your entire attack surface into 12 priority buckets, and writes a full report — automatically.

```
$ easyrecon target.com
```

That's it.

---

## Pipeline

```
  target.com
      │
      ▼
  ┌───────────────────────────────────────────────────────────────┐
  │  01  SUBDOMAIN ENUMERATION                                    │
  │      subfinder  ·  amass  ·  assetfinder  →  parallel run    │
  │      output: all_subdomains.txt  (merged + deduped)          │
  └────────────────────────────┬──────────────────────────────────┘
                               │
  ┌────────────────────────────▼──────────────────────────────────┐
  │  02  URL DISCOVERY                                            │
  │      gau  ·  waybackurls  ·  katana  →  parallel run         │
  │      output: all_urls.txt  (merged + deduped)                │
  └────────────────────────────┬──────────────────────────────────┘
                               │
  ┌────────────────────────────▼──────────────────────────────────┐
  │  03  LIVE HOST DETECTION                                      │
  │      httpx  →  status codes  ·  fingerprinting               │
  │      output: live_subdomains.txt  ·  live_urls.txt           │
  └────────────────────────────┬──────────────────────────────────┘
                               │
  ┌────────────────────────────▼──────────────────────────────────┐
  │  04  ATTACK SURFACE CATEGORIZATION                           │
  │      12 buckets  →  sensitive  admin  api  login             │
  │                      upload  params  backup  js  …           │
  └────────────────────────────┬──────────────────────────────────┘
                               │
  ┌────────────────────────────▼──────────────────────────────────┐
  │  05  REPORT                                                   │
  │      report.md  ·  errors.log  →  ready to work from        │
  └───────────────────────────────────────────────────────────────┘
```

---

## Time Comparison

| Task | Manual approach | easyrecon |
|:---|:---:|:---:|
| Subdomain enum (3 tools) | ~30 min | ~5 min |
| URL discovery (3 tools) | ~45 min | ~8 min |
| Live host probing | ~20 min | ~3 min |
| Attack surface triage | ~30 min | instant |
| Report | ~20 min | instant |
| **Total** | **~2.5 hrs** | **~16 min** |

Tools run in parallel per phase. No waiting for one to finish before the next starts.

---

## Attack Surface Categories

easyrecon reads every URL and sorts it into priority buckets so you know exactly what to test first.

| Priority | Category | Catches |
|:---:|:---|:---|
| `HIGH` | `sensitive` | `.git` · `.env` · `/backup` · `/config` · `/actuator` |
| `HIGH` | `admin` | `/admin` · `/dashboard` · `/panel` · `/cp` |
| `HIGH` | `login` | `/login` · `/auth` · `/wp-admin` · `/sso` |
| `MED` | `upload` | `/upload` · `/file` · `/media` · `/import` |
| `MED` | `api` | `/api/` · `/v1/` · `/graphql` · `/swagger` |
| `MED` | `params` | `?id=` · `?redirect=` · `?url=` · `?file=` |
| `MED` | `backup` | `.bak` · `.sql` · `.zip` · `.old` |
| `INFO` | `js` | `.js` files |
| `INFO` | `json` | `.json` endpoints |
| `INFO` | `php` | `.php` files |
| `INFO` | `xml` | `.xml` files |
| `INFO` | `errors` | 403 · 401 · 405 responses |

---

## Tools

| Tool | Phase | What it does |
|:---|:---:|:---|
| `subfinder` | Subdomain | Fast passive subdomain enumeration |
| `amass` | Subdomain | Deep passive subdomain enumeration |
| `assetfinder` | Subdomain | Lightweight subdomain discovery |
| `gau` | URLs | Historical URLs via AlienVault + Wayback |
| `waybackurls` | URLs | Wayback Machine URL extraction |
| `katana` | URLs | Active crawler with JS rendering |
| `httpx` | Live | HTTP probing · status codes · fingerprinting |

All tools install automatically on first run via `go install`. Nothing manual.

---

## Installation

**Requirements:** Python 3.8+  ·  Go

```bash
git clone https://github.com/unrealsrabon/easyrecon
cd easyrecon
chmod +x install.sh
./install.sh
```

The install script checks dependencies, installs all 7 tools, installs Python packages, and optionally adds `easyrecon` to your PATH.

---

## Usage

```bash
easyrecon target.com                          # full pipeline

easyrecon target.com --phase subdomain        # single phase
easyrecon target.com --phase urls
easyrecon target.com --phase live
easyrecon target.com --phase categorize
easyrecon target.com --phase report

easyrecon target.com --timeout 60             # override timeouts
easyrecon target.com --output ~/results       # custom output dir
easyrecon target.com --config custom.yaml     # custom config
easyrecon target.com --no-install             # skip install check
```

---

## Output

```
results/
└── target.com_2026-03-26_04-20/
    ├── raw/
    │   ├── subfinder.txt
    │   ├── amass.txt
    │   ├── assetfinder.txt
    │   ├── gau.txt
    │   ├── waybackurls.txt
    │   └── katana.txt
    ├── processed/
    │   ├── all_subdomains.txt
    │   ├── live_subdomains.txt
    │   ├── all_urls.txt
    │   └── live_urls.txt
    ├── categorized/
    │   ├── sensitive.txt
    │   ├── admin.txt
    │   ├── api.txt
    │   ├── params.txt
    │   └── ...
    ├── report.md
    └── errors.log
```

---

## Configuration

```bash
cp easyrecon.yaml ~/.easyrecon.yaml
```

```yaml
tools:
  amass:
    enabled: false
  subfinder:
    timeout: 60
    extra_args: "-recursive"

settings:
  output_dir: "~/results"
  threads: 50
  auto_install: true
```

Priority order: `--config flag`  >  `./easyrecon.yaml`  >  `~/.easyrecon.yaml`  >  defaults

---

## Legal

Only use easyrecon on targets you own or have **explicit written permission** to test.  
Unauthorized scanning is illegal in most jurisdictions. You are solely responsible for your actions.

---

## Contributing

Pull requests are welcome. Open an issue first to discuss proposed changes.

---

## License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

Made by [@unrealsrabon](https://github.com/unrealsrabon)  
Part of the [ai-will-replace-developers](https://github.com/ai-will-replace-developers) project

</div>
