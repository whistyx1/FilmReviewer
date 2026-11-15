#!/bin/zsh

cd -- "$(dirname -- "$0")" || exit 1

if [[ ! -x .venv/bin/python ]]; then
    if command -v python3.12 >/dev/null 2>&1; then
        python3.12 -m venv .venv || exit 1
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m venv .venv || exit 1
    else
        echo "Python 3 is needed. Install Python 3.12, then open this file again."
        read -k 1 "?Press any key to close..."
        exit 1
    fi
fi

if ! .venv/bin/python -c 'import PyQt6.QtWidgets' >/dev/null 2>&1; then
    echo "Installing Film Reviewer dependencies..."
    .venv/bin/python -m pip install -r requirements.txt || {
        echo "Installation failed. Check your internet connection and try again."
        read -k 1 "?Press any key to close..."
        exit 1
    }
fi

.venv/bin/python main.py
