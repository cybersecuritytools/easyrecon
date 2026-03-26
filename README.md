<div align="center">
  <br />
  <img src="https://api.iconify.design/lucide/scan-line.svg?color=%230ea5e9" width="56" alt="radar" />
  <h1>E A S Y R E C O N</h1>
  <p><strong>The recon command you run before anything else.</strong></p>

  <p>
    <img src="https://img.shields.io/badge/version-1.0.0-0ea5e9?style=for-the-badge&labelColor=f8fafc&color=0ea5e9" alt="Version" />
    <img src="https://img.shields.io/badge/build-passing-10b981?style=for-the-badge&labelColor=f8fafc&color=10b981" alt="Build" />
    <img src="https://img.shields.io/badge/license-MIT-64748b?style=for-the-badge&labelColor=f8fafc&color=64748b" alt="License" />
  </p>


</div>


> **Stop wasting the first hour of every engagement setting up your tools.**  
> `easyrecon` strips away the friction. Run one command, get a perfectly categorized attack surface, and jump straight into hunting. 

<br />

## <img src="https://api.iconify.design/lucide/flame.svg?color=%23ef4444" width="28" align="top" /> The Crucial Question: Why *Must* You Use EasyRecon?

Most hunters waste hours running tools one by one, manually filtering out dead domains, and losing track of juicy endpoints in massive text files. **EasyRecon completely eliminates this bottleneck.** 

<br />

<table width="100%">
  <tr>
    <th width="50%" align="center" style="font-size: 1.2em; color: #ef4444;">❌ The Old Way (Manual)</th>
    <th width="50%" align="center" style="font-size: 1.2em; color: #10b981;">✅ The EasyRecon Way</th>
  </tr>
  <tr>
    <td valign="top">
      <ul>
        <li>Run `subfinder`, wait to finish</li>
        <li>Run `amass`, wait to finish</li>
        <li>Manually concatenate and `sort -u`</li>
        <li>Run `httpx` to find live hosts</li>
        <li>Run `gau` & `waybackurls`</li>
        <li>Get a 5GB text file of random URLs</li>
        <li>Spend 2 hours searching for `?id=` or `/admin`</li>
      </ul>
    </td>
    <td valign="top">
      <ul>
        <li>Run `easyrecon target.com`</li>
        <li>Go grab a cup of coffee ☕</li>
        <li>Return to a fully weaponized, neatly categorized workspace</li>
        <li>Instantly open the `high-priority-admin.txt` vault</li>
        <li><strong>Start hacking immediately</strong></li>
      </ul>
    </td>
  </tr>
</table>

<br />

## <img src="https://api.iconify.design/lucide/gem.svg?color=%238b5cf6" width="28" align="top" /> Every Benefit, Broken Down

<table width="100%">
  <tr>
    <td width="50%" valign="top">
      <h3><img src="https://api.iconify.design/lucide/timer.svg?color=%233b82f6" width="24" align="top"/> Unmatched Speed</h3>
      <p>By leveraging intelligent multi-threading and asynchronous orchestration, we run industry-standard tools in parallel. What used to take hours now takes minutes. You are always the first to start testing on new targets.</p>
    </td>
    <td width="50%" valign="top">
      <h3><img src="https://api.iconify.design/lucide/brain-circuit.svg?color=%2310b981" width="24" align="top"/> Smart Categorization</h3>
      <p>EasyRecon doesn't just dump raw data. It analyzes every single URL and categorizes them into actionable buckets: APIs, Admin Panels, Sensitive Exposures, and Injectable Parameters.</p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3><img src="https://api.iconify.design/lucide/shield-check.svg?color=%23f59e0b" width="24" align="top"/> Zero Blind Spots</h3>
      <p>By overlapping capabilities of 7+ premier security tools (Subfinder, Amass, Katana, GAU, HTTPX, etc.), we ensure that if an endpoint exists, EasyRecon will find it. Maximum coverage guaranteed.</p>
    </td>
    <td width="50%" valign="top">
      <h3><img src="https://api.iconify.design/lucide/sliders-horizontal.svg?color=%23ef4444" width="24" align="top"/> Highly Customizable</h3>
      <p>Want to add your own secret internal tool? EasyRecon's modular architecture lets you hook in custom scripts and binaries natively through a simple YAML configuration.</p>
    </td>
  </tr>
</table>

<br />

## <img src="https://api.iconify.design/lucide/network.svg?color=%233b82f6" width="28" align="top" /> The Orchestration Pipeline

Visualizing the automated magic:

```mermaid
flowchart TD
    classDef primary fill:#eff6ff,stroke:#3b82f6,stroke-width:2px,color:#1e3a8a,font-weight:bold
    classDef secondary fill:#f8fafc,stroke:#94a3b8,stroke-width:1px,stroke-dasharray: 5 5

    Input((Target Domain)):::primary --> Subdomains[Subdomain Enumeration]:::primary
    
    Subdomains --> |Amass, Subfinder, Assetfinder| LiveHosts[Live Host Verification]:::primary
    LiveHosts --> |HTTPX| Crawling[Deep Crawling & History]:::primary
    
    Crawling --> |Katana, GAU, Waybackurls| Analysis[Smart Analysis Engine]:::primary
    
    Analysis --> High[🚨 High Priority & Amin Targets]:::primary
    Analysis --> Med[🔌 APIs & Parameters]:::primary
    Analysis --> Low[ℹ️ Informational & Asset Files]:::primary
```

<br />

## <img src="https://api.iconify.design/lucide/folders.svg?color=%233b82f6" width="28" align="top" /> Contextual Outcomes

Once setup and scanning are finished, `easyrecon` delivers precisely what you need, neatly organized. Focus on what matters:

* 🚨 **`/results/target.com/admin_panels.txt`** — Direct links to login gates.
* 🔑 **`/results/target.com/secrets_and_config.txt`** — `.env`, `.git`, configurations.
* 🔌 **`/results/target.com/api_endpoints.txt`** — Undocumented GraphQL / REST endpoints.
* 💉 **`/results/target.com/injectable_parameters.txt`** — URLs ready for XSS, SQLi, and SSRF payloads.

<br />

## <img src="https://api.iconify.design/lucide/rocket.svg?color=%233b82f6" width="28" align="top" /> Quick Start

### 1. Requirements
* Python 3.8+
* Go *(needed to easily grab the underlying tools)*

### 2. Install
```bash
git clone https://github.com/unrealsrabon/easyrecon
cd easyrecon
chmod +x install.sh
./install.sh
```

### 3. Usage & Examples
```bash
# Kick off a full orchestration
easyrecon target.com

# Go aggressive with threads
easyrecon target.com --threads 100 --output ~/bugbounty_vault

# Run only specific modules 
easyrecon target.com --phase enum

# For help
easyrecon --help
```

<br />

## <img src="https://api.iconify.design/lucide/book-open-check.svg?color=%233b82f6" width="24" align="top" /> Legal & License

**Disclaimer:** Only point `easyrecon` at assets you own or possess explicit, written permission to test. Unauthorized scanning is actionable and illegal.

Released under the **MIT License**.  
Crafted by [@unrealsrabon](https://github.com/unrealsrabon) — part of the *ai-will-replace-developers* initiative.
