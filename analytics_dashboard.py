import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# -----------------------
# Page Config
# -----------------------
st.set_page_config(
    page_title="ZHSF Enterprise Analytics",
    layout="wide"
)

st.markdown("<h1 style='text-align: center; color:#4B0082;'>📊 ZHSF Enterprise Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("### Executive Intelligence Panel")
st.markdown("---")

# -----------------------
# Sidebar Filters
# -----------------------
st.sidebar.header("🔧 Filters")

np.random.seed(42)
dates = pd.date_range(end=datetime.today(), periods=60)

start_date, end_date = st.sidebar.date_input(
    "📅 Select Date Range",
    [dates.min().date(), dates.max().date()],
    min_value=dates.min().date(),
    max_value=dates.max().date()
)

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# -----------------------
# Simulated Enterprise Data
# -----------------------
dates_filtered = pd.date_range(start=start_date, end=end_date)

chat_volume = np.random.randint(50, 200, len(dates_filtered))
enrollments = np.random.randint(10, 60, len(dates_filtered))

data = pd.DataFrame({
    "date": dates_filtered,
    "chats": chat_volume,
    "enrollments": enrollments
})

data["conversion_rate"] = (data["enrollments"] / data["chats"]) * 100
data["7_day_chat_avg"] = data["chats"].rolling(7).mean()
data["7_day_enroll_avg"] = data["enrollments"].rolling(7).mean()

# Retention Simulation
data["returning_users"] = np.random.randint(20, 80, len(data))
data["retention_rate"] = (data["returning_users"] / data["chats"]) * 100

# -----------------------
# KPI Calculation
# -----------------------
total_chats = data["chats"].sum()
total_enroll = data["enrollments"].sum()
avg_conversion = data["conversion_rate"].mean()
avg_retention = data["retention_rate"].mean()

previous_period = data.iloc[:len(data)//2]
current_period = data.iloc[len(data)//2:]

growth_chats = ((current_period["chats"].sum() - previous_period["chats"].sum()) / previous_period["chats"].sum()) * 100

# -----------------------
# KPI Section
# -----------------------
st.markdown("## 📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

def kpi_card(title, value, delta=None):
    st.markdown(f"""
        <div style='background:white;padding:20px;border-radius:12px;
        box-shadow:0 4px 10px rgba(0,0,0,0.1);text-align:center'>
        <h4>{title}</h4>
        <h2>{value}</h2>
        <p style='color:green'>{delta if delta else ""}</p>
        </div>
    """, unsafe_allow_html=True)

with col1:
    kpi_card("💬 Total Chats", f"{total_chats:,}", f"{growth_chats:.2f}% Growth")

with col2:
    kpi_card("📝 Total Enrollments", f"{total_enroll:,}")

with col3:
    kpi_card("✅ Avg Conversion", f"{avg_conversion:.2f}%")

with col4:
    kpi_card("🔁 Avg Retention", f"{avg_retention:.2f}%")

st.markdown("---")

# -----------------------
# Chat & Enrollment Trends
# -----------------------
st.subheader("📈 Engagement Trend (7-Day Rolling Average)")
st.line_chart(data.set_index("date")[["7_day_chat_avg", "7_day_enroll_avg"]])

# -----------------------
# Conversion Trend
# -----------------------
st.subheader("📊 Daily Conversion Rate")
st.line_chart(data.set_index("date")["conversion_rate"])

# -----------------------
# Enrollment Funnel (Improved)
# -----------------------
st.subheader("🎓 Enrollment Funnel Analysis")

funnel_data = pd.DataFrame({
    "Stage": ["Chats Initiated", "Interested Users", "Applications Started", "Enrolled"],
    "Users": [
        total_chats,
        int(total_chats * 0.7),
        int(total_chats * 0.5),
        total_enroll
    ]
})

st.bar_chart(funnel_data.set_index("Stage"))

# -----------------------
# Peak Usage Hours
# -----------------------
st.subheader("⏰ Peak Chatbot Usage Hours")
hours = np.random.randint(0, 24, 500)
hourly_distribution = pd.Series(hours).value_counts().sort_index()
st.bar_chart(hourly_distribution)

# -----------------------
# Export Feature
# -----------------------
st.markdown("---")
st.subheader("📥 Export Data")

csv = data.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Analytics Report (CSV)",
    data=csv,
    file_name="zhsf_enterprise_report.csv",
    mime="text/csv"
)

# -----------------------
# Footer
# -----------------------
st.markdown("---")
st.markdown("<p style='text-align:center; color:gray;'>© 2026 ZHSF Enterprise Analytics </p>", unsafe_allow_html=True)