#!/bin/bash
# environment_setup_helper.sh - Definitive Environment Setup Script
#
# This script is responsible for preparing a reliable and reproducible execution environment.
# It validates system dependencies, handles Homebrew quirks on older macOS versions,
# ensures 'uv' is installed and in the PATH, creates the project directory structure,
# and synchronizes the Python virtual environment with all required dependencies.

# --- Strict Mode ---
set -e
set -u
set -o pipefail

# --- Color Definitions for Logging ---
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# --- Logging Functions ---
log_info() { echo -e "${GREEN}[INFO]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $(date +'%Y-%m-%d %H:%M:%S') - $1"; }

# --- Core Functions ---

add_to_shell_profile() {
    local path_to_add="$1"
    local shell_profile=""
    local shell_name
    shell_name=$(basename "$SHELL")

    if [ "$shell_name" = "zsh" ]; then
        shell_profile="$HOME/.zshrc"
    elif [ "$shell_name" = "bash" ]; then
        shell_profile="$HOME/.bash_profile"
    else
        log_warning "Could not determine shell profile for shell: $shell_name. Please add '$path_to_add' to your PATH manually."
        return
    fi

    if [ -f "$shell_profile" ] && grep -q "export PATH=.*$path_to_add" "$shell_profile"; then
        log_info "'$path_to_add' is already in the PATH in '$shell_profile'."
    else
        log_info "Adding '$path_to_add' to PATH in '$shell_profile' for future sessions."
        # Append the export command to the profile file
        echo -e "\n# Added by document processing pipeline setup" >> "$shell_profile"
        echo "export PATH=\"$path_to_add:\$PATH\"" >> "$shell_profile"
        log_warning "Please run 'source $shell_profile' or open a new terminal for this change to be available everywhere."
    fi
}

pre_flight_checks() {
    log_info "Running pre-flight system checks..."
    local errors=0
    # 1. Check for Xcode Command Line Tools (essential for Homebrew builds)
    if ! xcode-select -p &> /dev/null; then
        log_error "Xcode Command Line Tools not found. This is required to build packages."
        log_error "Please run 'xcode-select --install' in your terminal and try again."
        errors=$((errors + 1))
    fi
    # 2. Check for Homebrew
    if ! command -v brew &> /dev/null; then
        log_error "Homebrew not found. Please install it from https://brew.sh/"
        errors=$((errors + 1))
    fi

    if [ $errors -gt 0 ]; then
        log_error "Halting setup due to critical missing system dependencies."
        exit 1
    fi
    log_info "Pre-flight system checks passed."
}

install_brew_dependency() {
    local package="$1"
    log_info "Checking for Homebrew package: '$package'..."
    if brew list "$package" &> /dev/null; then
        log_info "'$package' is already installed."
    else
        log_info "'$package' not found. Attempting installation..."
        if brew install "$package"; then
            log_info "Successfully installed '$package'."
        else
            log_warning "Standard 'brew install $package' failed. This is common on older macOS versions."
            log_warning "Attempting to force installation by building from source. This may take a while..."
            if brew install --build-from-source "$package"; then
                log_info "Successfully installed '$package' by building from source."
            else
                log_error "Failed to install '$package' even when building from source."
                log_error "Please try to resolve the Homebrew issue manually and rerun the script."
                exit 1
            fi
        fi
    fi
}

ensure_uv_installed() {
    log_info "Checking for 'uv' installer..."
    if command -v uv &> /dev/null; then
        log_info "'uv' is already installed."
    else
        log_info "'uv' not found. Installing now via official script..."
        if curl -LsSf https://astral.sh/uv/install.sh | sh; then
            local cargo_bin_path="$HOME/.cargo/bin"
            # Add uv to the current session's PATH
            export PATH="$cargo_bin_path:$PATH"
            log_info "'uv' has been installed to '$cargo_bin_path'."
            # Make the PATH change permanent
            add_to_shell_profile "$cargo_bin_path"
        else
            log_error "Failed to install 'uv'. Please check your network or try installing manually."
            exit 1
        fi
    fi
}

create_project_structure() {
    log_info "Creating project directory structure..."
    directories=(
        "pipeline_logs"
        "preprocessed_markdown"
        "document_assets"
        "final_markdown"
        "markitdown_output"
        "test_data"
    )
    for dir in "${directories[@]}"; do
        if [ -d "$dir" ]; then
            log_info "Directory '$dir' already exists. Skipping."
        else
            mkdir -p "$dir"
            log_info "Created directory: '$dir'"
        fi
    done
    log_info "Directory structure is in place."
}

setup_python_environment() {
    local venv_dir=".venv"
    local base_reqs="requirements.txt"
    local dev_reqs="requirements-dev.txt"

    log_info "Setting up Python virtual environment..."
    if [ ! -d "$venv_dir" ]; then
        log_info "Creating Python virtual environment at './${venv_dir}'..."
        uv venv "$venv_dir" -p python3
        log_info "Virtual environment created."
    else
        log_info "Using existing '${venv_dir}' directory."
    fi

    source "${venv_dir}/bin/activate"

    # Prioritize dev requirements if they exist for a full setup
    local requirements_to_install="$base_reqs"
    if [ -f "$dev_reqs" ]; then
        log_info "Found '$dev_reqs'. Installing full development and testing environment."
        requirements_to_install="$dev_reqs"
    elif [ ! -f "$base_reqs" ]; then
        log_error "'$base_reqs' not found. Cannot install dependencies."
        exit 1
    fi

    log_info "Synchronizing Python environment with '${requirements_to_install}'..."
    if uv pip sync "$requirements_to_install"; then
        log_info "Python environment is synchronized and ready."
    else
        log_error "Dependency synchronization failed. Please check the 'uv' output above."
        exit 1
    fi
}

# --- Main Execution Logic ---
main() {
    echo -e "${BLUE}--- Initializing Project Environment Setup ---${NC}"
    
    pre_flight_checks
    
    log_info "Installing required system dependencies via Homebrew..."
    install_brew_dependency "tesseract"
    install_brew_dependency "poppler"
    install_brew_dependency "coreutils" # For gtimeout, improves master script reliability
    
    ensure_uv_installed
    create_project_structure
    setup_python_environment
    
    echo -e "${GREEN}--- Environment Setup Complete ---${NC}"
    log_info "The project environment is now fully configured."
    log_info "You can now run the pipeline with './run_pipeline.sh' or the test suite with 'pytest'."
}

# Run the main function
main
