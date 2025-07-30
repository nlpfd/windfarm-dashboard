
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

# --- Load Data ---
@st.cache_data
def load_data():
    df = pd.read_csv("scottish_half_hourly_curtailment.csv", parse_dates=["Date"])
    df["DateOnly"] = df["Date"].dt.date
    df["Week"] = df["Date"].dt.strftime('%Y-W%U')
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df

df = load_data()

# --- UI Setup ---
st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        iframe {
            width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Scottish Wind Farm Curtailment Dashboard")

# --- Dropdowns and Filtering ---
windfarms = df["Generator_Full_Name"].unique()
selected_farm = st.selectbox("Choose Wind Farm", sorted(windfarms))

granularity = st.radio("Select Time Granularity", ["Daily", "Weekly", "Monthly"], horizontal=True)

filtered = df[df["Generator_Full_Name"] == selected_farm]

# --- Total ---
total = filtered["BOA_Volume"].sum()
st.markdown(f"### Total Curtailed (MWh)\n**{total:,.1f}**")

# --- Aggregation and Plotting ---
if granularity == "Daily":
    data = filtered.groupby("DateOnly")["BOA_Volume"].sum().reset_index()
    x_col = "DateOnly"
    title = f"Daily Curtailment for {selected_farm}"
elif granularity == "Weekly":
    data = filtered.groupby("Week")["BOA_Volume"].sum().reset_index()
    x_col = "Week"
    title = f"Weekly Curtailment for {selected_farm}"
else:
    data = filtered.groupby("Month")["BOA_Volume"].sum().reset_index()
    x_col = "Month"
    title = f"Monthly Curtailment for {selected_farm}"

fig = px.bar(data, x=x_col, y="BOA_Volume", title=title)
fig.update_traces(marker_color="steelblue")

# Axis styling for clarity on laptops
fig.update_layout(
    yaxis_title="Curtailment (MWh)",
    xaxis_title=granularity,
    title_x=0.0,
    margin=dict(l=10, r=10, t=40, b=50),
    height=500,
    xaxis_tickangle=-45,
)

st.plotly_chart(fig, use_container_width=True)

# --- Embedded Map ---
st.markdown("### 📍 Interactive Curtailment Map (2023–2025)")
components.iframe(
    src="https://www.google.com/maps/d/embed?mid=1XPZ5YKrHSGNfGw05w_NyET_U_hotcGk&ehbc=2E312F",
    width="100%",
    height=900
)
