from pathlib import Path
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px   # <-- add this line
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Small helper: export cleaned DataFrames as CSV bytes
# ──────────────────────────────────────────────────────────────────────────────
def df_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")

# ──────────────────────────────────────────────────────────────────────────────
# Page config & CRT styling
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Poor People Tax — Lottery → Crypto",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# WeatherStarr✨ vibe colors
PINK = "#ff69c9"
PINK_SOFT = "#ff8fd7"
PURPLE = "#b084f5"
CYAN = "#72f7ff"

CRT_CSS = """
<style>
:root {
  --bg: #0b0b12;
  --panel: #0f0f1a;
  --ink: #eaeaf2;
  --muted: #a9a9c6;
  --pink: #ff69c9;
  --pink-soft: #ff8fd7;
  --purple: #b084f5;
  --cyan: #72f7ff;
}
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 20% 0%, #121222 0%, var(--bg) 60%);
  color: var(--ink);
}
.scanlines:before {
  content: "";
  position: fixed;
  top:0; left:0; right:0; bottom:0;
  background: linear-gradient(rgba(255,255,255,0.03) 50%, rgba(0,0,0,0.03) 50%);
  background-size: 100% 3px;
  pointer-events: none;
  mix-blend-mode: overlay;
  z-index: 0;
}
.block-container { padding-top: 1.2rem; }
.crt-panel {
  background: linear-gradient(180deg, rgba(255,105,201,0.06), rgba(176,132,245,0.06));
  border: 1px solid rgba(114,247,255,0.18);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 0 0 1px rgba(255,105,201,0.06) inset, 0 10px 24px rgba(0,0,0,0.35);
}
h1, h2, h3 {
  text-shadow: 0 0 18px rgba(255,105,201,0.25), 0 0 2px rgba(114,247,255,0.2);
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f0f1a 0%, #0b0b12 60%);
  border-right: 1px solid rgba(114,247,255,0.12);
}
.small-caption { font-size: 0.85rem; color: var(--muted); }
</style>
<div class="scanlines"></div>
"""
st.markdown(CRT_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Paths & caching helpers
# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]  # repo root (app/app.py -> parents[1])
DATA_DIR = ROOT / "data"

@st.cache_data(show_spinner=False)
def load_csv_safe(path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Failed to load `{path}` → {e}")
        return pd.DataFrame()

def find_column(cols, *contains) -> Optional[str]:
    for c in cols:
        cl = c.lower()
        if any(key in cl for key in contains):
            return c
    return None

# ──────────────────────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────────────────────
crypto_df = load_csv_safe(DATA_DIR / "crypto_under30.csv")
lottery_df = load_csv_safe(DATA_DIR / "lottery_under30.csv")
bls_raw = load_csv_safe(DATA_DIR / "lottery_age_spend_bls_2018.csv")

# Sidebar status & global controls
with st.sidebar:
    st.markdown("## 🎛️ Controls")
    st.caption("Files detected (relative to `/data/`):")
    st.write(f"- `crypto_under30.csv`: **{'OK' if not crypto_df.empty else 'Missing/Empty'}**")
    st.write(f"- `lottery_under30.csv`: **{'OK' if not lottery_df.empty else 'Missing/Empty'}**")
    st.write(f"- `lottery_age_spend_bls_2018.csv`: **{'OK' if not bls_raw.empty else 'Missing/Empty'}**")
    st.markdown("---")
    glow = st.toggle("Extra glow ✨", value=True)
    line_style = st.radio(
        "Line style for time series",
        options=["Lines + markers", "Markers only"],
        index=0,
    )

# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="crt-panel" style="margin-bottom: 1rem; {'box-shadow: 0 0 36px rgba(255,105,201,0.23);' if glow else ''}">
      <h1 style="margin-bottom: 0.25rem; color:{PINK};">Poor People Tax: from tickets to tokens <span style="opacity:.8">app</span></h1>
      <div style="color:{CYAN};font-weight:600;">Lottery → Crypto (Under-30 focus, 2003–2024)</div>
      <div class="small-caption" style="margin-top:.35rem;">
        Retro / glitchcore WeatherStarr✨ • Dark CRT background • Cyan & pink accents
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Section: Lottery Era — BLS bar chart (clean + render)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("## 🎰 Lottery Era — Average Monthly Lottery Spend by Age (2017–2018)")

def prep_bls(bls_in: pd.DataFrame) -> pd.DataFrame:
    if bls_in.empty:
        return bls_in
    df = bls_in.rename(columns={
        "age_group": "AgeGroup",
        "avg_annual_spend_usd": "AvgAnnualSpend"
    }).copy()
    # Drop 'All ages'
    if "AgeGroup" in df.columns:
        df = df[df["AgeGroup"].str.lower() != "all ages"]
    # Monthly from annual
    if "AvgAnnualSpend" in df.columns:
        df["AvgMonthlySpend"] = pd.to_numeric(df["AvgAnnualSpend"], errors="coerce") / 12.0
    # Order
    age_order = ["Under 25", "25-34", "35-44", "45-54", "55-64", "65-74", "75+"]
    if "AgeGroup" in df.columns:
        df["AgeGroup"] = pd.Categorical(df["AgeGroup"], categories=age_order, ordered=True)
        df = df.sort_values("AgeGroup")
    return df

bls_df = prep_bls(bls_raw)

if bls_df.empty:
    st.warning("`lottery_age_spend_bls_2018.csv` missing or malformed. Expect columns like `age_group`, `avg_annual_spend_usd`.")
else:
    fig_bars = go.Figure()
    fig_bars.add_bar(
        x=bls_df["AgeGroup"].astype(str),
        y=bls_df["AvgMonthlySpend"],
        marker=dict(color=PINK, line=dict(color=PURPLE, width=1.2)),
        hovertemplate="<b>%{x}</b><br>$%{y:.2f} / month<extra></extra>",
        name="Avg monthly spend",
    )
    fig_bars.update_layout(
        template="plotly_dark",
        margin=dict(l=10, r=10, t=10, b=10),
        height=460,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title=None, showgrid=False, showline=True, linecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(title="Avg monthly lottery spending (USD)", gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.12)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_bars, use_container_width=True)
    st.caption(
        "Source: Bureau of Labor Statistics, CES 2017–2018 (BLS TED 2019). "
        "Example values from the reference image: Under 25 ≈ $7.55; 25–34 ≈ $40.32; 65–74 ≈ $132.43."
    )
    col_dl1, _ = st.columns([1, 2])
    with col_dl1:
        st.download_button(
            label="⬇️ Download BLS (cleaned CSV)",
            data=df_csv_bytes(bls_df[["AgeGroup", "AvgAnnualSpend", "AvgMonthlySpend", "year", "source"]]
                              .rename(columns={"year": "Year", "source": "Source"})),
            file_name="bls_lottery_spend_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ──────────────────────────────────────────────────────────────────────────────
# Lottery Era — Gallup line (clean + render)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("### Gallup: Under-30 Lottery Participation (2003, 2007, 2016)")

def prep_lottery(lot: pd.DataFrame) -> pd.DataFrame:
    if lot.empty:
        return lot
    df = lot.rename(columns={
        "year": "Year",
        "under30_lottery_pct": "Under30LotteryPct",
        "source": "Source"
    }).copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Under30LotteryPct"] = pd.to_numeric(df["Under30LotteryPct"], errors="coerce")
    df = df.dropna(subset=["Year", "Under30LotteryPct"]).sort_values("Year")
    return df

lot_line = prep_lottery(lottery_df)

if lot_line.empty:
    st.warning("`lottery_under30.csv` missing or malformed. Expect columns: `year, under30_lottery_pct, source`.")
else:
    fig_lot = go.Figure()
    mode_choice = "lines+markers" if line_style == "Lines + markers" else "markers"
    fig_lot.add_trace(go.Scatter(
        x=lot_line["Year"], y=lot_line["Under30LotteryPct"],
        mode=mode_choice,
        line=dict(width=3, color=PINK_SOFT),
        marker=dict(size=8, line=dict(width=1.2, color=PURPLE)),
        hovertemplate="<b>%{x}</b><br>%{y:.0f}% under 30 played<extra></extra>",
        name="Under-30 lottery participation",
    ))
    fig_lot.update_layout(
        template="plotly_dark",
        margin=dict(l=10, r=10, t=10, b=10),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title=None, showgrid=False, showline=True, linecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(title="% under 30", gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.12)", rangemode="tozero"),
        showlegend=False
    )
    st.plotly_chart(fig_lot, use_container_width=True)
    st.caption("Source: Gallup (2003, 2007, 2016). % of under-30s who reported playing the lottery.")
    col_dl1, _ = st.columns([1, 2])
    with col_dl1:
        st.download_button(
            label="⬇️ Download Gallup (cleaned CSV)",
            data=df_csv_bytes(lot_line[["Year", "Under30LotteryPct", "Source"]]),
            file_name="lottery_under30_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ──────────────────────────────────────────────────────────────────────────────
# 💫 Transition Memo — 2016: The Hope Market Goes Digital
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="crt-panel" style="margin-top:1rem; border-left: 4px solid {PINK_SOFT};
     background: rgba(18,18,18,0.9); padding:1.4em 1.6em; line-height:1.6;
     color:#e8e8e8; font-style:italic; box-shadow: 0 0 26px rgba(176,132,245,0.15);">
  <h4 style="color:{PINK_SOFT}; text-shadow: 0 0 10px rgba(255,105,201,0.35); margin-top:0;">
     💫  The Hope Market Goes Digital
  </h4>
  Around 2016, the scratchers stopped scratching.<br>
  The gas station tickets and quiet coins gave way to swipes and passwords.<br>
  Hope didn’t vanish — it migrated.<br>
  Crypto arrived like a digital lottery: instant, global, endlessly refreshing.<br>
  For a generation raised online, speculation became participation.<br>
  The promise stayed the same — turn luck into freedom —<br>
  only now the dream runs on code, and the house wears a new logo.
</div>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# Crypto Era — line chart (clean + render)
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("## ₿ Crypto Era — Under-30 Ownership (2015–2024)")

def prep_crypto(cdf: pd.DataFrame) -> pd.DataFrame:
    if cdf.empty:
        return cdf
    df = cdf.rename(columns={
        "year": "Year",
        "under30_crypto_pct": "Under30CryptoPct",
        "source": "Source"
    }).copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Under30CryptoPct"] = pd.to_numeric(df["Under30CryptoPct"], errors="coerce")
    df = df.dropna(subset=["Year", "Under30CryptoPct"]).sort_values("Year")
    return df

crypto_line = prep_crypto(crypto_df)

if crypto_line.empty:
    st.warning("`crypto_under30.csv` missing or malformed. Expect columns: `year, under30_crypto_pct, source`.")
else:
    fig_crypto = go.Figure()
    mode_choice = "lines+markers" if line_style == "Lines + markers" else "markers"
    fig_crypto.add_trace(go.Scatter(
        x=crypto_line["Year"], y=crypto_line["Under30CryptoPct"],
        mode=mode_choice,
        line=dict(width=3, color=CYAN),
        marker=dict(size=8, line=dict(width=1.2, color=PURPLE)),
        hovertemplate="<b>%{x}</b><br>%{y:.0f}% own crypto<extra></extra>",
        name="Under-30 crypto ownership",
    ))
    fig_crypto.update_layout(
        template="plotly_dark",
        margin=dict(l=10, r=10, t=10, b=10),
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title=None, showgrid=False, showline=True, linecolor="rgba(255,255,255,0.15)"),
        yaxis=dict(title="% under 30", gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.12)", rangemode="tozero"),
        showlegend=False
    )
    st.plotly_chart(fig_crypto, use_container_width=True)
    st.caption("Sources: Pew, Finder, CNBC/Credit Karma, Gemini. % of under-30s who own crypto (survey methodologies vary).")
    col_dl1, _ = st.columns([1, 2])
    with col_dl1:
        st.download_button(
            label="⬇️ Download Crypto (cleaned CSV)",
            data=df_csv_bytes(crypto_line[["Year", "Under30CryptoPct", "Source"]]),
            file_name="crypto_under30_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ──────────────────────────────────────────────────────────────────────────────
# 🧊 The New House: Who Holds the Coins? — Ownership Concentration Donut
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("💰 The New House: Who Holds the power?")
st.markdown("_Explore how Bitcoin ownership concentration changed over time._")

# Load data safely (so it won't crash if file missing)
@st.cache_data(show_spinner=False)
def load_concentration() -> pd.DataFrame:
    try:
        return pd.read_csv(DATA_DIR / "crypto_concentration.csv")
    except Exception as e:
        st.warning(f"Could not load crypto_concentration.csv — {e}")
        return pd.DataFrame()

conc = load_concentration()

if not conc.empty and "year" in conc.columns:
    year_min, year_max = int(conc.year.min()), int(conc.year.max())
    year = st.slider("Select a year", year_min, year_max, year_max)
    try:
        pct = conc.loc[conc.year == year, "top_0_01_pct_ownership"].iloc[0]
        other = 100 - pct
        source = conc.loc[conc.year == year, "source"].iloc[0]
    except Exception:
        st.error("Your CSV must have columns: year, top_0_01_pct_ownership, source")
        st.stop()

    # Build donut dataframe
    donut_df = pd.DataFrame({
        "group": ["Top 0.01% of holders", "All other holders"],
        "percent": [pct, other]
    })

    # Donut chart
    fig = px.pie(
        donut_df,
        names="group",
        values="percent",
        hole=0.55,
        color="group",
        color_discrete_map={
            "Top 0.01% of holders": CYAN,
            "All other holders": "#3a3a3f"
        },
    )

    # Chart style
    fig.update_traces(
        textinfo="percent",
        textfont_size=16,
        hovertemplate="%{label}: %{percent:.1%}",
        marker=dict(line=dict(color="rgba(255,255,255,0.15)", width=1))
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="var(--ink)"),
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        annotations=[dict(
            text=f"<b>{pct:.1f}%</b><br>of all<br>Bitcoin",
            font_size=16, font_color=PINK_SOFT, showarrow=False
        )],
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Source: {source} ({year}). The top 0.01% of holders control {pct:.1f}% of Bitcoin’s total supply.")
else:
    st.warning("`crypto_concentration.csv` missing or empty — expected columns: `year, top_0_01_pct_ownership, source`.")

# ──────────────────────────────────────────────────────────────────────────────
# Synthesis Card — cute + final aesthetic version
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("## Crossing Lines: From Tickets to Tokens")

st.markdown(
    f"""
<div class="crt-panel" style="text-align:center;">
  <table style="width:100%; border-collapse:collapse;">
    <thead>
      <tr style="font-weight:600; color:{CYAN};">
        <th style="text-align:left; width:32%; border-bottom:1px solid rgba(255,255,255,0.12); padding:8px;">&nbsp;</th>
        <th style="text-align:left; width:34%; border-bottom:1px solid rgba(255,255,255,0.12); padding:8px;">2003–2016</th>
        <th style="text-align:left; width:34%; border-bottom:1px solid rgba(255,255,255,0.12); padding:8px;">2015–2024</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); color:var(--muted);">🎟️ Speculative form</td>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06);">Lottery tickets</td>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06);">Crypto assets ₿</td>
      </tr>
      <tr>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); color:var(--muted);">🧾 Medium</td>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06);">Paper</td>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06);">Apps &amp; exchanges 📱</td>
      </tr>
      <tr>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); color:var(--muted);">🍀 Tone</td>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06);">Luck &amp; chance</td>
        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06);">Innovation &amp; hustle ⚙️</td>
      </tr>
      <tr>
        <td style="padding:8px; color:var(--muted);">🏦 Outcome</td>
        <td style="padding:8px;">House wins</td>
        <td style="padding:8px;">…still the house wins 🌀</td>
      </tr>
    </tbody>
  </table>

  <div class="small-caption" style="margin-top:10px; color:{PINK_SOFT};">
    <em>“Different syntax, same dream.”</em>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────────────────────────────────────
# ✨ Closing Reflection — Fancy CRT Glow Version
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="crt-panel" style="margin-top: 2rem; padding: 22px 28px; text-align:center;
     box-shadow: 0 0 26px rgba(176,132,245,0.2), 0 0 40px rgba(255,105,201,0.1);">
  <h3 style="color:{CYAN}; text-shadow: 0 0 12px rgba(114,247,255,0.4); margin-bottom:0.75rem;">
     A New Interface for an Old Game
  </h3>
  <p style="line-height:1.6; color:var(--ink); font-size:1.05rem;">
    The currency changed, but the dream stayed the same.<br>
    Whether <span style="color:{PINK_SOFT};">scratched</span>, 
    <span style="color:{PINK_SOFT};">swiped</span>, or 
    <span style="color:{PINK_SOFT};">staked</span>, 
    the promise never really leaves us —<br>
    that hope can be bought, and luck might one day pay off.<br>
    <span style="opacity:0.85;">The difference is in the syntax, not the story.</span>
  </p>
  <div class="small-caption" style="margin-top:10px; color:{PINK_SOFT}; font-style:italic;">
    Project by <strong style="color:{PINK};">Sarina Parrish</strong> • 2025<br>
    Data sources: Gallup, Pew, CNBC, Gemini, BLS
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# Footer
st.markdown("---")
st.caption(
    "Sources: BLS CES 2017–2018 (BLS TED 2019 image); Gallup (2003, 2007, 2016 lottery participation); "
    "Pew, Finder, CNBC/Credit Karma, Gemini (2015–2024 crypto ownership)."
)
