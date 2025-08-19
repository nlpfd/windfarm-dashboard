import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("scottish_half_hourly_curtailment.csv", parse_dates=["Date"])
    # ✅ Correct BOA volumes: MW × 0.5 h = MWh
    df["MWh"] = (df["BOA_Volume"] * 0.5).abs()  # use abs so values are positive
    return df

df = load_data()

# --- UI ---
st.set_page_config(layout="wide")

# Reduce top padding
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        iframe { width: 100% !important; }
    </style>
""", unsafe_allow_html=True)

st.title("Scottish Wind Farm Curtailment Dashboard - Prototype V2")

# --- Year selector ---
years = sorted(df["Date"].dt.year.unique())
selected_year = st.selectbox("Select Year", years, index=years.index(2024))
df = df[df["Date"].dt.year == selected_year]

# --- Farm selector ---
windfarms = df["Generator_Full_Name"].unique()
selected_farm = st.selectbox("Choose Wind Farm", ["All"] + sorted(windfarms))

# --- Time granularity ---
granularity = st.radio("Select Time Granularity", ["Daily", "Weekly", "Monthly"], horizontal=True)

# --- Filter by farm ---
filtered = df if selected_farm == "All" else df[df["Generator_Full_Name"] == selected_farm]
filtered = filtered.copy()

# --- Grouping keys from Date ---
filtered["DateOnly"] = filtered["Date"].dt.date
iso = filtered["Date"].dt.isocalendar()
filtered["Week"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
filtered["Month"] = filtered["Date"].dt.to_period("M").astype(str)

# --- Total ---
total = filtered["MWh"].sum()
st.markdown(f"### Total Curtailed (MWh) in {selected_year}\n**{total:,.1f}**")

# --- Plotting ---
title_prefix = "all listed Wind Farms" if selected_farm == "All" else selected_farm

if granularity == "Daily":
    daily = filtered.groupby("DateOnly", as_index=False)["MWh"].sum()
    # fill all days in the year
    all_days = pd.date_range(f"{selected_year}-01-01", f"{selected_year}-12-31", freq="D")
    daily = daily.set_index("DateOnly").reindex(all_days, fill_value=0).reset_index()
    daily.rename(columns={"index": "DateOnly"}, inplace=True)
    fig = px.bar(daily, x="DateOnly", y="MWh",
                 title=f"Daily Curtailment for {title_prefix} ({selected_year})")
    fig.update_traces(marker_color="steelblue")

elif granularity == "Weekly":
    weekly = filtered.groupby("Week", as_index=False)["MWh"].sum()

    # Generate all ISO weeks for the selected year
    all_week_dates = pd.date_range(
        f"{selected_year}-01-01", f"{selected_year}-12-31", freq="W-MON"
    )  # Mondays = start of ISO week
    all_weeks_iso = all_week_dates.isocalendar()
    all_weeks = (
        all_weeks_iso["year"].astype(str) + "-W" + all_weeks_iso["week"].astype(str).str.zfill(2)
    )
    all_weeks = sorted(all_weeks.unique())

    # Reindex weekly data
    weekly = weekly.set_index("Week").reindex(all_weeks, fill_value=0).reset_index()
    weekly.rename(columns={"index": "Week"}, inplace=True)

    fig = px.bar(weekly, x="Week", y="MWh",
                 title=f"Weekly Curtailment for {title_prefix} ({selected_year})")
    fig.update_traces(marker_color="mediumblue")

else:  # Monthly
    monthly = filtered.groupby("Month", as_index=False)["MWh"].sum()
    # generate all months in the year
    all_months = pd.period_range(f"{selected_year}-01", f"{selected_year}-12", freq="M").astype(str)
    monthly = monthly.set_index("Month").reindex(all_months, fill_value=0).reset_index()
    monthly.rename(columns={"index": "Month"}, inplace=True)
    fig = px.bar(monthly, x="Month", y="MWh",
                 title=f"Monthly Curtailment for {title_prefix} ({selected_year})")
    fig.update_traces(marker_color="darkblue")

fig.update_layout(
    yaxis_title="Curtailment (MWh)",
    xaxis_title=granularity,
    title_x=0.0,
    margin=dict(l=0, r=0, t=40, b=0),
    height=340
)
st.plotly_chart(fig, use_container_width=True)

# --- Responsive Embedded Google Map Below ---
st.markdown("### 📍 Interactive Curtailment Map (2023–2025)")
components.iframe(
    src="https://www.google.com/maps/d/embed?mid=1XPZ5YKrHSGNfGw05w_NyET_U_hotcGk&ehbc=2E312F",
    width=0, height=620
)
st.markdown(
    "<div style='font-size: 0.85rem; color: grey; margin-top: -0.5rem;'>"
    "📌 <em>Tip:</em> Click the icon in the top-left corner of the map to view the list of wind farms."
    "</div>",
    unsafe_allow_html=True
)

# --- Footer Text ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 0.9rem; color: grey;'>"
    "This is an experimental prototype built on NESO and BMRS Elexon curtailment data. "
    "It's intended for educational and exploratory use only, and should not be interpreted as an official representation of NESO data or policy."
    "</div>",
    unsafe_allow_html=True
)
