"""
easyrecon Tool Registry
Single source of truth for all external tools.
"""

from typing import Dict, Any

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "subfinder": {
        "cmd": "subfinder",
        "args": ["-d", "{target}", "-silent", "-all", "-recursive"],
        "install_cmd": "go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
        "phase": "subdomain",
        "enabled": True,
        "timeout": 120,
        "critical": False,
        "parse": "lines",
        "description": "Fast passive subdomain enumeration",
    },
    "amass": {
        "cmd": "amass",
        "args": ["enum", "-passive", "-d", "{target}", "-silent"],
        "install_cmd": "go install github.com/owasp-amass/amass/v4/...@master",
        "phase": "subdomain",
        "enabled": True,
        "timeout": 180,
        "critical": False,
        "parse": "lines",
        "description": "In-depth subdomain enumeration",
    },
    "assetfinder": {
        "cmd": "assetfinder",
        "args": ["--subs-only", "{target}"],
        "install_cmd": "go install github.com/tomnomnom/assetfinder@latest",
        "phase": "subdomain",
        "enabled": True,
        "timeout": 60,
        "critical": False,
        "parse": "lines",
        "description": "Lightweight subdomain finder",
    },
    "gau": {
        "cmd": "gau",
        "args": [
            "{target}",
            "--threads", "5",
            "--timeout", "60",
            "--blacklist", "png,jpg,gif,svg,ico,css,woff,ttf,eot,mp4,mp3,wav,woff2",
        ],
        "install_cmd": "go install github.com/lc/gau/v2/cmd/gau@latest",
        "phase": "urls",
        "enabled": True,
        "timeout": 120,
        "critical": False,
        "parse": "lines",
        "description": "Fetch known URLs from AlienVault and Wayback",
    },
    "waybackurls": {
        "cmd": "waybackurls",
        "args": ["{target}"],
        "install_cmd": "go install github.com/tomnomnom/waybackurls@latest",
        "phase": "urls",
        "enabled": True,
        "timeout": 90,
        "critical": False,
        "parse": "lines",
        "description": "Fetch URLs from Wayback Machine",
    },
    "katana": {
        "cmd": "katana",
        "args": [
            "-u", "{target}",
            "-silent",
            "-depth", "3",
            "-duc",
            "retry", "2",
            "-timeout", "30",
            "-no-color",
        ],
        "install_cmd": "go install github.com/projectdiscovery/katana/cmd/katana@latest",
        "phase": "urls",
        "enabled": True,
        "timeout": 180,
        "critical": False,
        "parse": "lines",
        "description": "Active web crawler with JS parsing",
    },
    "httpx": {
        "cmd": "httpx",
        "args": [
            "-l", "{input}",
            "-silent",
            "-status-code",
            "-title",
            "-server",
            "-tech-detect",
            "-timeout", "10",
            "-threads", "50",
        ],
        "install_cmd": "go install github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "phase": "live",
        "enabled": True,
        "timeout": 300,
        "critical": True,
        "parse": "lines",
        "description": "Fast HTTP probing and fingerprinting",
    },
}

PHASE_ORDER = ["subdomain", "urls", "live", "categorize", "report"]

PHASE_TOOLS = {
    "subdomain": ["subfinder", "amass", "assetfinder"],
    "urls": ["gau", "waybackurls", "katana"],
    "live": ["httpx"],
}

CATEGORY_PATTERNS = {
    "params": [
        "?id=", "?page=", "?url=", "?q=", "?search=", "?redirect=",
        "?next=", "?file=", "?path=", "?token=", "?key=", "?debug=",
        "?test=", "?ref=", "?return=", "?view=", "?type=", "?name=",
        "?user=", "?pass=", "?email=", "?data=", "?input=", "?output=",
    ],
    "admin": [
        "/admin", "/administrator", "/dashboard", "/panel", "/manage",
        "/cp", "/control", "/moderator", "/staff", "/backoffice",
        "/siteadmin", "/superuser", "/cms", "/management", "/backend",
    ],
    "api": [
        "/api/", "/v1/", "/v2/", "/v3/", "/v4/", "/graphql", "/swagger",
        "/openapi", "/rest/", "/endpoint", "/webhook", "/ws/", "/rpc",
        "/api-docs", "/swagger-ui", "/redoc", "/api/swagger",
    ],
    "sensitive": [
        "/.git", "/.env", "/.htaccess", "/.htpasswd", "/backup",
        "/config", "/secret", "/private", "/internal", "/debug",
        "/trace", "/phpinfo", "/server-status", "/server-info",
        "/actuator", "/metrics", "/health", "/info", "/.DS_Store",
        "/web.config", "/docker-compose", "/.svn", "/.hg",
        "/WEB-INF", "/.aws", "/.ssh", "/id_rsa", "/credentials",
    ],
    "login": [
        "/login", "/signin", "/sign-in", "/auth", "/authenticate",
        "/account", "/user/login", "/wp-login", "/wp-admin", "/portal",
        "/sso", "/oauth", "/saml", "/session", "/access",
    ],
    "upload": [
        "/upload", "/file", "/attachment", "/media", "/image",
        "/document", "/import", "/export", "/download", "/assets/upload",
        "/files/", "/uploads/", "/content/upload",
    ],
    "backup": [
        ".bak", ".old", ".backup", ".zip", ".tar", ".gz", ".sql",
        ".db", ".dump", ".copy", ".orig", ".swp", "~",
        ".tar.gz", ".tgz", ".rar", ".7z",
    ],
    "js": [".js"],
    "json": [".json"],
    "xml": [".xml"],
    "php": [".php"],
}

CATEGORY_PRIORITY = [
    "sensitive", "admin", "login", "upload", "api", "params",
    "backup", "php", "json", "xml", "js", "errors",
]
