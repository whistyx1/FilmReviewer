#!/bin/zsh

cd -- "$(dirname -- "$0")" || exit 1

if [[ ! -x .venv/bin/python ]]; then
    if command -v python3.12 >/dev/null 2>&1; then
        python3.12 -m venv .venv || exit 1
    else
        python3 -m venv .venv || exit 1
    fi
fi

.venv/bin/python -m pip install -r requirements.txt pyinstaller || exit 1
.venv/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir \
    --name FilmReviewer main.py || exit 1

echo "Mac app ready: dist/FilmReviewer.app"
echo "You can drag FilmReviewer.app to Applications or the Desktop."
