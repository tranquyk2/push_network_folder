"""
Bảng màu giao diện và hàm sinh QSS stylesheet.
Phiên bản v2 — thiết kế hiện đại, premium, dễ đọc.
"""

THEMES = {
    "dark": {
        "bg":               "#0f1117",
        "bg_secondary":     "#161822",
        "card":             "#1c1e2e",
        "card_border":      "#2a2d42",
        "card_hover":       "#22253a",
        "text":             "#e4e6f0",
        "text_secondary":   "#8b8ea8",
        "text_muted":       "#5c5f78",
        "accent":           "#7c6cff",
        "accent_hover":     "#9182ff",
        "accent_pressed":   "#6a59e0",
        "accent_subtle":    "rgba(124,108,255,0.12)",
        "accent_text":      "#ffffff",
        "success":          "#34d399",
        "error":            "#f87171",
        "warning":          "#fbbf24",
        "drop_border":      "#363954",
        "drop_border_active": "#7c6cff",
        "drop_bg":          "#161822",
        "drop_bg_active":   "rgba(124,108,255,0.08)",
        "toolbar_bg":       "#1c1e2e",
        "toolbar_border":   "#2a2d42",
        "section_header":   "#14151f",
        "divider":          "#2a2d42",
        "badge_bg":         "rgba(124,108,255,0.15)",
        "badge_text":       "#a99aff",
        "scrollbar_bg":     "transparent",
        "scrollbar_handle": "#363954",
    },
    "light": {
        "bg":               "#f0f1f7",
        "bg_secondary":     "#ffffff",
        "card":             "#ffffff",
        "card_border":      "#e2e4ef",
        "card_hover":       "#f7f7fc",
        "text":             "#1a1b2e",
        "text_secondary":   "#64668a",
        "text_muted":       "#9a9cb8",
        "accent":           "#6c5ce7",
        "accent_hover":     "#7f70f0",
        "accent_pressed":   "#5a4bd6",
        "accent_subtle":    "rgba(108,92,231,0.08)",
        "accent_text":      "#ffffff",
        "success":          "#059669",
        "error":            "#dc2626",
        "warning":          "#d97706",
        "drop_border":      "#d0d2e2",
        "drop_border_active": "#6c5ce7",
        "drop_bg":          "#f7f8fc",
        "drop_bg_active":   "rgba(108,92,231,0.06)",
        "toolbar_bg":       "#ffffff",
        "toolbar_border":   "#e2e4ef",
        "section_header":   "#f7f8fc",
        "divider":          "#e8e9f2",
        "badge_bg":         "rgba(108,92,231,0.10)",
        "badge_text":       "#6c5ce7",
        "scrollbar_bg":     "transparent",
        "scrollbar_handle": "#d0d2e2",
    },
}


def build_stylesheet(t: dict) -> str:
    """Sinh QSS (stylesheet) từ bảng màu theme hiện tại."""
    return f"""
    /* ═══════ Base ═══════ */
    QWidget {{
        background: {t['bg']};
        color: {t['text']};
        font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif;
        font-size: 13px;
    }}

    /* ═══════ Header ═══════ */
    QLabel#headerTitle {{
        font-size: 22px;
        font-weight: 800;
        color: {t['text']};
        letter-spacing: -0.3px;
    }}
    QLabel#headerSubtitle {{
        font-size: 12px;
        color: {t['text_secondary']};
        font-weight: 400;
    }}

    /* ═══════ Cards ═══════ */
    QFrame#card {{
        background: {t['card']};
        border: 1px solid {t['card_border']};
        border-radius: 16px;
    }}

    /* ═══════ Section Header ═══════ */
    QFrame#sectionHeader {{
        background: {t['section_header']};
        border: none;
        border-top-left-radius: 16px;
        border-top-right-radius: 16px;
        border-bottom-left-radius: 0px;
        border-bottom-right-radius: 0px;
        padding: 0px;
    }}
    QLabel#sectionTitle {{
        font-size: 11px;
        font-weight: 700;
        color: {t['text_muted']};
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}

    /* ═══════ Divider ═══════ */
    QFrame#divider {{
        background: {t['divider']};
        border: none;
        max-height: 1px;
        min-height: 1px;
    }}

    /* ═══════ Buttons — General ═══════ */
    QPushButton {{
        background: {t['card']};
        color: {t['text']};
        border: 1px solid {t['card_border']};
        border-radius: 10px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 12px;
    }}
    QPushButton:hover {{
        border-color: {t['accent']};
        color: {t['accent']};
        background: {t['accent_subtle']};
    }}
    QPushButton:pressed {{
        background: {t['accent_pressed']};
        color: {t['accent_text']};
        border-color: {t['accent_pressed']};
    }}

    /* ═══════ Primary Button ═══════ */
    QPushButton#primaryBtn {{
        background: {t['accent']};
        color: {t['accent_text']};
        border: none;
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 10px;
    }}
    QPushButton#primaryBtn:hover {{
        background: {t['accent_hover']};
    }}
    QPushButton#primaryBtn:pressed {{
        background: {t['accent_pressed']};
    }}

    /* ═══════ Toolbar Button (small, compact) ═══════ */
    QPushButton#toolbarBtn {{
        background: transparent;
        color: {t['text_secondary']};
        border: 1px solid {t['card_border']};
        border-radius: 8px;
        padding: 5px 12px;
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton#toolbarBtn:hover {{
        background: {t['accent_subtle']};
        color: {t['accent']};
        border-color: {t['accent']};
    }}
    QPushButton#toolbarBtn:pressed {{
        background: {t['accent']};
        color: {t['accent_text']};
    }}

    /* ═══════ Destination Chips ═══════ */
    QPushButton#destBtn {{
        background: {t['bg_secondary']};
        border: 1px solid {t['card_border']};
        border-radius: 20px;
        padding: 7px 18px;
        font-weight: 500;
        font-size: 12px;
        color: {t['text_secondary']};
    }}
    QPushButton#destBtn:hover {{
        border-color: {t['accent']};
        color: {t['accent']};
        background: {t['accent_subtle']};
    }}
    QPushButton#destBtn:checked {{
        background: {t['accent']};
        color: {t['accent_text']};
        border: 1px solid {t['accent']};
        font-weight: 600;
    }}

    /* ═══════ Icon Button (theme toggle etc.) ═══════ */
    QPushButton#iconBtn {{
        border-radius: 18px;
        padding: 6px;
        font-size: 16px;
        background: transparent;
        border: none;
    }}
    QPushButton#iconBtn:hover {{
        background: {t['accent_subtle']};
    }}

    /* ═══════ Inputs ═══════ */
    QLineEdit {{
        background: {t['bg_secondary']};
        border: 1px solid {t['card_border']};
        border-radius: 10px;
        padding: 9px 12px;
        color: {t['text']};
        font-size: 13px;
    }}
    QLineEdit:focus {{
        border: 1.5px solid {t['accent']};
    }}

    /* ═══════ Drop Zone ═══════ */
    QLabel#dropZone {{
        border: 2px dashed {t['drop_border']};
        border-radius: 16px;
        background: {t['drop_bg']};
        color: {t['text_secondary']};
        font-size: 13px;
        padding: 28px;
    }}
    QLabel#dropZoneActive {{
        border: 2.5px dashed {t['drop_border_active']};
        border-radius: 16px;
        background: {t['drop_bg_active']};
        color: {t['accent']};
        font-size: 13px;
        padding: 28px;
    }}

    /* ═══════ Progress Bar ═══════ */
    QProgressBar {{
        background: {t['bg_secondary']};
        border: 1px solid {t['card_border']};
        border-radius: 8px;
        text-align: center;
        color: {t['text']};
        height: 22px;
        font-size: 11px;
        font-weight: 600;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {t['accent']}, stop:1 {t['accent_hover']});
        border-radius: 7px;
    }}

    /* ═══════ Tab Widget ═══════ */
    QTabWidget::pane {{
        border: 1px solid {t['card_border']};
        border-radius: 12px;
        background: {t['card']};
        top: 6px;
        padding: 4px;
    }}
    QTabBar {{
        background: transparent;
        alignment: left;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {t['text_muted']};
        padding: 9px 18px;
        margin-right: 6px;
        margin-bottom: 4px;
        border: 1px solid transparent;
        border-radius: 10px;
        font-weight: 500;
        font-size: 12px;
    }}
    QTabBar::tab:hover {{
        color: {t['text']};
        background: {t['accent_subtle']};
        border: 1px solid transparent;
        border-radius: 10px;
    }}
    QTabBar::tab:selected {{
        background: {t['card']};
        color: {t['accent']};
        font-weight: 700;
        border: 1px solid {t['card_border']};
        border-bottom: 1px solid {t['card']};
        border-radius: 10px;
    }}

    /* ═══════ List Widget ═══════ */
    QListWidget {{
        background: {t['card']};
        border: none;
        border-radius: 10px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 8px 10px;
        border-radius: 8px;
        font-size: 12px;
    }}
    QListWidget::item:hover {{
        background: {t['accent_subtle']};
    }}

    /* ═══════ Scrollbar ═══════ */
    QScrollBar:vertical {{
        background: {t['scrollbar_bg']};
        width: 7px;
        margin: 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t['scrollbar_handle']};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t['accent']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* ═══════ Connection Warning ═══════ */
    QLabel#connWarning {{
        background: {t['error']};
        color: white;
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 600;
        font-size: 12px;
    }}

    /* ═══════ Status Label ═══════ */
    QLabel#statusLabel {{
        color: {t['text_secondary']};
        font-size: 12px;
        font-weight: 400;
    }}

    /* ═══════ Active Dest Info ═══════ */
    QLabel#destInfo {{
        color: {t['text_secondary']};
        font-size: 11px;
        padding: 4px 0;
    }}

    /* ═══════ Badge / Pill ═══════ */
    QLabel#badge {{
        background: {t['badge_bg']};
        color: {t['badge_text']};
        border-radius: 10px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 600;
    }}

    /* ═══════ Tooltip ═══════ */
    QToolTip {{
        background: {t['card']};
        color: {t['text']};
        border: 1px solid {t['card_border']};
        border-radius: 6px;
        padding: 5px 8px;
        font-size: 11px;
    }}
    """
