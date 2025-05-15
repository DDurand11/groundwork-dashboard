
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from supabase import create_client, Client

# Setup
st.set_page_config(layout="wide")

SUPABASE_URL = "https://kijnzbskkxtglwkizgqh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imtpam56YnNra3h0Z2x3a2l6Z3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDczMDM4NDYsImV4cCI6MjA2Mjg3OTg0Nn0.k7QeiXhW-wPpqel_VQbgBAmiOPasl7X190Xjpmz9XgI"

@st.cache_resource
def load_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = load_supabase()

st.title("Groundwork Insole Dashboard – 5-Minute Movement Analyzer")
st.markdown("Upload a 5-minute CSV session to analyze foot loading, symmetry, and fatigue trends.")

uploaded_file = st.file_uploader("Upload a TG0-style insole CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("CSV successfully loaded!")

    athlete_name = st.text_input("Athlete Name", "Demo Athlete")
    session_id = st.text_input("Session ID", "Session_001")

    # Time-Series Pressure Plot
    with st.expander("📊 Time-Series Pressure: First 5s"):
        capsense_cols = [col for col in df.columns if "CapSense" in col]
        fig, ax = plt.subplots(figsize=(12, 4))
        for col in capsense_cols:
            ax.plot(df[col][:500], label=col, alpha=0.4)
        ax.set_title("CapSense Sensor Readings (0–5s)")
        ax.set_ylabel("Pressure")
        ax.legend(ncol=6, fontsize=6)
        st.pyplot(fig)

    # Minute-by-Minute Breakdown
    st.header("📈 Minute-by-Minute Performance Breakdown")

    sampling_rate = 100
    block_duration = 60
    samples_per_block = sampling_rate * block_duration
    n_blocks = df.shape[0] // samples_per_block

    block_labels = []
    symmetry_scores = []
    total_loads = []
    forefoot_ratios = []
    rearfoot_ratios = []

    for i in range(n_blocks):
        start = i * samples_per_block
        end = (i + 1) * samples_per_block
        block = df.iloc[start:end]

        left = block["CapSense_0"] + block["CapSense_1"] + block["CapSense_2"]
        right = block["CapSense_10"] + block["CapSense_11"]
        symmetry = (right - left) / (right + left + 1e-5)
        symmetry_scores.append(symmetry.mean())

        pressure_cols = [col for col in block.columns if "CapSense" in col]
        total_pressure = block[pressure_cols].sum(axis=1).sum()
        total_loads.append(total_pressure)

        frame_vals = block.iloc[samples_per_block // 2][pressure_cols].astype(float).values
        grid = frame_vals.reshape((4, 3))
        forefoot = grid[2, :].sum()
        rearfoot = grid[0, :].sum()
        foot_total = grid.sum()
        forefoot_ratios.append(round(100 * forefoot / foot_total, 1))
        rearfoot_ratios.append(round(100 * rearfoot / foot_total, 1))
        block_labels.append(f"Min {i+1}")

    st.subheader("🔀 Symmetry Index Over Time")
    st.line_chart(pd.DataFrame({"Symmetry Index": symmetry_scores}, index=block_labels))

    st.subheader("📦 Total Load Per Minute")
    st.bar_chart(pd.DataFrame({"Total Load": total_loads}, index=block_labels))

    st.subheader("🦶 Foot Zone Distribution")
    st.line_chart(pd.DataFrame({
        "Forefoot Load (%)": forefoot_ratios,
        "Rearfoot Load (%)": rearfoot_ratios
    }, index=block_labels))

    st.subheader("📋 Fatigue / Performance Trend Summary")
    drift = round(symmetry_scores[-1] - symmetry_scores[0], 3)
    peak_load = max(total_loads)
    flag = "⚠️ Asymmetry drift detected." if abs(drift) > 0.05 else "✅ No major symmetry drift."
    st.markdown(
        f"- **Symmetry Shift:** {drift:+.3f}\n"
        f"- **Max Load:** {int(peak_load):,} CapSense units\n"
        f"- **{flag}**\n"
        f"- Suggest monitoring forefoot/rearfoot ratio changes for signs of fatigue."
    )

    # Save to Supabase
    if st.button("💾 Save this session to Supabase"):
        response = supabase.table("sessions").insert({
            "athlete_name": athlete_name,
            "session_id": session_id,
            "symmetry_index": round(np.mean(symmetry_scores), 2),
            "rearfoot_load": round(np.mean(rearfoot_ratios), 1),
            "midfoot_load": 0.0,
            "forefoot_load": round(np.mean(forefoot_ratios), 1),
            "toes_load": 0.0,
            "summary_text": f"{athlete_name} - symmetry drift: {drift:+.3f} - max load: {int(peak_load):,}"
        }).execute()

        if response.data:
            st.success("✅ Session saved to Supabase!")
        else:
            st.error("❌ Error saving session.")
else:
    st.info("Please upload a CSV file to begin.")
