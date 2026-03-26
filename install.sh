#!/usr/bin/env bash
# easyrecon installer
# Installs all required Go tools and Python dependencies

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

BANNER="
  ___  ___  ____  _  _  ____  ___  _____  __ _
 | __|/ _ \/ ___|\ \/ /|  _ \| __||  ___||  \` |
 | _|| |_| \\___  \  / | |_) | _|  | |    | .  |
 |___|\___/ |___/ \\/  |____/|___| |_|    |_|\\_|

  installer v1.0.0 — by @unrealsrabon
"

GO_TOOLS=(
    "subfinder:go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
    "amass:go install github.com/owasp-amass/amass/v4/...@master"
    "assetfinder:go install github.com/tomnomnom/assetfinder@latest"
    "gau:go install github.com/lc/gau/v2/cmd/gau@latest"
    "waybackurls:go install github.com/tomnomnom/waybackurls@latest"
    "katana:go install github.com/projectdiscovery/katana/cmd/katana@latest"
    "httpx:go install github.com/projectdiscovery/httpx/cmd/httpx@latest"
)

print_banner() {
    echo -e "${RED}${BOLD}${BANNER}${NC}"
}

print_step() {
    echo -e "${CYAN}[*]${NC} $1"
}

print_ok() {
    echo -e "${GREEN}[✅]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[⚠️ ]${NC} $1"
}

print_fail() {
    echo -e "${RED}[❌]${NC} $1"
}

print_info() {
    echo -e "${DIM}    → $1${NC}"
}

check_python() {
    print_step "Checking Python version..."
    if ! command -v python3 &>/dev/null; then
        print_fail "Python3 not found"
        print_info "Install from: https://python.org/downloads/"
        exit 1
    fi

    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
    PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)

    if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]); then
        print_fail "Python 3.8+ required. Found: $PY_VERSION"
        print_info "Install from: https://python.org/downloads/"
        exit 1
    fi

    print_ok "Python $PY_VERSION found"
}

check_go() {
    print_step "Checking Go installation..."
    if ! command -v go &>/dev/null; then
        print_fail "Go not found — required for tool installation"
        print_info "Install Go from: https://go.dev/dl/"
        print_info "Then run ./install.sh again"
        exit 1
    fi

    GO_VERSION=$(go version | awk '{print $3}')
    print_ok "Go found: $GO_VERSION"
}

install_go_tools() {
    print_step "Installing Go-based security tools..."
    echo ""

    FAILED=()

    for entry in "${GO_TOOLS[@]}"; do
        TOOL_NAME="${entry%%:*}"
        INSTALL_CMD="${entry#*:}"

        if command -v "$TOOL_NAME" &>/dev/null; then
            print_ok "$TOOL_NAME — already installed, skipping"
            continue
        fi

        echo -ne "  ${CYAN}⬇️  Installing ${BOLD}${TOOL_NAME}${NC}${CYAN}...${NC}"

        if eval "$INSTALL_CMD" &>/dev/null 2>&1; then
            if command -v "$TOOL_NAME" &>/dev/null; then
                echo -e "\r  ${GREEN}✅ ${BOLD}${TOOL_NAME}${NC}${GREEN} installed successfully${NC}          "
            else
                echo -e "\r  ${YELLOW}⚠️  ${TOOL_NAME} — binary not in PATH after install${NC}   "
                FAILED+=("$TOOL_NAME")
            fi
        else
            echo -e "\r  ${RED}❌ ${TOOL_NAME} — install failed${NC}                    "
            print_info "Run manually: $INSTALL_CMD"
            FAILED+=("$TOOL_NAME")
        fi
    done

    echo ""

    if [ ${#FAILED[@]} -gt 0 ]; then
        print_warn "Some tools failed to install: ${FAILED[*]}"
        print_info "easyrecon will still work with available tools"
    else
        print_ok "All Go tools installed"
    fi
}

install_python_deps() {
    print_step "Installing Python dependencies..."

    if python3 -m pip install -r requirements.txt --quiet 2>&1; then
        print_ok "Python dependencies installed"
    else
        print_warn "pip install had issues — trying with --break-system-packages"
        python3 -m pip install -r requirements.txt --break-system-packages --quiet 2>&1 || {
            print_fail "Could not install Python dependencies"
            print_info "Run: pip3 install rich pyfiglet pyyaml"
        }
    fi
}

make_executable() {
    print_step "Making easyrecon executable..."
    chmod +x easyrecon.py
    print_ok "easyrecon.py is now executable"
}

install_to_path() {
    echo ""
    echo -e "${BOLD}Add easyrecon to PATH?${NC} ${DIM}(enables 'easyrecon target.com' from anywhere)${NC}"
    read -p "$(echo -e ${CYAN}[?]${NC}) Add to /usr/local/bin? [y/N] " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        INSTALL_PATH="/usr/local/bin/easyrecon"
        SCRIPT_PATH="$(pwd)/easyrecon.py"

        if sudo ln -sf "$SCRIPT_PATH" "$INSTALL_PATH" 2>/dev/null; then
            print_ok "Symlink created: $INSTALL_PATH → $SCRIPT_PATH"
            print_ok "You can now run: easyrecon target.com from anywhere"
        else
            print_warn "Could not create symlink (permission denied)"
            print_info "Try: sudo ln -sf $(pwd)/easyrecon.py /usr/local/bin/easyrecon"
            print_info "Or add to PATH manually in ~/.zshrc or ~/.bashrc:"
            print_info "  export PATH=\$PATH:$(pwd)"
        fi
    else
        echo ""
        print_info "To run easyrecon from this directory:"
        print_info "  python3 easyrecon.py target.com"
        echo ""
        print_info "To add to PATH manually, add to ~/.zshrc or ~/.bashrc:"
        print_info "  export PATH=\$PATH:$(pwd)"
    fi
}

check_go_path() {
    if [[ ":$PATH:" != *":$HOME/go/bin:"* ]]; then
        print_warn "~/go/bin is not in your PATH"
        print_info "Add to ~/.zshrc or ~/.bashrc:"
        print_info "  export PATH=\$PATH:\$HOME/go/bin"
        echo ""

        SHELL_RC=""
        if [ -f "$HOME/.zshrc" ]; then
            SHELL_RC="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_RC="$HOME/.bashrc"
        fi

        if [ -n "$SHELL_RC" ]; then
            read -p "$(echo -e ${CYAN}[?]${NC}) Auto-add to $SHELL_RC? [y/N] " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo 'export PATH=$PATH:$HOME/go/bin' >> "$SHELL_RC"
                print_ok "Added to $SHELL_RC"
                print_info "Run: source $SHELL_RC  (or restart terminal)"
            fi
        fi
    fi
}

print_final() {
    echo ""
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}${BOLD}  easyrecon is ready!${NC}"
    echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  ${BOLD}Usage:${NC}"
    echo -e "  ${CYAN}easyrecon target.com${NC}              ${DIM}# Full recon${NC}"
    echo -e "  ${CYAN}easyrecon target.com --phase subdomain${NC}  ${DIM}# Subdomain only${NC}"
    echo -e "  ${CYAN}easyrecon --help${NC}                  ${DIM}# All options${NC}"
    echo ""
    echo -e "  ${DIM}Happy hunting! 💀${NC}"
    echo ""
}

# ── Main ──────────────────────────────────────────

print_banner
check_python
check_go
echo ""
install_go_tools
install_python_deps
make_executable
check_go_path
install_to_path
print_final
