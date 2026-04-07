#!/usr/bin/env bash
# easyrecon installer
# Installs all required Go tools and Python dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PY="$VENV_DIR/bin/python"
LAUNCHER_DIR="$HOME/.local/bin"
LAUNCHER_PATH="$LAUNCHER_DIR/easyrecon"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

BANNER="
   ___  ____ ________  __________  _________  ____ 
  / _ \/ __ \`/ ___/ / / / ___/ _ \/ ___/ __ \/ __ \\
 /  __/ /_/ (__  ) /_/ / /  /  __/ /__/ /_/ / / / /
 \___/\__,_/____/\__, /_/   \___/\___/\____/_/ /_/ 
                /____/

  installer v1.7 — by @unrealsrabon
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

detect_shell_rc() {
    local shell_name
    shell_name="$(basename "${SHELL:-}")"

    case "$shell_name" in
        zsh)
            echo "$HOME/.zshrc"
            ;;
        bash)
            if [ -f "$HOME/.bashrc" ]; then
                echo "$HOME/.bashrc"
            else
                echo "$HOME/.bash_profile"
            fi
            ;;
        *)
            if [ -f "$HOME/.zshrc" ]; then
                echo "$HOME/.zshrc"
            elif [ -f "$HOME/.bashrc" ]; then
                echo "$HOME/.bashrc"
            else
                echo "$HOME/.profile"
            fi
            ;;
    esac
}

ensure_path_export() {
    local path_expr="$1"
    local rc_file="$2"

    [ -f "$rc_file" ] || touch "$rc_file"

    if ! grep -Fq "$path_expr" "$rc_file"; then
        echo "$path_expr" >> "$rc_file"
        print_ok "Added PATH entry in $rc_file"
        print_info "Run: source $rc_file  (or restart terminal)"
    fi
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

    # Ensure Go binaries are found in PATH during current script execution
    USER_GOPATH=$(go env GOPATH 2>/dev/null || echo "$HOME/go")
    export PATH="$PATH:$USER_GOPATH/bin"

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
    print_step "Creating virtual environment..."

    if [ ! -x "$VENV_PY" ]; then
        python3 -m venv "$VENV_DIR"
        print_ok "Virtual environment created at $VENV_DIR"
    else
        print_ok "Virtual environment already exists"
    fi

    print_step "Installing Python dependencies into .venv..."
    "$VENV_PY" -m pip install --upgrade pip --quiet

    if "$VENV_PY" -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet 2>&1; then
        print_ok "Python dependencies installed in .venv"
    else
        print_fail "Could not install Python dependencies in .venv"
        print_info "Run: $VENV_PY -m pip install -r requirements.txt"
        exit 1
    fi
}

make_executable() {
    print_step "Making easyrecon executable..."
    chmod +x "$SCRIPT_DIR/easyrecon.py"
    print_ok "easyrecon.py is now executable"
}

install_to_path() {
    print_step "Installing global launcher..."
    mkdir -p "$LAUNCHER_DIR"
    TMP_LAUNCHER="$LAUNCHER_PATH.tmp"

    cat > "$TMP_LAUNCHER" <<EOF
#!/usr/bin/env bash
"$VENV_PY" "$SCRIPT_DIR/easyrecon.py" "\$@"
EOF

    chmod +x "$TMP_LAUNCHER"
    mv -f "$TMP_LAUNCHER" "$LAUNCHER_PATH"
    print_ok "Launcher installed: $LAUNCHER_PATH"
    print_ok "easyrecon will run with project .venv from anywhere"
}

check_go_path() {
    local shell_rc
    shell_rc="$(detect_shell_rc)"
    local user_gopath
    user_gopath=$(go env GOPATH 2>/dev/null || echo "$HOME/go")

    if [[ ":$PATH:" != *":$user_gopath/bin:"* ]]; then
        print_warn "$user_gopath/bin is not in your PATH"
        print_info "Add to your shell rc file:"
        print_info "  export PATH=\$PATH:$user_gopath/bin"
        ensure_path_export "export PATH=\$PATH:$user_gopath/bin" "$shell_rc"
    fi

    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        print_warn "~/.local/bin is not in your PATH"
        print_info "Add to your shell rc file:"
        print_info "  export PATH=\$PATH:\$HOME/.local/bin"
        ensure_path_export 'export PATH=$PATH:$HOME/.local/bin' "$shell_rc"
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
cd "$SCRIPT_DIR"
install_go_tools
install_python_deps
make_executable
check_go_path
install_to_path
print_final
