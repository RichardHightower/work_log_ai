#!/bin/bash

# Ensure the script is executable:
# chmod +x launch_zsh_history_tail.sh

mkdir -p ~/.history/bin
mkdir -p ~/.history/lib
mkdir -p ~/.history/data
mkdir -p ~/.history/history

PYTHON_SCRIPT="$HOME/.history/bin/zsh_history_tail.py"



check_python() {
  PYTHON_CMD=$(command -v python3.11)
  if [ -z "$PYTHON_CMD" ]; then
    echo "Python 3.11 is not installed or not available in the current PATH."
    exit 1
  fi
}

create_virtualenv() {
  VENV_DIR="$HOME/.history/lib./zsh_history_tail_venv"
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
  fi
}

install_packages() {
  local packages=("rumps" "watchdog" "openai")
  for package in "${packages[@]}"; do
    $PIP_CMD show "$package" >/dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo "Installing $package library..."
      $PIP_CMD install "$package"
    fi
  done
}

main() {
  check_python

  create_virtualenv

  # Activate the virtual environment
  source "$VENV_DIR/bin/activate"

  # Use pip from the virtual environment
  PIP_CMD="$VENV_DIR/bin/pip"

  echo "Using Python command: $PYTHON_CMD"
  echo "Using pip command: $PIP_CMD"

  install_packages

  echo "Installed packages:"
  $PIP_CMD list

  if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: $PYTHON_SCRIPT does not exist"
    exit 1
  fi

  # Run the Python script
  "$VENV_DIR/bin/python3.11" "$PYTHON_SCRIPT"
}

main
