
# groundwork_dashboard.py
# Streamlit-based prototype for Groundwork Performance Systems (Advanced Version)

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from supabase import create_client, Client

# Replace with your actual URL and key
SUPABASE_URL = "https://kijnzbskkxtglwkizgqh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtpam56YnNra3h0Z2x3a2l6Z3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczMDM4NDYsImV4cCI6MjA2Mjg3OTg0Nn0.k7QeiXhW-wPpqel_VQbgBAmiOPasl7X190Xjpmz9XgI"

@st.cache_resource
def load_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = load_supabase()

st.set_page_config(layout="wide")
st.title("Groundwork Insole Dashboard – Research-Style Data")

st.markdown("""
Upload your advanced insole CSV data (e.g., from TG0 research-style sensor output) to view foot pressure trends,
symmetry metrics, dynamic movement visualizations, and AI-generated session summaries.
""")

uploaded_file = st.file_uploader("Upload a TG0-style insole CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("CSV successfully loaded!")


    # Athlete info (mock demo)
    athlete_name = st.text_input("Athlete Name", "Demo Athlete")
    session_id = st.text_input("Session ID", "Session_001")

    # Time-Series Sensor Preview
    with st.expander("📊 Time-Series Pressure: First 5s"):
        capsense_cols = [col for col in df.columns if "CapSense" in col]
        fig, ax = plt.subplots(figsize=(12, 4))
        for col in capsense_cols:
            ax.plot(df[col][:500], label=col, alpha=0.4)
        ax.set_title("CapSense Sensor Readings (0–5s)")
        ax.set_ylabel("Pressure")
        ax.legend(ncol=6, fontsize=6)
        st.pyplot(fig)

    # Symmetry Analysis
    st.subheader("🦶 Pressure Symmetry Index (Forefoot Sensors)")
    left = df["CapSense_0"] + df["CapSense_1"] + df["CapSense_2"]
    right = df["CapSense_10"] + df["CapSense_11"]
    symmetry = (right - left) / (right + left + 1e-5)
    st.line_chart(symmetry)
    sym_label = "Right-dominant" if symmetry.mean() > 0.05 else "Left-dominant" if symmetry.mean() < -0.05 else "Balanced"
    st.metric("Average Symmetry Index (R-L)", round(symmetry.mean(), 2), delta=None)
    st.info(f"This session indicates a **{sym_label}** loading pattern.")

    # Dynamic Movement Profile
    st.subheader("🏃 Movement Profile (Accelerometer)")
    st.line_chart(df[["Accel_X", "Accel_Y", "Accel_Z"]])
    st.subheader("🔁 Rotational Profile (Gyroscope)")
    st.line_chart(df[["Gyro_Roll", "Gyro_Pitch", "Gyro_Yaw"]])

    # Heatmap Snapshot
    st.subheader("🔥 Foot Pressure Heatmap Snapshot (Frame 250)")
    sample_index = 250
    pressure_vals = df.loc[sample_index, [f"CapSense_{i}" for i in range(12)]].astype(float).values
    grid = pressure_vals.reshape((4, 3))
    fig2, ax2 = plt.subplots(figsize=(4, 6))
    heat = ax2.imshow(grid, cmap="hot", interpolation="nearest", origin="lower")
    ax2.set_xticks([0, 1, 2])
    ax2.set_xticklabels(["Lateral", "Mid", "Medial"])
    ax2.set_yticks([0, 1, 2, 3])
    ax2.set_yticklabels(["Heel", "Midfoot", "Forefoot", "Toes"])
    plt.colorbar(heat, ax=ax2)
    ax2.set_title("Pressure Snapshot (Mid-Step)")
    st.pyplot(fig2)

    # Force Region Distribution
    st.subheader("🧠 Load Distribution by Region")
    rearfoot = grid[0, :].sum()
    midfoot = grid[1, :].sum()
    forefoot = grid[2, :].sum()
    toes = grid[3, :].sum()
    total = rearfoot + midfoot + forefoot + toes
    st.markdown(f"""
    - **Rearfoot Load:** {round(100*rearfoot/total, 1)}%
    - **Midfoot Load:** {round(100*midfoot/total, 1)}%
    - **Forefoot Load:** {round(100*forefoot/total, 1)}%
    - **Toes Load:** {round(100*toes/total, 1)}%
    """)

    # Summary Interpretation
    st.subheader("📋 AI-Style Session Summary")
    st.markdown(f"""
    Athlete **{athlete_name}** completed session **{session_id}** with a {sym_label} stance and relatively balanced
    load distribution across foot zones. Pressure signals indicated {round(np.max(df[capsense_cols].mean(axis=1)) / 150)} step cycles. 

    Accelerometer data showed vertical peak activity consistent with walking or light jogging. Rotational data suggests
    controlled direction changes without excessive twisting. Heatmap frame reflects a typical mid-stance phase.

    👉 Consider monitoring future sessions for increasing asymmetry or persistent forefoot loading.
    """)
else:
    st.info("Please upload a CSV file to begin.")
# Save to Supabase
if st.button("💾 Save this session to Supabase"):
    response = supabase.table("sessions").insert({
        "athlete_name": athlete_name,
        "session_id": session_id,
        "symmetry_index": round(symmetry.mean(), 2),
        "rearfoot_load": round(100 * rearfoot / total, 1),
        "midfoot_load": round(100 * midfoot / total, 1),
        "forefoot_load": round(100 * forefoot / total, 1),
        "toes_load": round(100 * toes / total, 1),
        "summary_text": f"{athlete_name} - {sym_label} - {session_id} summary"
    }).execute()

    if response.data:
        st.success("✅ Session saved to Supabase!")
    else:
        st.error("❌ Error saving session.")
