import _snowflake
import json
import streamlit as st
import pandas as pd
import altair as alt
import calendar
import time
import hashlib
import re
import yaml
import logging
import os
from io import BytesIO
from difflib import SequenceMatcher
from snowflake.snowpark.context import get_active_session
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import uuid
import html




# ████████████████████████████████████████████████████████████████████████████
# ██                                                                        ██
# ██   UI CONFIGURATION — EDIT THIS SECTION TO CHANGE DESIGN & BEHAVIOUR   ██
# ██   All colours, sizes, chat settings, and Genie tuning live here.      ██
# ██   Do NOT hard-code values elsewhere in the file.                       ██
# ██                                                                        ██
# ████████████████████████████████████████████████████████████████████████████

# ── BRAND COLOURS ─────────────────────────────────────────────────────────────
UI_BRAND            = "#1E40AF"      # Primary blue (nav, active buttons, logo)
UI_BRAND_HOVER      = "#1D4ED8"      # Hover / pressed state
UI_BRAND_LIGHT      = "#DBEAFE"      # Light tint for backgrounds
UI_ACCENT           = "#5046e5"      # Genie / AI purple accent
UI_ACCENT_LIGHT     = "#e8e4f7"      # Light lavender (selected tile BG)

# ── SEMANTIC COLOURS ──────────────────────────────────────────────────────────
UI_SUCCESS          = "#059669"
UI_SUCCESS_BG       = "#D1FAE5"
UI_SUCCESS_BORDER   = "#A7F3D0"
UI_DANGER           = "#DC2626"
UI_DANGER_BG        = "#FEE2E2"
UI_WARNING          = "#D97706"
UI_WARNING_BG       = "#FEF3C7"
UI_INFO_BG          = "#e0f2fe"
UI_INFO_BORDER      = "#bae6fd"

# ── NEUTRAL COLOURS ───────────────────────────────────────────────────────────
UI_BG               = "#F8FAFC"      # App background
UI_PANEL            = "#FFFFFF"      # Card / container surface
UI_TEXT             = "#0F172A"      # Primary text
UI_TEXT_SUBTLE      = "#475569"      # Secondary text
UI_TEXT_MUTED       = "#94A3B8"      # Placeholder / disabled
UI_DIVIDER          = "#E5E7EB"      # Borders / separators

# ── KPI CARD GRADIENTS ────────────────────────────────────────────────────────
UI_KPI_GREEN   = ("#D1FAE5", "#A7F3D0")
UI_KPI_PURPLE  = ("#EDE9FE", "#DDD6FE")
UI_KPI_CYAN    = ("#CFFAFE", "#A5F3FC")
UI_KPI_BLUE    = ("#DBEAFE", "#BFDBFE")
UI_KPI_YELLOW  = ("#FEF3C7", "#FDE68A")
UI_KPI_LIME    = ("#ECFCCB", "#D9F99D")

# ── CHAT BUBBLES ──────────────────────────────────────────────────────────────
UI_USER_BUBBLE_BG    = "#1E40AF"     # User message bubble background
UI_USER_BUBBLE_TEXT  = "#FFFFFF"
UI_AI_BUBBLE_BG      = "#F1F5F9"    # AI message bubble background
UI_AI_BUBBLE_TEXT    = "#0F172A"
UI_CACHE_BADGE_BG    = "#EFF6FF"
UI_CACHE_BADGE_TEXT  = "#1D4ED8"
UI_CACHE_BADGE_BORDER= "#BFDBFE"

# ── LAYOUT & TYPOGRAPHY ───────────────────────────────────────────────────────
UI_MAX_WIDTH        = "1400px"
UI_RADIUS           = "14px"
UI_RADIUS_SM        = "12px"
UI_SHADOW_1         = "0 10px 30px rgba(2,8,23,.06)"
UI_SHADOW_2         = "0 2px 10px rgba(2,8,23,.06)"
UI_SHADOW_CARD      = "0 2px 8px rgba(0,0,0,.04), 0 1px 2px rgba(0,0,0,.06)"
UI_FONT_FAMILY      = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto"
UI_KPI_LABEL_SIZE   = "0.70rem"
UI_KPI_VALUE_SIZE   = "1.75rem"
UI_TAB_FONT_SIZE    = "0.9rem"
UI_TAB_FONT_WEIGHT  = "600"
UI_CHAT_FONT_SIZE   = "14px"
UI_CHAT_BUBBLE_MAX  = "76%"
UI_LOGO_HEIGHT      = "120px"

# ── CHAT WINDOW ───────────────────────────────────────────────────────────────
UI_CHAT_SCROLL_HEIGHT = 520          # px — increase for a taller chat window

# ── THEME BG PICKER ───────────────────────────────────────────────────────────
UI_THEME_DEFAULT_BG  = "#FBF9F4"
UI_THEME_BTN_COLOR   = "#1E40AF"
UI_THEME_BTN_SIZE    = "44px"
UI_THEME_BOTTOM      = "18px"
UI_THEME_RIGHT       = "18px"

# ── GENIE / AI ASSISTANT BEHAVIOUR ───────────────────────────────────────────
GENIE_CACHE_MAX_SIZE        = 200    # Max entries in in-memory LRU cache
GENIE_CACHE_TTL_SECONDS     = 3600   # Cache TTL (1 hour). Increase to cache longer.
GENIE_SIMILARITY_THRESHOLD  = 0.60   # 0.0–1.0. Lower = more aggressive cache hits.
GENIE_SHORT_TERM_MAX_MSGS   = 40     # Max messages kept in session (scroll window)
GENIE_MAX_CONV_PAIRS        = 4      # Prior turn pairs sent to Cortex for follow-ups
GENIE_MEMORY_REBUILD_EVERY  = 5      # Rebuild long-term memory every N new questions
GENIE_MEMORY_MAX_FACTS      = 6      # Max persona facts to store per user
GENIE_SESSION_RESTORE_DAYS  = 7      # Show sessions from last N days in Past Sessions
GENIE_MAX_TURNS_LOADED      = 40     # Max turns to load when resuming a session
GENIE_PRESCRIPTIVE_MODEL    = "llama3-8b"  # Cortex model for AI recommendations

# ████████████████████████████████████████████████████████████████████████████
# ██   END OF UI CONFIGURATION                                              ██
# ████████████████████████████████████████████████████████████████████████████


def _build_all_css() -> str:
    """Generate full CSS from UI config constants above. Called once at startup."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {{
  --bg:{UI_BG}; --panel:{UI_PANEL}; --text:{UI_TEXT};
  --text-subtle:{UI_TEXT_SUBTLE}; --text-muted:{UI_TEXT_MUTED};
  --brand:{UI_BRAND}; --brand-hover:{UI_BRAND_HOVER}; --brand-light:{UI_BRAND_LIGHT};
  --accent:{UI_ACCENT}; --accent-light:{UI_ACCENT_LIGHT};
  --success:{UI_SUCCESS}; --danger:{UI_DANGER}; --warning:{UI_WARNING};
  --divider:{UI_DIVIDER}; --radius:{UI_RADIUS}; --radius-sm:{UI_RADIUS_SM};
  --shadow-1:{UI_SHADOW_1}; --shadow-2:{UI_SHADOW_2}; --shadow-card:{UI_SHADOW_CARD};
}}
* {{ font-family: {UI_FONT_FAMILY}; }}
html,body,[class^="css"]{{ background:var(--bg); color:var(--text); }}
.main {{ padding:0; background:var(--bg); }}
.block-container {{ padding-top:1.5rem!important; padding-left:2rem!important; padding-right:2rem!important; max-width:{UI_MAX_WIDTH}; margin:0 auto; }}
.stApp>header+div {{ padding-top:0!important; }}
.stMainBlockContainer {{ padding-top:1rem!important; }}
#MainMenu {{ visibility:hidden; }}
footer {{ visibility:hidden; }}
header {{ visibility:hidden; }}
section[data-testid="stSidebar"] {{ display:none; }}
.yash-header-logo {{ height:{UI_LOGO_HEIGHT}!important; max-height:{UI_LOGO_HEIGHT}!important; width:auto!important; object-fit:contain!important; }}
[data-testid="column"]:has(>div>div>div[style*="OrderLens"]),
[data-testid="column"]:has(>div>div>div[style*="yash-header-logo"]) {{ display:flex!important; align-items:center!important; }}
.stHorizontalBlock:first-of-type {{ align-items:center!important; }}
.stHorizontalBlock:first-of-type .stButton>button {{ white-space:nowrap!important; height:42px!important; min-height:42px!important; line-height:42px!important; padding-top:0!important; padding-bottom:0!important; }}
.kpi-row {{ display:grid; grid-template-columns:repeat(6,1fr); gap:16px; margin-bottom:30px; }}
.kpi-card {{ border-radius:16px; padding:20px; position:relative; }}
.kpi-card-green  {{ background:linear-gradient(135deg,{UI_KPI_GREEN[0]}  0%,{UI_KPI_GREEN[1]}  100%); }}
.kpi-card-purple {{ background:linear-gradient(135deg,{UI_KPI_PURPLE[0]} 0%,{UI_KPI_PURPLE[1]} 100%); }}
.kpi-card-cyan   {{ background:linear-gradient(135deg,{UI_KPI_CYAN[0]}   0%,{UI_KPI_CYAN[1]}   100%); }}
.kpi-card-blue   {{ background:linear-gradient(135deg,{UI_KPI_BLUE[0]}   0%,{UI_KPI_BLUE[1]}   100%); }}
.kpi-card-yellow {{ background:linear-gradient(135deg,{UI_KPI_YELLOW[0]} 0%,{UI_KPI_YELLOW[1]} 100%); }}
.kpi-card-lime   {{ background:linear-gradient(135deg,{UI_KPI_LIME[0]}   0%,{UI_KPI_LIME[1]}   100%); }}
.kpi-label {{ font-size:{UI_KPI_LABEL_SIZE}; font-weight:600; color:#374151; text-transform:uppercase; letter-spacing:.5px; margin-bottom:8px; }}
.kpi-value {{ font-size:{UI_KPI_VALUE_SIZE}; font-weight:800; color:#1F2937; margin-bottom:8px; }}
.kpi-change {{ font-size:0.8rem; display:flex; align-items:center; gap:4px; }}
.kpi-change.positive {{ color:{UI_SUCCESS}; }}
.kpi-change.negative {{ color:{UI_DANGER}; }}
.kpi-change.neutral  {{ color:{UI_TEXT}; }}
.nav-tab {{ padding:10px 20px; border-radius:8px; font-weight:{UI_TAB_FONT_WEIGHT}; font-size:{UI_TAB_FONT_SIZE}; cursor:pointer; transition:all .2s; color:#4B5563; background:transparent; border:none; }}
.nav-tab:hover {{ background:#F3F4F6; }}
.nav-tab.active {{ background:{UI_BRAND}; color:white; }}
.dashboard-tabs {{ background:transparent; padding:8px 0; display:flex; gap:4px; width:100%; }}
.dashboard-tabs .stButton {{ flex:1; }}
.dashboard-tabs .stButton>button {{ background:transparent; color:{UI_BRAND}; border:none; border-radius:6px; padding:12px 18px; font-size:{UI_TAB_FONT_SIZE}; font-weight:{UI_TAB_FONT_WEIGHT}; width:100%; transition:all .2s; }}
.dashboard-tabs .stButton>button:hover {{ background:rgba(37,99,235,.1); }}
.dashboard-tabs .stButton>button[kind="primary"] {{ background:{UI_BRAND}; color:white; border:none; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ background:var(--panel); border-radius:{UI_RADIUS_SM}; padding:20px 24px 16px 24px; box-shadow:var(--shadow-card); border:1px solid #F3F4F6; margin-bottom:16px; height:100%; }}
.chart-title {{ font-size:1.1rem; font-weight:700; color:#111827; margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid #F3F4F6; }}
[data-testid="stTabs"] {{ width:100%; }}
[data-testid="stTabs"]>div>div {{ background:#e0efff; padding:8px; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,.1); }}
[data-testid="stTabs"] button[aria-selected="true"]  {{ background:{UI_BRAND}!important; color:white!important; border-radius:6px; font-weight:600; }}
[data-testid="stTabs"] button[aria-selected="false"] {{ background:transparent!important; color:{UI_BRAND}!important; border-radius:6px; font-weight:600; }}
.stButton>button {{ border-radius:8px; font-weight:600; transition:all .2s; }}
.theme-anchor {{ position:fixed; bottom:{UI_THEME_BOTTOM}; right:{UI_THEME_RIGHT}; z-index:1000000; display:flex; align-items:center; justify-content:center; width:{UI_THEME_BTN_SIZE}; height:{UI_THEME_BTN_SIZE}; border-radius:50%; background-color:{UI_THEME_BTN_COLOR}; border:none; box-shadow:0 4px 12px rgba(15,23,42,.2); font-size:11px; font-weight:700; color:#fff; cursor:pointer; letter-spacing:.5px; }}
.theme-anchor:hover {{ transform:scale(1.1); box-shadow:0 6px 16px rgba(15,23,42,.3); }}
.theme-anchor .theme-label-text {{ pointer-events:none; }}
div[data-testid="stColorPicker"] {{ position:fixed!important; bottom:{UI_THEME_BOTTOM}!important; right:{UI_THEME_RIGHT}!important; width:{UI_THEME_BTN_SIZE}!important; height:{UI_THEME_BTN_SIZE}!important; z-index:1000001!important; opacity:0!important; }}
div[data-testid="stColorPicker"] * {{ width:100%!important; height:100%!important; }}
div[data-testid="stColorPicker"] label {{ display:none!important; }}
form:has(.genie-tile-card) {{ margin:0;padding:0;border:none!important;box-shadow:none!important;background:transparent; }}
form:has(.genie-tile-card) .genie-tile-card {{ border-bottom-left-radius:0!important;border-bottom-right-radius:0!important;border-bottom:0!important; }}
form:has(.genie-tile-card) [data-testid="stFormSubmitButton"] {{ margin:0!important;padding:0!important; }}
form:has(.genie-tile-card) [data-testid="stFormSubmitButton"]>button {{ width:100%!important;border-radius:0 0 14px 14px!important;border:1.5px solid {UI_DIVIDER}!important;border-top:0!important;background:{UI_ACCENT}!important;color:#fff!important;font-weight:800!important;font-size:14px!important;padding:10px 12px!important;cursor:pointer!important; }}
form:has(.genie-tile-card) input[type="checkbox"],form:has(.genie-tile-card) [role="checkbox"],form:has(.genie-tile-card) .stCheckbox,form:has(.genie-tile-card) [data-testid="stCheckbox"],form:has(.genie-tile-card) label {{ display:none!important;visibility:hidden!important; }}
#genie-faqs .stButton>button {{ justify-content:flex-start;text-align:left;padding-left:28px;white-space:normal;position:relative; }}
#genie-faqs .stButton>button::before {{ content:"•";position:absolute;left:12px;top:50%;transform:translateY(-50%); }}
.g-user {{ display:flex;justify-content:flex-end;margin:6px 0; }}
.g-user-inner {{ max-width:{UI_CHAT_BUBBLE_MAX};background:{UI_USER_BUBBLE_BG};color:{UI_USER_BUBBLE_TEXT};padding:10px 14px;border-radius:16px 16px 4px 16px;font-size:{UI_CHAT_FONT_SIZE};line-height:1.5; }}
.g-user-lbl {{ font-size:11px;font-weight:700;opacity:.8;margin-bottom:3px; }}
.g-ai {{ display:flex;justify-content:flex-start;margin:6px 0; }}
.g-ai-inner {{ max-width:{UI_CHAT_BUBBLE_MAX};background:{UI_AI_BUBBLE_BG};color:{UI_AI_BUBBLE_TEXT};padding:10px 14px;border-radius:16px 16px 16px 4px;font-size:{UI_CHAT_FONT_SIZE};line-height:1.5; }}
.g-ai-lbl {{ font-size:11px;font-weight:700;color:#64748b;margin-bottom:3px; }}
.cache-badge {{ display:inline-flex;align-items:center;gap:4px;background:{UI_CACHE_BADGE_BG};color:{UI_CACHE_BADGE_TEXT};border:1px solid {UI_CACHE_BADGE_BORDER};border-radius:999px;font-size:11px;font-weight:700;padding:2px 9px;margin-bottom:4px; }}
.typing-indicator {{ display:flex;gap:5px;align-items:center;padding:10px 14px;background:{UI_AI_BUBBLE_BG};border-radius:16px 16px 16px 4px;width:fit-content; }}
.typing-dot {{ width:7px;height:7px;background:#94a3b8;border-radius:50%;animation:typingBounce 1.2s infinite; }}
.typing-dot:nth-child(2) {{ animation-delay:.2s; }}
.typing-dot:nth-child(3) {{ animation-delay:.4s; }}
@keyframes typingBounce {{ 0%,60%,100% {{ transform:translateY(0); }} 30% {{ transform:translateY(-6px); }} }}
.chat-scroll {{ height:{UI_CHAT_SCROLL_HEIGHT}px;overflow-y:auto;padding:12px 8px;scroll-behavior:smooth;border:1px solid {UI_DIVIDER};border-radius:{UI_RADIUS_SM};background:var(--panel);margin-bottom:12px; }}
.resume-banner {{ background:{UI_BRAND_LIGHT};border:1.5px solid #bfdbfe;border-radius:{UI_RADIUS};padding:18px 20px 10px;margin:16px 0 12px; }}
.prescriptive-content,.prescriptive-content * {{ font-family:inherit!important;font-size:{UI_CHAT_FONT_SIZE}!important;line-height:1.6!important;color:{UI_TEXT}!important; }}
.prescriptive-content strong,.prescriptive-content b {{ font-weight:700!important;color:{UI_TEXT}!important; }}
[data-testid="stExpander"] div.stButton>button {{ border-radius:8px!important;padding:.4rem .8rem!important;text-align:left!important;justify-content:flex-start!important;white-space:normal!important;word-break:break-word!important;height:auto!important;min-height:36px!important;line-height:1.4!important;font-size:13px!important; }}
[data-testid="stHorizontalBlock"]:has(.genie-left-col-top) [data-testid="column"] {{ align-items:flex-start!important;align-self:flex-start!important; }}
.stHorizontalBlock {{ gap:16px!important;align-items:stretch!important; }}
[data-testid="stVegaLiteChart"] {{ width:100%!important; }}
.insight-content {{ background:white;border-radius:{UI_RADIUS_SM};padding:20px;margin-top:15px;border:1px solid {UI_DIVIDER}; }}
.insight-item {{ padding:12px 0;border-bottom:1px solid #F3F4F6; }}
.insight-item:last-child {{ border-bottom:none; }}
.memory-fact {{ background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:7px 10px;margin-bottom:5px;font-size:13px;color:#14532d; }}
</style>
"""


def _build_autoscroll_js() -> str:
    return """<script>
(function(){
  function sc(){
    var els=document.querySelectorAll('.chat-scroll');
    els.forEach(function(e){e.scrollTop=e.scrollHeight;});
    var c=document.getElementById('genie-chat-messages');
    if(c){c.scrollTop=c.scrollHeight;}
  }
  sc(); setTimeout(sc,300); setTimeout(sc,700);
})();
</script>"""

# Get Snowflake session
session = get_active_session()

# Database configuration
DATABASE      = "SALES_OPS_PLANNING_DEV"
SCHEMA        = "INFORMATION_MART"
RAW_SCHEMA    = "RAW_VAULT"                       # New RAW schema for fulfillment source tables
STAGE         = "CORTEX_STAGE"
FILE          = "model.yml"
FULLPATH      = f"{DATABASE}.{SCHEMA}.{STAGE}"


# ══════════════════════════════════════════════════════════════════════════════
# YAML AUTO-UPDATE ENGINE
# Runs once per Genie session. Reads model.yml from the Snowflake stage,
# discovers all VW_* views in INFORMATION_MART, adds any missing ones with
# auto-classified columns, then pushes the updated YAML back to the stage.
# No manual YAML maintenance needed when new views are added to the DB.
# ══════════════════════════════════════════════════════════════════════════════

def _yaml_get_views(sf_session) -> list:
    try:
        rows = sf_session.sql(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
            f"WHERE TABLE_SCHEMA = '{SCHEMA}' AND TABLE_NAME LIKE 'VW_%' "
            "ORDER BY TABLE_NAME"
        ).collect()
        return [r[0] for r in rows]
    except Exception as exc:
        return []


def _yaml_get_columns(sf_session, view_name: str) -> list:
    try:
        rows = sf_session.sql(
            f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_SCHEMA = '{SCHEMA}' AND TABLE_NAME = '{view_name}' "
            f"ORDER BY ORDINAL_POSITION"
        ).collect()
        return [{"name": r[0], "data_type": r[1]} for r in rows]
    except Exception:
        return []


def _yaml_build_table_block(view_name: str, cols: list) -> dict:
    _FACT_SUFFIXES = ("_PCT", "_PERCENT", "_DAYS", "_HOURS", "_AMOUNT",
                      "_RATE", "_COUNT", "_TOTAL", "_MARGIN", "_QTY", "_QUANTITY")
    _TIME_COLS = {"PERIOD_YEAR", "PERIOD_MONTH", "PERIOD_WEEK", "EFFECTIVE_DATE"}
    dimensions, facts = [], []
    for col in cols:
        n = col["name"].upper()
        if any(n.endswith(s) for s in _FACT_SUFFIXES):
            facts.append({"name": col["name"],
                          "description": f"{col['name']} metric from {view_name}",
                          "type": "NUMERIC"})
        elif n in _TIME_COLS:
            dimensions.append({"name": col["name"],
                               "description": f"Time dimension {col['name']}",
                               "type": "TIME"})
        else:
            dimensions.append({"name": col["name"],
                               "description": f"{col['name']} attribute from {view_name}",
                               "type": "STRING"})
    return {
        "name": view_name,
        "table": f"{DATABASE}.{SCHEMA}.{view_name}",
        "description": f"Auto-generated definition for {view_name}",
        "dimensions": dimensions[:15],
        "facts": facts[:10],
    }


def _yaml_load_from_stage(sf_session) -> str:
    stage_path = f"@{FULLPATH}/{FILE}"
    tmp_dir = "/tmp/orderlens_yaml"
    try:
        import os as _os
        _os.makedirs(tmp_dir, exist_ok=True)
        sf_session.sql(f"GET {stage_path} file://{tmp_dir}/").collect()
        local = f"{tmp_dir}/{FILE}"
        if _os.path.exists(local):
            with open(local, "r", encoding="utf-8") as f:
                return f.read()
    except Exception:
        pass
    return ""


def _yaml_upload_to_stage(sf_session, yaml_content: str) -> bool:
    stage_path = f"@{FULLPATH}/{FILE}"
    try:
        from io import BytesIO as _BytesIO
        yaml_bytes  = yaml_content.encode("utf-8")
        yaml_stream = _BytesIO(yaml_bytes)
        sf_session.file.put_stream(
            yaml_stream, stage_path,
            auto_compress=False, overwrite=True
        )
        return True
    except Exception:
        return False


def run_yaml_auto_update(sf_session) -> dict:
    """
    Called once per Genie page load (result cached in session_state['yaml_sync_done']).
    Reads model.yml, discovers new VW_* views, adds missing tables, pushes back to stage.
    Returns: {status, added, message}
    """
    import yaml as _yaml
    result = {"status": "ok", "added": [], "message": ""}
    if not sf_session:
        return {"status": "error", "added": [], "message": "No session."}

    current_yaml = _yaml_load_from_stage(sf_session)
    try:
        model = (_yaml.safe_load(current_yaml) or {}) if current_yaml else {}
    except Exception:
        model = {}

    model.setdefault("tables", [])
    existing = {t.get("name") for t in model["tables"] if isinstance(t, dict)}

    all_views = _yaml_get_views(sf_session)
    if not all_views:
        return {"status": "no_changes", "added": [],
                "message": f"No VW_* views found in {SCHEMA}."}

    added = []
    for view in all_views:
        if view in existing:
            continue
        cols = _yaml_get_columns(sf_session, view)
        if not cols:
            continue
        model["tables"].append(_yaml_build_table_block(view, cols))
        added.append(view)

    if not added:
        return {"status": "no_changes", "added": [],
                "message": f"YAML up to date — {len(existing)} tables, {len(all_views)} views checked."}

    ts       = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    header   = f"# Auto-updated {ts} — added: {', '.join(added)}\n\n"
    yaml_str = header + _yaml.dump(
        model, default_flow_style=False, sort_keys=False,
        allow_unicode=True, width=120
    )

    try:
        import os as _os2
        with open(f"/tmp/orderlens_{FILE}", "w", encoding="utf-8") as f:
            f.write(yaml_str)
    except Exception:
        pass

    upload_ok = _yaml_upload_to_stage(sf_session, yaml_str)
    result.update({
        "added":   added,
        "message": (f"Added {len(added)} view(s): {', '.join(added)}. "
                    f"{'Stage updated.' if upload_ok else 'Stage upload failed.'}"),
        "status":  "ok" if upload_ok else "error",
    })
    return result


# Page config
st.set_page_config(
    page_title="OrderLens - Sales & Operations Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Session state defaults ───────────────────────────────────────────────────
_SS_DEFAULTS = {
    # App navigation
    "all_questions":       [],
    "user_questions":      [],
    "messages":            [],
    "pending_prompt":      None,
    "current_page":        "Dashboard",
    "active_agent":        None,        # dropoff | order_velocity | smart_fulfillment
    "agent_ran":           False,
    "agent_params":        {},
    "show_insights":       False,
    "active_tab":          "Business Health",
    "bg_color":            UI_THEME_DEFAULT_BG,
    # Genie core
    "selected_analysis":   None,
    "show_analysis":       False,
    "analyst_response":    None,
    "recent_analyses":     [],
    "last_custom_query":   None,
    "genie_messages":      [],
    "genie_input_version": 0,
    "saved_insights":      [],
    # Cache / memory
    "genie_cache":         None,
    "genie_cache_init":    False,
    "genie_memory":        None,
    "genie_memory_built":  False,
    "_mem_last_q_count":   -1,
    # Chat persistence (long-term)
    "chat_persistence":    None,
    "chat_persist_init":   False,
    "genie_session_id":    None,
    "genie_session_label": "",
    "chat_turn_index":     0,
    "restore_offered":     False,
    "restore_dismissed":   False,
    "_all_sessions_cache": [],
    "show_chats_panel":    False,
    "_genie_summary":      "",
    # YAML auto-sync
    "yaml_sync_done":      False,
    "yaml_sync_result":    None,
}
for _k, _v in _SS_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Theme BG Picker ──────────────────────────────────────────────────────────
# Colour/size/position controlled by UI_THEME_* constants in the UI CONFIG above.
def apply_custom_theme_picker(link_text: str = "BG"):
    if "bg_color" not in st.session_state:
        st.session_state.bg_color = UI_THEME_DEFAULT_BG
    st.markdown(
        f"<style>.stApp{{background-color:{st.session_state.bg_color}!important;"
        "transition:background-color .5s ease;}}</style>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="theme-anchor"><span class="theme-label-text">{link_text}</span></div>',
        unsafe_allow_html=True,
    )
    return st.color_picker("picker", key="bg_color", label_visibility="collapsed")


# Initialize theme picker + inject full CSS from UI config constants
apply_custom_theme_picker(link_text="BG")
st.markdown(_build_all_css(), unsafe_allow_html=True)


# Helper function to run queries
def run_query(query):
    try:
        return session.sql(query).to_pandas()
    except Exception as e:
        st.error(f"Unable to load data: {str(e)}")
        return pd.DataFrame()

# ============== GENIE (match another_app_for _bg.py) ==============
# Only change vs reference: history table location
GENIE_HISTORY_TABLE = "SALES_OPS_PLANNING_DEV.INFORMATION_MART.GENIE_QUESTION_HISTORY"
SAVED_INSIGHTS_TABLE = "SALES_OPS_PLANNING_DEV.INFORMATION_MART.SAVED_INSIGHTS"

def _sql_escape(s: str) -> str:
    return (s or "").replace("'", "''")

def _get_current_user_raw() -> str:
    """Best-effort viewer identity (may be NULL depending on runtime)."""
    try:
        df = session.sql("SELECT CURRENT_USER() AS U").to_pandas()
        if not df.empty and "U" in df.columns:
            val = df.at[0, "U"]
            if val is None or (hasattr(pd, "isna") and pd.isna(val)):
                return ""
            s = str(val).strip()
            if s in ("None", "nan", "null", "<NA>"):
                return ""
            return s
    except Exception:
        pass
    return ""

def _append_genie_question(query: str, analysis_type: str):
    """Persist question frequency per user into GENIE_QUESTION_HISTORY."""
    q = (query or "").strip()
    if not q:
        return
    norm_raw     = q.lower()[:2000]
    t_raw        = (analysis_type or "").strip()[:100]
    current_user = _get_current_user_raw() or "UNKNOWN"
    # Manual escaping — most reliable across Snowpark driver versions
    norm = norm_raw.replace("'", "''")
    t    = t_raw.replace("'", "''")
    usr  = current_user.replace("'", "''")
    try:
        # Check if this (normalised_query, user) pair already exists
        existing = session.sql(f"""
            SELECT COUNT(*) AS CNT FROM {GENIE_HISTORY_TABLE}
            WHERE normalized_query = '{norm}' AND "USER" = '{usr}'
        """).collect()
        if existing and existing[0][0] > 0:
            session.sql(f"""
                UPDATE {GENIE_HISTORY_TABLE}
                SET frequency      = frequency + 1,
                    last_asked_at  = CURRENT_TIMESTAMP(),
                    type           = '{t}'
                WHERE normalized_query = '{norm}' AND "USER" = '{usr}'
            """).collect()
        else:
            session.sql(f"""
                INSERT INTO {GENIE_HISTORY_TABLE}
                    (normalized_query, type, frequency, last_asked_at, "USER")
                VALUES
                    ('{norm}', '{t}', 1, CURRENT_TIMESTAMP(), '{usr}')
            """).collect()
        st.session_state.genie_history_error = None
    except Exception as e:
        st.session_state.genie_history_error = str(e)


def _save_insight(question: str, title: str, analysis_type: str = "custom", page: str = "genie"):
    """Persist a Saved Insight row for the current user."""
    q = (question or "").strip()
    t = (title or "").strip()
    if not q:
        return
    def _e(s, n=2000): return str(s or "")[:n].replace("'","''")
    try:
        current_user = _get_current_user_raw() or "UNKNOWN"
        title_val    = t or q[:80]
        analysis_val = (analysis_type or "custom").strip()
        page_val     = (page or "genie").strip()
        session.sql(f"""
            INSERT INTO {SAVED_INSIGHTS_TABLE}
                (CREATED_BY, PAGE, TITLE, QUESTION, VERIFIED_QUERY_NAME, SQL_TEXT, TAGS)
            VALUES
                ('{_e(current_user,200)}', '{_e(page_val,50)}', '{_e(title_val,200)}',
                 '{_e(q)}', '{_e(analysis_val,100)}', NULL, NULL)
        """).collect()
    except Exception as e:
        st.session_state["saved_insights_error"] = str(e)


def _get_saved_insights_for_user(n: int = 20, page: str = "genie"):
    """Return recent saved insights for the current user on a given page."""
    try:
        current_user = (_get_current_user_raw() or "UNKNOWN").replace("'","''")
        page_val     = (page or "genie").strip().replace("'","''")
        df = session.sql(f"""
            SELECT INSIGHT_ID, CREATED_AT, CREATED_BY, PAGE, TITLE, QUESTION, VERIFIED_QUERY_NAME
            FROM {SAVED_INSIGHTS_TABLE}
            WHERE PAGE = '{page_val}' AND COALESCE(CREATED_BY,'UNKNOWN') = '{current_user}'
            ORDER BY CREATED_AT DESC
            LIMIT {int(n)}
        """).to_pandas()
        if df is None or df.empty:
            return []
        out = []
        for _, row in df.iterrows():
            out.append({
                "insight_id": row.get("INSIGHT_ID"),
                "title": (row.get("TITLE") or "").strip(),
                "question": (row.get("QUESTION") or "").strip(),
                "created_by": (row.get("CREATED_BY") or "").strip(),
                "verified_query_name": (row.get("VERIFIED_QUERY_NAME") or "").strip(),
            })
        return out
    except Exception:
        return []


def _get_frequent_questions(n: int = 10):
    """Top n questions by total frequency across all users."""
    try:
        df = run_query(f"""
            SELECT normalized_query, SUM(frequency) AS cnt
            FROM {GENIE_HISTORY_TABLE}
            WHERE TRIM(normalized_query) != ''
            GROUP BY normalized_query
            ORDER BY cnt DESC
            LIMIT {int(n)}
        """)
        if df is None or df.empty:
            return []
        return [{"query": (row.get("NORMALIZED_QUERY") or "").strip(), "count": int(row.get("CNT", 0))} for _, row in df.iterrows()]
    except Exception:
        return []

def _get_frequent_questions_by_user(n: int = 10):
    """Top n questions by frequency for current user."""
    try:
        current_user = (_get_current_user_raw() or "UNKNOWN").replace("'", "''")
        df = session.sql(f"""
            SELECT normalized_query, frequency AS cnt
            FROM {GENIE_HISTORY_TABLE}
            WHERE "USER" = '{current_user}' AND TRIM(normalized_query) != ''
            ORDER BY frequency DESC
            LIMIT {int(n)}
        """).to_pandas()
        if df is None or df.empty:
            return []
        return [{"query": (row.get("NORMALIZED_QUERY") or "").strip(), "count": int(row.get("CNT", 0))} for _, row in df.iterrows()]
    except Exception:
        return []

def _get_app_owner_role() -> str:
    """Return CURRENT_ROLE() (app owner role when running with owner's rights)."""
    try:
        df = session.sql("SELECT CURRENT_ROLE() AS R").to_pandas()
        if not df.empty and "R" in df.columns:
            r = df.at[0, "R"]
            if r is not None and not (hasattr(pd, "isna") and pd.isna(r)):
                return str(r).strip()
    except Exception:
        pass
    return ""

def safe_number(val, default=0.0):
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return default
        return float(val)
    except Exception:
        return default

def safe_int(val, default=0):
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return default
        return int(float(val))
    except Exception:
        return default

def abbr_currency(v: float, currency_symbol: str = "$") -> str:
    """$4.2M style abbreviations."""
    n = abs(v)
    sign = "-" if v < 0 else ""
    if n >= 1_000_000_000: return f"{sign}{currency_symbol}{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:     return f"{sign}{currency_symbol}{n/1_000_000:.1f}M"
    if n >= 1_000:         return f"{sign}{currency_symbol}{n/1_000:.1f}K"
    return f"{sign}{currency_symbol}{n:.0f}"

def _safe_pct_str(val, default=0.0):
    v = safe_number(val, default)
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.1f}%"

def normalize_upper(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df2 = df.copy()
    df2.columns = [str(c).upper() for c in df2.columns]
    return df2

def get_num(df: pd.DataFrame, name: str, default=0.0):
    if df is None or df.empty:
        return default
    cols = {str(c).upper(): c for c in df.columns}
    key_up = name.upper()
    if key_up in cols:
        return safe_number(df.at[0, cols[key_up]], default)
    return default

def as_stage_url(db_sch_stage: str, file_name: str) -> str:
    return f"@{db_sch_stage}/{file_name}".replace("//", "/")

CORTEX_PRESCRIPTIVE_MODEL = "llama3-8b"
CORTEX_QUICK_MODEL = "llama3-8b"  # Model for quick analysis prescriptive (can use faster model)

def _extract_cortex_text(raw) -> str:
    """Extract plain text from CORTEX.COMPLETE response (handles both plain text and JSON-wrapped formats)."""
    if not raw or not isinstance(raw, str):
        return ""
    stripped = raw.strip()
    if stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
            if "choices" in parsed and parsed["choices"]:
                choice = parsed["choices"][0]
                return (choice.get("messages") or choice.get("message", {}).get("content", "") or stripped).strip()
            elif "message" in parsed:
                return str(parsed["message"]).strip()
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            pass
    return stripped


def _cortex_complete_prescriptive(content: list, run_df_func, question: str) -> str:
    """Use SNOWFLAKE.CORTEX.COMPLETE to generate business-driven prescriptive insights from query data."""
    data_parts = []
    for block in content or []:
        if block.get("type") != "sql":
            continue
        sql = block.get("statement", "")
        if not sql.strip():
            continue
        try:
            df = run_df_func(sql)
            if df is None or df.empty:
                continue
            head = df.head(40)
            data_parts.append(head.to_string(index=False, max_colwidth=40))
        except Exception:
            continue
    if not data_parts:
        return ""
    data_str = "\n\n---\n\n".join(data_parts)
    if len(data_str) > 15000:
        data_str = data_str[:15000] + "\n... (truncated)"
    prompt = (
        "You are a sales & operations business analyst. The user asked a question and received the following data from our analytics. "
        "Provide prescriptive insights: specific recommended actions and risks based on the data. "
        "Be concrete: cite numbers, dealer names, product names, amounts, and percentages from the data. "
        "Format as bullet points (use •). Do NOT use generic phrases like 'review the data'—give actionable recommendations.\n\n"
        f"User question: {question}\n\n"
        f"Data:\n{data_str}"
    )
    try:
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS RESPONSE",
            params=[CORTEX_PRESCRIPTIVE_MODEL, prompt]
        ).to_pandas()
        if not result.empty and "RESPONSE" in result.columns:
            text = _extract_cortex_text(result.at[0, "RESPONSE"])
            if text and len(text) > 20:
                return text
    except Exception:
        pass
    return ""

def _generate_prescriptive_from_data(content: list, run_df_func) -> str:
    """Generate data-driven prescriptive insights from SQL result dataframes when Cortex returns generic text."""
    bullets = []
    for block in content or []:
        if block.get("type") != "sql":
            continue
        sql = block.get("statement", "")
        if not sql.strip():
            continue
        try:
            df = run_df_func(sql)
            if df is None or df.empty or len(df.columns) < 2:
                continue
            upper = {str(c).upper(): c for c in df.columns}
            if "VENDOR_NAME" in upper or "DEALER_NAME" in upper:
                name_col = upper.get("VENDOR_NAME") or upper.get("DEALER_NAME")
                spend_col = upper.get("TOTAL_SPEND") or upper.get("SPEND") or upper.get("AMOUNT") or upper.get("REVENUE")
                if name_col and spend_col:
                    top = df.nlargest(5, spend_col) if pd.api.types.is_numeric_dtype(df[spend_col]) else df.head(5)
                    for _, row in top.iterrows():
                        name, amt = row.get(name_col, ""), safe_number(row.get(spend_col), 0)
                        if name and amt > 0:
                            bullets.append(f"• <b>{name}</b>: {abbr_currency(amt)} — Consider volume discounts or consolidation.")
            else:
                x_col, y_col = _pick_chart_columns(df)
                if x_col and y_col:
                    try:
                        numeric = pd.to_numeric(df[y_col], errors="coerce")
                        top = df.nlargest(5, y_col) if numeric.notna().any() else df.head(5)
                        for _, row in top.iterrows():
                            lab = str(row.get(x_col, ""))[:50]
                            val = safe_number(row.get(y_col), 0)
                            if lab and (val != 0 or lab):
                                bullets.append(f"• <b>{lab}</b>: {abbr_currency(val) if val >= 100 else f'{val:,.0f}'} — Review for optimization.")
                    except Exception:
                        pass
        except Exception:
            continue
    if not bullets:
        return ""
    return "<br/>".join(bullets[:8])

def _generate_prescriptive_from_dfs(dfs: list) -> str:
    """Generate prescriptive bullets from existing dataframes (quick analyses)."""
    bullets = []
    for df in dfs:
        if df is None or df.empty or len(df.columns) < 2:
            continue
        upper = {str(c).upper(): c for c in df.columns}
        if "VENDOR_NAME" in upper or "DEALER_NAME" in upper:
            name_col = upper.get("VENDOR_NAME") or upper.get("DEALER_NAME")
            spend_col = upper.get("TOTAL_SPEND") or upper.get("SPEND") or upper.get("AMOUNT") or upper.get("REVENUE")
            if name_col and spend_col:
                top = df.nlargest(5, spend_col) if pd.api.types.is_numeric_dtype(df[spend_col]) else df.head(5)
                for _, row in top.iterrows():
                    name, amt = row.get(name_col, ""), safe_number(row.get(spend_col), 0)
                    if name and amt > 0:
                        bullets.append(f"• <b>{name}</b>: {abbr_currency(amt)} — Consider volume discounts or consolidation.")
        else:
            x_col, y_col = _pick_chart_columns(df)
            if x_col and y_col:
                try:
                    numeric = pd.to_numeric(df[y_col], errors="coerce")
                    top = df.nlargest(5, y_col) if numeric.notna().any() else df.head(5)
                    for _, row in top.iterrows():
                        lab = str(row.get(x_col, ""))[:50]
                        val = safe_number(row.get(y_col), 0)
                        if lab and (val != 0 or lab):
                            bullets.append(f"• <b>{lab}</b>: {abbr_currency(val) if val >= 100 else f'{val:,.0f}'} — Review for optimization.")
                except Exception:
                    pass
    if not bullets:
        return ""
    # Remove duplicates while preserving order
    seen = set()
    unique_bullets = []
    for bullet in bullets:
        if bullet not in seen:
            seen.add(bullet)
            unique_bullets.append(bullet)
    return "<br/>".join(unique_bullets[:8])


def _cortex_complete_prescriptive_quick(vendors_df, question: str, metrics: dict = None, anomaly: str = None, monthly_df=None) -> str:
    """Use SNOWFLAKE.CORTEX.COMPLETE to generate fast prescriptive insights for quick analysis cards.
    Only sends deduplicated, compact data (top 10 rows) to minimize LLM latency."""
    # Build compact data: only vendors/products (top 10) + optional monthly summary
    data_parts = []
    if vendors_df is not None and not vendors_df.empty:
        try:
            data_parts.append(vendors_df.head(10).to_string(index=False, max_colwidth=30))
        except Exception:
            pass
    if monthly_df is not None and not monthly_df.empty:
        try:
            data_parts.append(monthly_df.tail(6).to_string(index=False, max_colwidth=30))
        except Exception:
            pass
    if not data_parts and not metrics:
        return ""
    data_str = "\n---\n".join(data_parts) if data_parts else ""
    # Build compact metrics context
    ctx = ""
    if metrics:
        ctx = "Metrics: " + ", ".join(f"{k}={v}" for k, v in metrics.items())
    if anomaly:
        ctx += f"\nAnomaly: {anomaly}"
    prompt = (
        "You are an S&OP analyst. Given this data, provide 4-5 specific prescriptive recommendations "
        "with concrete actions. Cite actual names, numbers, and percentages from the data. "
        "Use • bullet points. Be concise.\n\n"
        f"Question: {question}\n"
    )
    if ctx:
        prompt += f"{ctx}\n"
    if data_str:
        prompt += f"\nData:\n{data_str}"
    try:
        result = session.sql(
            "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS RESPONSE",
            params=[CORTEX_QUICK_MODEL, prompt]
        ).to_pandas()
        if not result.empty and "RESPONSE" in result.columns:
            text = _extract_cortex_text(result.at[0, "RESPONSE"])
            if text and len(text) > 20:
                return text
    except Exception:
        pass
    return ""

def _parse_descriptive_prescriptive(text: str):
    """Split analyst response into (descriptive, prescriptive) — kept for backward compat."""
    d, p, _ = _parse_three_sections(text)
    return d, p


def _parse_three_sections(text: str):
    """
    Parse Cortex response into (descriptive, prescriptive, predictive).
    Handles both **Bold** markers and plain-text markers.
    Returns (desc, pres, pred) — each may be None if not found.
    """
    import re as _re
    if not text or not text.strip():
        return None, None, None
    text = text.strip()

    di = _re.search(r'\b(?:\d+\.?\s+)?(?:\*{0,2})descriptive(?:\*{0,2})(?:\s*[-:])?',  text, _re.IGNORECASE)
    pi = _re.search(r'\b(?:\d+\.?\s+)?(?:\*{0,2})prescriptive(?:\*{0,2})(?:\s*[-:])?', text, _re.IGNORECASE)
    ri = _re.search(r'\b(?:\d+\.?\s+)?(?:\*{0,2})predictive(?:\*{0,2})(?:\s*[-:])?',   text, _re.IGNORECASE)

    def _ext(sm, *others):
        if not sm:
            return None
        s = sm.end()
        e = len(text)
        for o in others:
            if o and o.start() > sm.start():
                e = min(e, o.start())
        val = text[s:e].strip().lstrip("*").strip()
        return val if val else None

    desc = _ext(di, pi, ri)
    pres = _ext(pi, ri, di)
    pred = _ext(ri, di, pi)

    # Fallback: try plain markers if regex didn't find anything
    if not desc and not pres and not pred:
        for marker, attr in [
            (("**Descriptive**", "Descriptive:"), "desc"),
            (("**Prescriptive**", "Prescriptive:"), "pres"),
            (("**Predictive**", "Predictive:"), "pred"),
        ]:
            for m in marker:
                idx = text.find(m)
                if idx >= 0:
                    after = text[idx + len(m):].strip().lstrip(": \n")
                    if attr == "desc":   desc = after.split("**Prescriptive")[0].split("Prescriptive:")[0].strip() or None
                    elif attr == "pres": pres = after.split("**Predictive")[0].split("Predictive:")[0].strip() or None
                    elif attr == "pred": pred = after.strip() or None
                    break

    return desc, pres, pred


def _pick_chart_columns(df: pd.DataFrame) -> tuple:
    """Pick best (x_categorical, y_numeric) for bar chart."""
    if df is None or df.empty or len(df.columns) < 2:
        return (None, None)
    cols = list(df.columns)
    cat_prefer = ("DEALER_NAME", "VENDOR_NAME", "PRODUCT_NAME", "ORDER_STATUS", "MONTH", "DEALER_TYPE", "PRODUCT_CATEGORY")
    num_prefer = ("TOTAL_AMOUNT", "SPEND", "REVENUE", "ORDERS", "CNT", "QUANTITY", "AMOUNT")
    upper_cols = {str(c).upper(): c for c in cols}
    x_col = None
    for name in cat_prefer:
        if name in upper_cols:
            x_col = upper_cols[name]
            break
    if not x_col:
        for c in cols:
            try:
                if pd.api.types.is_string_dtype(df[c]) or pd.api.types.is_object_dtype(df[c]):
                    x_col = c
                    break
            except Exception:
                pass
    if not x_col:
        x_col = cols[0]
    y_col = None
    for name in num_prefer:
        if name in upper_cols and upper_cols[name] != x_col:
            y_col = upper_cols[name]
            break
    if not y_col:
        for c in cols:
            if c != x_col:
                try:
                    if pd.api.types.is_numeric_dtype(df[c]):
                        y_col = c
                        break
                except Exception:
                    pass
    if not y_col:
        y_col = cols[1] if len(cols) > 1 else None
    return (x_col, y_col)

def _apply_props(chart, height=320, title=None):
    chart = chart.properties(height=height)
    if title:
        chart = chart.properties(title=title).configure_title(color='#0f172a', fontSize=14, fontWeight='bold')
    return chart

def alt_bar(df, x, y, title=None, horizontal=False, color="#60A5FA", height=320):
    if df is None or df.empty:
        return
    data = df.copy()
    if horizontal:
        base = alt.Chart(data).encode(
            x=alt.X(y, type='quantitative', axis=alt.Axis(grid=False, title=None, format="~s")),
            y=alt.Y(x, type='nominal', sort='-x', axis=alt.Axis(grid=False, title=None)),
            tooltip=[x, alt.Tooltip(y, title="Value", format="~s")]
        )
    else:
        base = alt.Chart(data).encode(
            x=alt.X(x, type='nominal', axis=alt.Axis(grid=False, title=None)),
            y=alt.Y(y, type='quantitative', axis=alt.Axis(grid=False, title=None, format="~s")),
            tooltip=[x, alt.Tooltip(y, title="Value", format="~s")]
        )
    bar = base.mark_bar(color=color, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    if horizontal:
        text = base.mark_text(
            align='left',
            baseline='middle',
            dx=4,
            color='#111827'
        ).encode(text=alt.Text(y, format='~s'))
    else:
        text = base.mark_text(
            align='center',
            baseline='bottom',
            dy=-4,
            color='#111827'
        ).encode(text=alt.Text(y, format='~s'))
    chart = _apply_props(bar + text, height=height, title=title).configure_view(stroke=None)
    st.altair_chart(chart, use_container_width=True)

def alt_line_monthly(df: pd.DataFrame, month_col: str = 'MONTH', value_col: str = 'VALUE', height: int = 140, title=None):
    if df is None or df.empty:
        return
    data = df.copy()
    try:
        data[month_col] = pd.to_datetime(data[month_col].astype(str) + '-01')
        data = data.sort_values(month_col)
        data['MONTH_LABEL'] = data[month_col].dt.strftime('%b')
    except Exception:
        data['MONTH_LABEL'] = data[month_col].astype(str)
    chart = alt.Chart(data).mark_line(point=True, color='#60A5FA').encode(
        x=alt.X('MONTH_LABEL:N', axis=alt.Axis(title=None, labelAngle=0)),
        y=alt.Y(f'{value_col}:Q', axis=alt.Axis(title=None, grid=False, format='~s')),
        tooltip=[alt.Tooltip('MONTH_LABEL:N', title='Month'), alt.Tooltip(f'{value_col}:Q', format=',.0f')]
    ).properties(height=height)
    if title:
        chart = chart.properties(title=title).configure_title(color='#0f172a')
    st.altair_chart(chart, use_container_width=True)

_PERIOD_PAIRS = (
    (("THIS_MONTH_SPEND", "LAST_MONTH_SPEND"), ("This Month", "Previous Month")),
    (("CURRENT_MONTH_SPEND", "PREVIOUS_MONTH_SPEND"), ("This Month", "Previous Month")),
    (("CURR_MONTHLY_REVENUE", "PREV_MONTHLY_REVENUE"), ("Current Month", "Previous Month")),
    (("CURR_MONTH", "PREV_MONTH"), ("Current Month", "Previous Month")),
    (("THIS_QUARTER_SPEND", "LAST_QUARTER_SPEND"), ("This Quarter", "Previous Quarter")),
    (("THIS_YEAR_SPEND", "LAST_YEAR_SPEND"), ("This Year", "Previous Year")),
)

def _has_comparison_columns(df: pd.DataFrame) -> tuple:
    """Check if df has current vs previous period columns."""
    if df is None or df.empty:
        return (None, None, None, None, None)
    upper = {str(c).upper(): c for c in df.columns}
    cat_col = upper.get("DEALER_NAME") or upper.get("PRODUCT_NAME") or upper.get("CATEGORY")
    for (curr_name, prev_name), (curr_label, prev_label) in _PERIOD_PAIRS:
        curr_col = upper.get(curr_name)
        prev_col = upper.get(prev_name)
        if curr_col and prev_col:
            return (cat_col, curr_col, prev_col, curr_label, prev_label)
    return (None, None, None, None, None)

def alt_bar_comparison(df: pd.DataFrame, cat_col, curr_col: str, prev_col: str,
                      curr_label: str = "Current Month", prev_label: str = "Previous Month",
                      title=None, height: int = 320):
    """Grouped bar chart comparing two periods."""
    if df is None or df.empty:
        return
    if cat_col:
        data = df[[cat_col, curr_col, prev_col]].copy()
        data[curr_col] = pd.to_numeric(data[curr_col], errors="coerce").fillna(0)
        data[prev_col] = pd.to_numeric(data[prev_col], errors="coerce").fillna(0)
        data = data.melt(id_vars=[cat_col], var_name="Period", value_name="Spend")
    else:
        row = df.iloc[0]
        data = pd.DataFrame({
            "Period": [curr_label, prev_label],
            "Spend": [safe_number(row.get(curr_col), 0), safe_number(row.get(prev_col), 0)]
        })
    color_scale = alt.Scale(domain=[curr_label, prev_label], range=["#4ADE80", "#60A5FA"])
    if cat_col:
        data["Period"] = data["Period"].replace({curr_col: curr_label, prev_col: prev_label})
        base = alt.Chart(data).encode(
            x=alt.X(f"{cat_col}:N", axis=alt.Axis(title=None, labelAngle=-45 if len(data[cat_col].unique()) > 5 else 0)),
            y=alt.Y("Spend:Q", axis=alt.Axis(title=None, grid=False, format="~s")),
            xOffset="Period:N",
            color=alt.Color("Period:N", scale=color_scale, legend=alt.Legend(title=None)),
            tooltip=[alt.Tooltip(f"{cat_col}:N", title="Category"), alt.Tooltip("Period:N"), alt.Tooltip("Spend:Q", format=",.0f")]
        )
    else:
        base = alt.Chart(data).encode(
            x=alt.X("Period:N", axis=alt.Axis(title=None)),
            y=alt.Y("Spend:Q", axis=alt.Axis(title=None, grid=False, format="~s")),
            color=alt.Color("Period:N", scale=color_scale, legend=alt.Legend(title=None)),
            tooltip=[alt.Tooltip("Period:N"), alt.Tooltip("Spend:Q", format=",.0f")]
        )
    bar = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    text = base.mark_text(
        align='center',
        baseline='bottom',
        dy=-3,
        color='#111827'
    ).encode(text=alt.Text("Spend:Q", format='~s'))
    chart = _apply_props(bar + text, height=height, title=title).configure_view(stroke=None)
    st.altair_chart(chart, use_container_width=True)

DECISION_SUPPORT_INSTRUCTION = (
    "Do NOT start with 'This is our interpretation of your question.' "
    "Respond with exactly THREE sections in this order: "
    "(1) **Descriptive**: What the data shows with specific numbers and dealer/product names. "
    "For YES/NO questions start with a clear Yes or No first. "
    "(2) **Prescriptive**: 3-5 SPECIFIC recommended actions with exact findings and numbers. "
    "(3) **Predictive**: A short 30-90 day forecast tied to current metrics. "
    "State assumptions and give a confidence level (Low/Medium/High). "
    "Quantify likely impact where possible (e.g. estimated revenue change). "
    "NEVER use vague phrases like 'review the data below' without citing specific numbers. "
    "Answer the following question:\n\n"
)


# ══════════════════════════════════════════════════════════════════════════════
# ❶  GENIE QUERY CACHE  (in-memory LRU + Snowflake DB persistence)
#    Settings: GENIE_CACHE_MAX_SIZE, GENIE_CACHE_TTL_SECONDS,
#              GENIE_SIMILARITY_THRESHOLD  (all in UI CONFIG section above)
# ══════════════════════════════════════════════════════════════════════════════
class GenieQueryCache:
    CACHE_TABLE = f"{DATABASE}.{SCHEMA}.GENIE_QUERY_CACHE"

    def __init__(self, sf_session):
        self.session   = sf_session
        self.max_size  = GENIE_CACHE_MAX_SIZE
        self.ttl       = GENIE_CACHE_TTL_SECONDS
        self.threshold = GENIE_SIMILARITY_THRESHOLD
        self._mem: Dict[str, Any]  = {}
        self._order: List[str]     = []
        self.last_error            = ""
        self._ensure_table()
        self._warm_from_db()

    @staticmethod
    def _hash(q: str) -> str:
        return hashlib.md5(q.lower().strip().encode()).hexdigest()

    @staticmethod
    def _sim(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

    @staticmethod
    def _is_real(r: dict) -> bool:
        if not r or not isinstance(r, dict):
            return False
        if set(r.keys()) <= {"layout", "source", "gen_ok", "cache_fetch_time_ms"}:
            return False
        return bool(r.get("message", {}).get("content")) or bool(r.get("metrics")) or r.get("layout") == "quick"

    def _evict(self, h: str):
        if len(self._mem) >= self.max_size and h not in self._mem:
            old = self._order.pop(0)
            self._mem.pop(old, None)

    def _ensure_table(self):
        if not self.session:
            return
        try:
            self.session.sql(f"""
                CREATE TABLE IF NOT EXISTS {self.CACHE_TABLE} (
                    QUESTION_HASH  STRING NOT NULL,
                    QUESTION       STRING NOT NULL,
                    RESPONSE       VARIANT,
                    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    HIT_COUNT      INT DEFAULT 0,
                    LAST_HIT_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    PRIMARY KEY (QUESTION_HASH)
                )
            """).collect()
        except Exception:
            pass

    def _warm_from_db(self):
        if not self.session:
            return
        try:
            rows = self.session.sql(
                f"SELECT QUESTION_HASH, QUESTION, RESPONSE FROM {self.CACHE_TABLE} "
                f"ORDER BY HIT_COUNT DESC, LAST_HIT_AT DESC LIMIT 50"
            ).collect()
            for row in rows:
                h   = str(row[0])
                q   = str(row[1]) if row[1] else ""
                raw = row[2]
                # VARIANT from Snowflake may be dict, str, or None
                if raw is None:
                    continue
                if isinstance(raw, dict):
                    resp = raw
                elif isinstance(raw, str):
                    try:
                        resp = json.loads(raw)
                    except Exception:
                        continue
                else:
                    try:
                        resp = json.loads(str(raw))
                    except Exception:
                        continue
                if isinstance(resp, dict) and self._is_real(resp):
                    self._evict(h)
                    self._mem[h] = {"response": resp, "q": q.lower().strip(), "ts": time.time()}
                    self._order.append(h)
        except Exception as exc:
            self.last_error = str(exc)

    def get(self, question: str) -> Optional[Dict]:
        h = self._hash(question)
        # 1. in-memory exact
        entry = self._mem.get(h)
        if entry and time.time() - entry["ts"] < self.ttl:
            if h in self._order:
                self._order.remove(h)
            self._order.append(h)
            return entry["response"]
        # 2. DB exact match
        if self.session:
            try:
                rows = self.session.sql(
                    f"SELECT RESPONSE FROM {self.CACHE_TABLE} WHERE QUESTION_HASH = ? LIMIT 1",
                    params=[h]
                ).collect()
                if rows:
                    raw = rows[0][0]
                    if raw is None:
                        pass
                    else:
                        if isinstance(raw, dict):
                            resp = raw
                        elif isinstance(raw, str):
                            try:
                                resp = json.loads(raw)
                            except Exception:
                                resp = None
                        else:
                            try:
                                resp = json.loads(str(raw))
                            except Exception:
                                resp = None
                        if resp and isinstance(resp, dict) and self._is_real(resp):
                            self._evict(h)
                            self._mem[h] = {"response": resp, "q": question.lower().strip(), "ts": time.time()}
                            self._order.append(h)
                            try:
                                self.session.sql(
                                    f"UPDATE {self.CACHE_TABLE} SET HIT_COUNT = HIT_COUNT + 1, "
                                    f"LAST_HIT_AT = CURRENT_TIMESTAMP() WHERE QUESTION_HASH = ?",
                                    params=[h]
                                ).collect()
                            except Exception:
                                pass
                            return resp
            except Exception as exc:
                self.last_error = str(exc)
        # 3. semantic similarity (in-memory)
        q_low = question.lower().strip()
        for _, cached_entry in self._mem.items():
            if self._sim(q_low, cached_entry.get("q", "")) >= self.threshold:
                resp = cached_entry["response"]
                if self._is_real(resp):
                    return resp
        return None

    def set(self, question: str, response: dict) -> bool:
        if not self._is_real(response):
            return False
        h = self._hash(question)
        self._evict(h)
        self._mem[h] = {"response": response, "q": question.lower().strip(), "ts": time.time()}
        self._order.append(h)
        if self.session:
            try:
                resp_json = json.dumps(response, default=str)[:30000]
                q_esc     = question.replace("'", "''")[:2000]
                h_esc     = h  # MD5 hash — no quotes needed
                # Delete-then-insert avoids conflicts (no PRIMARY KEY on table)
                self.session.sql(
                    f"DELETE FROM {self.CACHE_TABLE} WHERE QUESTION_HASH = ?",
                    params=[h_esc]
                ).collect()
                # Use positional param for JSON — avoids all quoting issues
                self.session.sql(
                    f"INSERT INTO {self.CACHE_TABLE} (QUESTION_HASH, QUESTION, RESPONSE, HIT_COUNT) "
                    f"SELECT ?, ?, PARSE_JSON(?), 1",
                    params=[h_esc, q_esc, resp_json]
                ).collect()
            except Exception as exc1:
                self.last_error = str(exc1)
                return False
        return True


# ══════════════════════════════════════════════════════════════════════════════
# ❷  GENIE CHAT PERSISTENCE  (cross-session resume)
#    Settings: GENIE_SESSION_RESTORE_DAYS, GENIE_MAX_TURNS_LOADED
# ══════════════════════════════════════════════════════════════════════════════
class GenieChatPersistence:
    TABLE = f"{DATABASE}.{SCHEMA}.GENIE_CHAT_SESSIONS"

    def __init__(self, sf_session):
        self.session   = sf_session
        self._table_ok = False
        self._user     = "UNKNOWN"
        if sf_session:
            try:
                self._user = sf_session.sql("SELECT CURRENT_USER()").collect()[0][0] or "UNKNOWN"
            except Exception:
                pass
            self._init_table()

    def _init_table(self):
        try:
            self.session.sql(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE} (
                    SESSION_ID    STRING        NOT NULL,
                    USER_NAME     STRING        NOT NULL,
                    TURN_INDEX    INT           NOT NULL,
                    ROLE          STRING        NOT NULL,
                    CONTENT       STRING        NOT NULL,
                    CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP() NOT NULL,
                    SQL_USED      STRING,
                    SOURCE        STRING,
                    SESSION_LABEL STRING
                )
            """).collect()
            self._table_ok = True
        except Exception:
            # Table may already exist — probe with a lightweight SELECT
            try:
                self.session.sql(f"SELECT COUNT(*) FROM {self.TABLE} LIMIT 1").collect()
                self._table_ok = True
            except Exception:
                self._table_ok = False

    def save_turn(self, session_id: str, turn_index: int, role: str,
                  content: str, sql_used: str = "", source: str = "", session_label: str = ""):
        """Store one conversation turn. Uses manual escaping — most robust for Snowpark."""
        if not self._table_ok or not self.session:
            return
        def _e(s, n=4000): return str(s or "")[:n].replace("'", "''")
        try:
            sid = _e(session_id)
            usr = _e(self._user)
            ti  = int(turn_index)
            rol = _e(role, 20)
            con = _e(content)
            sql_u = _e(sql_used)
            src_v = _e(source, 100)
            lbl   = _e(session_label, 200)
            self.session.sql(f"""
                INSERT INTO {self.TABLE}
                    (SESSION_ID, USER_NAME, TURN_INDEX, ROLE, CONTENT,
                     SQL_USED, SOURCE, SESSION_LABEL)
                VALUES
                    ('{sid}', '{usr}', {ti}, '{rol}', '{con}',
                     '{sql_u}', '{src_v}', '{lbl}')
            """).collect()
        except Exception:
            pass

    def load_all_sessions(self) -> List[Dict]:
        if not self._table_ok or not self.session:
            return []
        try:
            df = self.session.sql(
                f"SELECT SESSION_ID, MAX(SESSION_LABEL) AS SESSION_LABEL, "
                f"MAX(CREATED_AT) AS LAST_AT, COUNT(*) AS TURN_COUNT "
                f"FROM {self.TABLE} "
                f"WHERE USER_NAME = ? "
                f"AND CREATED_AT >= DATEADD('day', ?, CURRENT_TIMESTAMP()) "
                f"GROUP BY SESSION_ID ORDER BY LAST_AT DESC LIMIT 20",
                params=[self._user, -GENIE_SESSION_RESTORE_DAYS]
            ).to_pandas()
            if df.empty:
                return []
            now = pd.Timestamp.utcnow().tz_localize(None)
            rows = []
            for _, r in df.iterrows():
                try:
                    age_h = (now - pd.Timestamp(r["LAST_AT"]).tz_localize(None)).total_seconds() / 3600
                except Exception:
                    age_h = 0.0
                rows.append({"session_id": str(r["SESSION_ID"]),
                              "session_label": str(r["SESSION_LABEL"] or "Previous chat"),
                              "age_hours": age_h, "turn_count": int(r["TURN_COUNT"])})
            return rows
        except Exception:
            return []

    def load_session_messages(self, session_id: str) -> List[Dict]:
        if not self._table_ok or not self.session:
            return []
        try:
            df = self.session.sql(
                f"SELECT ROLE, CONTENT, CREATED_AT, SQL_USED, SOURCE "
                f"FROM {self.TABLE} "
                f"WHERE SESSION_ID = ? AND USER_NAME = ? "
                f"ORDER BY TURN_INDEX ASC LIMIT {GENIE_MAX_TURNS_LOADED}",
                params=[session_id, self._user]
            ).to_pandas()
            return [{"role": str(r["ROLE"]), "content": str(r["CONTENT"]),
                     "timestamp": pd.Timestamp(r["CREATED_AT"]),
                     "response": None, "source": str(r.get("SOURCE",""))}
                    for _, r in df.iterrows()]
        except Exception:
            return []


# ══════════════════════════════════════════════════════════════════════════════
# ❸  GENIE LONG-TERM MEMORY  (Cortex extracts persona facts from history)
#    Settings: GENIE_MEMORY_MAX_FACTS, GENIE_PRESCRIPTIVE_MODEL
# ══════════════════════════════════════════════════════════════════════════════
class GenieLongTermMemory:
    def __init__(self, sf_session):
        self.session         = sf_session
        self._memories: List[str] = []
        self._raw_questions: List[str] = []
        self._source         = ""
        self.last_error      = ""
        self._build()

    def _fetch_questions(self) -> List[str]:
        """Try each table in priority order. Returns first non-empty result."""
        if not self.session:
            return []
        all_qs: List[str] = []
        sources_tried: List[str] = []
        for tbl, col, where in [
            (GENIE_HISTORY_TABLE,
             "normalized_query",
             "WHERE TRIM(normalized_query) != '' ORDER BY last_asked_at DESC LIMIT 30"),
            (f"{DATABASE}.{SCHEMA}.GENIE_CHAT_SESSIONS",
             "CONTENT",
             "WHERE ROLE = 'user' AND CONTENT IS NOT NULL AND TRIM(CONTENT) != '' ORDER BY CREATED_AT DESC LIMIT 30"),
            (f"{DATABASE}.{SCHEMA}.GENIE_QUERY_CACHE",
             "QUESTION",
             "WHERE QUESTION IS NOT NULL AND TRIM(QUESTION) != '' ORDER BY LAST_HIT_AT DESC LIMIT 30"),
        ]:
            try:
                df = self.session.sql(
                    f"SELECT {col} AS Q FROM {tbl} {where}"
                ).to_pandas()
                if not df.empty:
                    qs = [str(r).strip() for r in df["Q"].dropna()
                          if str(r).strip() and len(str(r).strip()) > 5]
                    if qs:
                        all_qs.extend(qs)
                        sources_tried.append(tbl.split(".")[-1])
            except Exception as exc:
                # Table doesn't exist yet or no access — not an error
                self.last_error += f" | {tbl.split('.')[-1]}: {exc}"

        if all_qs:
            # Deduplicate while preserving order
            seen: set = set()
            unique: List[str] = []
            for q in all_qs:
                if q not in seen:
                    seen.add(q)
                    unique.append(q)
            self._source = ", ".join(sources_tried)
            return unique[:30]
        return []

    def _extract_facts(self, questions: List[str]) -> List[str]:
        if not questions or not self.session:
            return []
        transcript = "\n".join(f"- {q}" for q in questions[:15])
        prompt = (
            "You are analyzing a sales & operations analyst's query history.\n\n"
            f"They recently asked:\n{transcript}\n\n"
            "Extract 3-6 concise facts about which KPIs, dealers, products, or time "
            "periods they focus on and any recurring concerns.\n\n"
            "Rules: one short sentence each (max 15 words), present tense "
            "('User tracks...'), respond NONE if too generic.\n\n"
            "Facts only, one per line:"
        )
        try:
            tdf = self.session.sql(
                "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS R",
                params=[GENIE_PRESCRIPTIVE_MODEL, prompt]
            ).to_pandas()
            raw = (tdf.at[0, "R"] if not tdf.empty else "") or ""
            if not raw.strip() or raw.strip().upper().startswith("NONE"):
                return []
            return [
                ln.strip() for ln in raw.splitlines()
                if ln.strip() and ln.strip().upper() not in ("NONE","N/A") and len(ln.strip()) > 8
            ][:GENIE_MEMORY_MAX_FACTS]
        except Exception as exc:
            self.last_error += f" | cortex: {exc}"
            return []

    def _build(self):
        questions = self._fetch_questions()
        self._raw_questions = questions
        if questions:
            self._memories = self._extract_facts(questions)

    def get_prefix(self) -> str:
        if not self._memories:
            return ""
        lines = "\n".join(f"- {m}" for m in self._memories)
        return "Context about this user (from past sessions):\n" + lines + "\n\n"

    def refresh(self):
        self._memories = []
        self._build()

    @property
    def count(self) -> int:
        return len(self._memories)


# ══════════════════════════════════════════════════════════════════════════════
# ❹  UPGRADED call_cortex_analyst  (supports multi-turn conversation history)
# ══════════════════════════════════════════════════════════════════════════════
def call_cortex_analyst(query_text: str, conversation_history: list = None) -> dict:
    """Call Cortex Analyst. conversation_history must strictly alternate user→analyst."""
    try:
        # Prepend long-term memory prefix if available (personalises Cortex answers)
        _mem = st.session_state.get("genie_memory")
        _mem_prefix = _mem.get_prefix() if (_mem and _mem.count > 0) else ""
        augmented = _mem_prefix + DECISION_SUPPORT_INSTRUCTION + (query_text or "").strip()
        messages  = []
        if conversation_history:
            _exp = "user"
            _ok  = True
            for _t in conversation_history:
                if _t.get("role") != _exp:
                    _ok = False
                    break
                _exp = "analyst" if _exp == "user" else "user"
            if _ok and conversation_history[0].get("role") == "user":
                messages = list(conversation_history)
        messages.append({"role": "user", "content": [{"type": "text", "text": augmented}]})
        resp = _snowflake.send_snow_api_request(
            "POST", "/api/v2/cortex/analyst/message",
            {"Content-Type": "application/json"}, {},
            {"messages": messages, "semantic_model_file": f"@{FULLPATH}/{FILE}"},
            None, 60000,
        )
        status = resp.get("status", 500)
        if status >= 400:
            return {"error": f"HTTP {status}: {resp.get('content','')}"}
        return json.loads(resp.get("content", "{}"))
    except Exception as e:
        return {"error": str(e)}


def _genie_date_filter():
    """Return date filter for Genie queries using app's date range."""
    if "start_date" not in st.session_state:
        st.session_state.start_date = date.today() - timedelta(days=30)
    if "end_date" not in st.session_state:
        st.session_state.end_date = date.today()
    sd = st.session_state.start_date
    ed = st.session_state.end_date
    return f"EFFECTIVE_DATE BETWEEN '{sd}' AND '{ed}'"

def run_quick_analysis(key: str) -> dict:
    """Run SQL for quick-analysis tiles (OrderLens: revenue, dealers, products, orders)."""
    flt = _genie_date_filter()
    base = f"FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW F"
    out = {
        "layout": "quick",
        "type": key,
        "metrics": {},
        "anomaly": None,
        "monthly_df": None,
        "vendors_df": None,
        "extra_dfs": {},
        "sql": {},
    }
    if key == "revenue_overview":
        # Total revenue to date
        total_to_date = normalize_upper(run_query(f"""
            SELECT SUM(F.TOTAL_AMOUNT) AS total_revenue
            {base} WHERE CURRENT_FLAG = 'Y' AND {flt}
        """))
        monthly_all = normalize_upper(run_query(f"""
            SELECT TO_CHAR(F.EFFECTIVE_DATE,'YYYY-MM') AS MONTH,
                   SUM(F.TOTAL_AMOUNT) AS VALUE_NUM
            {base} WHERE CURRENT_FLAG = 'Y' AND {flt}
            GROUP BY 1 ORDER BY 1
        """))
        quarterly_all = normalize_upper(run_query(f"""
            SELECT TO_CHAR(F.EFFECTIVE_DATE, 'YYYY-\"Q\"Q') AS QUARTER,
                   SUM(F.TOTAL_AMOUNT) AS VALUE_NUM
            {base} WHERE CURRENT_FLAG = 'Y' AND {flt}
            GROUP BY 1 ORDER BY 1
        """))
        # Compute MoM & QoQ from last two buckets
        cur_m = prev_m = 0.0
        cur_q = prev_q = 0.0
        try:
            if monthly_all is not None and not monthly_all.empty and "VALUE_NUM" in monthly_all.columns:
                cur_m = safe_number(monthly_all["VALUE_NUM"].iloc[-1], 0)
                prev_m = safe_number(monthly_all["VALUE_NUM"].iloc[-2], 0) if len(monthly_all) >= 2 else 0
        except Exception:
            cur_m = prev_m = 0.0
        try:
            if quarterly_all is not None and not quarterly_all.empty and "VALUE_NUM" in quarterly_all.columns:
                cur_q = safe_number(quarterly_all["VALUE_NUM"].iloc[-1], 0)
                prev_q = safe_number(quarterly_all["VALUE_NUM"].iloc[-2], 0) if len(quarterly_all) >= 2 else 0
        except Exception:
            cur_q = prev_q = 0.0
        mom_pct = (cur_m - prev_m) / prev_m * 100 if prev_m else 0
        qoq_pct = (cur_q - prev_q) / prev_q * 100 if prev_q else 0
        # Top 5 dealer share
        top5 = normalize_upper(run_query(f"""
            WITH dealer_spend AS (
              SELECT F.DEALER_NAME, SUM(F.TOTAL_AMOUNT) AS SPEND
              {base} WHERE CURRENT_FLAG = 'Y' AND {flt}
              GROUP BY 1
            ),
            total_spend AS (SELECT SUM(SPEND) AS TOT FROM dealer_spend),
            top5 AS (SELECT SPEND FROM dealer_spend ORDER BY SPEND DESC LIMIT 5)
            SELECT ROUND(SUM(top5.SPEND) / NULLIF((SELECT TOT FROM total_spend), 0) * 100, 2) AS PCT
            FROM top5
        """))
        total_rev = get_num(total_to_date, "TOTAL_REVENUE", 0)
        top5_pct = get_num(top5, "PCT", 0)
        out["metrics"] = {
            "total_ytd": safe_number(total_rev, 0),
            "mom_pct": safe_number(mom_pct, 0),
            "qoq_pct": safe_number(qoq_pct, 0),
            "top5_pct": safe_int(round(top5_pct, 0), 0),
        }
        # Data-driven anomaly (largest MoM spike)
        out["anomaly"] = None
        monthly_sql = f"""
            SELECT TO_CHAR(F.EFFECTIVE_DATE,'YYYY-MM') AS MONTH,
                   SUM(F.TOTAL_AMOUNT) AS MONTHLY_REVENUE,
                   COUNT(DISTINCT F.ORDER_ID) AS ORDER_COUNT,
                   COUNT(DISTINCT F.DEALER_ID) AS DEALER_COUNT
            {base} WHERE CURRENT_FLAG = 'Y' AND F.EFFECTIVE_DATE >= DATEADD('month', -12, CURRENT_DATE())
            GROUP BY 1 ORDER BY 1
        """
        out["sql"]["monthly_trend"] = monthly_sql
        monthly = normalize_upper(run_query(monthly_sql))
        if monthly.empty:
            monthly_sql2 = f"""
                SELECT TO_CHAR(F.EFFECTIVE_DATE,'YYYY-MM') AS MONTH,
                       SUM(F.TOTAL_AMOUNT) AS MONTHLY_REVENUE,
                       COUNT(DISTINCT F.ORDER_ID) AS ORDER_COUNT,
                       COUNT(DISTINCT F.DEALER_ID) AS DEALER_COUNT
                {base} WHERE CURRENT_FLAG = 'Y' AND F.EFFECTIVE_DATE >= DATEADD('month', -24, CURRENT_DATE())
                GROUP BY 1 ORDER BY 1
            """
            out["sql"]["monthly_trend_fallback"] = monthly_sql2
            monthly = normalize_upper(run_query(monthly_sql2))
        if not monthly.empty:
            monthly = monthly.rename(columns={"MONTHLY_REVENUE": "VALUE"})
        out["monthly_df"] = monthly
        out["extra_dfs"]["monthly_full"] = monthly
        try:
            if monthly is not None and not monthly.empty and "MONTH" in monthly.columns and "VALUE" in monthly.columns:
                _m = monthly.copy()
                _m["VALUE"] = _m["VALUE"].apply(lambda v: safe_number(v, 0))
                _m = _m.sort_values("MONTH")
                _m["prev"] = _m["VALUE"].shift(1)
                _m["pct"] = (_m["VALUE"] - _m["prev"]) / _m["prev"].replace({0: float('nan')})
                cand = _m.dropna(subset=["pct"])
                cand = cand[cand["pct"] > 0.20]
                if not cand.empty:
                    row = cand.loc[cand["pct"].idxmax()]
                    spike_month = str(row["MONTH"])
                    spike_pct = float(row["pct"]) * 100.0
                    topd = normalize_upper(run_query(f"""
                        SELECT F.DEALER_NAME, SUM(F.TOTAL_AMOUNT) AS SPEND
                        {base}
                        WHERE TO_CHAR(F.EFFECTIVE_DATE,'YYYY-MM') = '{spike_month}' AND CURRENT_FLAG = 'Y'
                        GROUP BY 1 ORDER BY 2 DESC LIMIT 1
                    """))
                    dealer = topd.at[0, "DEALER_NAME"] if topd is not None and not topd.empty and "DEALER_NAME" in topd.columns else "a top dealer"
                    d_amt = get_num(topd, "SPEND", 0) if topd is not None else 0
                    out["anomaly"] = (
                        f"{spike_month} revenue spiked by {spike_pct:.0f}% vs prior month, "
                        f"primarily driven by {dealer} ({abbr_currency(d_amt)})."
                    )
        except Exception:
            out["anomaly"] = None
        dealers_sql = f"""
            SELECT F.DEALER_NAME AS VENDOR_NAME, SUM(F.TOTAL_AMOUNT) AS SPEND
            {base} WHERE CURRENT_FLAG = 'Y' AND {flt}
            GROUP BY 1 ORDER BY 2 DESC LIMIT 10
        """
        out["sql"]["top_dealers"] = dealers_sql
        dealers = normalize_upper(run_query(dealers_sql))
        if dealers.empty:
            dealers_sql2 = f"""
                SELECT F.DEALER_NAME AS VENDOR_NAME, SUM(F.TOTAL_AMOUNT) AS SPEND
                {base} WHERE CURRENT_FLAG = 'Y' AND F.EFFECTIVE_DATE >= DATEADD('month', -12, CURRENT_DATE())
                GROUP BY 1 ORDER BY 2 DESC LIMIT 10
            """
            out["sql"]["top_dealers_fallback"] = dealers_sql2
            dealers = normalize_upper(run_query(dealers_sql2))
        out["vendors_df"] = dealers
        out["extra_dfs"]["top_dealers"] = dealers
    elif key == "dealer_analysis":
        dealers_df = run_query(f"""
            SELECT F.DEALER_NAME AS VENDOR_NAME, SUM(F.TOTAL_AMOUNT) AS SPEND,
                   COUNT(DISTINCT F.ORDER_ID) AS INVOICE_COUNT
            {base} WHERE CURRENT_FLAG = 'Y' AND {flt}
            GROUP BY 1 ORDER BY 2 DESC LIMIT 10
        """)
        out["vendors_df"] = dealers_df
        out["extra_dfs"]["dealer_top"] = dealers_df
        tot = float(dealers_df["SPEND"].sum()) if not dealers_df.empty and "SPEND" in dealers_df.columns else 0
        top5 = float(dealers_df.head(5)["SPEND"].sum()) if not dealers_df.empty and "SPEND" in dealers_df.columns else 0
        top5_pct = (top5 / tot * 100) if tot else 0
        out["metrics"] = {"summary": f"Top 5 dealers contribute ~{top5_pct:.0f}% of revenue in the selected period."}
        out["sql"]["dealer_analysis"] = f"SELECT F.DEALER_NAME ... {base} WHERE CURRENT_FLAG = 'Y' AND {flt}"
    elif key == "product_performance":
        prod_df = run_query(f"""
            SELECT F.PRODUCT_NAME AS VENDOR_NAME, SUM(F.TOTAL_AMOUNT) AS SPEND,
                   SUM(F.QUANTITY) AS CNT
            {base} WHERE CURRENT_FLAG = 'Y' AND {flt}
            GROUP BY 1 ORDER BY 2 DESC LIMIT 10
        """)
        out["vendors_df"] = prod_df
        out["extra_dfs"]["product_top"] = prod_df
        out["metrics"] = {"summary": "Top products by revenue and quantity (selected period)."}
        out["sql"]["product_performance"] = f"SELECT F.PRODUCT_NAME ... {base} WHERE CURRENT_FLAG = 'Y' AND {flt}"
    elif key == "order_status":
        status_df = run_query(f"""
            SELECT F.ORDER_STATUS AS VENDOR_NAME, COUNT(*) AS CNT, SUM(F.TOTAL_AMOUNT) AS SPEND
            {base} WHERE CURRENT_FLAG = 'Y' AND {flt}
            GROUP BY 1 ORDER BY 2 DESC
        """)
        out["vendors_df"] = status_df
        out["extra_dfs"]["order_status"] = status_df
        total_inv = int(status_df["CNT"].sum()) if not status_df.empty and "CNT" in status_df.columns else 0
        total_amt = float(status_df["SPEND"].sum()) if not status_df.empty and "SPEND" in status_df.columns else 0
        out["metrics"] = {"summary": f"{total_inv} orders in status buckets, total {total_amt:,.0f} revenue."}
        out["sql"]["order_status"] = f"SELECT F.ORDER_STATUS ... {base} WHERE CURRENT_FLAG = 'Y' AND {flt}"

    return out

def process_genie_query(query: str, analysis_type: str = "custom") -> dict:
    """Cache lookup → Cortex (with conversation history) → persist → return."""
    _t0 = time.time()

    st.session_state.genie_messages.append({
        "role": "user", "content": query,
        "timestamp": pd.Timestamp.now(), "response": None,
    })

    _cache = st.session_state.get("genie_cache")

    # Detect contextual follow-ups — bypass cache to avoid stale context
    _followup_signals = {"them","those","their","it","same","above","previous",
                         "that","these","which","how about","what about","also"}
    _is_contextual = bool(set(query.lower().split()) & _followup_signals) and len(query.split()) < 8

    # Cache lookup
    cached_resp = _cache.get(query) if (_cache and not _is_contextual) else None
    from_cache  = bool(cached_resp and _cache._is_real(cached_resp)) if _cache else False

    if from_cache:
        response = cached_resp
        response["cache_fetch_time_ms"] = (time.time() - _t0) * 1000
    else:
        # Build strict user→analyst conversation history
        _conv_history = []
        _prior = [m for m in st.session_state.genie_messages[:-1] if m.get("role") == "user"]
        if _prior:
            _all_prev = st.session_state.genie_messages[:-1]
            _pairs, _i = [], 0
            while _i < len(_all_prev) - 1:
                _um, _am = _all_prev[_i], _all_prev[_i + 1]
                if _um.get("role") == "user" and _am.get("role") == "assistant":
                    _u_txt = (_um.get("content") or "").strip()
                    _prev_resp = _am.get("response")
                    _a_txt = ""
                    if isinstance(_prev_resp, dict):
                        _a_txt = " ".join(
                            b.get("text","") for b in _prev_resp.get("message",{}).get("content",[])
                            if b.get("type") == "text"
                        ).strip()
                    if not _a_txt:
                        _a_txt = (_am.get("content") or "").strip()
                    if _u_txt and _a_txt:
                        _pairs.append((_u_txt[:1500], _a_txt[:1500]))
                    _i += 2
                else:
                    _i += 1
            for _u, _a in _pairs[-GENIE_MAX_CONV_PAIRS:]:
                _conv_history.append({"role":"user",    "content":[{"type":"text","text":_u}]})
                _conv_history.append({"role":"analyst", "content":[{"type":"text","text":_a}]})

        response = call_cortex_analyst(query, conversation_history=_conv_history or None)

        # Write to cache
        if _cache and not response.get("error") and not _is_contextual:
            ok = _cache.set(query, response)
            if not ok and _cache.last_error:
                st.session_state["_cache_write_error"] = _cache.last_error

    # Short bubble text — always plain text, never HTML
    # For cache hits: extract actual answer text so result panel renders correctly
    if from_cache:
        # Clear prescriptive cache so result panel re-renders fresh for this question
        for _qk in list(st.session_state.keys()):
            if str(_qk).startswith("_pres_cache_") or str(_qk).startswith("_pred_"):
                del st.session_state[_qk]
    if True:  # unified text extraction for both cache and fresh responses
        _blocks = response.get("message",{}).get("content",[]) if isinstance(response, dict) else []
        _full   = next((b.get("text","") for b in _blocks if b.get("type") == "text"), "")
        if _full:
            # Take first sentence, strip markdown
            _first = _full.split(".")[0].strip()
            _first = re.sub(r"\*\*(.+?)\*\*", r"\1", _first)   # strip **bold**
            _first = re.sub(r"\*(.+?)\*",   r"\1", _first)       # strip *italic*
            assistant_text = (_first[:150] + "…") if len(_first) > 150 else _first
        elif response.get("error"):
            assistant_text = f"Error: {str(response['error'])[:200]}"
        else:
            assistant_text = "Analysis complete. See results below."

    st.session_state.genie_messages.append({
        "role": "assistant", "content": assistant_text[:600],
        "timestamp": pd.Timestamp.now(), "response": response,
        "from_cache": from_cache,
    })
    st.session_state.genie_messages = st.session_state.genie_messages[-GENIE_SHORT_TERM_MAX_MSGS:]

    if analysis_type == "custom":
        st.session_state.last_custom_query = query
    st.session_state.recent_analyses.insert(0, {
        "query": query, "type": analysis_type,
        "timestamp": pd.Timestamp.now(), "response": response,
    })
    st.session_state.recent_analyses = st.session_state.recent_analyses[:10]
    _append_genie_question(query, analysis_type)

    # Persist both turns to Snowflake chat sessions table
    _cp  = st.session_state.get("chat_persistence")
    _sid = st.session_state.get("genie_session_id", "")
    _lbl = st.session_state.get("genie_session_label", "")
    if _cp and _sid and _cp._table_ok:
        try:
            _ti = st.session_state.get("chat_turn_index", 0)
            # User turn
            _cp.save_turn(_sid, _ti, "user", query, "", "user_input", _lbl)
            _ti += 1
            # Assistant turn — store the FULL Cortex text (not the truncated bubble)
            _resp_content = (
                response.get("message", {}).get("content", [])
                if isinstance(response, dict) else []
            )
            _sql_used = " | ".join(
                b.get("statement", "") for b in _resp_content
                if b.get("type") == "sql"
            )[:2000]
            _a_full = next(
                (b.get("text", "") for b in _resp_content if b.get("type") == "text"),
                assistant_text
            )[:4000]
            _cp.save_turn(_sid, _ti, "assistant", _a_full, _sql_used, "cortex", _lbl)
            st.session_state["chat_turn_index"] = _ti + 1
        except Exception:
            pass  # Never block the UI for persistence errors

    return response


# Cortex Analyst API call function
def send_analyst_message(prompt: str) -> dict:
    """Calls the Cortex Analyst REST API and returns the response."""
    request_body = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "semantic_model_file": f"@{FULLPATH}/{FILE}",
    }
    resp = _snowflake.send_snow_api_request(
        "POST",
        "/api/v2/cortex/analyst/message",
        {},
        {},
        request_body,
        {},
        30000,
    )
    if resp["status"] < 400:
        return json.loads(resp["content"])
    else:
        raise Exception(f"Failed request with status {resp['status']}: {resp}")
    
def normalize_query(query: str) -> str:
    if not query:
        return query
    return query.replace("SALES_OPS_PLANNING", DATABASE)

def calc_change(current, previous):
    """Calculate percentage change between current and previous values.
    Returns a tuple of (change_value, has_previous_data)"""
    if previous and previous != 0:
        return ((current - previous) / previous) * 100, True
    elif current and current > 0:
        # No previous data but have current data - treat as increase
        return 100, False  # Mark as "new" data
    return 0, True

def format_change(change_tuple):
    """Format change value for display.
    change_tuple: (change_value, has_previous_data)"""
    if isinstance(change_tuple, tuple):
        change, has_prev = change_tuple
    else:
        change, has_prev = change_tuple, True
    
    if not has_prev and change > 0:
        # No previous data but have current - show as positive
        return f"↗ New", "positive"
    
    # If change rounds to 0% (absolute value < 0.5), show as neutral black
    if abs(change) < 0.5:
        return "0%", "neutral"
    elif change > 0:
        return f"↗ {change:.0f}%", "positive"
    elif change < 0:
        return f"↘ {abs(change):.0f}%", "negative"
    # Fallback - zero change
    return "0%", "neutral"

# ============== HEADER ==============
# Embedded YASH logo (base64)
YASH_LOGO_B64 = 'we can use yash logo url'
# Header with three columns
header_cols = st.columns([1, 2, 1])

# Left: Title (OrderLens)
with header_cols[0]:
    st.markdown("""
    <div style='display:flex;align-items:center;gap:12px;padding:8px 0;min-height:52px;'>
        <div>
            <div style='font-size:40px;font-weight:700;letter-spacing:.2px;line-height:1.2;color:#1E40AF;'>OrderLens</div>
            <div style='color:#DC2626;font-size:12px;font-weight:500;'>Sales & Operations Analytics</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Center: Navigation (Dashboard, Genie, Order Life Cycle, Forecast)
with header_cols[1]:
    # Inject CSS to force all nav buttons to single-line, uniform height
    st.markdown("""
    <style>
    div[data-testid="stHorizontalBlock"]:has(button[data-testid="baseButton-secondary"]) 
        button, 
    div[data-testid="stHorizontalBlock"]:has(button[data-testid="baseButton-primary"]) 
        button {
        white-space: nowrap !important;
        height: 42px !important;
        min-height: 42px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        line-height: 42px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    nav_cols = st.columns([1, 1, 1.3, 1, 1.1])

    with nav_cols[0]:
        if st.button("Dashboard", key="nav_dash",
                     type="primary" if st.session_state.current_page == "Dashboard" else "secondary",
                     use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()

    with nav_cols[1]:
        if st.button("Genie", key="nav_genie",
                     type="primary" if st.session_state.current_page == "Genie" else "secondary",
                     use_container_width=True):
            st.session_state.current_page = "Genie"
            st.rerun()

    with nav_cols[2]:
        if st.button("Order Life Cycle", key="nav_orders",
                     type="primary" if st.session_state.current_page == "Order Life Cycle" else "secondary",
                     use_container_width=True):
            st.session_state.current_page = "Order Life Cycle"
            st.rerun()

    with nav_cols[3]:
        if st.button("Forecast", key="nav_forecast",
                     type="primary" if st.session_state.current_page == "Forecast" else "secondary",
                     use_container_width=True):
            st.session_state.current_page = "Forecast"
            st.rerun()

    with nav_cols[4]:
        if st.button("AI Agents", key="nav_agents",
                     type="primary" if st.session_state.current_page == "AI Agents" else "secondary",
                     use_container_width=True):
            st.session_state.current_page = "AI Agents"
            st.session_state.active_agent = None
            st.session_state.agent_ran    = False
            st.rerun()

# Right: YASH Technologies logo (embedded in this file — no external file or URL)
with header_cols[2]:
    st.markdown(f"""
    <div style='display:flex;align-items:center;justify-content:flex-end;padding:8px 0;min-height:52px;'>
        <img class="yash-header-logo" src="data:image/png;base64,{YASH_LOGO_B64}" alt="YASH Technologies" />
    </div>
    """, unsafe_allow_html=True)

# Divider
st.markdown("<hr style='margin:4px 0 16px 0;border:none;border-top:1.5px solid #e5e7eb;'>", unsafe_allow_html=True)

# ============== DASHBOARD PAGE ==============
if st.session_state.current_page == "Dashboard":
    
    # Welcome Section
    st.markdown('<div class="welcome-title">Welcome to Personal Sales Dashboard</div>', unsafe_allow_html=True)
    
    # Date and Filter Controls
    TODAY = date.today()
    MIN_DATE = date(2024, 1, 1)
    
    if "time_filter" not in st.session_state:
        st.session_state.time_filter = "Last 30 Days"
    if "start_date" not in st.session_state:
        st.session_state.start_date = TODAY - timedelta(days=30)
    if "end_date" not in st.session_state:
        st.session_state.end_date = TODAY
    
    # Filter Row
    filter_col1, filter_col2, filter_spacer, time_col1, time_col2, time_col3, time_col4 = st.columns([2, 1.5, 2, 1, 0.7, 0.7, 0.8])
    
    with filter_col1:
        date_range = st.date_input(
            "Date Range",
            value=(st.session_state.start_date, st.session_state.end_date),
            min_value=MIN_DATE,
            max_value=TODAY,
            label_visibility="collapsed"
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            new_start, new_end = date_range
            # Check if dates changed from current values
            if (new_start != st.session_state.start_date or new_end != st.session_state.end_date):
                # Store previous filter to detect changes
                previous_filter = st.session_state.time_filter
                
                # Update dates first
                st.session_state.start_date, st.session_state.end_date = new_start, new_end
                
                # Check if it matches any preset
                is_last_30 = (new_start == TODAY - timedelta(days=30) and new_end == TODAY)
                quarter_start_month = ((TODAY.month - 1) // 3) * 3 + 1
                is_qtd = (new_start == date(TODAY.year, quarter_start_month, 1) and new_end == TODAY)
                is_ytd = (new_start == date(TODAY.year, 1, 1) and new_end == TODAY)
                
                if is_last_30:
                    new_filter = "Last 30 Days"
                elif is_qtd:
                    new_filter = "QTD"
                elif is_ytd:
                    new_filter = "YTD"
                else:
                    # Any other date selection is Custom
                    new_filter = "Custom"
                
                # Update filter if it changed
                if new_filter != previous_filter:
                    st.session_state.time_filter = new_filter
                    st.rerun()
            else:
                # Dates didn't change, but ensure they're set
                st.session_state.start_date, st.session_state.end_date = date_range
    
    with filter_col2:
        # Fetch dealers who have orders in the selected date range
        dealers_df = run_query(f"""
            SELECT DISTINCT DEALER_NAME
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
            WHERE CURRENT_FLAG = 'Y' AND EFFECTIVE_DATE BETWEEN '{st.session_state.start_date}' AND '{st.session_state.end_date}'
            ORDER BY DEALER_NAME
        """)
        dealer_options = ["All Dealers"] + (dealers_df['DEALER_NAME'].tolist() if not dealers_df.empty else [])
        dealer_filter = st.selectbox("Dealer", dealer_options, label_visibility="collapsed")
    
    # Build dealer filter clause (unqualified for single-table queries, qualified for joined queries)
    if dealer_filter and dealer_filter != "All Dealers":
        dealer_val = dealer_filter.replace(chr(39), chr(39)+chr(39))
        dealer_filter_clause = f"AND DEALER_NAME = '{dealer_val}'"
        dealer_filter_clause_f = f"AND f.DEALER_NAME = '{dealer_val}'"  # For queries with f alias (joins)
    else:
        dealer_filter_clause = ""
        dealer_filter_clause_f = ""
    
    with time_col1:
        if st.button("Last 30 Days", key="t30", 
                     type="primary" if st.session_state.time_filter == "Last 30 Days" else "secondary",
                     use_container_width=True):
            st.session_state.time_filter = "Last 30 Days"
            st.session_state.start_date = TODAY - timedelta(days=30)
            st.session_state.end_date = TODAY
            st.rerun()
    
    with time_col2:
        if st.button("QTD", key="tqtd",
                     type="primary" if st.session_state.time_filter == "QTD" else "secondary",
                     use_container_width=True):
            st.session_state.time_filter = "QTD"
            quarter_start_month = ((TODAY.month - 1) // 3) * 3 + 1
            st.session_state.start_date = date(TODAY.year, quarter_start_month, 1)
            st.session_state.end_date = TODAY
            st.rerun()
    
    with time_col3:
        if st.button("YTD", key="tytd",
                     type="primary" if st.session_state.time_filter == "YTD" else "secondary",
                     use_container_width=True):
            st.session_state.time_filter = "YTD"
            st.session_state.start_date = date(TODAY.year, 1, 1)
            st.session_state.end_date = TODAY
            st.rerun()
    
    with time_col4:
        if st.button("Custom", key="tcustom",
                     type="primary" if st.session_state.time_filter == "Custom" else "secondary",
                     use_container_width=True):
            st.session_state.time_filter = "Custom"
    
    start_date = st.session_state.start_date
    end_date = st.session_state.end_date
    date_filter = f"EFFECTIVE_DATE BETWEEN '{start_date}' AND '{end_date}'"
    
    # Previous period for comparison
    days_diff = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days_diff - 1)
    prev_date_filter = f"EFFECTIVE_DATE BETWEEN '{prev_start}' AND '{prev_end}'"
    
    
    if st.session_state.show_insights:
        st.markdown("""
        <div class="insight-content">
            <div class="insight-item"><strong>Revenue Performance:</strong> <span>Strong growth trajectory with 12% increase vs last period</span></div>
            <div class="insight-item"><strong>Top Products:</strong> <span>Premium configurations driving 65% of total revenue</span></div>
            <div class="insight-item"><strong>Dealer Trends:</strong> <span>Enterprise dealers showing 3.2x higher order values</span></div>
            <div class="insight-item"><strong>Growth Opportunity:</strong> <span>45% of standard dealers ready for premium upselling</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    # Fetch KPI Data
    # Current Period
    revenue_current_df = run_query(f"""
        SELECT COALESCE(SUM(TOTAL_AMOUNT), 0) as REVENUE
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
    """)
    
    orders_current_df = run_query(f"""
        SELECT COUNT(DISTINCT ORDER_ID) as COUNT
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
    """)
    
    aov_current_df = run_query(f"""
        WITH orders AS (
            SELECT ORDER_ID, SUM(TOTAL_AMOUNT) as TOTAL_AMOUNT
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
            WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
            GROUP BY ORDER_ID
        )
        SELECT AVG(TOTAL_AMOUNT) as AOV FROM orders
    """)
    
    dealers_current_df = run_query(f"""
        SELECT COUNT(DISTINCT DEALER_ID) as COUNT
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
    """)
    
    products_current_df = run_query(f"""
        SELECT COUNT(DISTINCT PRODUCT_ID) as COUNT
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
    """)
    
    units_current_df = run_query(f"""
        SELECT COALESCE(SUM(QUANTITY), 0) as UNITS
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
    """)
    
    # Previous Period
    revenue_prev_df = run_query(f"""
        SELECT COALESCE(SUM(TOTAL_AMOUNT), 0) as REVENUE
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {prev_date_filter} {dealer_filter_clause}
    """)
    
    orders_prev_df = run_query(f"""
        SELECT COUNT(DISTINCT ORDER_ID) as COUNT
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {prev_date_filter} {dealer_filter_clause}
    """)
    
    aov_prev_df = run_query(f"""
        WITH orders AS (
            SELECT ORDER_ID, SUM(TOTAL_AMOUNT) as TOTAL_AMOUNT
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
            WHERE CURRENT_FLAG = 'Y' AND {prev_date_filter} {dealer_filter_clause}
            GROUP BY ORDER_ID
        )
        SELECT AVG(TOTAL_AMOUNT) as AOV FROM orders
    """)
    
    dealers_prev_df = run_query(f"""
        SELECT COUNT(DISTINCT DEALER_ID) as COUNT
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {prev_date_filter} {dealer_filter_clause}
    """)
    
    products_prev_df = run_query(f"""
        SELECT COUNT(DISTINCT PRODUCT_ID) as COUNT
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {prev_date_filter} {dealer_filter_clause}
    """)
    
    units_prev_df = run_query(f"""
        SELECT COALESCE(SUM(QUANTITY), 0) as UNITS
        FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
        WHERE CURRENT_FLAG = 'Y' AND {prev_date_filter} {dealer_filter_clause}
    """)
    
    # Extract values
    revenue_current = float(revenue_current_df['REVENUE'].iloc[0]) if not revenue_current_df.empty else 0
    revenue_prev = float(revenue_prev_df['REVENUE'].iloc[0]) if not revenue_prev_df.empty else 0
    orders_current = int(orders_current_df['COUNT'].iloc[0]) if not orders_current_df.empty else 0
    orders_prev = int(orders_prev_df['COUNT'].iloc[0]) if not orders_prev_df.empty else 0
    aov_current = float(aov_current_df['AOV'].iloc[0]) if not aov_current_df.empty else 0
    aov_prev = float(aov_prev_df['AOV'].iloc[0]) if not aov_prev_df.empty else 0
    dealers_current = int(dealers_current_df['COUNT'].iloc[0]) if not dealers_current_df.empty else 0
    dealers_prev = int(dealers_prev_df['COUNT'].iloc[0]) if not dealers_prev_df.empty else 0
    products_current = int(products_current_df['COUNT'].iloc[0]) if not products_current_df.empty else 0
    products_prev = int(products_prev_df['COUNT'].iloc[0]) if not products_prev_df.empty else 0
    units_current = int(units_current_df['UNITS'].iloc[0]) if not units_current_df.empty else 0
    units_prev = int(units_prev_df['UNITS'].iloc[0]) if not units_prev_df.empty else 0
    
    # Calculate changes
    revenue_change, revenue_class = format_change(calc_change(revenue_current, revenue_prev))
    orders_change, orders_class = format_change(calc_change(orders_current, orders_prev))
    aov_change, aov_class = format_change(calc_change(aov_current, aov_prev))
    dealers_change, dealers_class = format_change(calc_change(dealers_current, dealers_prev))
    products_change, products_class = format_change(calc_change(products_current, products_prev))
    units_change, units_class = format_change(calc_change(units_current, units_prev))
    
    # KPI Cards Row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5, kpi_col6 = st.columns(6)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="kpi-card kpi-card-green">
            <div class="kpi-label">TOTAL REVENUE</div>
            <div class="kpi-value">${revenue_current/1000000:.1f}M</div>
            <div class="kpi-change {revenue_class}">{revenue_change} vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col2:
        st.markdown(f"""
        <div class="kpi-card kpi-card-purple">
            <div class="kpi-label">TOTAL ORDERS</div>
            <div class="kpi-value">{orders_current:,}</div>
            <div class="kpi-change {orders_class}">{orders_change} vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col3:
        st.markdown(f"""
        <div class="kpi-card kpi-card-cyan">
            <div class="kpi-label">AVERAGE ORDER VALUE</div>
            <div class="kpi-value">${aov_current:,.0f}</div>
            <div class="kpi-change {aov_class}">{aov_change} vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col4:
        st.markdown(f"""
        <div class="kpi-card kpi-card-blue">
            <div class="kpi-label">ACTIVE DEALERS</div>
            <div class="kpi-value">{dealers_current:,}</div>
            <div class="kpi-change {dealers_class}">{dealers_change} vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col5:
        st.markdown(f"""
        <div class="kpi-card kpi-card-yellow">
            <div class="kpi-label">ACTIVE PRODUCTS</div>
            <div class="kpi-value">{products_current:,}</div>
            <div class="kpi-change {products_class}">{products_change} vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col6:
        st.markdown(f"""
        <div class="kpi-card kpi-card-lime">
            <div class="kpi-label">TOTAL UNITS</div>
            <div class="kpi-value">{units_current:,}</div>
            <div class="kpi-change {units_class}">{units_change} vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Content Tabs
    st.markdown('<div class="dashboard-tabs">', unsafe_allow_html=True)
    tab_col1, tab_col2, tab_col3, tab_col4 = st.columns(4)
    
    with tab_col1:
        if st.button("Business Health", key="tab_health",
                     type="primary" if st.session_state.active_tab == "Business Health" else "secondary",
                     use_container_width=True):
            st.session_state.active_tab = "Business Health"
            st.rerun()
    
    with tab_col2:
        if st.button("Dealer Performance", key="tab_dealer",
                     type="primary" if st.session_state.active_tab == "Dealer Performance" else "secondary",
                     use_container_width=True):
            st.session_state.active_tab = "Dealer Performance"
            st.rerun()
    
    with tab_col3:
        if st.button("Configurations", key="tab_config",
                     type="primary" if st.session_state.active_tab == "Configurations" else "secondary",
                     use_container_width=True):
            st.session_state.active_tab = "Configurations"
            st.rerun()
    
    with tab_col4:
        if st.button("Features", key="tab_features",
                     type="primary" if st.session_state.active_tab == "Features" else "secondary",
                     use_container_width=True):
            st.session_state.active_tab = "Features"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tab Content
    if st.session_state.active_tab == "Business Health":
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            with st.container(border=True):
                st.markdown('<div class="chart-title">SALES BY PRODUCT TYPE</div>', unsafe_allow_html=True)
                
                sales_by_type = run_query(f"""
                SELECT 
                    p.PRODUCT_TYPE,
                    COUNT(DISTINCT f.ORDER_ID) as ORDER_COUNT,
                    SUM(f.TOTAL_AMOUNT) as TOTAL_SALES
                FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                JOIN {DATABASE}.{SCHEMA}.DIM_PRODUCT_VW p ON f.PRODUCT_ID = p.PRODUCT_ID AND p.CURRENT_FLAG = 'Y'
                WHERE f.CURRENT_FLAG = 'Y' AND f.{date_filter} {dealer_filter_clause_f}
                GROUP BY p.PRODUCT_TYPE
                ORDER BY TOTAL_SALES DESC
                """)
                
                if not sales_by_type.empty:
                    sales_by_type['SALES_LABEL'] = sales_by_type['TOTAL_SALES'].map(lambda v: f"${v/1000000:.1f}M" if v >= 1000000 else f"${v/1000:.0f}K")
                    base = alt.Chart(sales_by_type).encode(
                        x=alt.X('TOTAL_SALES:Q', title='Total Sales', axis=alt.Axis(format='~s')),
                        y=alt.Y('PRODUCT_TYPE:N', title='', sort='-x'),
                        tooltip=['PRODUCT_TYPE', 'ORDER_COUNT', alt.Tooltip('TOTAL_SALES:Q', format='$,.0f', title='Total Sales')]
                    )
                    bars = base.mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, color='#FDE047')
                    labels = base.mark_text(align='left', baseline='middle', dx=4, color='#111827', fontSize=11).encode(
                        text='SALES_LABEL:N'
                    )
                    chart = (bars + labels).properties(height=300)
                    st.altair_chart(chart, use_container_width=True)
        
        with chart_col2:
            with st.container(border=True):
                st.markdown('<div class="chart-title">ORDER STATUS DISTRIBUTION</div>', unsafe_allow_html=True)
                
                # ORDER STATUS DISTRIBUTION
                order_status = run_query(f"""
                SELECT 
                    ORDER_STATUS,
                    COUNT(DISTINCT ORDER_ID) as ORDER_COUNT
                FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
                GROUP BY ORDER_STATUS
                ORDER BY ORDER_COUNT DESC
                """)
                
                if not order_status.empty:
                    # Calculate total for percentage
                    total_orders = order_status['ORDER_COUNT'].sum()
                    order_status['PERCENTAGE'] = (order_status['ORDER_COUNT'] / total_orders * 100).round(1)
                    # Create label with status and count
                    order_status['LABEL'] = order_status.apply(
                        lambda row: f"{row['ORDER_STATUS']} ({row['ORDER_COUNT']:,})", axis=1
                    )
                    
                    # Get actual status values from data and assign moderately bright colors
                    status_values = order_status['ORDER_STATUS'].tolist()
                    # Moderately bright color palette: medium green, medium yellow, medium blue, medium red, medium purple, medium pink
                    color_palette = ['#4ADE80', '#FBBF24', '#60A5FA', '#F87171', '#A78BFA', '#F472B6']
                    status_colors = alt.Scale(
                        domain=status_values,
                        range=color_palette[:len(status_values)]
                    )
                    
                    # Create donut chart with legend showing formatted labels with counts
                    # Create display version with status + count for legend
                    order_status_display = order_status.copy()
                    order_status_display['STATUS_DISPLAY'] = order_status_display.apply(
                        lambda row: f"{row['ORDER_STATUS']} ({row['ORDER_COUNT']:,})", axis=1
                    )
                    
                    # Update color scale domain to use display labels
                    status_display_values = order_status_display['STATUS_DISPLAY'].tolist()
                    status_display_colors = alt.Scale(
                        domain=status_display_values,
                        range=color_palette[:len(status_display_values)]
                    )
                    
                    # Create the donut chart using STATUS_DISPLAY for color encoding
                    order_status_display['PCT_LABEL'] = order_status_display['PERCENTAGE'].map(lambda v: f"{v:.1f}%")
                    arcs = alt.Chart(order_status_display).mark_arc(innerRadius=50, outerRadius=100).encode(
                        theta=alt.Theta('ORDER_COUNT:Q', stack=True),
                        color=alt.Color('STATUS_DISPLAY:N', scale=status_display_colors, legend=alt.Legend(
                            orient='bottom',
                            title='ORDER STATUS',
                            labelFontSize=11,
                            titleFontSize=12,
                            titleFontWeight='bold',
                            labelLimit=250,
                            direction='horizontal'
                        )),
                        tooltip=[
                            'ORDER_STATUS', 
                            alt.Tooltip('ORDER_COUNT:Q', format=',', title='Orders'),
                            alt.Tooltip('PERCENTAGE:Q', format='.1f', title='Percentage (%)')
                        ]
                    )
                    labels = alt.Chart(order_status_display).mark_text(
                        radius=115, fontSize=12, fontWeight='bold', color='#111827'
                    ).encode(
                        theta=alt.Theta('ORDER_COUNT:Q', stack=True),
                        text='PCT_LABEL:N'
                    )
                    chart = (arcs + labels).properties(height=300)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No order status data available")
        
        # Monthly/Weekly Performance Trends
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            # Determine if we should show monthly or weekly trends
            days_diff = (end_date - start_date).days + 1
            is_monthly_view = days_diff > 35  # More than ~5 weeks, show monthly
            
            if is_monthly_view:
                st.markdown('<div class="chart-title">Monthly Performance Trends</div>', unsafe_allow_html=True)
                
                trend_col1, trend_col2 = st.columns(2)
                
                with trend_col1:
                    st.markdown('<div style="font-weight:600;font-size:14px;margin-bottom:10px;color:#374151;">Total Revenue Trend</div>', unsafe_allow_html=True)
                    
                    monthly_revenue = run_query(f"""
                    SELECT 
                        TO_CHAR(DATE_TRUNC('month', EFFECTIVE_DATE), 'YYYY-MM') AS MONTH_STR,
                        DATE_TRUNC('month', EFFECTIVE_DATE) AS MONTH,
                        SUM(TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                    WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
                    GROUP BY MONTH, MONTH_STR
                    ORDER BY MONTH
                    """)
                    
                    if not monthly_revenue.empty:
                        # Format month names (e.g., "Jan", "Feb", etc.) and ensure chronological order
                        monthly_revenue['MONTH_NAME'] = pd.to_datetime(monthly_revenue['MONTH']).dt.strftime('%b')
                        # Create ordered list for sorting
                        month_order = monthly_revenue['MONTH_NAME'].tolist()
                        
                        chart = alt.Chart(monthly_revenue).mark_area(
                            line={'color': '#4ECDC4', 'strokeWidth': 2},
                            point={'color': '#4ECDC4', 'size': 60},
                            color=alt.Gradient(
                                gradient='linear',
                                stops=[
                                    alt.GradientStop(color='#DBEAFE', offset=0),
                                    alt.GradientStop(color='#BFDBFE', offset=1)
                                ],
                                x1=1, x2=1, y1=1, y2=0
                            )
                        ).encode(
                            x=alt.X('MONTH_NAME:N', title='Month', sort=month_order, axis=alt.Axis(labelAngle=0)),
                            y=alt.Y('REVENUE_M:Q', title='Revenue ($M)'),
                            tooltip=[
                                alt.Tooltip('MONTH_NAME:N', title='Month'),
                                alt.Tooltip('REVENUE_M:Q', format=',.1f', title='Revenue ($M)')
                            ]
                        ).properties(height=250)
                        st.altair_chart(chart, use_container_width=True)
                
                with trend_col2:
                    st.markdown('<div style="font-weight:600;font-size:14px;margin-bottom:10px;color:#374151;">Total Orders Trend</div>', unsafe_allow_html=True)
                    
                    monthly_orders = run_query(f"""
                    SELECT 
                        TO_CHAR(DATE_TRUNC('month', EFFECTIVE_DATE), 'YYYY-MM') AS MONTH_STR,
                        DATE_TRUNC('month', EFFECTIVE_DATE) AS MONTH,
                        COUNT(DISTINCT ORDER_ID) AS ORDERS
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                    WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
                    GROUP BY MONTH, MONTH_STR
                    ORDER BY MONTH
                    """)
                    
                    if not monthly_orders.empty:
                        # Format month names (e.g., "Jan", "Feb", etc.) and ensure chronological order
                        monthly_orders['MONTH_NAME'] = pd.to_datetime(monthly_orders['MONTH']).dt.strftime('%b')
                        # Create ordered list for sorting
                        month_order = monthly_orders['MONTH_NAME'].tolist()
                        
                        chart = alt.Chart(monthly_orders).mark_area(
                            line={'color': '#95E1D3', 'strokeWidth': 2},
                            point={'color': '#95E1D3', 'size': 60},
                            color=alt.Gradient(
                                gradient='linear',
                                stops=[
                                    alt.GradientStop(color='#D1FAE5', offset=0),
                                    alt.GradientStop(color='#A7F3D0', offset=1)
                                ],
                                x1=1, x2=1, y1=1, y2=0
                            )
                        ).encode(
                            x=alt.X('MONTH_NAME:N', title='Month', sort=month_order, axis=alt.Axis(labelAngle=0)),
                            y=alt.Y('ORDERS:Q', title='Orders'),
                            tooltip=[
                                alt.Tooltip('MONTH_NAME:N', title='Month'),
                                alt.Tooltip('ORDERS:Q', format=',', title='Orders')
                            ]
                        ).properties(height=250)
                        st.altair_chart(chart, use_container_width=True)
            else:
                # Weekly view for month or less
                st.markdown('<div class="chart-title">Weekly Performance Trends</div>', unsafe_allow_html=True)
                
                trend_col1, trend_col2 = st.columns(2)
                
                with trend_col1:
                    st.markdown('<div style="font-weight:600;font-size:14px;margin-bottom:10px;color:#374151;">Weekly Revenue Trend</div>', unsafe_allow_html=True)
                    
                    weekly_revenue = run_query(f"""
                    SELECT 
                        DATE_TRUNC('week', EFFECTIVE_DATE) AS WEEK,
                        TO_CHAR(DATE_TRUNC('week', EFFECTIVE_DATE), 'MMM DD') AS WEEK_STR,
                        SUM(TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                    WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
                    GROUP BY WEEK, WEEK_STR
                    ORDER BY WEEK
                    """)
                    
                    if not weekly_revenue.empty:
                        week_order = weekly_revenue['WEEK_STR'].tolist()
                        chart = alt.Chart(weekly_revenue).mark_line(
                            point=True,
                            strokeWidth=3,
                            color='#4ECDC4'
                        ).encode(
                            x=alt.X('WEEK_STR:N', title='Week', sort=week_order, axis=alt.Axis(labelAngle=-45)),
                            y=alt.Y('REVENUE_M:Q', title='Revenue ($M)'),
                            tooltip=[
                                alt.Tooltip('WEEK_STR:N', title='Week'),
                                alt.Tooltip('REVENUE_M:Q', format=',.1f', title='Revenue ($M)')
                            ]
                        ).properties(height=250)
                        st.altair_chart(chart, use_container_width=True)
                
                with trend_col2:
                    st.markdown('<div style="font-weight:600;font-size:14px;margin-bottom:10px;color:#374151;">Weekly Orders Trend</div>', unsafe_allow_html=True)
                    
                    weekly_orders = run_query(f"""
                    SELECT 
                        DATE_TRUNC('week', EFFECTIVE_DATE) AS WEEK,
                        TO_CHAR(DATE_TRUNC('week', EFFECTIVE_DATE), 'MMM DD') AS WEEK_STR,
                        COUNT(DISTINCT ORDER_ID) AS ORDERS
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                    WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
                    GROUP BY WEEK, WEEK_STR
                    ORDER BY WEEK
                    """)
                    
                    if not weekly_orders.empty:
                        week_order = weekly_orders['WEEK_STR'].tolist()
                        chart = alt.Chart(weekly_orders).mark_line(
                            point=True,
                            strokeWidth=3,
                            color='#95E1D3'
                        ).encode(
                            x=alt.X('WEEK_STR:N', title='Week', sort=week_order, axis=alt.Axis(labelAngle=-45)),
                            y=alt.Y('ORDERS:Q', title='Orders'),
                            tooltip=[
                                alt.Tooltip('WEEK_STR:N', title='Week'),
                                alt.Tooltip('ORDERS:Q', format=',', title='Orders')
                            ]
                        ).properties(height=250)
                        st.altair_chart(chart, use_container_width=True)
        
        # Product Category Performance (Full Width)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="chart-title">Product Category Performance</div>', unsafe_allow_html=True)
            
            # Get dealer performance data for product categories
            category_performance = run_query(f"""
                SELECT 
                    DEALER_NAME,
                    SUM(TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
                FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
                GROUP BY DEALER_NAME
                ORDER BY REVENUE_M DESC
                LIMIT 10
            """)
            
            if not category_performance.empty:
                max_revenue = category_performance['REVENUE_M'].max()
                
                # Build HTML for custom progress bar visualization
                bar_html = ""
                for _, row in category_performance.iterrows():
                    dealer_name = row['DEALER_NAME']
                    revenue = row['REVENUE_M']
                    percentage = (revenue / max_revenue) * 100 if max_revenue > 0 else 0
                    
                    bar_html += f"""
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="font-size: 14px; font-weight: 500; color: #1f2937;">{dealer_name}</span>
                            <span style="font-size: 14px; font-weight: 600; color: #1f2937;">${revenue:.2f}M</span>
                        </div>
                        <div style="background: #e5e7eb; border-radius: 6px; height: 12px; overflow: hidden;">
                            <div style="background: #4ADE80; height: 100%; width: {percentage:.1f}%; border-radius: 6px;"></div>
                        </div>
                    </div>
                    """
                
                st.markdown(bar_html, unsafe_allow_html=True)
            else:
                st.info("No data available for the selected period")
    
    elif st.session_state.active_tab == "Dealer Performance":
        # Bubble chart: Total Orders vs Total Revenue, colored by Dealer Type, sized by Avg Order Value
        dealer_perf_bubble = run_query(f"""
            SELECT 
                f.DEALER_NAME,
                d.DEALER_TYPE,
                COUNT(DISTINCT f.ORDER_ID) AS ORDERS,
                SUM(f.TOTAL_AMOUNT) / 1000000.0 AS REVENUE_MILLIONS,
                SUM(f.TOTAL_AMOUNT) / NULLIF(COUNT(DISTINCT f.ORDER_ID), 0) AS AVG_ORDER_VALUE,
                COUNT(DISTINCT f.PRODUCT_ID) AS PRODUCT_COUNT
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
            JOIN {DATABASE}.{SCHEMA}.DIM_DEALER_VW d ON f.DEALER_ID = d.DEALER_ID AND d.CURRENT_FLAG = 'Y'
            WHERE f.CURRENT_FLAG = 'Y' AND f.{date_filter} {dealer_filter_clause_f}
            GROUP BY f.DEALER_NAME, d.DEALER_TYPE
            HAVING COUNT(DISTINCT f.ORDER_ID) > 0
            ORDER BY REVENUE_MILLIONS DESC
        """)
        
        # Unique Products by dealer
        unique_products = run_query(f"""
            SELECT 
                f.DEALER_NAME,
                COUNT(DISTINCT f.PRODUCT_ID) AS UNIQUE_PRODUCTS
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
            WHERE f.CURRENT_FLAG = 'Y' AND f.{date_filter} {dealer_filter_clause_f}
            GROUP BY f.DEALER_NAME
            ORDER BY UNIQUE_PRODUCTS DESC
            LIMIT 15
        """)
        
        # Total Revenue by dealer
        revenue_by_dealer = run_query(f"""
            SELECT 
                DEALER_NAME,
                SUM(TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
            WHERE CURRENT_FLAG = 'Y' AND {date_filter} {dealer_filter_clause}
            GROUP BY DEALER_NAME
            ORDER BY REVENUE_M DESC
            LIMIT 15
        """)
        
        # Dealer Type distribution
        dealer_type_dist = run_query(f"""
            SELECT 
                d.DEALER_TYPE,
                COUNT(DISTINCT f.DEALER_ID) AS DEALER_COUNT,
                SUM(f.TOTAL_AMOUNT) AS REVENUE
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
            JOIN {DATABASE}.{SCHEMA}.DIM_DEALER_VW d ON f.DEALER_ID = d.DEALER_ID AND d.CURRENT_FLAG = 'Y'
            WHERE f.CURRENT_FLAG = 'Y' AND f.{date_filter} {dealer_filter_clause_f}
            GROUP BY d.DEALER_TYPE
        """)
        
        dealer_row1_col1, dealer_row1_col2 = st.columns([3, 2])
        
        with dealer_row1_col1:
            with st.container(border=True):
                st.markdown('<div class="chart-title">Dealer Performance</div>', unsafe_allow_html=True)
                
                if not dealer_perf_bubble.empty:
                    # Distinct medium-light colors per dealer type
                    unique_types = list(dealer_perf_bubble['DEALER_TYPE'].dropna().unique())
                    dealer_palette = ['#4ADE80', '#FBBF24', '#60A5FA', '#F87171', '#A78BFA', '#F472B6']  # Business Health colors
                    color_scale = alt.Scale(
                        domain=unique_types,
                        range=dealer_palette[: len(unique_types)]
                    )
                    
                    chart = alt.Chart(dealer_perf_bubble).mark_circle(size=150, opacity=0.7).encode(
                        x=alt.X('ORDERS:Q', title='Total Orders', axis=alt.Axis(format=',.0f'),
                               scale=alt.Scale(zero=False)),
                        y=alt.Y('REVENUE_MILLIONS:Q', title='Total Revenue (Millions $)',
                               axis=alt.Axis(format=',.0f'), scale=alt.Scale(zero=False)),
                        color=alt.Color('DEALER_TYPE:N', title='Dealer Type',
                            scale=color_scale,
                            legend=alt.Legend(orient='bottom', direction='horizontal')),
                        size=alt.Size('AVG_ORDER_VALUE:Q', title='Avg Order Value',
                            scale=alt.Scale(range=[100, 1000]),
                            legend=alt.Legend(format='$,.0f', orient='bottom')),
                        tooltip=[
                            alt.Tooltip('DEALER_NAME:N', title='Dealer'),
                            alt.Tooltip('DEALER_TYPE:N', title='Type'),
                            alt.Tooltip('ORDERS:Q', title='Orders', format=','),
                            alt.Tooltip('REVENUE_MILLIONS:Q', title='Revenue ($M)', format=',.0f'),
                            alt.Tooltip('AVG_ORDER_VALUE:Q', title='Avg Order', format='$,.0f'),
                            alt.Tooltip('PRODUCT_COUNT:Q', title='Products', format=',')
                        ]
                    ).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No dealer performance data available")
        
        with dealer_row1_col2:
            with st.container(border=True):
                st.markdown('<div class="chart-title">Revenue by Dealer Type</div>', unsafe_allow_html=True)
                
                if not dealer_type_dist.empty:
                    # Distinct medium-light colors per dealer type (match bubble chart)
                    unique_types = list(dealer_type_dist['DEALER_TYPE'].dropna().unique())
                    dealer_palette = ['#4ADE80', '#FBBF24', '#60A5FA', '#F87171', '#A78BFA', '#F472B6']  # Business Health colors
                    color_scale_donut = alt.Scale(
                        domain=unique_types,
                        range=dealer_palette[: len(unique_types)]
                    )
                    total_dealers = dealer_type_dist['DEALER_COUNT'].sum()
                    dealer_type_dist['PCT'] = (dealer_type_dist['DEALER_COUNT'] / total_dealers * 100).round(1)
                    dealer_type_dist['PCT_LABEL'] = dealer_type_dist['PCT'].map(lambda v: f"{v:.1f}%")
                    
                    arcs = alt.Chart(dealer_type_dist).mark_arc(innerRadius=60, outerRadius=120).encode(
                        theta=alt.Theta('DEALER_COUNT:Q', stack=True),
                        color=alt.Color(
                            'DEALER_TYPE:N',
                            scale=color_scale_donut,
                            legend=alt.Legend(title='Dealer Type', orient='bottom', direction='horizontal')
                        ),
                        tooltip=[
                            'DEALER_TYPE',
                            alt.Tooltip('DEALER_COUNT:Q', format=',', title='Dealers'),
                            alt.Tooltip('PCT:Q', format='.1f', title='Share (%)'),
                            alt.Tooltip('REVENUE:Q', format='$,.0f', title='Revenue')
                        ]
                    )
                    labels = alt.Chart(dealer_type_dist).mark_text(
                        radius=135, fontSize=12, fontWeight='bold', color='#111827'
                    ).encode(
                        theta=alt.Theta('DEALER_COUNT:Q', stack=True),
                        text='PCT_LABEL:N'
                    )
                    chart = (arcs + labels).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No dealer type data available")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        dealer_row2_col1, dealer_row2_col2 = st.columns(2)
        
        with dealer_row2_col1:
            with st.container(border=True):
                st.markdown('<div class="chart-title">Unique Products by Dealer</div>', unsafe_allow_html=True)
                
                if not unique_products.empty:
                    # Medium light blue gradient
                    max_products = unique_products['UNIQUE_PRODUCTS'].max()
                    base = alt.Chart(unique_products).encode(
                        x=alt.X('UNIQUE_PRODUCTS:Q', title='Unique Products'),
                        y=alt.Y('DEALER_NAME:N', title='', sort='-x'),
                        tooltip=['DEALER_NAME', alt.Tooltip('UNIQUE_PRODUCTS:Q', format=',', title='Unique Products')]
                    )
                    bars = base.mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8).encode(
                        color=alt.Color('UNIQUE_PRODUCTS:Q', 
                                      scale=alt.Scale(domain=[0, max_products], range=['#DBEAFE', '#60A5FA']),
                                      legend=None)
                    )
                    labels = base.mark_text(align='left', baseline='middle', dx=4, color='#111827', fontSize=11).encode(
                        text=alt.Text('UNIQUE_PRODUCTS:Q', format=',')
                    )
                    chart = (bars + labels).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No unique products data available")
        
        with dealer_row2_col2:
            with st.container(border=True):
                st.markdown('<div class="chart-title">Total Revenue (Millions $) by Dealer</div>', unsafe_allow_html=True)
                
                if not revenue_by_dealer.empty:
                    # Medium light blue gradient
                    max_revenue = revenue_by_dealer['REVENUE_M'].max()
                    revenue_by_dealer['REV_LABEL'] = revenue_by_dealer['REVENUE_M'].map(lambda v: f"{v:.1f}M")
                    base = alt.Chart(revenue_by_dealer).encode(
                        x=alt.X('REVENUE_M:Q', title='Total Revenue (Millions $)'),
                        y=alt.Y('DEALER_NAME:N', title='', sort='-x'),
                        tooltip=['DEALER_NAME', alt.Tooltip('REVENUE_M:Q', format=',.1f', title='Revenue ($M)')]
                    )
                    bars = base.mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8).encode(
                        color=alt.Color('REVENUE_M:Q', 
                                      scale=alt.Scale(domain=[0, max_revenue], range=['#DBEAFE', '#60A5FA']),
                                      legend=None)
                    )
                    labels = base.mark_text(align='left', baseline='middle', dx=4, color='#111827', fontSize=11).encode(
                        text='REV_LABEL:N'
                    )
                    chart = (bars + labels).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No revenue data available")
    
    elif st.session_state.active_tab == "Configurations":
        # 1. Revenue By Config
        config_revenue = run_query(f"""
            SELECT 
                CONFIG_NAME,
                SUM(TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
            WHERE CURRENT_FLAG = 'Y' AND CONFIG_NAME IS NOT NULL AND {date_filter} {dealer_filter_clause}
            GROUP BY CONFIG_NAME
            ORDER BY REVENUE_M DESC
        """)
        
        # 2. Average Order Value By Config
        avg_config_value = run_query(f"""
            SELECT 
                CONFIG_NAME,
                SUM(TOTAL_AMOUNT) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) AS AVG_ORDER_VALUE
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
            WHERE CURRENT_FLAG = 'Y' AND CONFIG_NAME IS NOT NULL AND {date_filter} {dealer_filter_clause}
            GROUP BY CONFIG_NAME
            ORDER BY AVG_ORDER_VALUE DESC
        """)
        
        # 3. Configuration preference by dealer type (config name vs dealer type)
        config_by_dealer_type = run_query(f"""
            SELECT 
                d.DEALER_TYPE,
                f.CONFIG_NAME,
                COUNT(DISTINCT f.ORDER_ID) AS ORDER_COUNT,
                SUM(f.TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
            JOIN {DATABASE}.{SCHEMA}.DIM_DEALER_VW d ON f.DEALER_ID = d.DEALER_ID AND d.CURRENT_FLAG = 'Y'
            WHERE f.CURRENT_FLAG = 'Y' AND f.CONFIG_NAME IS NOT NULL AND f.{date_filter} {dealer_filter_clause_f}
            GROUP BY d.DEALER_TYPE, f.CONFIG_NAME
            ORDER BY d.DEALER_TYPE, REVENUE_M DESC
        """)
        
        config_row1_col1, config_row1_col2 = st.columns(2)
        
        with config_row1_col1:
            with st.container(border=True):
                st.markdown('<div class="chart-title">Revenue By Config</div>', unsafe_allow_html=True)
                
                if not config_revenue.empty:
                    config_revenue['REV_LABEL'] = config_revenue['REVENUE_M'].map(lambda v: f"{v:.1f}M")
                    base = alt.Chart(config_revenue).encode(
                        x=alt.X('REVENUE_M:Q', title='Revenue ($M)'),
                        y=alt.Y('CONFIG_NAME:N', title='', sort='-x'),
                        tooltip=['CONFIG_NAME', alt.Tooltip('REVENUE_M:Q', format=',.1f', title='Revenue ($M)')]
                    )
                    bars = base.mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, color='#60A5FA')
                    labels = base.mark_text(align='left', baseline='middle', dx=4, color='#111827', fontSize=11).encode(
                        text='REV_LABEL:N'
                    )
                    chart = (bars + labels).properties(height=360)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No configuration revenue data available")
        
        with config_row1_col2:
            with st.container(border=True):
                st.markdown('<div class="chart-title">Average Order Value By Config</div>', unsafe_allow_html=True)
                
                if not avg_config_value.empty:
                    avg_config_value['AOV_LABEL'] = avg_config_value['AVG_ORDER_VALUE'].map(lambda v: f"${v/1000:.0f}K" if v >= 1000 else f"${v:.0f}")
                    base = alt.Chart(avg_config_value).encode(
                        x=alt.X('AVG_ORDER_VALUE:Q', title='Average Order Value ($)', axis=alt.Axis(format='$,.0f')),
                        y=alt.Y('CONFIG_NAME:N', title='', sort='-x'),
                        tooltip=['CONFIG_NAME', alt.Tooltip('AVG_ORDER_VALUE:Q', format='$,.0f', title='Avg Order Value')]
                    )
                    bars = base.mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, color='#4ADE80')
                    labels = base.mark_text(align='left', baseline='middle', dx=4, color='#111827', fontSize=11).encode(
                        text='AOV_LABEL:N'
                    )
                    chart = (bars + labels).properties(height=360)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No average order value data available")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown('<div class="chart-title">Configuration Preference by Dealer Type</div>', unsafe_allow_html=True)
            
            if not config_by_dealer_type.empty:
                # Distinct medium-light colors per dealer type
                unique_types = list(config_by_dealer_type['DEALER_TYPE'].dropna().unique())
                dealer_palette = ['#4ADE80', '#FBBF24', '#60A5FA', '#F87171', '#A78BFA', '#F472B6']  # Business Health colors
                color_scale = alt.Scale(
                    domain=unique_types,
                    range=dealer_palette[:len(unique_types)]
                )
                
                # Get top configs for better visualization
                top_configs = config_by_dealer_type.groupby('CONFIG_NAME')['REVENUE_M'].sum().nlargest(10).index.tolist()
                filtered_config = config_by_dealer_type[config_by_dealer_type['CONFIG_NAME'].isin(top_configs)]
                
                filtered_config['REV_LABEL'] = filtered_config['REVENUE_M'].map(lambda v: f"{v:.1f}M")
                base = alt.Chart(filtered_config).encode(
                    x=alt.X('CONFIG_NAME:N', title='Config Name', sort='-y'),
                    y=alt.Y('REVENUE_M:Q', title='Revenue ($M)'),
                    color=alt.Color('DEALER_TYPE:N', scale=color_scale, legend=alt.Legend(title='Dealer Type', orient='bottom', direction='horizontal')),
                    xOffset='DEALER_TYPE:N',
                    tooltip=['DEALER_TYPE', 'CONFIG_NAME', alt.Tooltip('REVENUE_M:Q', format=',.1f', title='Revenue ($M)'), alt.Tooltip('ORDER_COUNT:Q', format=',', title='Orders')]
                )
                bars = base.mark_bar()
                labels = base.mark_text(align='center', baseline='bottom', dy=-3, color='#111827', fontSize=10).encode(
                    text='REV_LABEL:N'
                )
                chart = (bars + labels).properties(height=400)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No configuration preference by dealer type data available")
    
    elif st.session_state.active_tab == "Features":
        # 1. Top 10 features by revenue
        top_features = run_query(f"""
            SELECT
                fe.FEATURE_NAME,
                SUM(f.TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
            LEFT JOIN {DATABASE}.{SCHEMA}.DIM_FEATURE_VW fe ON f.FEATURE_ID = fe.FEATURE_ID AND fe.CURRENT_FLAG = 'Y'
            WHERE f.CURRENT_FLAG = 'Y' AND f.FEATURE_ID IS NOT NULL AND f.{date_filter} {dealer_filter_clause_f}
            GROUP BY fe.FEATURE_NAME
            ORDER BY REVENUE_M DESC
            LIMIT 10
        """)
        
        # 2. Features by revenue based on dealer type
        features_by_dealer_type = run_query(f"""
            SELECT 
                d.DEALER_TYPE,
                fe.FEATURE_NAME,
                SUM(f.TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
            JOIN {DATABASE}.{SCHEMA}.DIM_DEALER_VW d ON f.DEALER_ID = d.DEALER_ID AND d.CURRENT_FLAG = 'Y'
            LEFT JOIN {DATABASE}.{SCHEMA}.DIM_FEATURE_VW fe ON f.FEATURE_ID = fe.FEATURE_ID AND fe.CURRENT_FLAG = 'Y'
            WHERE f.CURRENT_FLAG = 'Y' AND f.FEATURE_ID IS NOT NULL AND fe.FEATURE_NAME IS NOT NULL AND f.{date_filter} {dealer_filter_clause_f}
            GROUP BY d.DEALER_TYPE, fe.FEATURE_NAME
            ORDER BY REVENUE_M DESC
        """)
        
        # 3. Features by revenue based on product type
        features_by_product_type = run_query(f"""
            SELECT 
                p.PRODUCT_TYPE,
                fe.FEATURE_NAME,
                SUM(f.TOTAL_AMOUNT) / 1000000.0 AS REVENUE_M
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
            JOIN {DATABASE}.{SCHEMA}.DIM_PRODUCT_VW p ON f.PRODUCT_ID = p.PRODUCT_ID AND p.CURRENT_FLAG = 'Y'
            LEFT JOIN {DATABASE}.{SCHEMA}.DIM_FEATURE_VW fe ON f.FEATURE_ID = fe.FEATURE_ID AND fe.CURRENT_FLAG = 'Y'
            WHERE f.CURRENT_FLAG = 'Y' AND f.FEATURE_ID IS NOT NULL AND p.PRODUCT_TYPE IS NOT NULL AND fe.FEATURE_NAME IS NOT NULL AND f.{date_filter} {dealer_filter_clause_f}
            GROUP BY p.PRODUCT_TYPE, fe.FEATURE_NAME
            ORDER BY REVENUE_M DESC
        """)
        
        features_row1_col1, features_row1_col2 = st.columns(2)
        
        with features_row1_col1:
            with st.container(border=True):
                st.markdown('<div class="chart-title">Top 10 Features by Revenue</div>', unsafe_allow_html=True)
                
                if not top_features.empty:
                    # Use feature name if available, otherwise feature ID
                    top_features['DISPLAY_NAME'] = top_features.apply(
                        lambda row: row['FEATURE_NAME'] if pd.notna(row['FEATURE_NAME']) and row['FEATURE_NAME'] else row['FEATURE_ID'], 
                        axis=1
                    )
                    top_features['REVENUE_LABEL'] = top_features['REVENUE_M'].map(lambda v: f"${v:.2f}M")
                    base = alt.Chart(top_features).encode(
                        x=alt.X('REVENUE_M:Q', title='Revenue ($M)'),
                        y=alt.Y('DISPLAY_NAME:N', title='', sort='-x'),
                        tooltip=['DISPLAY_NAME', alt.Tooltip('REVENUE_M:Q', format=',.2f', title='Revenue ($M)')]
                    )
                    bars = base.mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, color='#60A5FA')
                    labels = base.mark_text(
                        align='left',
                        baseline='middle',
                        dx=4,
                        color='#111827',
                        fontSize=11
                    ).encode(text='REVENUE_LABEL:N')
                    chart = (bars + labels).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No features revenue data available")
        
        with features_row1_col2:
            with st.container(border=True):
                st.markdown('<div class="chart-title">Feature Revenue By Dealer Type</div>', unsafe_allow_html=True)
                
                if not features_by_dealer_type.empty:
                    # Get top 10 feature names by total revenue
                    top_feature_names = features_by_dealer_type.groupby('FEATURE_NAME')['REVENUE_M'].sum().nlargest(10).index.tolist()
                    filtered_features = features_by_dealer_type[features_by_dealer_type['FEATURE_NAME'].isin(top_feature_names)]
                    
                    # Grouped horizontal bar chart: different color per dealer type
                    unique_dealer_types = filtered_features['DEALER_TYPE'].dropna().unique()
                    dealer_type_colors = ['#4ADE80', '#FBBF24', '#60A5FA', '#F87171', '#A78BFA', '#F472B6']
                    color_scale_dealer = alt.Scale(domain=list(unique_dealer_types), range=dealer_type_colors[:len(unique_dealer_types)])
                    
                    filtered_features['REV_LABEL'] = filtered_features['REVENUE_M'].map(lambda v: f"${v:.2f}M")
                    base = alt.Chart(filtered_features).encode(
                        x=alt.X('REVENUE_M:Q', title='Revenue ($M)'),
                        y=alt.Y('FEATURE_NAME:N', title='Feature', sort='-x'),
                        color=alt.Color('DEALER_TYPE:N', scale=color_scale_dealer, legend=alt.Legend(title='Dealer Type', orient='bottom', direction='horizontal')),
                        yOffset='DEALER_TYPE:N',
                        tooltip=['DEALER_TYPE', 'FEATURE_NAME', alt.Tooltip('REVENUE_M:Q', format=',.2f', title='Revenue ($M)')]
                    )
                    bars = base.mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
                    labels = base.mark_text(
                        align='left',
                        baseline='middle',
                        dx=4,
                        color='#111827',
                        fontSize=10
                    ).encode(text='REV_LABEL:N')
                    chart = (bars + labels).properties(height=400)
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No features by dealer type data available")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.markdown('<div class="chart-title">Feature Revenue By Product Type</div>', unsafe_allow_html=True)
            
            if not features_by_product_type.empty:
                # Get top 10 feature names by total revenue
                top_feature_names_pt = features_by_product_type.groupby('FEATURE_NAME')['REVENUE_M'].sum().nlargest(10).index.tolist()
                filtered_features_pt = features_by_product_type[features_by_product_type['FEATURE_NAME'].isin(top_feature_names_pt)]
                
                # Grouped horizontal bar chart: different color per product type
                unique_product_types = filtered_features_pt['PRODUCT_TYPE'].dropna().unique()
                product_type_colors = ['#4ADE80', '#FBBF24', '#60A5FA', '#F87171', '#A78BFA', '#F472B6']
                color_scale_product = alt.Scale(domain=list(unique_product_types), range=product_type_colors[:len(unique_product_types)])
                
                filtered_features_pt['REV_LABEL'] = filtered_features_pt['REVENUE_M'].map(lambda v: f"${v:.2f}M")
                base = alt.Chart(filtered_features_pt).encode(
                    x=alt.X('REVENUE_M:Q', title='Revenue ($M)'),
                    y=alt.Y('FEATURE_NAME:N', title='Feature', sort='-x'),
                    color=alt.Color('PRODUCT_TYPE:N', scale=color_scale_product, legend=alt.Legend(title='Product Type', orient='bottom', direction='horizontal')),
                    yOffset='PRODUCT_TYPE:N',
                    tooltip=['PRODUCT_TYPE', 'FEATURE_NAME', alt.Tooltip('REVENUE_M:Q', format=',.2f', title='Revenue ($M)')]
                )
                bars = base.mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
                labels = base.mark_text(
                    align='left',
                    baseline='middle',
                    dx=4,
                    color='#111827',
                    fontSize=10
                ).encode(text='REV_LABEL:N')
                chart = (bars + labels).properties(height=400)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No features by product type data available")

# ============== GENIE PAGE ==============
elif st.session_state.current_page == "Genie":

    # run_df alias so procureIQ pattern works in OrderLens
    def run_df(sql: str) -> pd.DataFrame:
        return run_query(sql)

    def _cortex_complete_prescriptive_from_dfs(dfs, question, context_text=""):
        """Call Cortex to generate prescriptive from a list of dataframes."""
        data_parts = []
        for df in dfs:
            if df is None or df.empty:
                continue
            try:
                data_parts.append(df.head(40).to_string(index=False, max_colwidth=40))
            except Exception:
                continue
        if not data_parts:
            return ""
        data_str = "\n---\n".join(data_parts)
        if len(data_str) > 12000:
            data_str = data_str[:12000] + "\n...(truncated)"
        prompt = (
            "You are a sales & operations analyst. Given this data, provide 4-5 specific prescriptive "
            "recommendations with concrete actions. Cite actual names, numbers, percentages. "
            "Use • bullet points. Be concise.\n\n"
            f"Question: {question}\n"
        )
        if context_text:
            prompt += f"Context: {context_text[:500]}\n"
        prompt += f"\nData:\n{data_str}"
        try:
            result = session.sql(
                "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS RESPONSE",
                params=[CORTEX_PRESCRIPTIVE_MODEL, prompt]
            ).to_pandas()
            if not result.empty and "RESPONSE" in result.columns:
                raw = result.at[0, "RESPONSE"] or ""
                if raw.strip().startswith("{"):
                    try:
                        parsed = json.loads(raw.strip())
                        text = (parsed.get("choices", [{}])[0].get("messages") or
                                parsed.get("choices", [{}])[0].get("message", {}).get("content", "") or
                                raw).strip()
                        if text and len(text) > 20:
                            return text
                    except Exception:
                        pass
                elif raw.strip() and len(raw.strip()) > 20:
                    return raw.strip()
        except Exception:
            pass
        return ""

    # ── One-time initialisation per browser session ──────────────────────────
    if not st.session_state.get("genie_cache_init"):
        try:
            st.session_state.genie_cache = GenieQueryCache(session)
        except Exception:
            st.session_state.genie_cache = None
        st.session_state.genie_cache_init = True

    if not st.session_state.get("chat_persist_init"):
        try:
            st.session_state.chat_persistence = GenieChatPersistence(session)
        except Exception as _pe:
            st.session_state.chat_persistence = None
            st.session_state["_chat_persist_error"] = str(_pe)
        st.session_state.chat_persist_init = True

    # ── YAML auto-sync (once per session) ────────────────────────────────────
    if not st.session_state.get("yaml_sync_done"):
        try:
            _yaml_sync = run_yaml_auto_update(session)
            st.session_state["yaml_sync_result"] = _yaml_sync
        except Exception as _ye:
            st.session_state["yaml_sync_result"] = {
                "status": "error", "added": [], "message": str(_ye)[:200]
            }
        st.session_state["yaml_sync_done"] = True

    if not st.session_state.get("genie_session_id"):
        st.session_state.genie_session_id    = str(uuid.uuid4())
        st.session_state.genie_session_label = "Chat on " + datetime.now().strftime("%b %d %H:%M")

    # Memory: build once, rebuild every 10 messages
    _cur_q  = len([m for m in st.session_state.genie_messages if m.get("role") == "user"])
    _last_q = st.session_state.get("_mem_last_q_count", -1)
    _need_mem = (
        not st.session_state.get("genie_memory_built")
        or (_cur_q > 0 and _cur_q != _last_q and _cur_q % 10 == 0)
    )
    if _need_mem:
        try:
            st.session_state.genie_memory = GenieLongTermMemory(session)
        except Exception:
            if not st.session_state.get("genie_memory"):
                st.session_state.genie_memory = None
        st.session_state.genie_memory_built  = True
        st.session_state._mem_last_q_count   = _cur_q

    # ── Quick tile definitions ───────────────────────────────────────────────
    _BAR_SVG = '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="4" y="14" width="4" height="6" rx="1" fill="white"/><rect x="10" y="10" width="4" height="10" rx="1" fill="white"/><rect x="16" y="6" width="4" height="14" rx="1" fill="white"/></svg>'''
    _DLR_SVG = '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="9" cy="7" r="3" stroke="white" stroke-width="1.5" fill="none"/><path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" stroke="white" stroke-width="1.5" fill="none"/><rect x="14" y="8" width="8" height="2" rx="0.5" fill="white"/><rect x="14" y="12" width="6" height="2" rx="0.5" fill="white"/><rect x="14" y="16" width="8" height="2" rx="0.5" fill="white"/></svg>'''
    _PRD_SVG = '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 3h8l5 5v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z" stroke="white" stroke-width="1.5" fill="none"/><line x1="7" y1="9" x2="17" y2="9" stroke="white" stroke-width="1.5"/><line x1="7" y1="13" x2="15" y2="13" stroke="white" stroke-width="1.5"/></svg>'''
    _ORD_SVG = '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="white" stroke-width="1.5" fill="none"/><path d="M12 6v6l4 2" stroke="white" stroke-width="1.5" stroke-linecap="round"/></svg>'''

    QUICK_ANALYSES = {
        "revenue_overview":    {"title": "Revenue Overview",    "icon_svg": _BAR_SVG, "desc": "Track total revenue, monthly trends and major changes",          "question": "Show me total revenue YTD, monthly trends, and top 5 dealers"},
        "dealer_analysis":     {"title": "Dealer Analysis",     "icon_svg": _DLR_SVG, "desc": "Understand dealer-wise revenue, concentration, and dependency",  "question": "Analyze dealer concentration and dependency"},
        "product_performance": {"title": "Product Performance", "icon_svg": _PRD_SVG, "desc": "Identify top products, revenue, and quantity trends",            "question": "Show top products by revenue and quantity"},
        "order_status":        {"title": "Order Status",        "icon_svg": _ORD_SVG, "desc": "See order status distribution, fulfillment, and bottlenecks",    "question": "Show order status distribution by count and revenue"},
    }

    DECISION_SUPPORT_INSTRUCTION = (
        "Do NOT start with 'This is our interpretation of your question.' "
        "Respond with exactly THREE sections in this order: "
        "(1) **Descriptive**: What the data shows with specific numbers and dealer/product names. "
        "For YES/NO questions start with a clear Yes or No first. "
        "(2) **Prescriptive**: 3-5 SPECIFIC recommended actions with exact findings and numbers. "
        "(3) **Predictive**: A short 30-90 day forecast tied to current metrics. "
        "State assumptions and give a confidence level (Low/Medium/High). "
        "Quantify likely impact where possible (e.g. estimated revenue change). "
        "NEVER use vague phrases like 'review the data below' without citing specific numbers. "
        "Answer the following question:\n\n"
    )

    def call_cortex_analyst(query_text: str, conversation_history: list = None):
        try:
            _mem = st.session_state.get("genie_memory")
            _mem_prefix = _mem.get_prefix() if (_mem and _mem.count > 0) else ""
            augmented = _mem_prefix + DECISION_SUPPORT_INSTRUCTION + (query_text or "").strip()
            messages  = []
            if conversation_history:
                _exp, _ok = "user", True
                for _t in conversation_history:
                    if _t.get("role") != _exp:
                        _ok = False; break
                    _exp = "analyst" if _exp == "user" else "user"
                if _ok and conversation_history[0].get("role") == "user":
                    messages = list(conversation_history)
            messages.append({"role": "user", "content": [{"type": "text", "text": augmented}]})
            resp = _snowflake.send_snow_api_request(
                "POST", "/api/v2/cortex/analyst/message",
                {"Content-Type": "application/json"}, {},
                {"messages": messages, "semantic_model_file": f"@{FULLPATH}/{FILE}"},
                None, 60000,
            )
            status = resp.get("status", 500)
            if status >= 400:
                return {"error": f"HTTP {status}: {resp.get('content','')}"}
            return json.loads(resp.get("content", "{}"))
        except Exception as e:
            return {"error": str(e)}

    def process_genie_query(query: str, analysis_type: str = "custom"):
        import time as _time

        st.session_state.genie_messages.append({
            "role": "user", "content": query,
            "timestamp": pd.Timestamp.now(), "response": None,
        })

        _cache = st.session_state.get("genie_cache")
        _t0    = _time.time()

        _followup_signals = {"them", "those", "their", "it", "same", "above",
                             "previous", "that", "these", "which one", "how about",
                             "what about", "and", "also"}
        _q_words       = set(query.lower().split())
        _is_contextual = bool(_q_words & _followup_signals) and len(query.split()) < 8

        _conv_history      = []
        _prior_user_msgs   = [m for m in st.session_state.genie_messages[:-1] if m.get("role") == "user"]
        _is_followup       = len(_prior_user_msgs) > 0

        cached_resp = None
        if _cache and not _is_contextual:
            cached_resp = _cache.get(query)

        from_cache = cached_resp is not None and _cache._is_real(cached_resp)

        if from_cache:
            response = cached_resp
            response["cache_fetch_time_ms"] = (_time.time() - _t0) * 1000
        else:
            if _is_followup:
                _all_prev = st.session_state.genie_messages[:-1]
                _pairs, _i = [], 0
                while _i < len(_all_prev) - 1:
                    _um, _am = _all_prev[_i], _all_prev[_i + 1]
                    if _um.get("role") == "user" and _am.get("role") == "assistant":
                        _u_txt   = (_um.get("content") or "").strip()
                        _prev_resp = _am.get("response")
                        _a_txt = ""
                        if isinstance(_prev_resp, dict):
                            _blocks = _prev_resp.get("message", {}).get("content", [])
                            _a_txt = " ".join(b.get("text","") for b in _blocks if b.get("type")=="text").strip()
                        if not _a_txt:
                            _a_txt = (_am.get("content") or "").strip()
                        if _u_txt and _a_txt:
                            _pairs.append((_u_txt[:1500], _a_txt[:1500]))
                        _i += 2
                    else:
                        _i += 1
                for _u_txt, _a_txt in _pairs[-4:]:
                    _conv_history.append({"role": "user",     "content": [{"type": "text", "text": _u_txt}]})
                    _conv_history.append({"role": "analyst",  "content": [{"type": "text", "text": _a_txt}]})

            response = call_cortex_analyst(query, conversation_history=_conv_history if _conv_history else None)

            if _cache and not response.get("error") and not _is_contextual:
                ok = _cache.set(query, response)
                if not ok and _cache.last_error:
                    st.session_state["_cache_write_error"] = _cache.last_error
                else:
                    st.session_state.pop("_cache_write_error", None)

        # Bubble text — empty for cache hits (badge shows); short summary for fresh
        if from_cache:
            assistant_text = ""
        else:
            _blocks    = response.get("message", {}).get("content", []) if isinstance(response, dict) else []
            _full_text = next((b.get("text","") for b in _blocks if b.get("type")=="text"), "")
            if _full_text:
                _first = _full_text.split(".")[0].strip()
                assistant_text = (_first[:120] + "…") if len(_first) > 120 else _first
            elif response.get("error"):    assistant_text = str(response["error"])
            elif response.get("layout"):   assistant_text = "Analysis complete."
            else:                          assistant_text = ""

        st.session_state.genie_messages.append({
            "role": "assistant", "content": assistant_text[:600],
            "timestamp": pd.Timestamp.now(), "response": response,
            "from_cache": from_cache,
        })
        st.session_state.genie_messages = st.session_state.genie_messages[-GENIE_SHORT_TERM_MAX_MSGS:]

        if analysis_type == "custom":
            st.session_state.last_custom_query = query
        st.session_state.recent_analyses.insert(0, {
            "query": query, "type": analysis_type,
            "timestamp": pd.Timestamp.now(), "response": response,
        })
        st.session_state.recent_analyses = st.session_state.recent_analyses[:10]
        _append_genie_question(query, analysis_type)

        _cp  = st.session_state.get("chat_persistence")
        _sid = st.session_state.get("genie_session_id", "")
        _lbl = st.session_state.get("genie_session_label", "")
        if _cp and _sid:
            try:
                _ti = st.session_state.get("chat_turn_index", 0)
                _cp.save_turn(_sid, _ti, "user", query, "", "user_input", _lbl)
                _ti += 1
                _sql_used, _src, _full_text2 = "", "", assistant_text
                if isinstance(response, dict):
                    _sql_used = str(response.get("sql","") or "")[:2000]
                    _src      = response.get("source","")
                    _fp = " ".join(b.get("text","") for b in response.get("message",{}).get("content",[]) if b.get("type")=="text").strip()
                    if _fp:
                        _full_text2 = _fp
                _cp.save_turn(_sid, _ti, "assistant", _full_text2[:3500], _sql_used, _src, _lbl)
                st.session_state.chat_turn_index = _ti + 1
            except Exception:
                pass

        _msg_count = len(st.session_state.get("genie_messages", []))
        _mem_obj   = st.session_state.get("genie_memory")
        if _mem_obj and _msg_count % 10 == 0:
            try:
                _mem_obj.refresh()
            except Exception:
                pass

        return response

    # Prefill from other pages
    prefill_q = st.session_state.pop("genie_prefill_question", None)
    if prefill_q and isinstance(prefill_q, str) and prefill_q.strip():
        st.session_state.selected_analysis = "custom"
        st.session_state.last_custom_query = prefill_q.strip()
        st.session_state.show_analysis     = True
        with st.spinner("Analyzing..."):
            st.session_state.analyst_response = process_genie_query(prefill_q.strip())
        st.rerun()

    # ── Welcome header ───────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:8px;">
        <h1 style="font-size:28px;font-weight:900;color:#1a1a1a;margin:0 0 4px 0;">Welcome to OrderLens Genie</h1>
        <p style="font-size:16px;color:#64748b;margin:0;">Let Genie run one of these quick analyses for you</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick-analysis tile cards — FULL WIDTH on top (like DealerPulse) ────
    ICON_BG         = "#5046e5"
    LAVENDER        = "#e8e4f7"
    CARD_BORDER     = "#e5e7eb"
    SELECTED_BORDER = "#5046e5"
    tile_cols = st.columns(4, gap="medium")
    clicked_key = None
    sel  = st.session_state.get("selected_analysis")
    show = st.session_state.get("show_analysis", False)

    for idx, (key, analysis) in enumerate(QUICK_ANALYSES.items()):
        with tile_cols[idx]:
            with st.form(f"tile_{key}", border=False):
                selected = bool(show and sel == key)
                bg     = LAVENDER if selected else "#fff"
                border = SELECTED_BORDER if selected else CARD_BORDER
                st.markdown(f"""
                <div class="genie-tile-card" style="background:{bg};border:1.5px solid {border};
                     border-radius:14px;padding:18px;box-shadow:0 2px 8px rgba(0,0,0,.04);min-height:155px;">
                    <div style="width:46px;height:46px;border-radius:12px;display:flex;align-items:center;
                         justify-content:center;margin-bottom:12px;background:{ICON_BG};">
                        {analysis['icon_svg']}
                    </div>
                    <div style="font-size:15px;font-weight:800;color:#1a1a1a;margin-bottom:5px;">{analysis['title']}</div>
                    <div style="font-size:12px;color:#64748b;line-height:1.4;">{analysis['desc']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.form_submit_button("Select", use_container_width=True):
                    clicked_key = key

    if clicked_key is not None:
        a = QUICK_ANALYSES[clicked_key]
        st.session_state.selected_analysis = clicked_key
        st.session_state.show_analysis     = True
        st.session_state.last_custom_query = a.get("question", "")
        for _k in list(st.session_state.keys()):
            if str(_k).startswith("_pres_") or str(_k).startswith("_pred_"):
                del st.session_state[_k]
        with st.spinner(f"Running {a['title']} analysis..."):
            quick_result = run_quick_analysis(clicked_key)
            st.session_state.analyst_response = quick_result
            st.session_state.recent_analyses.insert(0, {
                "query": a["question"], "type": clicked_key,
                "timestamp": pd.Timestamp.now(), "response": quick_result,
            })
            _tile_summary = (
                f"I ran a {a['title']} analysis. "
                f"The question was: '{a['question']}'. "
                f"The analysis covers: {a['desc']}."
            )
            _m_tile = quick_result.get("metrics") or {}
            if "total_ytd" in _m_tile:
                _tile_summary += (
                    f" Total revenue YTD: {abbr_currency(safe_number(_m_tile.get('total_ytd'),0))}. "
                    f"MoM change: {_safe_pct_str(_m_tile.get('mom_pct'),0)}. "
                    f"Top 5 dealers: {safe_int(_m_tile.get('top5_pct'),0)}% of revenue."
                )
            st.session_state.genie_messages.append({"role":"user","content":a["question"],"timestamp":pd.Timestamp.now(),"response":None})
            st.session_state.genie_messages.append({"role":"assistant","content":_tile_summary,"timestamp":pd.Timestamp.now(),"response":quick_result,"from_cache":False})
            st.session_state.recent_analyses = st.session_state.recent_analyses[:10]
            _append_genie_question(a["question"], clicked_key)
        st.rerun()

    # ── Two-column layout below tiles ────────────────────────────────────────
    left_col, right_col = st.columns([0.35, 0.65], gap="medium", vertical_alignment="top")

    # ════════════════════════════════════════════════════════════════════════
    # LEFT COLUMN
    # ════════════════════════════════════════════════════════════════════════
    with left_col:
        # Warnings (non-blocking)
        if st.session_state.get("genie_history_error"):
            st.warning(f"Question history not saving: {st.session_state.genie_history_error}")
        if st.session_state.get("_chat_persist_error"):
            st.warning(f"⚠️ Chat history: {st.session_state['_chat_persist_error']}")
        if st.session_state.get("_cache_write_error"):
            st.warning(f" Cache: {st.session_state['_cache_write_error']}")
        if not _get_current_user_raw():
            _owner_role = _get_app_owner_role()
            _gs = f'GRANT READ SESSION ON ACCOUNT TO ROLE {_owner_role};' if _owner_role else "GRANT READ SESSION ON ACCOUNT TO ROLE <role>;"
            st.info(f"**User showing as UNKNOWN.** Admin must run: `{_gs}`")

        with st.container(border=True):

            # ── Analysis Library ─────────────────────────────────────────────
            st.markdown('<div style="font-size:15px;font-weight:800;color:#0f172a;margin-bottom:10px;">Analysis Library</div>', unsafe_allow_html=True)
            _ra = st.session_state.get("recent_analyses", [])
            with st.container(border=True):
                st.markdown('<div style="font-size:12px;font-weight:700;color:#64748b;margin-bottom:6px;">Recent analysis</div>', unsafe_allow_html=True)
                if _ra:
                    for _ri, _ritem in enumerate(_ra[:3]):
                        _rq = (_ritem.get("query") or "")
                        _rq_label = (_rq[:50] + "…") if len(_rq) > 50 else _rq
                        if st.button(_rq_label, key=f"lib_recent_{_ri}", use_container_width=True, type="secondary"):
                            st.session_state.selected_analysis = "custom"
                            st.session_state.last_custom_query = _rq
                            st.session_state.show_analysis     = True
                            with st.spinner("Running..."):
                                st.session_state.analyst_response = process_genie_query(_rq)
                            st.rerun()
                else:
                    st.markdown('<div style="font-size:12px;color:#94a3b8;font-style:italic;padding:4px 0;">Run analyses to see them here.</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

            # ── Saved Insights ────────────────────────────────────────────────
            with st.expander("Saved insights", expanded=False):
                saved_insights = _get_saved_insights_for_user(20, page="genie")
                if saved_insights:
                    for i, item in enumerate(saved_insights):
                        title = item["title"] or (item["question"][:55] + "…")
                        if st.button(title, key=f"saved_insight_{i}", use_container_width=True, type="secondary"):
                            st.session_state.selected_analysis = "custom"
                            st.session_state.last_custom_query = item["question"]
                            st.session_state.show_analysis     = True
                            with st.spinner("Running..."):
                                st.session_state.analyst_response = process_genie_query(item["question"])
                            st.rerun()
                else:
                    st.markdown('<div style="font-size:12px;color:#94a3b8;text-align:center;padding:8px 0;">Save any Genie answer to see it here.</div>', unsafe_allow_html=True)

            # ── Frequently asked by you ───────────────────────────────────────
            with st.expander("Frequently asked by you", expanded=False):
                faqs_by_you = _get_frequent_questions_by_user(5)
                if faqs_by_you:
                    for i, item in enumerate(faqs_by_you):
                        q   = item["query"]
                        cnt = item["count"]
                        lbl = (q[:55] + "…") if len(q) > 55 else q
                        if st.button(f"{lbl} ({cnt})", key=f"faq_by_you_{i}", use_container_width=True, type="secondary"):
                            st.session_state.selected_analysis = "custom"
                            st.session_state.last_custom_query = q
                            st.session_state.show_analysis     = True
                            with st.spinner("Running..."):
                                st.session_state.analyst_response = process_genie_query(q)
                            st.rerun()
                else:
                    st.markdown('<div style="font-size:12px;color:#94a3b8;text-align:center;padding:8px 0;">No questions yet.</div>', unsafe_allow_html=True)

            # ── Most frequent (all) ───────────────────────────────────────────
            with st.expander("Most frequent (all)", expanded=False):
                faqs = _get_frequent_questions(5)
                if faqs:
                    for i, item in enumerate(faqs):
                        q   = item["query"]
                        cnt = item["count"]
                        lbl = (q[:55] + "…") if len(q) > 55 else q
                        if st.button(f"{lbl} ({cnt})", key=f"faq_{i}", use_container_width=True, type="secondary"):
                            st.session_state.selected_analysis = "custom"
                            st.session_state.last_custom_query = q
                            st.session_state.show_analysis     = True
                            with st.spinner("Running..."):
                                st.session_state.analyst_response = process_genie_query(q)
                            st.rerun()
                else:
                    st.caption("Ask questions to see most frequent across all users.")

    # RIGHT COLUMN: AI Assistant
    # ════════════════════════════════════════════════════════════════════════
    with right_col:
        with st.container(border=True):

            # ── Header row ───────────────────────────────────────────────────
            _msg_count = len(st.session_state.get("genie_messages", []))
            _hdr_left, _hdr_chats, _hdr_sum, _hdr_dl, _hdr_clr = st.columns([2.2, 0.9, 1.2, 1.1, 0.9], gap="small")
            with _hdr_left:
                st.markdown('<div style="font-size:15px;font-weight:800;color:#0f172a;padding-top:6px;">AI Assistant</div>', unsafe_allow_html=True)
            with _hdr_chats:
                _chats_clicked = st.button("Chats", use_container_width=True, help="Browse & resume previous conversations", key="btn_genie_chats")
            with _hdr_sum:
                _sum_clicked = st.button("Summarize", use_container_width=True, disabled=_msg_count < 2, help="Compress conversation into a summary", key="btn_genie_summarize")
            with _hdr_dl:
                def _build_md_export():
                    _msgs  = st.session_state.get("genie_messages", [])
                    _label = st.session_state.get("genie_session_label", "Chat")
                    _lines = [f"# OrderLens Genie — {_label}", "", f"*Exported {datetime.now().strftime('%Y-%m-%d %H:%M')}*", "", "---", ""]
                    for _m in _msgs:
                        if not _m.get("content"): continue
                        _pfx = "**You:** " if _m["role"] == "user" else "**Genie:** "
                        _lines.append(_pfx + _m["content"]); _lines.append("")
                    return "\n".join(_lines)
                st.download_button("Export MD", data=_build_md_export(),
                    file_name="genie_chat_" + datetime.now().strftime("%Y%m%d_%H%M") + ".md",
                    mime="text/markdown", use_container_width=True,
                    disabled=_msg_count == 0, help="Download chat as Markdown", key="btn_genie_export")
            with _hdr_clr:
                _clr_clicked = st.button("Clear", use_container_width=True, disabled=_msg_count == 0, type="secondary", help="Clear messages & start fresh", key="btn_genie_clear")

            # ── Handle: Chats panel toggle ────────────────────────────────────
            if _chats_clicked:
                _prev_show = st.session_state.get("show_chats_panel", False)
                st.session_state["show_chats_panel"] = not _prev_show
                if not _prev_show:
                    _cp_tmp = st.session_state.get("chat_persistence")
                    st.session_state["_all_sessions_cache"] = (_cp_tmp.load_all_sessions() if _cp_tmp else [])

            if st.session_state.get("show_chats_panel", False):
                _all_sess2 = st.session_state.get("_all_sessions_cache", [])
                _cp_tmp2   = st.session_state.get("chat_persistence")
                with st.container(border=True):
                    st.markdown("<div style='font-size:14px;font-weight:800;color:#1e40af;margin-bottom:12px;'> Previous Conversations</div>", unsafe_allow_html=True)
                    if st.button("New Conversation", key="btn_panel_new", use_container_width=True, type="primary"):
                        st.session_state.genie_messages      = []
                        st.session_state.analyst_response    = None
                        st.session_state.show_analysis       = False
                        st.session_state.selected_analysis   = None
                        st.session_state.last_custom_query   = ""
                        st.session_state.genie_session_id    = str(uuid.uuid4())
                        st.session_state.genie_session_label = "Chat on " + datetime.now().strftime("%b %d %H:%M")
                        st.session_state.chat_turn_index     = 0
                        st.session_state.restore_dismissed   = True
                        st.session_state.restore_offered     = False
                        st.session_state["show_chats_panel"] = False
                        st.rerun()
                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                    if not _all_sess2:
                        st.info("No previous conversations found in the last 7 days.", icon="")
                    else:
                        for _si3, _sess3 in enumerate(_all_sess2):
                            _age_h3   = _sess3.get("age_hours", 0)
                            _label3   = _sess3.get("session_label","Previous chat")
                            _nturns3  = _sess3.get("turn_count", 0)
                            _age_str3 = ("< 1 hr ago" if _age_h3 < 1 else f"{int(_age_h3)}h ago" if _age_h3 < 24 else f"{int(_age_h3/24)}d {int(_age_h3%24)}h ago")
                            _is_cur3  = _sess3.get("session_id") == st.session_state.get("genie_session_id","")
                            _sl3, _sr3 = st.columns([5, 2], gap="small")
                            with _sl3:
                                _cur_tag3 = (" <span style='background:#dcfce7;color:#15803d;border-radius:10px;padding:1px 8px;font-size:10px;font-weight:700;'>Active</span>") if _is_cur3 else ""
                                st.markdown(
                                    f"<div style='background:{'#eff6ff' if _is_cur3 else '#f8fafc'};"
                                    f"border:1px solid {'#bfdbfe' if _is_cur3 else '#e2e8f0'};"
                                    f"border-radius:10px;padding:9px 12px;margin-bottom:4px;'>"
                                    f"<div style='font-size:13px;font-weight:700;color:#0f172a;'>{html.escape(_label3)}{_cur_tag3}</div>"
                                    f"<div style='font-size:11px;color:#64748b;margin-top:2px;'>{_nturns3} messages &nbsp;·&nbsp; {_age_str3}</div></div>",
                                    unsafe_allow_html=True,
                                )
                            with _sr3:
                                if _is_cur3:
                                    st.markdown("<div style='padding:10px 0;text-align:center;font-size:12px;color:#64748b;'>Current</div>", unsafe_allow_html=True)
                                else:
                                    if st.button("Resume", key=f"btn_panel_resume_{_si3}", use_container_width=True, type="primary"):
                                        with st.spinner("Loading conversation..."):
                                            _msgs3 = _cp_tmp2.load_session_messages(_sess3["session_id"]) if _cp_tmp2 else []
                                        st.session_state.genie_messages      = _msgs3
                                        st.session_state.chat_turn_index     = len(_msgs3)
                                        st.session_state.genie_session_id    = _sess3["session_id"]
                                        st.session_state.genie_session_label = _sess3["session_label"]
                                        st.session_state.restore_dismissed   = True
                                        st.session_state["show_chats_panel"] = False
                                        st.rerun()
                        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                        if st.button("Close", key="btn_panel_close", use_container_width=True, type="secondary"):
                            st.session_state["show_chats_panel"] = False
                            st.rerun()

            # ── Handle: Summarize ─────────────────────────────────────────────
            if _sum_clicked:
                _transcript = "\n".join([
                    f"{'User' if _m['role']=='user' else 'Genie'}: {_m.get('content','')}"
                    for _m in st.session_state.get("genie_messages", []) if _m.get("content")
                ])
                try:
                    with st.spinner("Summarizing conversation..."):
                        _tdf = session.sql(
                            "SELECT SNOWFLAKE.CORTEX.COMPLETE(?,?) AS R",
                            params=[CORTEX_PRESCRIPTIVE_MODEL,
                                    "Summarize this sales & operations analytics conversation in 4-5 bullet points. "
                                    "Keep key findings, dealer names, and important numbers:\n\n"
                                    + _transcript[:3000]]
                        ).to_pandas()
                        _summary = (_tdf.at[0,"R"] if not _tdf.empty else "") or "Previous conversation summarized."
                except Exception:
                    _summary = "Previous conversation context retained."
                st.session_state.genie_messages = [{
                    "role": "assistant", "content": f"Conversation summary:\n{_summary}",
                    "timestamp": pd.Timestamp.now(), "response": None,
                }]
                st.rerun()

            # ── Handle: Clear ─────────────────────────────────────────────────
            if _clr_clicked:
                st.session_state.genie_messages      = []
                st.session_state.analyst_response    = None
                st.session_state.show_analysis       = False
                st.session_state.selected_analysis   = None
                st.session_state.last_custom_query   = ""
                st.session_state.genie_session_id    = str(uuid.uuid4())
                st.session_state.genie_session_label = "Chat on " + datetime.now().strftime("%b %d %H:%M")
                st.session_state.chat_turn_index     = 0
                st.session_state.restore_dismissed   = True
                st.session_state.restore_offered     = False
                st.session_state["_all_sessions_cache"] = []
                for _k in list(st.session_state.keys()):
                    if str(_k).startswith("_pres_") or str(_k).startswith("_pred_"):
                        del st.session_state[_k]
                st.rerun()

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

            # ════════════════════════════════════════════════════════════════
            # SCROLLABLE CHAT AREA
            # ════════════════════════════════════════════════════════════════
            with st.container(height=320, border=True):
                _all_messages = st.session_state.get("genie_messages", [])
                _cp_ref       = st.session_state.get("chat_persistence")

                # Session-restore picker (shown when chat is empty)
                if (not _all_messages and _cp_ref and not st.session_state.get("restore_dismissed")):
                    if not st.session_state.get("restore_offered"):
                        try:
                            _sessions = _cp_ref.load_all_sessions()
                        except Exception:
                            _sessions = []
                        st.session_state["_all_sessions_cache"] = _sessions
                        st.session_state["restore_offered"]     = True

                _all_sessions_restore = st.session_state.get("_all_sessions_cache", [])

                if (not _all_messages and _all_sessions_restore and not st.session_state.get("restore_dismissed")):
                    st.markdown("""
                    <div class="resume-banner">
                        <div style="font-size:16px;font-weight:800;color:#1e40af;margin-bottom:4px;"> Resume a previous conversation</div>
                        <div style="font-size:13px;color:#374151;margin-bottom:14px;">You have chats from the last 7 days. Pick one to continue, or start fresh.</div>
                    </div>""", unsafe_allow_html=True)
                    for _si_r, _sess_r in enumerate(_all_sessions_restore):
                        _age_r   = _sess_r.get("age_hours", 0)
                        _label_r = _sess_r.get("session_label","Previous chat")
                        _tc_r    = _sess_r.get("turn_count", 0)
                        _age_s_r = ("< 1 hr ago" if _age_r < 1 else f"{int(_age_r)}h ago" if _age_r < 24 else f"{int(_age_r/24)}d {int(_age_r%24)}h ago")
                        _rcl, _rcr = st.columns([5, 2], gap="small")
                        with _rcl:
                            st.markdown(
                                f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;margin-bottom:6px;">'
                                f'<div style="font-size:13px;font-weight:700;color:#0f172a;">{html.escape(_label_r)}</div>'
                                f'<div style="font-size:11px;color:#64748b;margin-top:2px;">{_tc_r} messages · {_age_s_r}</div></div>',
                                unsafe_allow_html=True,
                            )
                        with _rcr:
                            if st.button("Resume", key=f"btn_resume_r_{_si_r}", use_container_width=True, type="primary"):
                                with st.spinner("Loading conversation..."):
                                    _msgs_r = _cp_ref.load_session_messages(_sess_r["session_id"])
                                st.session_state.genie_messages      = _msgs_r
                                st.session_state.chat_turn_index     = len(_msgs_r)
                                st.session_state.genie_session_id    = _sess_r["session_id"]
                                st.session_state.genie_session_label = _sess_r["session_label"]
                                st.session_state.restore_dismissed   = True
                                st.rerun()
                    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                    if st.button("Start a new conversation", key="btn_start_fresh", use_container_width=True, type="secondary"):
                        st.session_state.restore_dismissed = True
                        st.rerun()

                elif not _all_messages:
                    if not st.session_state.get("show_analysis"):
                        st.markdown("""
                        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:500px;text-align:center;">
                            <div style="font-size:32px;margin-bottom:16px;color:#94a3b8;">&#x2022;</div>
                            <div style="font-size:18px;font-weight:800;color:#1a1a1a;margin-bottom:8px;">Start a Conversation</div>
                            <div style="font-size:14px;color:#64748b;max-width:400px;">Ask questions about your Sales &amp; Operations data, or select a quick analysis above.</div>
                        </div>""", unsafe_allow_html=True)

                # ── Render message bubbles ────────────────────────────────────
                for _msg_idx, _msg in enumerate(_all_messages):
                    _role     = _msg.get("role","user")
                    _content  = _msg.get("content","") or ""
                    _response = _msg.get("response")
                    _cached   = _msg.get("from_cache", False)

                    if _role == "user":
                        st.markdown(f"""
                        <div class="g-user">
                            <div class="g-user-inner">
                                <div class="g-user-lbl">You</div>
                                {html.escape(_content)}
                            </div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        if _cached:
                            st.markdown('<span class="cache-badge"> Cache hit — answered instantly</span>', unsafe_allow_html=True)
                        if _content:
                            st.markdown(f"""
                            <div class="g-ai">
                                <div class="g-ai-inner">
                                    <div class="g-ai-lbl">Genie</div>
                                    {html.escape(_content)}
                                </div>
                            </div>""", unsafe_allow_html=True)
                        # Older messages: only show SQL expander
                        _is_latest = (_msg_idx == len(_all_messages) - 1)
                        if _response and not _is_latest:
                            _old_blocks = (_response.get("message",{}).get("content",[]) if isinstance(_response, dict) else [])
                            for _ob in _old_blocks:
                                if _ob.get("type") == "sql":
                                    with st.expander("View SQL used", expanded=False):
                                        st.code(_ob.get("statement",""), language="sql")

                # ── Full result panel renders INSIDE the scroll container ──────
                _active_response = st.session_state.get("analyst_response")
                if not _active_response and _all_messages:
                    for _lm in reversed(_all_messages):
                        if _lm.get("role") == "assistant" and _lm.get("response"):
                            _active_response = _lm["response"]
                            break

                if _active_response and not isinstance(_active_response, bool):
                    st.session_state.show_analysis     = True
                    st.session_state.analyst_response  = _active_response

                if st.session_state.get("show_analysis") and st.session_state.get("analyst_response"):
                    _resp_inner = st.session_state.analyst_response
                    _akey_inner = st.session_state.selected_analysis
                    _a_inner    = QUICK_ANALYSES.get(_akey_inner, {})
                    _dtitle_inner = (
                        (st.session_state.get("last_custom_query") or "Custom Query")
                        if _akey_inner == "custom"
                        else _a_inner.get("title","Analysis")
                    )
                    _dtitle_safe = html.escape(str(_dtitle_inner))

                    if "error" in _resp_inner:
                        _err_msg = str(_resp_inner["error"])
                        st.markdown(f"""
                        <div style="background:#fef2f2;border:1.5px solid #fecaca;border-radius:12px;padding:14px 16px;margin:10px 0;">
                            <div style="font-size:13px;font-weight:700;color:#b91c1c;margin-bottom:4px;">⚠️ Could not get AI answer</div>
                            <div style="font-size:12px;color:#7f1d1d;">{html.escape(_err_msg)}</div>
                        </div>""", unsafe_allow_html=True)

                    elif _resp_inner.get("layout") == "quick":
                        # ── Quick-analysis tile result ─────────────────────────
                        _akey_q = st.session_state.get("selected_analysis","")
                        _a_q    = QUICK_ANALYSES.get(_akey_q, {})
                        _qtitle = _a_q.get("title", _dtitle_safe)

                        _qc1, _qspace, _qc2 = st.columns([1, 5, 1])
                        with _qc1:
                            if st.button("Reset", key="back_btn_q"):
                                st.session_state.show_analysis    = False
                                st.session_state.analyst_response = None
                                st.rerun()
                        with _qc2:
                            _q_text_save = (_a_q.get("question") or "").strip()
                            if _q_text_save and st.button(" Save", key="btn_save_quick_inner"):
                                _save_insight(_q_text_save, _qtitle, analysis_type=_akey_q or "quick", page="genie")

                        st.markdown(f"""
                        <div style="margin:8px 0 14px 0;">
                            <div style="font-size:11px;font-weight:700;color:#64748b;">Your question</div>
                            <div style="font-size:17px;font-weight:800;color:#1a1a1a;">{html.escape(_qtitle)}</div>
                        </div>""", unsafe_allow_html=True)

                        _m = _resp_inner.get("metrics") or {}
                        if "total_ytd" in _m:
                            _ytd_v  = abbr_currency(safe_number(_m.get("total_ytd"),0))
                            _mom_v  = _safe_pct_str(_m.get("mom_pct"),0)
                            _qoq_v  = _safe_pct_str(_m.get("qoq_pct"),0)
                            _top5_v = safe_int(_m.get("top5_pct"),0)
                            _mom_n  = safe_number(_m.get("mom_pct"),0)
                            _qoq_n  = safe_number(_m.get("qoq_pct"),0)
                            def _dc(v): return "#059669" if v>0 else ("#dc2626" if v<0 else "#0f172a")
                            st.markdown(f"""
                            <div style="background:linear-gradient(135deg,#e0f2fe,#dbeafe);border:1.5px solid #bae6fd;border-radius:14px;padding:18px;margin-bottom:18px;">
                                <div style="font-size:14px;font-weight:800;color:#0f172a;margin-bottom:12px;"> Key Insights</div>
                                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
                                    <div style="background:rgba(255,255,255,.85);padding:12px;border-radius:10px;"><div style="font-size:11px;color:#64748b;font-weight:700;">Total Revenue (YTD)</div><div style="font-size:22px;font-weight:900;color:#0f172a;">{_ytd_v}</div></div>
                                    <div style="background:rgba(255,255,255,.85);padding:12px;border-radius:10px;"><div style="font-size:11px;color:#64748b;font-weight:700;">MoM Change</div><div style="font-size:22px;font-weight:900;color:{_dc(_mom_n)};">{_mom_v}</div></div>
                                    <div style="background:rgba(255,255,255,.85);padding:12px;border-radius:10px;"><div style="font-size:11px;color:#64748b;font-weight:700;">Top 5 Dealers</div><div style="font-size:22px;font-weight:900;color:#0f172a;">{_top5_v}%</div></div>
                                    <div style="background:rgba(255,255,255,.85);padding:12px;border-radius:10px;"><div style="font-size:11px;color:#64748b;font-weight:700;">QoQ Change</div><div style="font-size:22px;font-weight:900;color:{_dc(_qoq_n)};">{_qoq_v}</div></div>
                                </div>
                            </div>""", unsafe_allow_html=True)
                        elif _m.get("summary"):
                            st.info(_m["summary"])

                        if _resp_inner.get("anomaly"):
                            st.markdown(f"""
                            <div style="background:#fffbeb;border:1.5px solid #fde68a;border-radius:10px;padding:12px 16px;margin-bottom:16px;display:flex;gap:10px;align-items:flex-start;">
                                <span style="font-size:18px;">⚠️</span>
                                <div><div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:2px;">Anomaly Detected</div>
                                <div style="font-size:13px;color:#475569;">{_resp_inner['anomaly']}</div></div>
                            </div>""", unsafe_allow_html=True)

                        _mdf = _resp_inner.get("monthly_df")
                        if _mdf is not None and not _mdf.empty and "MONTH" in _mdf.columns:
                            _vcol = ("VALUE" if "VALUE" in _mdf.columns else (_mdf.columns[1] if len(_mdf.columns)>1 else None))
                            if _vcol:
                                st.markdown("**Monthly Trend**")
                                alt_line_monthly(_mdf, month_col="MONTH", value_col=_vcol, height=240, title="Monthly Revenue Trend")

                        _vdf = _resp_inner.get("vendors_df")
                        if _vdf is not None and not _vdf.empty:
                            _vc  = "VENDOR_NAME" if "VENDOR_NAME" in _vdf.columns else (_vdf.columns[0] if _vdf.columns.any() else None)
                            _vs  = ("SPEND" if "SPEND" in _vdf.columns else (_vdf.columns[1] if len(_vdf.columns)>1 else None))
                            if _vc and _vs:
                                st.markdown("**Top Dealers by Revenue**")
                                alt_bar(_vdf.head(15), x=_vc, y=_vs, color="#1E40AF", height=260, horizontal=True)
                                st.dataframe(_vdf, use_container_width=True, height=240)

                        _extra = _resp_inner.get("extra_dfs") or {}
                        for _ename, _edf in _extra.items():
                            if _edf is None or _edf.empty or _ename in ("monthly_full",):
                                continue
                            st.markdown(f"**{_ename.replace('_',' ').title()}**")
                            _xce, _yce = _pick_chart_columns(_edf)
                            if _xce and _yce:
                                _use_he = str(_xce).upper() in ("ORDER_STATUS","DEALER_NAME","VENDOR_NAME")
                                alt_bar(_edf, x=_xce, y=_yce, color="#5046e5", height=240, horizontal=_use_he)
                            st.dataframe(_edf, use_container_width=True, height=220)

                        _all_dfs_q = [df for df in [_mdf, _vdf] + list(_extra.values()) if df is not None and not df.empty]
                        if _all_dfs_q:
                            _pres_q = _cortex_complete_prescriptive_from_dfs(_all_dfs_q, _a_q.get("question",_qtitle), context_text=str(_m)[:500] if _m else "")
                            if not _pres_q:
                                _pres_q = _generate_prescriptive_from_dfs(_all_dfs_q)
                            if _pres_q:
                                with st.expander("Prescriptive — Recommendations & Actions", expanded=False):
                                    st.markdown(f'<div class="prescriptive-content">{_pres_q}</div>', unsafe_allow_html=True)
                            # Generate Predictive for quick analyses via Cortex
                            _pred_cache_key_q = f"_pred_q_{abs(hash(_qtitle)) % 1_000_000}"
                            if _pred_cache_key_q not in st.session_state:
                                try:
                                    _pred_prompt = (
                                        f"Based on this S&O data analysis for '{_a_q.get('question', _qtitle)}', "
                                        f"provide a brief 30-90 day predictive forecast. "
                                        f"State 2-3 key assumptions, likely outcomes with numbers, "
                                        f"and a confidence level (Low/Medium/High). Be concise (3-4 sentences)."
                                        + (f"\n\nKey metrics: {str(_m)[:400]}" if _m else "")
                                    )
                                    _pred_df = session.sql(
                                        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS RESPONSE",
                                        params=[CORTEX_PRESCRIPTIVE_MODEL, _pred_prompt]
                                    ).to_pandas()
                                    _pred_q = (_pred_df.at[0,"RESPONSE"] if not _pred_df.empty else "") or ""
                                    st.session_state[_pred_cache_key_q] = _pred_q.strip() if len(_pred_q.strip()) > 20 else ""
                                except Exception:
                                    st.session_state[_pred_cache_key_q] = ""
                            _pred_q = st.session_state.get(_pred_cache_key_q, "")
                            if _pred_q:
                                with st.expander("Predictive — 30–90 Day Forecast", expanded=False):
                                    st.markdown(
                                        f'<div style="background:#f0fdf4;border-left:4px solid #22c55e;'
                                        f'border-radius:8px;padding:14px;font-size:14px;color:#0f172a;line-height:1.7;">'
                                        f'{html.escape(_pred_q).replace(chr(10),"<br/>")}</div>',
                                        unsafe_allow_html=True
                                    )

                    elif "message" in _resp_inner and "content" in _resp_inner.get("message",{}):
                        # ── Cortex custom query result ─────────────────────────
                        _content_r = _resp_inner["message"]["content"]
                        _all_text_r = "\n\n".join(b.get("text","") for b in _content_r if b.get("type")=="text").strip()

                        _cur_question = st.session_state.get("last_custom_query") or _dtitle_inner or ""

                        _rc1, _rspace, _rc2 = st.columns([1, 5, 1])
                        with _rc1:
                            if st.button("Reset", key="back_btn_cortex"):
                                st.session_state.show_analysis    = False
                                st.session_state.analyst_response = None
                                st.rerun()
                        with _rc2:
                            if _cur_question and st.button(" Save", key="btn_save_cortex"):
                                _save_insight(_cur_question, _cur_question[:80], analysis_type=_akey_inner or "custom", page="genie")

                        st.markdown(f"""
                        <div style="margin:8px 0 12px 0;">
                            <div style="font-size:11px;font-weight:700;color:#64748b;">Your question</div>
                            <div style="font-size:15px;font-weight:800;color:#1a1a1a;">{_dtitle_safe}</div>
                        </div>""", unsafe_allow_html=True)

                        _desc_r, _pres_r, _pred_r = _parse_three_sections(_all_text_r) if _all_text_r else (None, None, None)
                        _generic_pres = "See the supporting data and charts below for specific numbers to act on."

                        if _all_text_r and not _pres_r:
                            _desc_r = _desc_r or _all_text_r
                            _pres_r = _generic_pres

                        _pres_cache_key = f"_pres_{abs(hash(_all_text_r[:100])) % 1_000_000}"
                        _is_generic_r = (
                            _pres_r == _generic_pres
                            or (_pres_r and any(p in (_pres_r or "").lower() for p in (
                                "see the supporting data","review the data below",
                                "supporting data and charts","specific numbers to act on"
                            )))
                        )
                        if _is_generic_r:
                            if _pres_cache_key not in st.session_state:
                                _cp_r = _cortex_complete_prescriptive(_content_r, run_df, _cur_question)
                                if not _cp_r:
                                    _cp_r = _generate_prescriptive_from_data(_content_r, run_df)
                                st.session_state[_pres_cache_key] = _cp_r or _pres_r
                            _pres_r = st.session_state.get(_pres_cache_key, _pres_r)

                        # ── Descriptive card ──────────────────────────────────
                        if _desc_r:
                            _desc_esc_r = html.escape(_desc_r).replace("\n","<br/>")
                            st.markdown(f"""
                            <div style="margin-bottom:12px;">
                                <div style="padding:14px;background:#e0f2fe;border-radius:10px;border-left:4px solid #0284c7;">
                                    <div style="font-size:12px;font-weight:800;color:#0369a1;margin-bottom:8px;">Descriptive — What the data shows</div>
                                    <div style="color:#0f172a;font-size:14px;line-height:1.6;word-wrap:break-word;overflow-wrap:break-word;max-width:100%;">{_desc_esc_r}</div>
                                </div>
                            </div>""", unsafe_allow_html=True)
                        elif _all_text_r and not _pres_r:
                            _raw_esc_r = html.escape(_all_text_r).replace("\n","<br/>")
                            st.markdown(f"""
                            <div style="padding:14px;background:#f5f3ff;border-radius:10px;border-left:4px solid #5046e5;margin-bottom:12px;">
                                <div style="color:#0f172a;font-size:14px;line-height:1.6;">{_raw_esc_r}</div>
                            </div>""", unsafe_allow_html=True)

                        # ── Prescriptive expander ─────────────────────────────
                        if _pres_r:
                            with st.expander("Prescriptive — Recommendations & Actions", expanded=False):
                                _pf = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html.escape(_pres_r))
                                _plines = []
                                for _pl in _pf.replace("<br/>","\n").split("\n"):
                                    _pl = _pl.strip()
                                    if _pl:
                                        _plines.append(f"<li style='margin-bottom:8px;line-height:1.6;'>{_pl.lstrip('•*').strip()}</li>")
                                if _plines:
                                    st.markdown(f"<ul style='margin:0;padding-left:22px;font-size:14px;color:#0f172a;'>{''.join(_plines)}</ul>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="prescriptive-content">{_pres_r}</div>', unsafe_allow_html=True)

                        # ── Predictive expander ───────────────────────────────
                        # Use parsed section OR generate via Cortex if missing
                        _pred_cache_key_r = f"_pred_r_{abs(hash(_all_text_r[:100])) % 1_000_000}"
                        if not _pred_r:
                            if _pred_cache_key_r not in st.session_state:
                                try:
                                    # Collect SQL result DFs for context
                                    _sql_dfs_r = []
                                    for _blk_pred in _content_r:
                                        if _blk_pred.get("type") == "sql":
                                            try:
                                                _pdf = run_df(_blk_pred.get("statement",""))
                                                if _pdf is not None and not _pdf.empty:
                                                    _sql_dfs_r.append(_pdf.head(10).to_string(index=False, max_colwidth=40))
                                            except Exception:
                                                pass
                                    _data_ctx = "\n\n".join(_sql_dfs_r)[:6000] if _sql_dfs_r else ""
                                    _pred_prompt_r = (
                                        f"Based on this S&O analysis for the question: '{_cur_question}', "
                                        f"provide a brief 30-90 day predictive forecast. "
                                        f"State 2-3 key assumptions, likely outcomes with numbers, "
                                        f"and a confidence level (Low/Medium/High). Be concise (3-4 sentences)."
                                        + (f"\n\nData context:\n{_data_ctx}" if _data_ctx else "")
                                    )
                                    _pred_df_r = session.sql(
                                        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS RESPONSE",
                                        params=[CORTEX_PRESCRIPTIVE_MODEL, _pred_prompt_r]
                                    ).to_pandas()
                                    _pred_gen = (_pred_df_r.at[0,"RESPONSE"] if not _pred_df_r.empty else "") or ""
                                    st.session_state[_pred_cache_key_r] = _pred_gen.strip() if len(_pred_gen.strip()) > 20 else ""
                                except Exception:
                                    st.session_state[_pred_cache_key_r] = ""
                            _pred_r = st.session_state.get(_pred_cache_key_r, "")

                        if _pred_r:
                            with st.expander("Predictive — 30–90 Day Forecast", expanded=False):
                                _pred_esc = html.escape(_pred_r).replace("\n","<br/>")
                                st.markdown(
                                    f'<div style="background:#f0fdf4;border-left:4px solid #22c55e;'
                                    f'border-radius:8px;padding:14px;font-size:14px;color:#0f172a;line-height:1.7;">'
                                    f'{_pred_esc}</div>',
                                    unsafe_allow_html=True
                                )

                        _resp_hash = abs(hash(str(id(_resp_inner)))) % 1_000_000
                        for _bidx_r, _blk_r2 in enumerate(_content_r):
                            if _blk_r2.get("type") == "sql":
                                _sql_r = _blk_r2.get("statement","")
                                try:
                                    _df_r = run_df(_sql_r)
                                    if _df_r is not None and not _df_r.empty:
                                        with st.expander("View supporting data", expanded=True):
                                            _res_r = _has_comparison_columns(_df_r)
                                            if _res_r[1] and _res_r[2]:
                                                _cat_r, _cur_r, _prv_r, _cl_r, _pl_r = _res_r
                                                alt_bar_comparison(_df_r, _cat_r, _cur_r, _prv_r, curr_label=_cl_r or "Current", prev_label=_pl_r or "Previous", height=300)
                                            else:
                                                _xc2, _yc2 = _pick_chart_columns(_df_r)
                                                if _xc2 and _yc2:
                                                    _use_h2 = str(_xc2).upper() in ("DEALER_NAME","ORDER_STATUS","VENDOR_NAME","PRODUCT_NAME","DEALER_TYPE")
                                                    alt_bar(_df_r, x=_xc2, y=_yc2, color='#5046e5', height=280, horizontal=_use_h2)
                                            st.dataframe(_df_r, use_container_width=True, height=280)
                                            st.download_button("Download Results", _df_r.to_csv(index=False), "results.csv", key=f"dl_inner_{_resp_hash}_{_bidx_r}")
                                    with st.expander("View SQL used", expanded=False):
                                        st.code(_sql_r, language="sql")
                                except Exception as _eq:
                                    st.error(f"Query error: {_eq}")
                                    with st.expander("View SQL used"):
                                        st.code(_sql_r, language="sql")

                # Auto-scroll anchor
                st.markdown('<div id="genie-bottom" style="height:4px;"></div>', unsafe_allow_html=True)

            # Auto-scroll JS
            st.markdown(_build_autoscroll_js(), unsafe_allow_html=True)

            # ── Chat Input ────────────────────────────────────────────────────
            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            with st.form("genie_question_form", clear_on_submit=True):
                input_col, btn_col = st.columns([0.88, 0.12])
                with input_col:
                    user_query = st.text_input(
                        "Ask a question",
                        placeholder="Ask about Sales & Operations data...",
                        label_visibility="collapsed",
                        key=f"genie_chat_input_{st.session_state.genie_input_version}"
                    )
                with btn_col:
                    send_clicked = st.form_submit_button("→")

            if send_clicked and user_query:
                st.session_state.selected_analysis  = "custom"
                st.session_state.last_custom_query  = user_query.strip()
                st.session_state.show_analysis      = True
                st.session_state.genie_input_version = st.session_state.genie_input_version + 1
                st.session_state.restore_dismissed  = True
                for _k in list(st.session_state.keys()):
                    if str(_k).startswith("_pres_") or str(_k).startswith("_pred_"):
                        del st.session_state[_k]
                with st.spinner("Analyzing..."):
                    st.session_state.analyst_response = process_genie_query(user_query)
                st.rerun()

# ================= ORDER LIFE CYCLE PAGE =================
elif st.session_state.current_page == "Order Life Cycle":
    st.title("Order Details Lookup")
    st.markdown("Search and view comprehensive information about any order")
    st.markdown("---")
    
    order_ids_df = run_query("""
        SELECT DISTINCT ORDER_ID
        FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.FACT_ORDER_HISTORY_VW
        ORDER BY ORDER_ID DESC
    """)
    
    order_options = order_ids_df["ORDER_ID"].tolist() if not order_ids_df.empty else []
    
    selected_orders = st.multiselect(
        "Select Order ID(s)",
        options=order_options,
        placeholder="Select one or more orders"
    )
    
    if selected_orders:
        order_ids_safe = ",".join("'" + oid.replace("'", "''") + "'" for oid in selected_orders)
        order_filter = f"ORDER_ID IN ({order_ids_safe})"
    else:
        order_filter = None
    
    if order_filter:
        with st.spinner("Loading order details..."):
            try:
                order_details = run_query(f"""
                    SELECT *
                    FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.FACT_ORDER_HISTORY_VW
                    WHERE {order_filter}
                    ORDER BY EFFECTIVE_DATE DESC
                """)
                
                aggregated_order_details = run_query(f"""
                    SELECT
                        ORDER_ID,
                        EFFECTIVE_DATE,
                        ORDER_STATUS,
                        DELIVERY_DATE,
                        EXPECTED_DELIVERY_DATE,
                        SUM(QUANTITY) AS QUANTITY_ORDERED,
                        SUM(TOTAL_AMOUNT) AS TOTAL_AMOUNT
                    FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.FACT_ORDER_HISTORY_VW
                    WHERE {order_filter}
                    GROUP BY
                        ORDER_ID,
                        EFFECTIVE_DATE,
                        ORDER_STATUS,
                        DELIVERY_DATE,
                        EXPECTED_DELIVERY_DATE
                    ORDER BY
                        ORDER_ID,
                        CASE UPPER(ORDER_STATUS)
                            WHEN 'DELIVERED' THEN 4
                            WHEN 'SHIPPED'   THEN 3
                            WHEN 'CONFIRMED' THEN 2
                            WHEN 'PLACED'    THEN 1
                            ELSE 0
                        END
                """)
                
                if order_details.empty:
                    st.error("No orders found")
                else:
                    st.success(f"{order_details['ORDER_ID'].nunique()} order(s) loaded")
                    
                    # Order Summary: Common information with latest status
                    order_summary = run_query(f"""
                        SELECT
                            ORDER_ID,
                            MAX(CASE WHEN ORDER_STATUS = 'PLACED' THEN ORDER_STATUS_DATE END) AS ORDER_DATE,
                            MAX(CASE WHEN CURRENT_FLAG = 'Y' THEN ORDER_STATUS END) AS LATEST_STATUS,
                            MAX(DEALER_ID) AS DEALER_ID,
                            MAX(DEALER_NAME) AS DEALER_NAME,
                            SUM(QUANTITY) AS TOTAL_QUANTITY,
                            SUM(TOTAL_AMOUNT) AS TOTAL_AMOUNT,
                            COUNT(DISTINCT PRODUCT_ID) AS PRODUCT_COUNT,
                            MIN(EFFECTIVE_DATE) AS FIRST_EFFECTIVE_DATE,
                            MAX(EFFECTIVE_DATE) AS LAST_EFFECTIVE_DATE,
                            MAX(EXPECTED_DELIVERY_DATE) AS EXPECTED_DELIVERY_DATE
                        FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.FACT_ORDER_HISTORY_VW
                        WHERE {order_filter}
                        GROUP BY ORDER_ID
                        ORDER BY ORDER_ID
                    """)
                    
                    # Order Status Details: Status-specific information with order_status_date
                    order_status_details = run_query(f"""
                        SELECT
                            ORDER_ID,
                            ORDER_STATUS,
                            EFFECTIVE_DATE,
                            ORDER_STATUS_DATE,
                            SUM(QUANTITY) AS QUANTITY,
                            SUM(TOTAL_AMOUNT) AS AMOUNT
                        FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.FACT_ORDER_HISTORY_VW
                        WHERE {order_filter}
                        GROUP BY ORDER_ID, ORDER_STATUS, EFFECTIVE_DATE, ORDER_STATUS_DATE
                        ORDER BY ORDER_ID, 
                            CASE UPPER(ORDER_STATUS)
                                WHEN 'PLACED' THEN 1
                                WHEN 'CONFIRMED' THEN 2
                                WHEN 'SHIPPED' THEN 3
                                WHEN 'DELIVERED' THEN 4
                                ELSE 5
                            END,
                            EFFECTIVE_DATE
                    """)
                    
                    # Order Summary: Display as rectangular tiles (one per order) styled like KPIs
                    if not order_summary.empty:
                        st.markdown('<h2 style="font-size: 24px; font-weight: 700; margin-bottom: 20px; color: #1F2937;">Order Summary</h2>', unsafe_allow_html=True)
                        
                        # Display multiple tiles if multiple orders selected
                        num_orders = len(order_summary)
                        cols_per_row = 3
                        num_rows = (num_orders + cols_per_row - 1) // cols_per_row
                        
                        for row_idx in range(num_rows):
                            cols = st.columns(cols_per_row)
                            for col_idx in range(cols_per_row):
                                order_idx = row_idx * cols_per_row + col_idx
                                if order_idx < num_orders:
                                    summary_row = order_summary.iloc[order_idx]
                                    order_date_str = summary_row['ORDER_DATE'].strftime('%Y-%m-%d') if pd.notna(summary_row['ORDER_DATE']) else 'N/A'
                                    total_amount = f"${float(summary_row['TOTAL_AMOUNT']):,.2f}" if pd.notna(summary_row['TOTAL_AMOUNT']) else "$0.00"
                                    total_quantity = int(summary_row['TOTAL_QUANTITY']) if pd.notna(summary_row['TOTAL_QUANTITY']) else 0
                                    expected_delivery_date = summary_row['EXPECTED_DELIVERY_DATE'].strftime('%Y-%m-%d') if pd.notna(summary_row['EXPECTED_DELIVERY_DATE']) else 'N/A'
                                    
                                    with cols[col_idx]:
                                        # Rectangular tile with single color like KPIs
                                        st.markdown(f"""
                                            <div class="kpi-card kpi-card-blue" style="margin-bottom: 16px;">
                                                <div class="kpi-label">ORDER ID: {summary_row['ORDER_ID']}</div>
                                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; text-align: left;">
                                                    <div>
                                                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 4px;">Order Date</div>
                                                        <div style="font-size: 14px; font-weight: 600;">{order_date_str}</div>
                                                    </div>
                                                    <div>
                                                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 4px;">Quantity</div>
                                                        <div style="font-size: 14px; font-weight: 600;">{total_quantity}</div>
                                                    </div>
                                                    <div>
                                                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 4px;">Total Amount</div>
                                                        <div style="font-size: 16px; font-weight: 700;">{total_amount}</div>
                                                    </div>
                                                    <div>
                                                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 4px;">Expected Delivery Date</div>
                                                        <div style="font-size: 14px; font-weight: 600;">{expected_delivery_date}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        """, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Order Status Information: Display as table with separate header
                    st.markdown('<h2 style="font-size: 24px; font-weight: 700; margin-top: 30px; margin-bottom: 20px; color: #1F2937;">Order Status Information</h2>', unsafe_allow_html=True)
                    
                    if not order_status_details.empty:
                        status_display = order_status_details.copy()
                        status_display["AMOUNT"] = status_display["AMOUNT"].apply(
                            lambda x: f"${float(x):,.2f}" if x else "$0.00"
                        )
                        status_display = status_display.rename(columns={
                            "ORDER_ID": "Order Number",
                            "ORDER_STATUS": "Status",
                            "ORDER_STATUS_DATE": "Order Status Date"
                        })
                        # Select only the columns we want to display
                        status_display = status_display[["Order Number", "Status", "Order Status Date"]]
                        st.dataframe(status_display, use_container_width=True, hide_index=True)
                    else:
                        st.info("No order status details available")
                    
                    st.markdown("---")
                    
                    product_rows = (
                        order_details
                        .sort_values("ORDER_STATUS_DATE", ascending=False)
                        .drop_duplicates(subset=["PRODUCT_ID"])
                    )
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    st.markdown('<h2 style="font-size: 24px; font-weight: 700; margin-bottom: 20px; color: #1F2937; width: 100%;">Order Details</h2>', unsafe_allow_html=True)
                    
                    # Increase tab size with CSS
                    st.markdown("""
                    <style>
                    [data-testid="stTabs"] button {
                        font-size: 16px !important;
                        padding: 14px 24px !important;
                        font-weight: 600 !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    tab1, tab2, tab3 = st.tabs(["Product Info", "Dealer Info", "Bill Of Materials"])
                    
                    with tab1:
                        st.markdown('<h2 style="font-size: 28px; font-weight: 700; margin-bottom: 20px; color: #1F2937;">Product Information</h2>', unsafe_allow_html=True)
                        
                        product_ids = (
                            product_rows["PRODUCT_ID"]
                            .dropna()
                            .astype(str)
                            .unique()
                            .tolist()
                        )
                        
                        if product_ids:
                            product_ids_safe = ",".join(
                                "'" + pid.replace("'", "''") + "'"
                                for pid in product_ids
                            )
                            
                            product_info = run_query(f"""
                                SELECT
                                    c.PRODUCT_ID,
                                    c.PRODUCT_NAME,
                                    c.MATERIAL_TYPE,
                                    c.MATERIAL_GROUP,
                                    c.PRODUCT_HIERARCHY,
                                    c.UNIT_OF_MEASURE,
                                    c.PRODUCT_TYPE,
                                    c.PRODUCT_CATEGORY,
                                    c.PRODUCT_FAMILY,
                                    c.PRODUCT_GROUP,
                                    c.CONFIG_ID,
                                    c.CONFIG_NAME,
                                    c.CONFIG_TYPE,
                                    c.CONFIG_STATUS,
                                    c.IS_DEFAULT_CONFIG,
                                    c.UNIT_PRICE,
                                    o.TOTAL_QUANTITY_ORDERED
                                FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.PRODUCT_CATALOG_VW c
                                JOIN (
                                    SELECT
                                        PRODUCT_ID,
                                        CONFIG_ID,
                                        QUANTITY AS TOTAL_QUANTITY_ORDERED
                                    FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.FACT_ORDER_HISTORY_VW
                                    WHERE {order_filter}
                                ) o
                                  ON c.PRODUCT_ID = o.PRODUCT_ID
                                 AND c.CONFIG_ID = o.CONFIG_ID
                                QUALIFY ROW_NUMBER() OVER (
                                    PARTITION BY c.PRODUCT_ID
                                    ORDER BY c.IS_DEFAULT_CONFIG DESC
                                ) = 1
                                ORDER BY c.PRODUCT_NAME
                            """)
                            
                            if not product_info.empty:
                                for col in ["UNIT_PRICE"]:
                                    product_info[col] = product_info[col].apply(
                                        lambda x: f"${float(x):,.2f}" if x else "$0.00"
                                    )
                                
                                product_info["TOTAL_QUANTITY_ORDERED"] = (
                                    product_info["TOTAL_QUANTITY_ORDERED"].fillna(0).astype(int)
                                )
                                
                                product_info["IS_DEFAULT_CONFIG"] = product_info[
                                    "IS_DEFAULT_CONFIG"
                                ].apply(lambda x: "Yes" if x else "No")
                                
                                st.dataframe(product_info, use_container_width=True, hide_index=True)
                            else:
                                st.warning("No product configurations matched the order unit price")
                        else:
                            st.info("No products associated with selected orders")
                    
                    with tab2:
                        st.markdown('<h2 style="font-size: 28px; font-weight: 700; margin-bottom: 20px; color: #1F2937;">Dealer Information</h2>', unsafe_allow_html=True)
                        
                        dealer_ids = (
                            order_details['DEALER_ID']
                            .dropna()
                            .astype(str)
                            .unique()
                            .tolist()
                        )
                        
                        if dealer_ids:
                            dealer_ids_safe = ",".join(
                                "'" + did.replace("'", "''") + "'"
                                for did in dealer_ids
                            )
                            
                            dealer_info = run_query(f"""
                                SELECT
                                    f.DEALER_ID,
                                    f.DEALER_NAME,
                                    d.DEALER_TYPE,
                                    d.COUNTRY,
                                    d.REGION,
                                    d.CITY,
                                    SUM(k.ORDER_COUNT) AS TOTAL_ORDERS,
                                    SUM(k.REVENUE) AS TOTAL_REVENUE,
                                    CASE
                                        WHEN SUM(k.ORDER_COUNT) > 0
                                        THEN SUM(k.REVENUE) / SUM(k.ORDER_COUNT)
                                        ELSE 0
                                    END AS AVG_ORDER_VALUE
                                FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.FACT_ORDER_HISTORY_VW f
                                LEFT JOIN SALES_OPS_PLANNING_DEV.INFORMATION_MART.DEALER_ORDER_KPI_VW k
                                    ON f.DEALER_ID = k.DEALER_ID
                                LEFT JOIN (SELECT * FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.DIM_DEALER_VW WHERE CURRENT_FLAG = 'Y') d
                                    ON f.DEALER_ID = d.DEALER_ID
                                WHERE f.DEALER_ID IN ({dealer_ids_safe})
                                GROUP BY
                                    f.DEALER_ID,
                                    f.DEALER_NAME,
                                    d.DEALER_TYPE,
                                    d.COUNTRY,
                                    d.REGION,
                                    d.CITY
                                ORDER BY f.DEALER_NAME
                            """)
                            
                            dealer_info["TOTAL_REVENUE"] = dealer_info["TOTAL_REVENUE"].apply(
                                lambda x: f"${float(x):,.0f}" if x else "$0"
                            )
                            dealer_info["AVG_ORDER_VALUE"] = dealer_info["AVG_ORDER_VALUE"].apply(
                                lambda x: f"${float(x):,.0f}" if x else "$0"
                            )
                            dealer_info["TOTAL_ORDERS"] = dealer_info["TOTAL_ORDERS"].fillna(0).astype(int)
                            
                            st.dataframe(dealer_info, use_container_width=True, hide_index=True)
                        else:
                            st.info("No dealer information found")
                    
                    with tab3:
                        st.markdown('<h2 style="font-size: 28px; font-weight: 700; margin-bottom: 20px; color: #1F2937;">Bill Of Materials</h2>', unsafe_allow_html=True)
                        
                        parent_product_ids = (
                            product_rows['PRODUCT_ID']
                            .dropna()
                            .astype(str)
                            .unique()
                            .tolist()
                        )
                        
                        if parent_product_ids:
                            parent_product_ids_safe = ",".join(
                                "'" + pid.replace("'", "''") + "'"
                                for pid in parent_product_ids
                            )
                            
                            bom_df = run_query(f"""
                                SELECT
                                    PARENT_PRODUCT,
                                    PARENT_PRODUCT_NAME,
                                    CHILD_PRODUCT,
                                    CHILD_PRODUCT_NAME,
                                    QUANTITY_PER_ASSEMBLY,
                                    UNIT_OF_MEASURE,
                                    SCRAP_FACTOR
                                FROM SALES_OPS_PLANNING_DEV.INFORMATION_MART.PRODUCT_BOM_VW
                                WHERE PARENT_PRODUCT IN ({parent_product_ids_safe})
                                ORDER BY
                                    PARENT_PRODUCT
                            """)
                            
                            if not bom_df.empty:
                                
                                if "SCRAP_FACTOR" in bom_df.columns:
                                    bom_df["SCRAP_FACTOR"] = bom_df["SCRAP_FACTOR"].apply(
                                        lambda x: f"{float(x) * 100:.1f}%" if x is not None else "0.0%"
                                    )
                                
                                st.dataframe(bom_df, use_container_width=True, hide_index=True)
                            else:
                                st.info("No BOM data found for selected products")
                        else:
                            st.info("No parent products available for BOM lookup")
            
            except Exception as e:
                st.error(f"Error loading orders: {str(e)}")
    else:
        st.info("Select one or more Order IDs to view details")

# ============== FORECAST PAGE ==============
elif st.session_state.current_page == "Forecast":
    st.markdown('<div class="welcome-title">Sales Forecast</div>', unsafe_allow_html=True)
    st.markdown("Projected demand and revenue")
    
    # Filters row
    available_products = run_query(f"""
        SELECT DISTINCT PRODUCT_ID, PRODUCT_NAME
        FROM {DATABASE}.{SCHEMA}.PRODUCT_FORECAST_KPI_VW
        ORDER BY PRODUCT_NAME
    """)
    
    available_months = run_query(f"""
        SELECT DISTINCT TO_CHAR(DATE_TRUNC('MONTH', FORECAST_PERIOD_END), 'YYYY-MM') AS MONTH
        FROM {DATABASE}.{SCHEMA}.PRODUCT_FORECAST_KPI_VW
        ORDER BY MONTH
    """)
    
    filter_col1, filter_col2 = st.columns([3, 1])
    
    with filter_col1:
        if not available_products.empty:
            product_options = available_products.apply(lambda row: f"{row['PRODUCT_ID']} - {row['PRODUCT_NAME']}", axis=1).tolist()
            selected_products = st.multiselect(
                "Filter by Product",
                options=product_options,
                default=[],
                key="forecast_product_filter"
            )
            selected_product_ids = [opt.split(' - ')[0] for opt in selected_products] if selected_products else []
            if selected_product_ids:
                product_ids_safe = ",".join([f"'{pid.replace(chr(39), chr(39)+chr(39))}'" for pid in selected_product_ids])
                product_filter_clause = f"AND f.PRODUCT_ID IN ({product_ids_safe})"
            else:
                product_filter_clause = ""
        else:
            product_filter_clause = ""
            selected_product_ids = []
    
    with filter_col2:
        if not available_months.empty:
            month_options = ['All'] + available_months['MONTH'].tolist()
            selected_month = st.selectbox("Filter by Month", options=month_options, index=0, key="forecast_month_filter")
            if selected_month != 'All':
                forecast_month_clause = f"AND TO_CHAR(DATE_TRUNC('MONTH', f.FORECAST_PERIOD_END), 'YYYY-MM') = '{selected_month}'"
            else:
                forecast_month_clause = ""
        else:
            forecast_month_clause = ""
    
    # Monthly Forecast Charts
    forecast_col1, forecast_col2 = st.columns(2)
    
    with forecast_col1:
        with st.container(border=True):
            st.markdown('<div class="chart-title">Monthly Forecast Quantity</div>', unsafe_allow_html=True)
            
            forecast_qty = run_query(f"""
            SELECT 
                TO_CHAR(DATE_TRUNC('MONTH', F.FORECAST_PERIOD_END), 'YYYY-MM') AS MONTH,
                SUM(F.FORECAST_QUANTITY) AS QTY
            FROM {DATABASE}.{SCHEMA}.PRODUCT_FORECAST_KPI_VW F
            WHERE 1=1 {product_filter_clause} {forecast_month_clause}
            GROUP BY MONTH
            ORDER BY MONTH
            """)
            
            if not forecast_qty.empty:
                forecast_qty['QTY_LABEL'] = forecast_qty['QTY'].map(lambda v: f"{v/1000:.0f}K" if v >= 1000 else f"{v:,.0f}")
                base = alt.Chart(forecast_qty).encode(
                    x=alt.X('QTY:Q', title='Total Quantity'),
                    y=alt.Y('MONTH:N', title='Month', sort=None),
                    tooltip=['MONTH', alt.Tooltip('QTY:Q', format=',')]
                )
                bars = base.mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, color='#60A5FA')
                labels = base.mark_text(align='left', baseline='middle', dx=4, color='#111827', fontSize=11).encode(
                    text='QTY_LABEL:N'
                )
                chart = (bars + labels).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No forecast quantity data available")
    
    with forecast_col2:
        with st.container(border=True):
            st.markdown('<div class="chart-title">Monthly Forecast Revenue</div>', unsafe_allow_html=True)
            
            forecast_rev = run_query(f"""
            SELECT 
                TO_CHAR(DATE_TRUNC('MONTH', F.FORECAST_PERIOD_END), 'YYYY-MM') AS MONTH,
                SUM(F.FORECAST_REVENUE) / 1000000.0 AS REVENUE_M
            FROM {DATABASE}.{SCHEMA}.PRODUCT_FORECAST_KPI_VW F
            WHERE 1=1 {product_filter_clause} {forecast_month_clause}
            GROUP BY MONTH
            ORDER BY MONTH
            """)
            
            if not forecast_rev.empty:
                forecast_rev['REV_LABEL'] = forecast_rev['REVENUE_M'].map(lambda v: f"${v:.1f}M")
                base = alt.Chart(forecast_rev).encode(
                    x=alt.X('REVENUE_M:Q', title='Total Revenue ($M)'),
                    y=alt.Y('MONTH:N', title='Month', sort=None),
                    tooltip=['MONTH', alt.Tooltip('REVENUE_M:Q', format=',.1f')]
                )
                bars = base.mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, color='#4ADE80')
                labels = base.mark_text(align='left', baseline='middle', dx=4, color='#111827', fontSize=11).encode(
                    text='REV_LABEL:N'
                )
                chart = (bars + labels).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No forecast revenue data available")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Product Mix and Revenue Share
    forecast_mix_col1, forecast_mix_col2 = st.columns(2)
    
    with forecast_mix_col1:
        with st.container(border=True):
            st.markdown('<div class="chart-title">Product Mix: Quantity vs Revenue</div>', unsafe_allow_html=True)
            
            product_mix = run_query(f"""
            SELECT 
                p.PRODUCT_CATEGORY AS CATEGORY,
                p.PRODUCT_TYPE,
                SUM(f.FORECAST_QUANTITY) AS FORECAST_QUANTITY,
                SUM(f.FORECAST_REVENUE) / 1000000.0 AS FORECAST_REVENUE_M
            FROM {DATABASE}.{SCHEMA}.PRODUCT_FORECAST_KPI_VW f
            LEFT JOIN {DATABASE}.{SCHEMA}.DIM_PRODUCT_VW p ON f.PRODUCT_ID = p.PRODUCT_ID AND p.CURRENT_FLAG = 'Y'
            WHERE 1=1 {product_filter_clause} {forecast_month_clause} AND p.PRODUCT_CATEGORY IS NOT NULL AND p.PRODUCT_TYPE IS NOT NULL
            GROUP BY p.PRODUCT_CATEGORY, p.PRODUCT_TYPE
            ORDER BY FORECAST_REVENUE_M DESC
            """)
            
            if not product_mix.empty:
                # Use PRODUCT_TYPE for color encoding with Business Health colors
                unique_types = product_mix['PRODUCT_TYPE'].dropna().unique()
                type_colors = ['#4ADE80', '#FBBF24', '#60A5FA', '#F87171', '#A78BFA', '#F472B6']
                color_scale_type = alt.Scale(
                    domain=list(unique_types),
                    range=type_colors[:len(unique_types)]
                )
                
                chart = alt.Chart(product_mix).mark_circle(size=100).encode(
                    x=alt.X('FORECAST_QUANTITY:Q', title='Forecast Quantity'),
                    y=alt.Y('FORECAST_REVENUE_M:Q', title='Forecast Revenue (Millions $)'),
                    color=alt.Color('PRODUCT_TYPE:N', scale=color_scale_type, legend=alt.Legend(title='Product Type', orient='bottom', direction='horizontal')),
                    tooltip=['CATEGORY', 'PRODUCT_TYPE', alt.Tooltip('FORECAST_QUANTITY:Q', format=',', title='Quantity'), alt.Tooltip('FORECAST_REVENUE_M:Q', format=',.1f', title='Revenue ($M)')]
                ).properties(height=400)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No product mix data available")
    
    with forecast_mix_col2:
        with st.container(border=True):
            st.markdown('<div class="chart-title">Revenue Share by Product Family</div>', unsafe_allow_html=True)
            
            revenue_share = run_query(f"""
            SELECT 
                p.PRODUCT_FAMILY,
                SUM(f.FORECAST_REVENUE) / 1000000.0 AS REVENUE_M
            FROM {DATABASE}.{SCHEMA}.PRODUCT_FORECAST_KPI_VW f
            LEFT JOIN {DATABASE}.{SCHEMA}.DIM_PRODUCT_VW p ON f.PRODUCT_ID = p.PRODUCT_ID AND p.CURRENT_FLAG = 'Y'
            WHERE 1=1 {product_filter_clause} {forecast_month_clause} AND p.PRODUCT_FAMILY IS NOT NULL
            GROUP BY p.PRODUCT_FAMILY
            ORDER BY REVENUE_M DESC
            LIMIT 10
            """)
            
            if not revenue_share.empty:
                revenue_share = revenue_share.sort_values('REVENUE_M', ascending=False).reset_index(drop=True)
                revenue_share['REV_LABEL'] = revenue_share['REVENUE_M'].map(lambda v: f"${v:.1f}M")
                family_order = revenue_share['PRODUCT_FAMILY'].tolist()
                
                base = alt.Chart(revenue_share).encode(
                    x=alt.X('PRODUCT_FAMILY:N', title='Product Family', sort=family_order, axis=alt.Axis(labelAngle=-45, labelLimit=100)),
                    y=alt.Y('REVENUE_M:Q', title='Revenue ($M)'),
                    tooltip=[
                        'PRODUCT_FAMILY',
                        alt.Tooltip('REVENUE_M:Q', format=',.1f', title='Revenue ($M)')
                    ]
                )
                bars = base.mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color='#60A5FA')
                labels = base.mark_text(
                    align='center', baseline='bottom', dy=-4, color='#111827', fontSize=9
                ).encode(text='REV_LABEL:N')
                chart = (bars + labels).properties(height=400)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No revenue share data available")

# ============== AI AGENTS PAGE ==============
elif st.session_state.current_page == "AI Agents":

    CORTEX_MODEL = "llama3-8b"

    def _ai_complete(prompt: str) -> str:
        try:
            df = session.sql(
                "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS R",
                params=[CORTEX_MODEL, prompt[:3000]]
            ).to_pandas()
            return (df.at[0, "R"] or "").strip() if not df.empty else ""
        except Exception as e:
            return f"[AI generation failed: {str(e)[:100]}]"

    # ── Helper: get the actual data date range from the table ─────────────────
    @st.cache_data(ttl=300)
    def _get_data_range():
        df = run_query(f"""
            SELECT
                MIN(EFFECTIVE_DATE) AS MIN_DT,
                MAX(EFFECTIVE_DATE) AS MAX_DT,
                COUNT(DISTINCT DEALER_NAME) AS DEALER_COUNT,
                COUNT(DISTINCT ORDER_ID) AS ORDER_COUNT
            FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
            WHERE CURRENT_FLAG = 'Y'
        """)
        if df.empty or df["MIN_DT"].iloc[0] is None:
            return None
        return df.iloc[0]

    # ── CSS ───────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .ag-hero {
        background: linear-gradient(135deg,#1E40AF 0%,#5046e5 100%);
        border-radius:14px; padding:28px 32px; margin-bottom:24px; color:#fff;
    }
    .ag-hero h1 { font-size:26px; font-weight:900; margin:0 0 6px 0; color:#fff; }
    .ag-hero p  { font-size:14px; margin:0; opacity:.88; }
    .ag-card {
        background:#fff; border:2px solid #e5e7eb; border-radius:14px;
        padding:24px 20px 18px; transition:border-color .2s,box-shadow .2s;
    }
    .ag-card:hover { border-color:#5046e5; box-shadow:0 6px 20px rgba(80,70,229,.14); }
    .ag-icon {
        width:48px; height:48px; border-radius:12px; font-size:24px;
        display:flex; align-items:center; justify-content:center; margin-bottom:14px;
    }
    .ag-icon-rev { background:linear-gradient(135deg,#1E40AF,#3b82f6); }
    .ag-icon-int { background:linear-gradient(135deg,#5046e5,#7c3aed); }
    .ag-title { font-size:16px; font-weight:800; color:#0f172a; margin-bottom:6px; }
    .ag-desc  { font-size:13px; color:#64748b; line-height:1.6; margin-bottom:16px; }
    .ag-active-banner {
        border-radius:12px; padding:20px 24px; margin-bottom:20px; color:#fff;
        display:flex; align-items:center; gap:14px;
    }
    .ag-badge {
        display:inline-block; font-size:10px; font-weight:800; border-radius:999px;
        padding:2px 9px; text-transform:uppercase; letter-spacing:.4px; margin-bottom:8px;
    }
    .param-box {
        background:#f8fafc; border:1px solid #e2e8f0;
        border-radius:10px; padding:16px 18px; margin-bottom:4px;
    }
    .param-lbl { font-size:11px; font-weight:700; color:#64748b;
        text-transform:uppercase; letter-spacing:.5px; margin-bottom:8px; }
    .step-pill {
        display:inline-flex; align-items:center; gap:6px;
        background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;
        border-radius:999px; font-size:11px; font-weight:700;
        padding:4px 12px; margin:8px 0 10px 0;
    }
    .kpi-row {
        display:flex; justify-content:space-between; align-items:center;
        border-bottom:1px solid #f1f5f9; padding:7px 0; font-size:13px;
    }
    .kpi-val { font-weight:800; color:#0f172a; }
    .kpi-lbl { color:#64748b; }
    </style>
    """, unsafe_allow_html=True)

    # ── Detect data range once ─────────────────────────────────────────────────
    data_info = _get_data_range()
    if data_info is not None:
        data_min  = str(data_info["MIN_DT"])[:10]
        data_max  = str(data_info["MAX_DT"])[:10]
        total_dealers = int(data_info["DEALER_COUNT"])
        total_orders  = int(data_info["ORDER_COUNT"])
    else:
        data_min, data_max, total_dealers, total_orders = None, None, 0, 0

    active = st.session_state.get("active_agent")

    # ═══════════════════════════════════════════════════════════════════════════
    # CATALOG — always shown at the top
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="ag-hero">
        <h1>AI Agents</h1>
        <p>Autonomous multi-step workflows that analyse your order data, diagnose issues,
        optimise fulfillment routing, generate AI action plans and produce exportable
        reports — all in one click.</p>
    </div>
    """, unsafe_allow_html=True)

    if data_info is not None:
        st.caption(
            f"Data available: **{data_min}** → **{data_max}** | "
            f"**{total_dealers}** dealers | **{total_orders:,}** orders"
        )

    # ── Three agent cards ──────────────────────────────────────────────────────
    cat_c1, cat_c2, cat_c3 = st.columns(3, gap="large")

    with cat_c1:
        st.markdown("""
        <div class="ag-card">
            <div class="ag-icon ag-icon-rev">🔍</div>
            <div class="ag-title">Order Drop-Off Agent</div>
            <div class="ag-desc">
                Finds every stuck ORDER ID in your pipeline right now. Shows exactly
                how many days each order has been sitting at the same status, detects
                SLA breaches using expected vs actual delivery dates, and generates a
                per-order action list your ops team can act on directly.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        _btn1_type = "primary" if st.session_state.get("active_agent") == "dropoff" else "secondary"
        if st.button("Launch Order Drop-Off Agent", key="launch_dropoff",
                     use_container_width=True, type=_btn1_type):
            st.session_state.active_agent = "dropoff"
            st.session_state.agent_ran    = False
            st.session_state.agent_params = {}
            st.rerun()

    with cat_c2:
        st.markdown("""
        <div class="ag-card">
            <div class="ag-icon ag-icon-int">🚦</div>
            <div class="ag-title">Order Velocity Agent</div>
            <div class="ag-desc">
                Finds specific dealer–product combinations that are overdue for reorder
                right now — based on each dealer's own historical reorder cycle.
                Generates a proactive outreach task list with channel, message hook and
                urgency — before revenue is lost.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        _btn2_type = "primary" if st.session_state.get("active_agent") == "order_velocity" else "secondary"
        if st.button("Launch Order Velocity Agent", key="launch_int",
                     use_container_width=True, type=_btn2_type):
            st.session_state.active_agent = "order_velocity"
            st.session_state.agent_ran    = False
            st.session_state.agent_params = {}
            st.rerun()

    with cat_c3:
        st.markdown("""
        <div class="ag-card">
            <div class="ag-icon" style="background:linear-gradient(135deg,#0891b2,#0f766e);">🚚</div>
            <div class="ag-title">Smart Fulfillment Agent</div>
            <div class="ag-desc">
                Optimises order routing across your warehouses, dark stores and retail
                outlets. For any product going to any region, finds the <b>fastest</b>
                node (Speed mode) or the <b>cheapest</b> node (Cost mode) — with full
                stock check, carrier, cost and delivery-day breakdown.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        _btn3_type = "primary" if st.session_state.get("active_agent") == "smart_fulfillment" else "secondary"
        if st.button("Launch Smart Fulfillment Agent", key="launch_sf",
                     use_container_width=True, type=_btn3_type):
            st.session_state.active_agent = "smart_fulfillment"
            st.session_state.agent_ran    = False
            st.session_state.agent_params = {}
            st.rerun()

    # ── If no agent is active, stop here ──────────────────────────────────────
    if active is None:
        st.stop()

    st.markdown("<hr style='margin:24px 0 20px;border:none;border-top:2px solid #e5e7eb;'>",
                unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════════════════════════
    # AGENT 1 — ORDER DROP-OFF AGENT
    # ═══════════════════════════════════════════════════════════════════════════
    if active == "dropoff":

        col_hd, col_back = st.columns([5, 1])
        with col_back:
            if st.button("✕ Close Agent", key="close_dropoff", type="secondary",
                         use_container_width=True):
                st.session_state.active_agent = None
                st.session_state.agent_ran    = False
                st.rerun()

        st.markdown("""
        <div class="ag-active-banner" style="background:linear-gradient(135deg,#0f766e,#0284c7);">
            <div style="font-size:32px;">🔍</div>
            <div>
                <div style="font-size:18px;font-weight:900;">Order Drop-Off Agent</div>
                <div style="font-size:13px;opacity:.9;">
                    Maps your 4-stage pipeline, finds where orders are getting stuck,
                    identifies worst-performing dealers per stage, and generates AI fixes.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Parameters ────────────────────────────────────────────────────────
        st.markdown("#### Parameters")
        dp1, dp2, dp3 = st.columns(3, gap="medium")

        with dp1:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Analysis Period</div>', unsafe_allow_html=True)
                do_period = st.selectbox(
                    "Period", ["Full data range", "Latest 75% of data",
                               "Latest 50% of data", "Latest 25% of data"],
                    key="do_period", label_visibility="collapsed"
                )
                do_frac_map = {"Full data range": 1.0, "Latest 75% of data": 0.75,
                               "Latest 50% of data": 0.5, "Latest 25% of data": 0.25}
                do_frac = do_frac_map[do_period]
                st.caption("Uses your actual data dates automatically.")

        with dp2:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Min Orders per Dealer</div>', unsafe_allow_html=True)
                do_min_orders = st.slider("Min", 1, 20, 1, key="do_min",
                                          label_visibility="collapsed")
                st.caption(f"Only dealers with ≥ **{do_min_orders}** total orders.")

        with dp3:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Top N Dealers to Show per Stage</div>', unsafe_allow_html=True)
                do_top_n = st.slider("Top N", 3, 15, 5, key="do_topn",
                                     label_visibility="collapsed")
                st.caption(f"Show **{do_top_n}** worst-performing dealers per stage.")

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Run Order Drop-Off Agent", key="run_dropoff",
                     type="primary", use_container_width=True):
            st.session_state.agent_ran    = True
            st.session_state.agent_params = {
                "frac": do_frac, "min_orders": do_min_orders,
                "top_n": do_top_n, "period_label": do_period
            }

        if not st.session_state.get("agent_ran") or            st.session_state.agent_params.get("frac") is None:
            st.info("Set parameters above and click **Run Order Drop-Off Agent**.")
            st.stop()

        params_do     = st.session_state.agent_params
        do_f          = params_do["frac"]
        do_minord     = params_do["min_orders"]
        do_topn       = params_do["top_n"]
        do_period_lbl = params_do["period_label"]

        st.markdown("---")
        st.markdown("#### Running Agent...")

        # ── STEP 1: Overall pipeline funnel ───────────────────────────────────
        st.markdown('<div class="step-pill">⚙ Step 1 — Building Pipeline Funnel</div>',
                    unsafe_allow_html=True)

        STAGES = ["PLACED", "CONFIRMED", "SHIPPED", "DELIVERED"]

        with st.spinner("Counting orders at each pipeline stage..."):
            funnel_df = run_query(f"""
                WITH date_bounds AS (
                    SELECT
                        MIN(EFFECTIVE_DATE) AS dt_min,
                        MAX(EFFECTIVE_DATE) AS dt_max,
                        DATEDIFF('day', MIN(EFFECTIVE_DATE), MAX(EFFECTIVE_DATE)) AS total_days
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                    WHERE CURRENT_FLAG = 'Y'
                ),
                analysis_window AS (
                    SELECT
                        dt_max,
                        CASE WHEN {do_f} >= 1.0 THEN dt_min
                             ELSE DATEADD('day', -ROUND(total_days * {do_f}, 0), dt_max)
                        END AS a_start
                    FROM date_bounds
                ),
                orders_in_window AS (
                    SELECT DISTINCT f.ORDER_ID
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                    CROSS JOIN analysis_window aw
                    WHERE f.CURRENT_FLAG = 'Y'
                      AND f.EFFECTIVE_DATE BETWEEN aw.a_start AND aw.dt_max
                ),
                stage_reach AS (
                    SELECT
                        f.ORDER_ID,
                        MAX(CASE WHEN UPPER(f.ORDER_STATUS) = 'PLACED'    THEN 1 ELSE 0 END) AS reached_placed,
                        MAX(CASE WHEN UPPER(f.ORDER_STATUS) = 'CONFIRMED' THEN 1 ELSE 0 END) AS reached_confirmed,
                        MAX(CASE WHEN UPPER(f.ORDER_STATUS) = 'SHIPPED'   THEN 1 ELSE 0 END) AS reached_shipped,
                        MAX(CASE WHEN UPPER(f.ORDER_STATUS) = 'DELIVERED' THEN 1 ELSE 0 END) AS reached_delivered
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                    INNER JOIN orders_in_window o ON f.ORDER_ID = o.ORDER_ID
                    WHERE f.CURRENT_FLAG = 'Y'
                    GROUP BY f.ORDER_ID
                )
                SELECT
                    SUM(reached_placed)    AS PLACED_COUNT,
                    SUM(reached_confirmed) AS CONFIRMED_COUNT,
                    SUM(reached_shipped)   AS SHIPPED_COUNT,
                    SUM(reached_delivered) AS DELIVERED_COUNT,
                    COUNT(*)               AS TOTAL_ORDERS
                FROM stage_reach
            """)

        if funnel_df.empty or funnel_df["TOTAL_ORDERS"].iloc[0] == 0:
            st.warning("No orders found in the selected period. Try 'Full data range'.")
            st.stop()

        placed_n    = int(funnel_df["PLACED_COUNT"].iloc[0]    or 0)
        confirmed_n = int(funnel_df["CONFIRMED_COUNT"].iloc[0] or 0)
        shipped_n   = int(funnel_df["SHIPPED_COUNT"].iloc[0]   or 0)
        delivered_n = int(funnel_df["DELIVERED_COUNT"].iloc[0] or 0)
        total_n     = int(funnel_df["TOTAL_ORDERS"].iloc[0]    or 0)

        # Use PLACED as base (100%)
        base = placed_n if placed_n > 0 else 1

        stage_data = [
            {"stage": "PLACED",    "count": placed_n,    "pct": 100.0},
            {"stage": "CONFIRMED", "count": confirmed_n, "pct": round(confirmed_n/base*100, 1)},
            {"stage": "SHIPPED",   "count": shipped_n,   "pct": round(shipped_n/base*100, 1)},
            {"stage": "DELIVERED", "count": delivered_n, "pct": round(delivered_n/base*100, 1)},
        ]

        # Dropout between consecutive stages
        for i in range(1, len(stage_data)):
            prev = stage_data[i-1]["count"]
            curr = stage_data[i]["count"]
            stage_data[i]["dropout_n"]   = max(0, prev - curr)
            stage_data[i]["dropout_pct"] = round(max(0, prev - curr) / prev * 100, 1) if prev > 0 else 0
        stage_data[0]["dropout_n"]   = 0
        stage_data[0]["dropout_pct"] = 0.0

        # Find biggest dropout stage
        biggest_drop_stage = max(stage_data[1:], key=lambda x: x["dropout_pct"])

        # ── STEP 2: Funnel visualisation ──────────────────────────────────────
        st.markdown('<div class="step-pill">⚙ Step 2 — Pipeline Funnel Analysis</div>',
                    unsafe_allow_html=True)

        st.markdown("#### Order Pipeline Funnel")

        # Funnel tiles
        stage_colors = {
            "PLACED":    ("#1e40af", "#dbeafe"),
            "CONFIRMED": ("#0284c7", "#e0f2fe"),
            "SHIPPED":   ("#0f766e", "#d1fae5"),
            "DELIVERED": ("#059669", "#d1fae5"),
        }
        tile_cols = st.columns(4)
        for sd, tc in zip(stage_data, tile_cols):
            fg, bg = stage_colors[sd["stage"]]
            dropout_badge = ""
            if sd["dropout_pct"] > 0:
                bcol = "#dc2626" if sd["dropout_pct"] >= 20 else "#d97706" if sd["dropout_pct"] >= 10 else "#64748b"
                dropout_badge = (
                    f'<div style="margin-top:8px;font-size:11px;font-weight:700;color:{bcol};">'
                    f'▼ {sd["dropout_pct"]:.1f}% dropped from prev stage</div>'
                )
            is_worst = sd["stage"] == biggest_drop_stage["stage"]
            border   = "2px solid #dc2626" if is_worst else f"2px solid {bg}"
            _bottleneck_badge = (
                '<div style="font-size:10px;font-weight:800;color:#dc2626;margin-bottom:4px;">⚠ BOTTLENECK</div>'
                if is_worst else ""
            )
            tc.markdown(
                f'<div style="background:{bg};border:{border};border-radius:12px;'
                f'padding:16px 12px;text-align:center;">'
                + _bottleneck_badge +
                f'<div style="font-size:22px;font-weight:900;color:{fg};">{sd["count"]:,}</div>'
                f'<div style="font-size:12px;font-weight:700;color:{fg};">{sd["stage"]}</div>'
                f'<div style="font-size:12px;color:{fg};opacity:.8;">{sd["pct"]:.1f}% of placed</div>'
                + dropout_badge +
                '</div>',
                unsafe_allow_html=True
            )

        # Funnel flow summary
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        funnel_row_cols = st.columns(3)
        for i, sd in enumerate(stage_data[1:], 1):
            fcol = funnel_row_cols[i-1]
            prev_s = stage_data[i-1]["stage"]
            drop_c = "#dc2626" if sd["dropout_pct"] >= 20 else "#d97706" if sd["dropout_pct"] >= 10 else "#059669"
            fcol.markdown(
                f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;'
                f'padding:12px 14px;text-align:center;">'
                f'<div style="font-size:11px;color:#64748b;margin-bottom:4px;">'
                f'{prev_s} → {sd["stage"]}</div>'
                f'<div style="font-size:20px;font-weight:900;color:{drop_c};">'
                f'{sd["dropout_pct"]:.1f}%</div>'
                f'<div style="font-size:11px;color:#64748b;">dropout rate</div>'
                f'<div style="font-size:12px;font-weight:700;color:{drop_c};">'
                f'{sd["dropout_n"]:,} orders lost</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # ── STEP 3: Dealer breakdown per stage ────────────────────────────────
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="step-pill">⚙ Step 3 — Dealer Breakdown by Stage</div>',
                    unsafe_allow_html=True)
        st.markdown("#### Dealer Performance by Stage")
        st.caption(f"Showing dealers with ≥ {do_minord} orders. "
                   f"Completion % = orders that reached this stage ÷ total placed orders for that dealer.")

        with st.spinner("Analysing dealer completion rates per stage..."):
            dealer_stage_df = run_query(f"""
                WITH date_bounds AS (
                    SELECT
                        MIN(EFFECTIVE_DATE) AS dt_min,
                        MAX(EFFECTIVE_DATE) AS dt_max,
                        DATEDIFF('day', MIN(EFFECTIVE_DATE), MAX(EFFECTIVE_DATE)) AS total_days
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                    WHERE CURRENT_FLAG = 'Y'
                ),
                analysis_window AS (
                    SELECT dt_max,
                        CASE WHEN {do_f} >= 1.0 THEN dt_min
                             ELSE DATEADD('day', -ROUND(total_days * {do_f}, 0), dt_max)
                        END AS a_start
                    FROM date_bounds
                ),
                dealer_orders AS (
                    SELECT DISTINCT f.ORDER_ID, f.DEALER_NAME
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                    CROSS JOIN analysis_window aw
                    WHERE f.CURRENT_FLAG = 'Y'
                      AND f.EFFECTIVE_DATE BETWEEN aw.a_start AND aw.dt_max
                ),
                dealer_stage_reach AS (
                    SELECT
                        d.DEALER_NAME,
                        d.ORDER_ID,
                        MAX(CASE WHEN UPPER(f.ORDER_STATUS) = 'PLACED'    THEN 1 ELSE 0 END) AS rp,
                        MAX(CASE WHEN UPPER(f.ORDER_STATUS) = 'CONFIRMED' THEN 1 ELSE 0 END) AS rc,
                        MAX(CASE WHEN UPPER(f.ORDER_STATUS) = 'SHIPPED'   THEN 1 ELSE 0 END) AS rs,
                        MAX(CASE WHEN UPPER(f.ORDER_STATUS) = 'DELIVERED' THEN 1 ELSE 0 END) AS rd
                    FROM dealer_orders d
                    JOIN {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                        ON d.ORDER_ID = f.ORDER_ID
                    WHERE f.CURRENT_FLAG = 'Y'
                    GROUP BY d.DEALER_NAME, d.ORDER_ID
                )
                SELECT
                    DEALER_NAME,
                    COUNT(*)              AS TOTAL_ORDERS,
                    SUM(rp)               AS PLACED_CNT,
                    SUM(rc)               AS CONFIRMED_CNT,
                    SUM(rs)               AS SHIPPED_CNT,
                    SUM(rd)               AS DELIVERED_CNT,
                    ROUND(SUM(rc) * 100.0 / NULLIF(SUM(rp), 0), 1) AS CONFIRMED_PCT,
                    ROUND(SUM(rs) * 100.0 / NULLIF(SUM(rp), 0), 1) AS SHIPPED_PCT,
                    ROUND(SUM(rd) * 100.0 / NULLIF(SUM(rp), 0), 1) AS DELIVERED_PCT
                FROM dealer_stage_reach
                GROUP BY DEALER_NAME
                HAVING COUNT(*) >= {do_minord}
                ORDER BY DELIVERED_PCT ASC
            """)

        if dealer_stage_df.empty:
            st.warning(f"No dealers found with ≥ {do_minord} orders. Reduce the min orders filter.")
            st.stop()

        # Full dealer table
        disp_dealer = dealer_stage_df.copy()
        for col in ["CONFIRMED_PCT", "SHIPPED_PCT", "DELIVERED_PCT"]:
            disp_dealer[col] = disp_dealer[col].apply(
                lambda v: f"{float(v):.1f}%" if v is not None else "0.0%"
            )
        disp_dealer.columns = ["Dealer", "Total Orders", "Placed", "Confirmed", "Shipped",
                                "Delivered", "Confirmed %", "Shipped %", "Delivered %"]
        st.dataframe(disp_dealer, use_container_width=True, hide_index=True)

        # Per-stage worst dealers
        st.markdown("#### Worst-Performing Dealers by Stage")
        stage_tabs = st.tabs(["PLACED → CONFIRMED", "CONFIRMED → SHIPPED", "SHIPPED → DELIVERED"])

        stage_pct_cols = ["CONFIRMED_PCT", "SHIPPED_PCT", "DELIVERED_PCT"]
        stage_cnt_pairs = [("PLACED_CNT","CONFIRMED_CNT"), ("CONFIRMED_CNT","SHIPPED_CNT"),
                           ("SHIPPED_CNT","DELIVERED_CNT")]
        stage_labels    = ["PLACED → CONFIRMED", "CONFIRMED → SHIPPED", "SHIPPED → DELIVERED"]

        for tab, stage_pct, (from_col, to_col), slbl in zip(
            stage_tabs, stage_pct_cols, stage_cnt_pairs, stage_labels
        ):
            with tab:
                worst = dealer_stage_df.copy()
                worst = worst[worst[from_col] > 0].copy()
                worst["STAGE_DROP_PCT"] = (
                    (worst[from_col] - worst[to_col]) / worst[from_col] * 100
                ).clip(lower=0).round(1)
                worst = worst.nlargest(do_topn, "STAGE_DROP_PCT")[
                    ["DEALER_NAME", from_col, to_col, "STAGE_DROP_PCT"]
                ].copy()
                worst.columns = ["Dealer", f"Orders at '{from_col.replace('_CNT','')}'",
                                  f"Reached '{to_col.replace('_CNT','')}'", "Drop-off %"]

                if worst.empty:
                    st.info("No drop-off data for this stage.")
                else:
                    for _, wr in worst.iterrows():
                        dpct  = float(wr["Drop-off %"])
                        color = "#dc2626" if dpct >= 25 else "#d97706" if dpct >= 10 else "#059669"
                        _from_lbl = f"Orders at '{from_col.replace('_CNT','')}'" 
                        _to_lbl   = f"Reached '{to_col.replace('_CNT','')}'" 
                        from_val  = int(wr[_from_lbl]) if _from_lbl in wr.index and not pd.isna(wr[_from_lbl]) else 0
                        to_val    = int(wr[_to_lbl])   if _to_lbl   in wr.index and not pd.isna(wr[_to_lbl])   else 0
                        st.markdown(
                            f'<div style="background:#fff;border:1.5px solid #e5e7eb;'
                            f'border-left:4px solid {color};border-radius:10px;'
                            f'padding:12px 16px;margin-bottom:8px;display:flex;'
                            f'justify-content:space-between;align-items:center;">'
                            f'<div>'
                            f'<div style="font-size:14px;font-weight:700;color:#0f172a;">'
                            f'{html.escape(str(wr["Dealer"]))}</div>'
                            f'<div style="font-size:12px;color:#64748b;margin-top:2px;">'
                            f'{from_val:,} orders entered → {to_val:,} progressed</div>'
                            f'</div>'
                            f'<div style="text-align:right;">'
                            f'<div style="font-size:22px;font-weight:900;color:{color};">'
                            f'{dpct:.1f}%</div>'
                            f'<div style="font-size:11px;color:{color};font-weight:600;">drop-off</div>'
                            f'</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

        # ── STEP 4: AI Bottleneck Analysis ────────────────────────────────────
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="step-pill">⚙ Step 4 — AI Bottleneck Analysis</div>',
                    unsafe_allow_html=True)
        st.markdown("#### AI Bottleneck & Fix Recommendations")

        # Get worst dealers at the bottleneck stage
        bneck_stage_idx = STAGES.index(biggest_drop_stage["stage"])
        if bneck_stage_idx > 0:
            bneck_from = STAGES[bneck_stage_idx - 1]
            bneck_to   = biggest_drop_stage["stage"]
            bneck_from_col = f"{bneck_from}_CNT"
            bneck_to_col   = f"{bneck_to}_CNT"

            bneck_dealers = dealer_stage_df.copy()
            bneck_dealers = bneck_dealers[bneck_dealers[bneck_from_col] > 0].copy()
            bneck_dealers["DROP_PCT"] = (
                (bneck_dealers[bneck_from_col] - bneck_dealers[bneck_to_col])
                / bneck_dealers[bneck_from_col] * 100
            ).clip(lower=0).round(1)
            bneck_dealers = bneck_dealers.nlargest(min(5, do_topn), "DROP_PCT")
        else:
            bneck_from, bneck_to = "PLACED", "CONFIRMED"
            bneck_dealers = pd.DataFrame()

        # Build dealer summary for AI
        bneck_dealer_txt = ""
        if not bneck_dealers.empty:
            bneck_dealer_txt = "\n".join(
                f"- {row['DEALER_NAME']}: {float(row['DROP_PCT']):.1f}% drop "
                f"({int(row[bneck_from_col])} → {int(row[bneck_to_col])} orders)"
                for _, row in bneck_dealers.iterrows()
            )

        with st.spinner("Generating AI bottleneck analysis..."):
            ai_bottleneck = _ai_complete(
                f"You are a Sales & Operations analyst reviewing an order pipeline.\n\n"
                f"PIPELINE SUMMARY (based on {placed_n:,} placed orders):\n"
                f"- PLACED:    {placed_n:,} orders (100%)\n"
                f"- CONFIRMED: {confirmed_n:,} orders ({stage_data[1]['pct']:.1f}%) — "
                f"{stage_data[1]['dropout_pct']:.1f}% dropout\n"
                f"- SHIPPED:   {shipped_n:,} orders ({stage_data[2]['pct']:.1f}%) — "
                f"{stage_data[2]['dropout_pct']:.1f}% dropout\n"
                f"- DELIVERED: {delivered_n:,} orders ({stage_data[3]['pct']:.1f}%) — "
                f"{stage_data[3]['dropout_pct']:.1f}% dropout\n\n"
                f"BIGGEST BOTTLENECK: {bneck_from} → {bneck_to} "
                f"({biggest_drop_stage['dropout_pct']:.1f}% dropout, "
                f"{biggest_drop_stage['dropout_n']:,} orders lost)\n\n"
                f"WORST DEALERS AT THIS STAGE:\n{bneck_dealer_txt}\n\n"
                f"Provide:\n"
                f"1. Bottleneck diagnosis (2 sentences — what is likely causing orders to stop "
                f"at the {bneck_from} → {bneck_to} stage, citing the dropout numbers)\n"
                f"2. Three specific fixes with expected outcomes (bullet points)\n"
                f"3. One dealer-specific action for the worst-performing dealer\n"
                f"Be direct, cite the numbers, no generic advice."
            )

        # Render AI output
        _ai_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', ai_bottleneck)
        _ai_html = html.escape(_ai_html).replace("&lt;strong&gt;","<strong>").replace("&lt;/strong&gt;","</strong>")
        _ai_html = _ai_html.replace("\n", "<br/>")
        st.markdown(
            f'<div style="background:#f0fdf4;border-left:4px solid #059669;'
            f'border-radius:10px;padding:18px 20px;font-size:13px;line-height:1.8;">'
            f'{_ai_html}</div>',
            unsafe_allow_html=True
        )

        # ── STEP 5: Per-dealer AI fixes for worst bottleneck dealers ──────────
        if not bneck_dealers.empty:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown(f"#### Per-Dealer Action Plans — {bneck_from} → {bneck_to} Bottleneck")

            for _, drow in bneck_dealers.iterrows():
                d_name  = str(drow["DEALER_NAME"])
                d_drop  = float(drow["DROP_PCT"])
                d_from  = int(drow[bneck_from_col])
                d_to    = int(drow[bneck_to_col])
                d_slug  = d_name.replace(" ","_").replace("/","_")[:16]

                with st.spinner(f"Generating fix for {d_name}..."):
                    d_fix = _ai_complete(
                        f"Order pipeline issue for dealer '{d_name}':\n"
                        f"Stage {bneck_from} → {bneck_to}: {d_drop:.1f}% dropout "
                        f"({d_from} orders entered, only {d_to} progressed).\n\n"
                        f"Write a specific 3-point action plan to fix this dropout.\n"
                        f"Each point must include: the action, who does it, and expected outcome.\n"
                        f"Be specific to the {bneck_from} → {bneck_to} transition. No generic advice."
                    )

                d_color = "#dc2626" if d_drop >= 25 else "#d97706" if d_drop >= 10 else "#059669"
                with st.expander(
                    f"{'🔴' if d_drop >= 25 else '🟡'} {d_name}  |  "
                    f"Drop-off: {d_drop:.1f}%  |  {d_from} → {d_to} orders at {bneck_to}",
                    expanded=True
                ):
                    _fix_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', d_fix)
                    _fix_html = html.escape(_fix_html).replace("&lt;strong&gt;","<strong>").replace("&lt;/strong&gt;","</strong>")
                    _fix_html = _fix_html.replace("\n", "<br/>")
                    st.markdown(
                        f'<div style="background:#fff;border-left:4px solid {d_color};'
                        f'border-radius:8px;padding:14px 16px;font-size:13px;line-height:1.75;">'
                        f'{_fix_html}</div>',
                        unsafe_allow_html=True
                    )

                    # Action buttons
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    st.markdown("**Quick Actions**")
                    da1, da2, da3 = st.columns(3, gap="small")
                    with da1:
                        _dflag_key = f"do_flag_{d_slug}"
                        _dflagged  = st.session_state.get(_dflag_key, False)
                        if st.button(
                            "✅ Flagged for Follow-up" if _dflagged else "🚩 Flag for Follow-up",
                            key=f"do_flag_btn_{d_slug}", use_container_width=True, type="secondary"
                        ):
                            st.session_state[_dflag_key] = not _dflagged
                            st.rerun()
                    with da2:
                        _dshow_key = f"do_txt_{d_slug}"
                        if st.button("📋 View Plan as Text", key=f"do_txt_btn_{d_slug}",
                                     use_container_width=True, type="secondary"):
                            st.session_state[_dshow_key] = not st.session_state.get(_dshow_key, False)
                            st.rerun()
                        if st.session_state.get(_dshow_key, False):
                            st.code(d_fix, language=None)
                    with da3:
                        _dplan_txt = (
                            f"ORDER DROP-OFF ACTION PLAN\n"
                            f"Dealer : {d_name}\n"
                            f"Stage  : {bneck_from} → {bneck_to}\n"
                            f"Drop   : {d_drop:.1f}% ({d_from} → {d_to} orders)\n\n"
                            f"{d_fix}"
                        )
                        st.download_button(
                            "⬇ Download This Plan",
                            data=_dplan_txt,
                            file_name=f"dropoff_{d_slug}_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            key=f"do_dl_{d_slug}",
                            use_container_width=True, type="secondary"
                        )

        # ── Export full report ─────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("**Export Full Pipeline Report**")
        exp_c1, exp_c2 = st.columns(2, gap="medium")

        with exp_c1:
            # Funnel summary CSV
            funnel_exp = pd.DataFrame([{
                "Stage": sd["stage"],
                "Order Count": sd["count"],
                "% of Placed": f"{sd['pct']:.1f}%",
                "Dropout %": f"{sd.get('dropout_pct',0):.1f}%",
                "Orders Lost": sd.get("dropout_n", 0),
            } for sd in stage_data])
            st.download_button(
                "⬇ Download Funnel Summary (CSV)",
                data=funnel_exp.to_csv(index=False),
                file_name=f"order_funnel_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", key="dl_funnel",
                use_container_width=True
            )

        with exp_c2:
            # Dealer breakdown CSV
            dealer_exp = dealer_stage_df.copy()
            dealer_exp.columns = ["Dealer","Total Orders","Placed","Confirmed","Shipped",
                                   "Delivered","Confirmed %","Shipped %","Delivered %"]
            st.download_button(
                "⬇ Download Dealer Breakdown (CSV)",
                data=dealer_exp.to_csv(index=False),
                file_name=f"dealer_dropoff_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", key="dl_dealer_drop",
                use_container_width=True
            )

    # AGENT 2 — ORDER VELOCITY AGENT
    # ═══════════════════════════════════════════════════════════════════════════
    elif active == "order_velocity":

        col_hd2, col_back2 = st.columns([5, 1])
        with col_back2:
            if st.button("✕ Close Agent", key="close_int", type="secondary",
                         use_container_width=True):
                st.session_state.active_agent = None
                st.session_state.agent_ran    = False
                st.rerun()

        st.markdown("""
        <div class="ag-active-banner" style="background:linear-gradient(135deg,#0f766e,#0891b2);">
            <div style="font-size:32px;">🚦</div>
            <div>
                <div style="font-size:18px;font-weight:900;">Order Velocity Agent</div>
                <div style="font-size:13px;opacity:.9;">
                    Detects dealers whose ordering pace has slowed — diagnoses whether it's
                    a specific product category cooling down or an overall activity drop,
                    then writes targeted re-engagement plans.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Parameters ────────────────────────────────────────────────────────
        st.markdown("#### Parameters")
        v1, v2, v3 = st.columns(3, gap="medium")

        with v1:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Split Point</div>', unsafe_allow_html=True)
                ov_split_lbl = st.selectbox(
                    "Split", ["50% / 50%", "33% / 67%", "25% / 75%"],
                    key="ov_split", label_visibility="collapsed"
                )
                ov_split_map = {"50% / 50%": 0.5, "33% / 67%": 0.33, "25% / 75%": 0.25}
                ov_sf        = ov_split_map[ov_split_lbl]
                st.caption("Splits data into current vs prior period using actual date range.")

        with v2:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Min Order Count Drop %</div>', unsafe_allow_html=True)
                ov_thresh = st.slider("Drop", 5, 60, 20, step=5,
                                      key="ov_thresh", label_visibility="collapsed")
                st.caption(f"Flag dealers with ≥ **{ov_thresh}%** fewer orders in current period.")

        with v3:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Max Dealers to Analyse</div>', unsafe_allow_html=True)
                ov_max = st.slider("Max", 3, 20, 10, key="ov_max",
                                   label_visibility="collapsed")
                st.caption(f"Analyse top **{ov_max}** slowdown dealers.")

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Run Order Velocity Agent", key="run_int",
                     type="primary", use_container_width=True):
            st.session_state.agent_ran    = True
            st.session_state.agent_params = {
                "split": ov_sf, "thresh": ov_thresh, "max": ov_max
            }

        if not st.session_state.get("agent_ran") or \
           st.session_state.agent_params.get("split") is None:
            st.info("Set parameters above and click **Run Order Velocity Agent**.")
            st.stop()

        params    = st.session_state.agent_params
        ov_sf     = params["split"]
        ov_thresh = params["thresh"]
        ov_max    = params["max"]

        st.markdown("---")
        st.markdown("#### Running Agent...")

        # ── STEP 1: Order count & frequency split ─────────────────────────────
        st.markdown('<div class="step-pill">⚙ Step 1 — Comparing Order Velocity (Current vs Prior Period)</div>',
                    unsafe_allow_html=True)

        with st.spinner("Fetching order counts across your data range..."):
            vel_df = run_query(f"""
                WITH date_bounds AS (
                    SELECT
                        MIN(EFFECTIVE_DATE) AS dt_min,
                        MAX(EFFECTIVE_DATE) AS dt_max,
                        DATEDIFF('day', MIN(EFFECTIVE_DATE), MAX(EFFECTIVE_DATE)) AS total_days
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                    WHERE CURRENT_FLAG = 'Y'
                ),
                split_date AS (
                    SELECT
                        dt_min, dt_max,
                        DATEADD('day', ROUND(total_days * {1 - ov_sf}, 0), dt_min) AS split_pt,
                        ROUND(total_days * {1 - ov_sf}, 0) AS prior_days,
                        ROUND(total_days * {ov_sf}, 0)     AS curr_days
                    FROM date_bounds
                ),
                current_p AS (
                    SELECT f.DEALER_NAME,
                           COUNT(DISTINCT f.ORDER_ID)   AS CURR_ORDERS,
                           COUNT(DISTINCT f.PRODUCT_ID) AS CURR_PRODUCTS,
                           SUM(f.TOTAL_AMOUNT)          AS CURR_REV,
                           s.curr_days
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                    CROSS JOIN split_date s
                    WHERE f.CURRENT_FLAG = 'Y'
                      AND f.EFFECTIVE_DATE > s.split_pt
                      AND f.EFFECTIVE_DATE <= s.dt_max
                    GROUP BY f.DEALER_NAME, s.curr_days
                ),
                prior_p AS (
                    SELECT f.DEALER_NAME,
                           COUNT(DISTINCT f.ORDER_ID)   AS PREV_ORDERS,
                           COUNT(DISTINCT f.PRODUCT_ID) AS PREV_PRODUCTS,
                           SUM(f.TOTAL_AMOUNT)          AS PREV_REV,
                           s.prior_days
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                    CROSS JOIN split_date s
                    WHERE f.CURRENT_FLAG = 'Y'
                      AND f.EFFECTIVE_DATE >= s.dt_min
                      AND f.EFFECTIVE_DATE <= s.split_pt
                    GROUP BY f.DEALER_NAME, s.prior_days
                )
                SELECT
                    c.DEALER_NAME,
                    COALESCE(p.PREV_ORDERS, 0)   AS PREV_ORDERS,
                    COALESCE(c.CURR_ORDERS, 0)   AS CURR_ORDERS,
                    COALESCE(p.PREV_PRODUCTS, 0) AS PREV_PRODUCTS,
                    COALESCE(c.CURR_PRODUCTS, 0) AS CURR_PRODUCTS,
                    COALESCE(p.PREV_REV, 0)      AS PREV_REV,
                    COALESCE(c.CURR_REV, 0)      AS CURR_REV,
                    ROUND(COALESCE(p.PREV_ORDERS,0) / NULLIF(p.prior_days,0), 4) AS PREV_ORDERS_PER_DAY,
                    ROUND(COALESCE(c.CURR_ORDERS,0) / NULLIF(c.curr_days,0), 4)  AS CURR_ORDERS_PER_DAY,
                    CASE WHEN COALESCE(p.PREV_ORDERS,0) > 0
                         THEN ROUND(
                            (COALESCE(c.CURR_ORDERS,0) - p.PREV_ORDERS)
                            / p.PREV_ORDERS * 100, 1)
                         ELSE NULL END AS ORDER_CHANGE_PCT
                FROM current_p c
                LEFT JOIN prior_p p ON c.DEALER_NAME = p.DEALER_NAME
                WHERE COALESCE(p.PREV_ORDERS,0) > 0
                  AND COALESCE(c.CURR_ORDERS,0) < p.PREV_ORDERS * (1 - {ov_thresh}/100.0)
                ORDER BY ORDER_CHANGE_PCT ASC
                LIMIT {ov_max}
            """)

        if vel_df.empty:
            st.warning(
                f"No dealers found with order count drop ≥ {ov_thresh}% between the two periods. "
                f"Try reducing the drop threshold (e.g. 10–15%)."
            )
            st.stop()

        st.success(f"Found **{len(vel_df)} dealers** whose ordering pace slowed by ≥ {ov_thresh}%.")

        disp_v = vel_df.copy()
        disp_v["PREV_REV"]            = disp_v["PREV_REV"].apply(lambda v: f"${float(v):,.0f}")
        disp_v["CURR_REV"]            = disp_v["CURR_REV"].apply(lambda v: f"${float(v):,.0f}")
        disp_v["PREV_ORDERS_PER_DAY"] = disp_v["PREV_ORDERS_PER_DAY"].apply(lambda v: f"{float(v):.3f}")
        disp_v["CURR_ORDERS_PER_DAY"] = disp_v["CURR_ORDERS_PER_DAY"].apply(lambda v: f"{float(v):.3f}")
        disp_v["ORDER_CHANGE_PCT"]    = disp_v["ORDER_CHANGE_PCT"].apply(lambda v: f"{float(v):.1f}%")
        disp_v.columns = [
            "Dealer", "Prior Orders", "Current Orders",
            "Prior Products", "Current Products",
            "Prior Revenue", "Current Revenue",
            "Prior Orders/Day", "Current Orders/Day", "Order Change %"
        ]
        st.dataframe(disp_v, use_container_width=True, hide_index=True)

        # ── STEP 2: Category-level diagnosis per dealer ───────────────────────
        st.markdown('<div class="step-pill">⚙ Step 2 — Diagnosing Product Category Breakdown</div>',
                    unsafe_allow_html=True)

        ov_results = []
        for _, row in vel_df.iterrows():
            dealer      = str(row["DEALER_NAME"])
            prev_orders = int(row["PREV_ORDERS"])
            curr_orders = int(row["CURR_ORDERS"])
            prev_rev    = float(row["PREV_REV"])
            curr_rev    = float(row["CURR_REV"])
            drop_pct    = float(row["ORDER_CHANGE_PCT"])
            prev_opd    = float(row["PREV_ORDERS_PER_DAY"])
            curr_opd    = float(row["CURR_ORDERS_PER_DAY"])
            prev_prod   = int(row["PREV_PRODUCTS"])
            curr_prod   = int(row["CURR_PRODUCTS"])

            cat_df = run_query(f"""
                WITH date_bounds AS (
                    SELECT MIN(EFFECTIVE_DATE) AS dt_min,
                           MAX(EFFECTIVE_DATE) AS dt_max,
                           DATEDIFF('day', MIN(EFFECTIVE_DATE), MAX(EFFECTIVE_DATE)) AS total_days
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW
                    WHERE CURRENT_FLAG = 'Y'
                ),
                split_date AS (
                    SELECT dt_min, dt_max,
                           DATEADD('day', ROUND(total_days * {1 - ov_sf}, 0), dt_min) AS split_pt
                    FROM date_bounds
                ),
                curr_cat AS (
                    SELECT f.PRODUCT_NAME,
                           COUNT(DISTINCT f.ORDER_ID) AS CURR_CNT,
                           SUM(f.TOTAL_AMOUNT)        AS CURR_AMT
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                    CROSS JOIN split_date s
                    WHERE f.CURRENT_FLAG = 'Y'
                      AND f.DEALER_NAME = '{dealer.replace(chr(39), chr(39)+chr(39))}'
                      AND f.EFFECTIVE_DATE > s.split_pt
                      AND f.EFFECTIVE_DATE <= s.dt_max
                    GROUP BY f.PRODUCT_NAME
                ),
                prev_cat AS (
                    SELECT f.PRODUCT_NAME,
                           COUNT(DISTINCT f.ORDER_ID) AS PREV_CNT,
                           SUM(f.TOTAL_AMOUNT)        AS PREV_AMT
                    FROM {DATABASE}.{SCHEMA}.FACT_ORDER_HISTORY_VW f
                    CROSS JOIN split_date s
                    WHERE f.CURRENT_FLAG = 'Y'
                      AND f.DEALER_NAME = '{dealer.replace(chr(39), chr(39)+chr(39))}'
                      AND f.EFFECTIVE_DATE >= s.dt_min
                      AND f.EFFECTIVE_DATE <= s.split_pt
                    GROUP BY f.PRODUCT_NAME
                )
                SELECT
                    COALESCE(p.PRODUCT_NAME, c.PRODUCT_NAME) AS PRODUCT_NAME,
                    COALESCE(p.PREV_CNT, 0)  AS PREV_ORDERS,
                    COALESCE(c.CURR_CNT, 0)  AS CURR_ORDERS,
                    COALESCE(p.PREV_AMT, 0)  AS PREV_REV,
                    COALESCE(c.CURR_AMT, 0)  AS CURR_REV,
                    COALESCE(c.CURR_CNT,0) - COALESCE(p.PREV_CNT,0) AS ORDER_DELTA
                FROM prev_cat p
                FULL OUTER JOIN curr_cat c ON p.PRODUCT_NAME = c.PRODUCT_NAME
                ORDER BY ORDER_DELTA ASC
                LIMIT 8
            """)

            if not cat_df.empty:
                n_dropped  = int((cat_df["ORDER_DELTA"] < 0).sum())
                n_total    = len(cat_df)
                drop_type  = "product-specific" if n_dropped <= max(1, n_total // 2) else "broad activity drop"
                cat_summary = "; ".join(
                    f"{r['PRODUCT_NAME']}: {int(r['PREV_ORDERS'])}→{int(r['CURR_ORDERS'])} orders"
                    for _, r in cat_df.head(5).iterrows()
                )
            else:
                drop_type   = "unknown"
                cat_summary = "No product breakdown available"
                n_dropped   = 0
                n_total     = 0

            ov_results.append({
                "dealer": dealer, "prev_orders": prev_orders, "curr_orders": curr_orders,
                "drop_pct": drop_pct, "prev_rev": prev_rev, "curr_rev": curr_rev,
                "prev_opd": prev_opd, "curr_opd": curr_opd,
                "prev_prod": prev_prod, "curr_prod": curr_prod,
                "drop_type": drop_type, "cat_summary": cat_summary,
                "n_dropped": n_dropped, "n_total": n_total, "cat_df": cat_df,
            })

        # ── STEP 3: AI Re-engagement Plans ────────────────────────────────────
        st.markdown('<div class="step-pill">⚙ Step 3 — Generating AI Re-engagement Plans</div>',
                    unsafe_allow_html=True)

        for item in ov_results:
            with st.spinner(f"Generating plan for {item['dealer']}..."):
                plan = _ai_complete(
                    f"Order velocity analysis for dealer '{item['dealer']}':\n"
                    f"- Orders dropped {abs(item['drop_pct']):.1f}%: "
                    f"{item['prev_orders']} → {item['curr_orders']} orders\n"
                    f"- Order frequency: {item['prev_opd']:.3f} orders/day → {item['curr_opd']:.3f} orders/day\n"
                    f"- Products ordered: {item['prev_prod']} → {item['curr_prod']}\n"
                    f"- Revenue: ${item['prev_rev']:,.0f} → ${item['curr_rev']:,.0f}\n"
                    f"- Drop type diagnosed as: {item['drop_type']}\n"
                    f"- Product breakdown (prev→curr orders): {item['cat_summary']}\n\n"
                    f"Generate a re-engagement plan:\n"
                    f"1. Root cause diagnosis (2 sentences — is this a product cooling off or "
                    f"overall relationship disengagement? Cite the numbers.)\n"
                    f"2. Three specific re-engagement actions (bullet points, concrete and product-specific)\n"
                    f"3. 30-day success metric (one sentence with a specific order count target)\n"
                    f"Be direct, data-specific, no generic advice."
                )
            item["plan"] = plan

        st.markdown('<div class="step-pill">✅ Step 4 — Re-engagement Plans Ready</div>',
                    unsafe_allow_html=True)
        st.markdown("#### Re-engagement Plans")

        for item in ov_results:
            drop_abs = abs(item["drop_pct"])
            drop_icon = "🔴" if drop_abs >= 40 else "🟡"
            type_badge_bg  = "#fff1f2" if item["drop_type"] == "broad activity drop" else "#fefce8"
            type_badge_clr = "#dc2626" if item["drop_type"] == "broad activity drop" else "#854d0e"

            with st.expander(
                f"{drop_icon} {item['dealer']}  |  Order Drop: {item['drop_pct']:.1f}%  |  "
                f"{item['curr_orders']} orders now vs {item['prev_orders']} before",
                expanded=True
            ):
                st.markdown(
                    f'<span style="background:{type_badge_bg};color:{type_badge_clr};'
                    f'border-radius:999px;font-size:11px;font-weight:800;'
                    f'padding:3px 12px;display:inline-block;margin-bottom:10px;">'
                    f'{"⚠ Broad Activity Drop" if item["drop_type"]=="broad activity drop" else "🎯 Product-Specific Slowdown"}'
                    f' — {item["n_dropped"]} of {item["n_total"]} products slowed</span>',
                    unsafe_allow_html=True
                )

                col_a, col_b = st.columns([1.3, 1])

                with col_a:
                    st.markdown("**AI Re-engagement Plan**")
                    _plan_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item["plan"])
                    _plan_html = html.escape(_plan_html).replace(
                        "&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
                    _plan_html = _plan_html.replace(chr(10), "<br/>")
                    st.markdown(
                        f'<div style="background:#f0fdfa;border-left:4px solid #0f766e;'
                        f'border-radius:8px;padding:14px 16px;font-size:13px;line-height:1.75;">'
                        f'{_plan_html}</div>',
                        unsafe_allow_html=True
                    )

                with col_b:
                    st.markdown("**Velocity KPI Snapshot**")
                    for lbl, val in [
                        ("Prior Orders",      str(item["prev_orders"])),
                        ("Current Orders",    str(item["curr_orders"])),
                        ("Order Drop %",      f"{item['drop_pct']:.1f}%"),
                        ("Prior Freq",        f"{item['prev_opd']:.3f}/day"),
                        ("Current Freq",      f"{item['curr_opd']:.3f}/day"),
                        ("Prior Products",    str(item["prev_prod"])),
                        ("Current Products",  str(item["curr_prod"])),
                        ("Prior Revenue",     f"${item['prev_rev']:,.0f}"),
                        ("Current Revenue",   f"${item['curr_rev']:,.0f}"),
                    ]:
                        st.markdown(
                            f'<div class="kpi-row">'
                            f'<span class="kpi-lbl">{lbl}</span>'
                            f'<span class="kpi-val">{val}</span></div>',
                            unsafe_allow_html=True
                        )

                    if not item["cat_df"].empty:
                        st.markdown("<br>**Product Order Shift**", unsafe_allow_html=True)
                        cat_disp = item["cat_df"][["PRODUCT_NAME","PREV_ORDERS","CURR_ORDERS","ORDER_DELTA"]].copy()
                        cat_disp.columns = ["Product","Prior Orders","Current Orders","Δ Orders"]
                        cat_disp["Δ Orders"] = cat_disp["Δ Orders"].apply(
                            lambda v: f"{'▼' if v < 0 else '▲'} {abs(int(v))}"
                        )
                        st.dataframe(cat_disp, use_container_width=True, hide_index=True, height=200)

                # Quick Actions
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown("**Quick Actions**")
                _slug = item["dealer"].replace(" ","_").replace("/","_")[:16]
                qa1, qa2, qa3 = st.columns(3, gap="small")

                with qa1:
                    _flag_key = f"ov_flag_{_slug}"
                    _flagged  = st.session_state.get(_flag_key, False)
                    if st.button(
                        "✅ Flagged for Follow-up" if _flagged else "🚩 Flag for Follow-up",
                        key=f"ov_flag_btn_{_slug}", use_container_width=True, type="secondary"
                    ):
                        st.session_state[_flag_key] = not _flagged
                        st.rerun()

                with qa2:
                    _show_key = f"ov_txt_{_slug}"
                    if st.button("📋 View Plan as Text", key=f"ov_txt_btn_{_slug}",
                                 use_container_width=True, type="secondary"):
                        st.session_state[_show_key] = not st.session_state.get(_show_key, False)
                        st.rerun()
                    if st.session_state.get(_show_key, False):
                        st.code(item["plan"], language=None)

                with qa3:
                    _plan_txt = (
                        f"ORDER VELOCITY RE-ENGAGEMENT PLAN\n"
                        f"Dealer         : {item['dealer']}\n"
                        f"Order Drop     : {item['drop_pct']:.1f}%\n"
                        f"Prior Orders   : {item['prev_orders']}\n"
                        f"Current Orders : {item['curr_orders']}\n"
                        f"Prior Freq     : {item['prev_opd']:.3f} orders/day\n"
                        f"Current Freq   : {item['curr_opd']:.3f} orders/day\n"
                        f"Drop Type      : {item['drop_type']}\n\n"
                        f"{item['plan']}"
                    )
                    st.download_button(
                        "⬇ Download This Plan",
                        data=_plan_txt,
                        file_name=f"velocity_{_slug}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        key=f"ov_dl_{_slug}",
                        use_container_width=True, type="secondary"
                    )

        # ── Export full report ─────────────────────────────────────────────────
        st.markdown("---")
        exp_rows = [{
            "Dealer":           r["dealer"],
            "Order Drop %":     f"{r['drop_pct']:.1f}%",
            "Prior Orders":     r["prev_orders"],
            "Current Orders":   r["curr_orders"],
            "Prior Orders/Day": f"{r['prev_opd']:.3f}",
            "Curr Orders/Day":  f"{r['curr_opd']:.3f}",
            "Drop Type":        r["drop_type"],
            "Prior Revenue":    f"${r['prev_rev']:,.0f}",
            "Current Revenue":  f"${r['curr_rev']:,.0f}",
            "Re-engagement Plan": r.get("plan",""),
        } for r in ov_results]
        st.download_button(
            "Download Order Velocity Report (CSV)",
            data=pd.DataFrame(exp_rows).to_csv(index=False),
            file_name=f"order_velocity_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv", key="dl_int"
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # AGENT 3 — SMART FULFILLMENT AGENT
    # ═══════════════════════════════════════════════════════════════════════════
    elif active == "smart_fulfillment":

        col_hd3, col_back3 = st.columns([5, 1])
        with col_back3:
            if st.button("✕ Close Agent", key="close_sf", type="secondary",
                         use_container_width=True):
                st.session_state.active_agent = None
                st.session_state.agent_ran    = False
                st.rerun()

        st.markdown("""
        <div class="ag-active-banner" style="background:linear-gradient(135deg,#0891b2,#0f766e);">
            <div style="font-size:32px;">🚚</div>
            <div>
                <div style="font-size:18px;font-weight:900;">Smart Fulfillment Agent</div>
                <div style="font-size:13px;opacity:.9;">
                    Routes any order to the optimal fulfillment node — fastest delivery
                    or lowest cost — with live stock check across all warehouses,
                    dark stores and retail outlets.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── STEP 0: Verify fulfillment tables exist ────────────────────────────
        @st.cache_data(ttl=120)
        def _sf_tables_exist():
            try:
                chk = run_query(f"""
                    SELECT COUNT(*) AS CNT
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = '{RAW_SCHEMA}'
                      AND TABLE_NAME IN (
                          'FULFILLMENT_NODES',
                          'INVENTORY_BY_LOCATION',
                          'SHIPPING_COST_MATRIX'
                      )
                """)
                return int(chk["CNT"].iloc[0]) == 3 if not chk.empty else False
            except Exception:
                return False

        @st.cache_data(ttl=60)
        def _sf_load_nodes():
            return run_query(f"""
                SELECT WAREHOUSE_ID, WAREHOUSE_NAME, NODE_TYPE,
                       CITY, REGION, LAT, LON, CONTACT_EMAIL
                FROM {DATABASE}.{RAW_SCHEMA}.FULFILLMENT_NODES
                WHERE IS_ACTIVE = TRUE
                ORDER BY NODE_TYPE, CITY
            """)

        @st.cache_data(ttl=60)
        def _sf_load_products():
            return run_query(f"""
                SELECT DISTINCT PRODUCT_NAME
                FROM {DATABASE}.{RAW_SCHEMA}.INVENTORY_BY_LOCATION
                WHERE IS_ACTIVE = TRUE
                ORDER BY PRODUCT_NAME
            """)

        @st.cache_data(ttl=60)
        def _sf_load_regions():
            return run_query(f"""
                SELECT DISTINCT TO_REGION AS REGION
                FROM {DATABASE}.{RAW_SCHEMA}.SHIPPING_COST_MATRIX
                WHERE IS_ACTIVE = TRUE
                ORDER BY TO_REGION
            """)

        if not _sf_tables_exist():
            st.error(
                "⚠️  Smart Fulfillment tables not found. "
                "Please run **STEP1**, **STEP2** and **STEP3** SQL scripts first "
                "in your Snowflake worksheet to create the required tables and views.",
                icon="🚨"
            )
            st.markdown("""
            <div style="background:#fff7ed;border:1.5px solid #fed7aa;border-radius:12px;padding:18px 20px;margin-top:12px;">
            <div style="font-weight:800;font-size:14px;color:#c2410c;margin-bottom:10px;">📋 What you need to run first:</div>
            <div style="font-size:13px;color:#374151;line-height:2;">
            <b>Step 1</b> → STEP1_CREATE_RAW_TABLES.sql — creates the 3 raw source tables<br/>
            <b>Step 2</b> → STEP2_INSERT_SAMPLE_DATA.sql — loads sample fulfillment data<br/>
            <b>Step 3</b> → STEP3_CREATE_VIEWS.sql — creates the INFORMATION_MART views the agent queries
            </div>
            </div>
            """, unsafe_allow_html=True)
            st.stop()

        # ── Network overview ───────────────────────────────────────────────────
        st.markdown('<div class="step-pill">⚙ Step 1 — Fulfillment Network Overview</div>',
                    unsafe_allow_html=True)

        nodes_df    = _sf_load_nodes()
        products_df = _sf_load_products()
        regions_df  = _sf_load_regions()

        if nodes_df.empty:
            st.warning("No active fulfillment nodes found. Check FULFILLMENT_NODES table.")
            st.stop()

        n_warehouses  = int((nodes_df["NODE_TYPE"] == "WAREHOUSE").sum())
        n_dark_stores = int((nodes_df["NODE_TYPE"] == "DARK_STORE").sum())
        n_retail      = int((nodes_df["NODE_TYPE"] == "RETAIL").sum())
        n_products    = len(products_df)
        n_regions     = len(regions_df)

        nc1, nc2, nc3, nc4, nc5 = st.columns(5)
        for col, lbl, val, bg, fg in [
            (nc1, "Warehouses",   n_warehouses,  "#dbeafe", "#1e40af"),
            (nc2, "Dark Stores",  n_dark_stores, "#fef3c7", "#d97706"),
            (nc3, "Retail Nodes", n_retail,      "#d1fae5", "#059669"),
            (nc4, "Products",     n_products,    "#f3e8ff", "#7c3aed"),
            (nc5, "Regions",      n_regions,     "#e0f2fe", "#0284c7"),
        ]:
            col.markdown(
                f'<div style="background:{bg};border-radius:10px;padding:14px;text-align:center;">'
                f'<div style="font-size:26px;font-weight:900;color:{fg};">{val}</div>'
                f'<div style="font-size:11px;font-weight:700;color:{fg};">{lbl}</div>'
                f'</div>', unsafe_allow_html=True
            )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Node table
        with st.expander("📍 View All Fulfillment Nodes", expanded=False):
            disp_nodes = nodes_df.copy()
            disp_nodes["LAT"] = disp_nodes["LAT"].apply(lambda v: f"{float(v):.4f}")
            disp_nodes["LON"] = disp_nodes["LON"].apply(lambda v: f"{float(v):.4f}")
            disp_nodes.columns = ["Node ID","Name","Type","City","Region","Lat","Lon","Contact"]
            st.dataframe(disp_nodes, use_container_width=True, hide_index=True)

        # ── Parameters ────────────────────────────────────────────────────────
        st.markdown("#### Routing Parameters")
        sf1, sf2, sf3 = st.columns(3, gap="medium")

        product_list = sorted(products_df["PRODUCT_NAME"].tolist()) if not products_df.empty else []
        region_list  = sorted(regions_df["REGION"].tolist())        if not regions_df.empty else []

        with sf1:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Product to Route</div>', unsafe_allow_html=True)
                sf_product = st.selectbox("Product", product_list,
                                          key="sf_product", label_visibility="collapsed")
                st.caption("Select the product you want to fulfill.")

        with sf2:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Delivery Region</div>', unsafe_allow_html=True)
                sf_region = st.selectbox("Region", region_list,
                                         key="sf_region", label_visibility="collapsed")
                st.caption("Where the order needs to be delivered.")

        with sf3:
            with st.container(border=True):
                st.markdown('<div class="param-lbl">Priority Mode</div>', unsafe_allow_html=True)
                sf_mode = st.radio(
                    "Mode", ["⚡ Speed — Fastest delivery", "💰 Cost — Lowest total cost"],
                    key="sf_mode", label_visibility="collapsed"
                )
                is_speed_mode = sf_mode.startswith("⚡")
                st.caption(
                    "Speed: shortest delivery days. Cost: lowest shipping cost."
                    if not is_speed_mode else
                    "Speed: closest node with stock, fastest carrier."
                )

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        if st.button("Run Smart Fulfillment Agent", key="run_sf",
                     type="primary", use_container_width=True):
            st.session_state.agent_ran    = True
            st.session_state.agent_params = {
                "product": sf_product, "region": sf_region, "speed": is_speed_mode
            }

        if not st.session_state.get("agent_ran") or \
           st.session_state.agent_params.get("product") is None:
            st.info("Select a product, delivery region and priority mode, then click **Run Smart Fulfillment Agent**.")
            st.stop()

        params_sf    = st.session_state.agent_params
        sf_prod      = params_sf["product"]
        sf_reg       = params_sf["region"]
        sf_speed     = params_sf["speed"]
        mode_label   = "SPEED" if sf_speed else "COST"

        st.markdown("---")
        st.markdown("#### Running Agent...")

        # ── STEP 2: Stock check across all nodes ──────────────────────────────
        st.markdown('<div class="step-pill">⚙ Step 2 — Stock Check Across All Nodes</div>',
                    unsafe_allow_html=True)

        with st.spinner(f"Checking stock for '{sf_prod}' across all fulfillment nodes..."):
            stock_df = run_query(f"""
                SELECT
                    i.WAREHOUSE_ID,
                    i.WAREHOUSE_NAME,
                    n.NODE_TYPE,
                    n.CITY,
                    n.REGION          AS NODE_REGION,
                    n.LAT,
                    n.LON,
                    n.CONTACT_EMAIL,
                    i.STOCK_QTY,
                    i.REORDER_THRESHOLD,
                    CASE WHEN i.STOCK_QTY <= i.REORDER_THRESHOLD THEN 'LOW_STOCK' ELSE 'IN_STOCK' END AS STOCK_STATUS,
                    i.LAST_UPDATED
                FROM {DATABASE}.{RAW_SCHEMA}.INVENTORY_BY_LOCATION i
                INNER JOIN {DATABASE}.{RAW_SCHEMA}.FULFILLMENT_NODES n
                    ON i.WAREHOUSE_ID = n.WAREHOUSE_ID
                WHERE i.IS_ACTIVE = TRUE
                  AND n.IS_ACTIVE = TRUE
                  AND i.PRODUCT_NAME = '{sf_prod.replace(chr(39), chr(39)+chr(39))}'
                  AND i.STOCK_QTY > 0
                ORDER BY i.STOCK_QTY DESC
            """)

        if stock_df.empty:
            st.error(f"❌ No stock found for **{sf_prod}** at any active node. "
                     "Check INVENTORY_BY_LOCATION table.")
            st.stop()

        st.success(f"✅ **{sf_prod}** is in stock at **{len(stock_df)}** node(s).")

        # Stock table
        disp_stock = stock_df[["WAREHOUSE_NAME","NODE_TYPE","CITY","NODE_REGION",
                                "STOCK_QTY","REORDER_THRESHOLD","STOCK_STATUS"]].copy()
        disp_stock.columns = ["Node","Type","City","Region","Stock Qty","Reorder Threshold","Status"]
        st.dataframe(disp_stock, use_container_width=True, hide_index=True)

        # ── STEP 3: Shipping options for nodes that have stock ─────────────────
        st.markdown('<div class="step-pill">⚙ Step 3 — Routing Options to {}</div>'.format(sf_reg),
                    unsafe_allow_html=True)

        node_ids = "','".join(stock_df["WAREHOUSE_ID"].tolist())

        with st.spinner(f"Fetching shipping options from all stocked nodes to {sf_reg}..."):
            routes_df = run_query(f"""
                SELECT
                    s.FROM_NODE_ID,
                    s.FROM_NODE_NAME,
                    n.NODE_TYPE,
                    n.CITY          AS FROM_CITY,
                    i.STOCK_QTY,
                    s.TO_REGION,
                    s.TO_CITY,
                    s.SHIPPING_COST,
                    s.EST_DELIVERY_DAYS,
                    s.CARRIER,
                    s.SERVICE_TYPE,
                    CASE s.EST_DELIVERY_DAYS
                        WHEN 1 THEN 'Same/Next Day'
                        WHEN 2 THEN '2-Day'
                        WHEN 3 THEN '3-Day'
                        ELSE CONCAT(s.EST_DELIVERY_DAYS, '-Day')
                    END AS SPEED_LABEL
                FROM {DATABASE}.{RAW_SCHEMA}.SHIPPING_COST_MATRIX s
                INNER JOIN {DATABASE}.{RAW_SCHEMA}.FULFILLMENT_NODES n
                    ON s.FROM_NODE_ID = n.WAREHOUSE_ID
                INNER JOIN {DATABASE}.{RAW_SCHEMA}.INVENTORY_BY_LOCATION i
                    ON s.FROM_NODE_ID = i.WAREHOUSE_ID
                    AND i.PRODUCT_NAME = '{sf_prod.replace(chr(39), chr(39)+chr(39))}'
                    AND i.IS_ACTIVE = TRUE
                    AND i.STOCK_QTY > 0
                WHERE s.IS_ACTIVE = TRUE
                  AND n.IS_ACTIVE = TRUE
                  AND s.FROM_NODE_ID IN ('{node_ids}')
                  AND s.TO_REGION = '{sf_reg.replace(chr(39), chr(39)+chr(39))}'
                ORDER BY s.EST_DELIVERY_DAYS ASC, s.SHIPPING_COST ASC
            """)

        if routes_df.empty:
            st.warning(
                f"No shipping routes found from stocked nodes to **{sf_reg}**. "
                f"Check SHIPPING_COST_MATRIX for routes to this region."
            )
            st.stop()

        # ── STEP 4: Pick the winner (speed or cost) ────────────────────────────
        st.markdown('<div class="step-pill">⚙ Step 4 — Selecting Optimal Route</div>',
                    unsafe_allow_html=True)

        if sf_speed:
            # Speed mode: fastest delivery days, then cheapest among ties
            winner = routes_df.sort_values(
                ["EST_DELIVERY_DAYS","SHIPPING_COST"], ascending=[True,True]
            ).iloc[0]
        else:
            # Cost mode: cheapest, then fastest among ties
            winner = routes_df.sort_values(
                ["SHIPPING_COST","EST_DELIVERY_DAYS"], ascending=[True,True]
            ).iloc[0]

        # ── Winner card ────────────────────────────────────────────────────────
        w_node     = str(winner["FROM_NODE_NAME"])
        w_type     = str(winner["NODE_TYPE"])
        w_city     = str(winner["FROM_CITY"])
        w_stock    = int(winner["STOCK_QTY"])
        w_cost     = float(winner["SHIPPING_COST"])
        w_days     = int(winner["EST_DELIVERY_DAYS"])
        w_carrier  = str(winner["CARRIER"])
        w_svc      = str(winner["SERVICE_TYPE"])
        w_speed_lbl= str(winner["SPEED_LABEL"])
        w_to_city  = str(winner["TO_CITY"]) if winner["TO_CITY"] else sf_reg

        mode_color  = "#0f766e" if sf_speed else "#1e40af"
        mode_icon   = "⚡" if sf_speed else "💰"
        mode_title  = "FASTEST ROUTE" if sf_speed else "CHEAPEST ROUTE"

        st.markdown(
            f'<div style="background:linear-gradient(135deg,{mode_color},{mode_color}cc);'
            f'border-radius:14px;padding:22px 28px;color:white;margin:12px 0;">'
            f'<div style="font-size:11px;font-weight:800;opacity:.8;letter-spacing:1px;'
            f'margin-bottom:8px;">{mode_icon} RECOMMENDED — {mode_title}</div>'
            f'<div style="font-size:22px;font-weight:900;margin-bottom:4px;">'
            f'{html.escape(w_node)}</div>'
            f'<div style="font-size:14px;opacity:.9;">'
            f'{html.escape(w_type)} · {html.escape(w_city)}</div>'
            f'<div style="display:flex;gap:24px;margin-top:16px;flex-wrap:wrap;">'
            f'<div><div style="font-size:11px;opacity:.7;">DELIVERY</div>'
            f'<div style="font-size:20px;font-weight:900;">{w_speed_lbl}</div></div>'
            f'<div><div style="font-size:11px;opacity:.7;">COST</div>'
            f'<div style="font-size:20px;font-weight:900;">₹{w_cost:,.0f}</div></div>'
            f'<div><div style="font-size:11px;opacity:.7;">CARRIER</div>'
            f'<div style="font-size:20px;font-weight:900;">{html.escape(w_carrier)}</div></div>'
            f'<div><div style="font-size:11px;opacity:.7;">SERVICE</div>'
            f'<div style="font-size:20px;font-weight:900;">{html.escape(w_svc)}</div></div>'
            f'<div><div style="font-size:11px;opacity:.7;">STOCK AT NODE</div>'
            f'<div style="font-size:20px;font-weight:900;">{w_stock} units</div></div>'
            f'</div></div>',
            unsafe_allow_html=True
        )

        # ── All routes comparison table ────────────────────────────────────────
        st.markdown("#### All Available Routes — Comparison")
        st.caption(f"All nodes with **{sf_prod}** in stock that ship to **{sf_reg}**. "
                   f"{'Sorted fastest first.' if sf_speed else 'Sorted cheapest first.'}")

        disp_routes = routes_df.copy()
        disp_routes["SHIPPING_COST"] = disp_routes["SHIPPING_COST"].apply(lambda v: f"₹{float(v):,.0f}")
        disp_routes["STOCK_QTY"]     = disp_routes["STOCK_QTY"].apply(lambda v: f"{int(v)} units")
        disp_routes = disp_routes[[
            "FROM_NODE_NAME","NODE_TYPE","FROM_CITY","STOCK_QTY",
            "SPEED_LABEL","EST_DELIVERY_DAYS","SHIPPING_COST","CARRIER","SERVICE_TYPE"
        ]]
        disp_routes.columns = [
            "Node","Type","City","Stock",
            "Delivery Speed","Days","Shipping Cost","Carrier","Service"
        ]
        st.dataframe(disp_routes, use_container_width=True, hide_index=True)

        # ── STEP 5: AI Routing Explanation ────────────────────────────────────
        st.markdown('<div class="step-pill">⚙ Step 5 — AI Routing Explanation</div>',
                    unsafe_allow_html=True)

        other_routes = routes_df[routes_df["FROM_NODE_NAME"] != w_node].head(3)
        alt_summary  = "; ".join(
            f"{r['FROM_NODE_NAME']} ({r['EST_DELIVERY_DAYS']}d, ₹{float(r['SHIPPING_COST']):,.0f})"
            for _, r in other_routes.iterrows()
        ) if not other_routes.empty else "No alternatives available"

        with st.spinner("Generating AI routing explanation..."):
            ai_routing = _ai_complete(
                f"You are a logistics routing agent. Explain this routing decision clearly.\n\n"
                f"ORDER DETAILS:\n"
                f"- Product: {sf_prod}\n"
                f"- Delivery to: {sf_reg} ({w_to_city})\n"
                f"- Priority: {'Fastest delivery' if sf_speed else 'Lowest cost'}\n\n"
                f"RECOMMENDED ROUTE:\n"
                f"- Node: {w_node} ({w_type}, {w_city})\n"
                f"- Delivery: {w_speed_lbl} ({w_days} days)\n"
                f"- Shipping cost: ₹{w_cost:,.0f}\n"
                f"- Carrier: {w_carrier} ({w_svc})\n"
                f"- Stock available: {w_stock} units\n\n"
                f"ALTERNATIVES CONSIDERED: {alt_summary}\n\n"
                f"Write:\n"
                f"1. Why this node was chosen (2 sentences — cite delivery days and cost vs alternatives)\n"
                f"2. One risk to watch (stock level, carrier reliability, or distance)\n"
                f"3. One action if this route fails (fallback option)\n"
                f"Be direct, cite the numbers. No generic advice."
            )

        _ai_r_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', ai_routing)
        _ai_r_html = html.escape(_ai_r_html).replace("&lt;strong&gt;","<strong>").replace("&lt;/strong&gt;","</strong>")
        _ai_r_html = _ai_r_html.replace("\n","<br/>")
        st.markdown(
            f'<div style="background:#f0fdfa;border-left:4px solid #0f766e;border-radius:10px;'
            f'padding:18px 20px;font-size:13px;line-height:1.85;">'
            f'{_ai_r_html}</div>',
            unsafe_allow_html=True
        )

        # ── STEP 6: Low stock alert on winner node ─────────────────────────────
        if w_stock <= int(winner.get("REORDER_THRESHOLD", 10) if "REORDER_THRESHOLD" in winner.index else 10):
            st.warning(
                f"⚠️ **Low stock alert:** {w_node} only has **{w_stock} units** of {sf_prod} "
                f"— at or below reorder threshold. Consider restocking before routing more orders here.",
                icon="⚠️"
            )

        # ── Export ─────────────────────────────────────────────────────────────
        st.markdown("---")
        ex_sf1, ex_sf2 = st.columns(2, gap="medium")

        routing_summary = {
            "Product":          sf_prod,
            "Delivery Region":  sf_reg,
            "Priority Mode":    mode_label,
            "Recommended Node": w_node,
            "Node Type":        w_type,
            "Node City":        w_city,
            "Delivery Speed":   w_speed_lbl,
            "Delivery Days":    w_days,
            "Shipping Cost":    f"₹{w_cost:,.0f}",
            "Carrier":          w_carrier,
            "Service Type":     w_svc,
            "Stock at Node":    f"{w_stock} units",
            "AI Explanation":   ai_routing,
            "Generated At":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        with ex_sf1:
            all_routes_exp = routes_df.copy()
            all_routes_exp["SHIPPING_COST"] = all_routes_exp["SHIPPING_COST"].apply(lambda v: f"₹{float(v):,.0f}")
            all_routes_exp.columns = [c.replace("_"," ").title() for c in all_routes_exp.columns]
            st.download_button(
                "⬇ Download All Routes (CSV)",
                data=all_routes_exp.to_csv(index=False),
                file_name=f"fulfillment_routes_{sf_prod.replace(' ','_')}_{sf_reg}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", key="dl_sf_routes",
                use_container_width=True
            )

        with ex_sf2:
            report_txt = (
                f"SMART FULFILLMENT AGENT — ROUTING REPORT\n"
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"{'='*55}\n\n"
                + "\n".join(f"{k:<22}: {v}" for k, v in routing_summary.items() if k != "AI Explanation")
                + f"\n\n{'='*55}\nAI ROUTING EXPLANATION:\n{'='*55}\n\n{ai_routing}"
            )
            st.download_button(
                "⬇ Download Routing Report (TXT)",
                data=report_txt,
                file_name=f"routing_{sf_prod.replace(' ','_')}_{sf_reg}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain", key="dl_sf_report",
                use_container_width=True
            )  
