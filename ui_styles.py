import streamlit as st


TACTICAL_CSS = """
<style>
:root {
  --bg: #131313;
  --bg-soft: #1c1b1b;
  --panel: rgba(28, 27, 27, 0.68);
  --panel-strong: #201f1f;
  --panel-border: rgba(135, 146, 155, 0.16);
  --text: #e5e2e1;
  --muted: #bdc8d1;
  --primary: #81cfff;
  --primary-strong: #29b6f6;
  --success: #05e777;
  --danger: #ff8a73;
  --warning: #ffb4a5;
}

.stApp {
  background:
    radial-gradient(circle at top right, rgba(41, 182, 246, 0.08), transparent 24%),
    linear-gradient(180deg, #0f0f0f 0%, #131313 100%);
  color: var(--text);
}

[data-testid="stHeader"], #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] {
  display: none !important;
}

.block-container {
  max-width: 820px !important;
  padding: 1rem 1rem 6rem !important;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  margin-bottom: 12px;
  padding: 0 12px;
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  background: rgba(19, 19, 19, 0.78);
  backdrop-filter: blur(18px);
}

.topbar-title {
  color: var(--primary);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0;
  text-align: center;
}

.topbar-link {
  color: var(--muted);
  font-size: 13px;
  text-decoration: none;
  font-weight: 700;
}

.glass-card {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  padding: 16px;
  backdrop-filter: blur(16px);
  box-shadow: 0 0 0 1px rgba(129, 207, 255, 0.03) inset;
}

.section-title {
  font-size: 12px;
  color: var(--muted);
  margin: 12px 0 8px;
  padding-left: 10px;
  border-left: 2px solid var(--primary);
}

.hero-issue {
  color: var(--text);
  font-weight: 700;
  font-size: 16px;
}

.hero-date {
  color: var(--muted);
  font-size: 12px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(32, 31, 31, 0.95);
  border: 1px solid var(--panel-border);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--success);
  box-shadow: 0 0 8px var(--success);
}

.number-row {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 8px;
  align-items: center;
}

.number-orb {
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "JetBrains Mono", monospace;
  font-weight: 700;
  font-size: 22px;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.13), transparent 62%),
    rgba(28, 27, 27, 0.9);
}

.number-separator {
  color: var(--muted);
  text-align: center;
  align-self: center;
}

.orb-primary {
  color: var(--primary);
  border: 1px solid rgba(129, 207, 255, 0.45);
  box-shadow: 0 0 12px rgba(129, 207, 255, 0.18);
}

.orb-accent {
  color: var(--danger);
  border: 1px solid rgba(255, 138, 115, 0.45);
  box-shadow: 0 0 12px rgba(255, 138, 115, 0.16);
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  min-height: 132px;
}

.metric-label {
  color: var(--muted);
  font-size: 12px;
}

.metric-value {
  margin-top: 18px;
  font-size: 40px;
  line-height: 1;
  font-family: "JetBrains Mono", monospace;
  font-weight: 700;
}

.metric-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--muted);
}

.result-card {
  margin-bottom: 12px;
}

.result-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 4px;
}

.result-desc {
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 10px;
}

.ball-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.ball-mini {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: "JetBrains Mono", monospace;
  font-weight: 700;
  background: rgba(19, 19, 19, 0.92);
}

.ball-mini.primary {
  color: var(--primary);
  border: 1px solid rgba(129, 207, 255, 0.38);
}

.ball-mini.accent {
  color: var(--danger);
  border: 1px solid rgba(255, 138, 115, 0.38);
}

.code-line {
  font-family: "JetBrains Mono", monospace;
  color: var(--text);
  background: rgba(14, 14, 14, 0.78);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 13px;
}

.access-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(129, 207, 255, 0.24);
  background: rgba(18, 32, 38, 0.72);
}

.access-strip.locked {
  border-color: rgba(255, 180, 165, 0.24);
  background: rgba(37, 27, 25, 0.72);
}

.access-badge {
  flex: 0 0 auto;
  padding: 7px 10px;
  border-radius: 999px;
  color: #04151f;
  background: var(--primary);
  font-size: 12px;
  font-weight: 800;
}

.locked .access-badge {
  background: var(--warning);
}

.unlock-panel {
  border-color: rgba(129, 207, 255, 0.28);
}

.access-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.access-chip {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 6px 10px;
  border-radius: 999px;
  color: var(--text);
  background: rgba(19, 19, 19, 0.82);
  border: 1px solid var(--panel-border);
  font-size: 12px;
}

.disclaimer-card {
  margin-top: 18px;
  padding: 14px;
  border: 1px solid rgba(255, 180, 165, 0.18);
  border-radius: 14px;
  background: rgba(19, 19, 19, 0.72);
}

.bottom-nav {
  position: sticky;
  bottom: 8px;
  z-index: 40;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 16px;
  padding: 8px;
  border-radius: 18px;
  background: rgba(19, 19, 19, 0.92);
  border: 1px solid var(--panel-border);
  backdrop-filter: blur(18px);
}

.nav-item {
  min-height: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border-radius: 12px;
  color: var(--muted);
  font-size: 11px;
}

.nav-item.active {
  color: #0c1a22;
  background: var(--primary-strong);
  font-weight: 700;
}

.muted {
  color: var(--muted);
  font-size: 13px;
}

.small-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 6px;
}

.heat-box {
  border-radius: 8px;
  min-height: 54px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  border: 1px solid rgba(135, 146, 155, 0.18);
}

.pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pill {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid var(--panel-border);
  background: rgba(19, 19, 19, 0.9);
  font-family: "JetBrains Mono", monospace;
  font-size: 13px;
}

.divider {
  height: 1px;
  background: rgba(135, 146, 155, 0.14);
  margin: 16px 0;
}

.stButton > button {
  min-height: 48px;
  border-radius: 12px;
  border: 1px solid rgba(129, 207, 255, 0.35);
  background: linear-gradient(180deg, #29b6f6 0%, #178fc5 100%);
  color: #04151f;
  font-weight: 800;
}

.stButton > button:hover {
  border-color: rgba(129, 207, 255, 0.8);
  color: #04151f;
  filter: brightness(1.06);
}

.stButton > button:disabled {
  background: rgba(229, 226, 225, 0.08);
  color: rgba(229, 226, 225, 0.45);
  border-color: rgba(135, 146, 155, 0.16);
}

@media (max-width: 640px) {
  .stApp {
    background: #0f0f0f;
  }
  [data-testid="stAppViewContainer"] > .main {
    width: 100vw !important;
  }
  .block-container {
    max-width: 100vw !important;
    width: 100vw !important;
    padding: 0.35rem 0.5rem 5.5rem !important;
  }
  .topbar {
    height: 42px;
    margin-bottom: 6px;
    padding: 0 9px;
    border-radius: 10px;
  }
  .topbar-title {
    font-size: 17px;
  }
  .topbar .muted {
    font-size: 11px;
  }
  .topbar-link {
    font-size: 11px;
  }
  .glass-card {
    border-radius: 12px;
    padding: 12px;
  }
  .section-title {
    margin: 10px 0 7px;
    font-size: 11px;
  }
  .hero-issue {
    font-size: 14px;
  }
  .hero-date,
  .status-pill,
  .result-desc,
  .metric-label,
  .metric-hint,
  .muted {
    font-size: 11px;
  }
  .number-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .number-separator {
    display: none;
  }
  .number-orb {
    width: 56px;
    height: 56px;
    flex: 0 0 56px;
    aspect-ratio: auto;
    font-size: 16px;
  }
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
  .metric-card {
    min-height: 96px;
  }
  .metric-value {
    margin-top: 10px;
    font-size: 28px;
  }
  .result-card {
    margin-bottom: 9px;
  }
  .result-title {
    font-size: 14px;
  }
  .ball-strip {
    gap: 6px;
  }
  .ball-mini {
    width: 34px;
    height: 34px;
    font-size: 13px;
  }
  .code-line {
    border-radius: 10px;
    padding: 9px 10px;
    font-size: 12px;
    word-break: break-all;
  }
  .access-strip {
    gap: 8px;
    margin-bottom: 7px;
    padding: 8px 10px;
    border-radius: 10px;
  }
  .access-strip.access-compact {
    align-items: center;
    flex-direction: row;
    min-height: 42px;
  }
  .access-strip.access-compact .result-title {
    font-size: 13px;
    margin-bottom: 0;
  }
  .access-strip.access-compact .result-desc {
    margin-bottom: 0;
    line-height: 1.35;
  }
  .access-badge {
    align-self: flex-start;
    padding: 5px 9px;
    font-size: 11px;
  }
  .access-chip-row {
    gap: 6px;
    margin: 9px 0;
  }
  .access-chip {
    min-height: 28px;
    padding: 5px 8px;
    font-size: 11px;
  }
  .disclaimer-card {
    margin-top: 12px;
    padding: 12px;
    border-radius: 10px;
  }
  .small-grid {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 5px;
  }
  .heat-box {
    min-height: 44px;
    border-radius: 7px;
    font-size: 11px;
  }
  .stButton > button {
    min-height: 44px;
    border-radius: 10px;
    font-size: 14px;
  }
  .stSelectbox [data-baseweb="select"] > div,
  .stTextInput input,
  .stNumberInput input {
    min-height: 42px;
    border-radius: 10px;
  }
  .stTextArea textarea {
    border-radius: 10px;
  }
  [data-testid="stHorizontalBlock"] {
    gap: 0.38rem;
  }
  [data-testid="stVerticalBlock"] {
    gap: 0.28rem;
  }
  [data-testid="stWidgetLabel"] {
    min-height: 1rem;
    margin-bottom: 0.15rem;
  }
  [data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
  }
  pre {
    white-space: pre-wrap !important;
    word-break: break-word !important;
  }
}
</style>
"""


def inject_styles():
    st.markdown(TACTICAL_CSS, unsafe_allow_html=True)
