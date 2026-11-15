"""Colors and shared Qt stylesheet."""

BACKGROUND = "#101210"
SURFACE = "#1A1D19"
SURFACE_ALT = "#20241F"
BORDER = "#394036"
TEXT = "#E9EBE5"
MUTED = "#A5ADA1"
LIME = "#ADD166"
SAGE = "#83A979"

STYLESHEET = f"""
QWidget {{ color: {TEXT}; font-size: 14px; }}
QMainWindow, QScrollArea, QWidget#page, QScrollArea > QWidget > QWidget {{ background: {BACKGROUND}; }}
QDialog {{ background: {BACKGROUND}; }}
QLabel {{ background: transparent; }}
QLabel#brand {{ color: {TEXT}; font-family: Georgia; font-size: 18px; font-weight: 700; }}
QLabel#displayTitle {{ color: {TEXT}; font-family: Georgia; font-size: 31px; font-weight: 700; }}
QLabel#directorLead {{ color: {MUTED}; font-family: Georgia; font-size: 16px; font-style: italic; }}
QLabel#sectionTitle {{ font-family: Georgia; font-size: 18px; font-weight: 700; }}
QLabel#fieldCaption {{ color: {MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QLabel#hint {{ color: {MUTED}; font-size: 12px; }}
QLabel#attribution {{ color: #7E8878; font-size: 10px; }}
QFrame#scorePanel, QFrame#reviewPanel {{ background: transparent; border: 0; border-top: 1px solid {BORDER}; }}
QFrame#previewCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #222820, stop:1 #191D19);
    border: 1px solid #485342; border-radius: 10px;
}}
QFrame#previewDivider {{ background: #475043; border: 0; }}
QFrame#verticalDivider {{ background: {BORDER}; border: 0; }}
QLabel#poster {{
    background: #252B24; border: 1px solid #4D5942; border-radius: 7px;
    color: {MUTED}; font-size: 11px; font-weight: 700;
}}
QLineEdit, QTextEdit {{
    background: {SURFACE_ALT}; border: 1px solid #424A3D;
    border-radius: 8px; padding: 10px 12px;
    selection-background-color: {LIME}; selection-color: {BACKGROUND};
}}
QLineEdit:focus, QTextEdit:focus {{ border: 1px solid {LIME}; }}
QLineEdit#titleInput {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #293027, stop:0.4 #212620, stop:1 #1C211C);
    font-size: 17px; font-weight: 500; padding: 12px 15px;
}}
QLineEdit#directorInput {{
    background: transparent; border: 0; border-bottom: 1px solid #475044;
    border-radius: 0; padding: 2px 2px 4px; font-family: Georgia;
    font-size: 16px; font-style: italic;
}}
QLineEdit#directorInput:focus {{ border-bottom: 1px solid {LIME}; }}
QListWidget#suggestions {{ background: #252A22; border: 1px solid #4B5643; border-radius: 8px; padding: 4px; outline: none; }}
QListWidget#suggestions::item {{ padding: 8px; border-radius: 5px; }}
QListWidget#suggestions::item:selected, QListWidget#suggestions::item:hover {{ background: #394832; color: {TEXT}; }}
QListWidget#historyList {{ background: {SURFACE_ALT}; border: 1px solid #424A3D; border-radius: 8px; padding: 5px; outline: none; }}
QListWidget#historyList::item {{ padding: 10px 8px; border-radius: 5px; }}
QListWidget#historyList::item:selected {{ background: #394832; color: {TEXT}; }}
QListWidget#historyList::item:hover {{ background: #303D2A; }}
QLabel#metricName {{ font-size: 14px; font-weight: 600; }}
QLabel#metricValue {{
    font-size: 15px; font-weight: 700; border: 1px solid #65745A;
    border-radius: 7px; background: #242A22;
}}
QPushButton#helpButton {{ color: {MUTED}; background: #2C3329; border: 1px solid #59634F; border-radius: 10px; font-size: 12px; font-weight: 700; padding: 0; }}
QPushButton#helpButton:hover {{ color: {LIME}; border-color: {LIME}; }}
QLabel#mathLine {{ font-size: 16px; font-weight: 600; }}
QLabel#totalMath {{ color: {MUTED}; font-size: 13px; }}
QLabel#finalScore {{ color: {LIME}; font-family: Georgia; font-size: 39px; font-weight: 700; }}
QLabel#previewTitle {{ font-size: 20px; font-weight: 700; }}
QLabel#previewScore {{ color: {LIME}; font-size: 20px; font-weight: 700; }}
QLabel#previewNotes {{ color: {TEXT}; font-size: 13px; }}
QLabel#previewMetricName {{ color: #C4CCC0; font-size: 12px; }}
QLabel#previewStars {{ color: {LIME}; font-size: 12px; }}
QPushButton#quietButton {{ color: {LIME}; background: #252D21; border: 1px solid #46553D; border-radius: 8px; padding: 8px 13px; font-weight: 600; }}
QPushButton#quietButton:hover {{ background: #303D2A; }}
QPushButton#accentButton {{
    color: {BACKGROUND}; background: {LIME}; border: 1px solid {LIME};
    border-radius: 8px; padding: 9px 15px; font-weight: 700;
}}
QPushButton#accentButton:hover {{ background: #C2DF82; }}
QPushButton#accentButton:disabled {{ color: #87917C; background: #30392B; border-color: #495541; }}
QScrollBar:vertical {{ background: {BACKGROUND}; width: 8px; }}
QScrollBar::handle:vertical {{ background: #4B5945; border-radius: 4px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
