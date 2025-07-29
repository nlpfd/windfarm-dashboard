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

# --- UI ---
st.set_page_config(layout="wide")

# Reduce top padding
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Scottish Wind Farm Curtailment Dashboard")

windfarms = df["Generator_Full_Name"].unique()
selected_farm = st.selectbox("Choose Wind Farm", sorted(windfarms))

granularity = st.radio("Select Time Granularity", ["Daily", "Weekly", "Monthly"], horizontal=True)

filtered = df[df["Generator_Full_Name"] == selected_farm]

# --- Total ---
total = filtered["BOA_Volume"].sum()
st.markdown(f"### Total Curtailed (MWh)
{total:,.1f}**")

# --- Plotting ---
if granularity == "Daily":
    daily = filtered.groupby("DateOnly")["BOA_Volume"].sum().reset_index()
    fig = px.bar(daily, x="DateOnly", y="BOA_Volume", title=f"Daily Curtailment for {selected_farm}")
    fig.update_traces(marker_color="steelblue")

elif granularity == "Weekly":
    weekly = filtered.groupby("Week")["BOA_Volume"].sum().reset_index()
    fig = px.bar(weekly, x="Week", y="BOA_Volume", title=f"Weekly Curtailment for {selected_farm}")
    fig.update_traces(marker_color="mediumblue")

else:  # Monthly
    monthly = filtered.groupby("Month")["BOA_Volume"].sum().reset_index()
    fig = px.bar(monthly, x="Month", y="BOA_Volume", title=f"Monthly Curtailment for {selected_farm}")
    fig.update_traces(marker_color="darkblue")

fig.update_layout(
    yaxis_title="Curtailment (MWh)",
    xaxis_title=granularity,
    title_x=0.0,
    margin=dict(l=0, r=0, t=40, b=0),
    height=400
)

st.plotly_chart(fig, use_container_width=True)

# --- Embedded Google Map Below ---
st.markdown("### 📍 Interactive Curtailment Map (2023–2025)")

components.iframe(
    src="https://www.google.com/maps/d/embed?mid=1XPZ5YKrHSGNfGw05w_NyET_U_hotcGk&ehbc=2E312F",
    width="100%",
    height=900
)
