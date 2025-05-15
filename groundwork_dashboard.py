
# groundwork_dashboard.py
# Streamlit-based prototype for Groundwork Performance Systems

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Groundwork Insole Dashboard")

st.markdown("""
Upload your insole CSV data to view pressure maps, symmetry metrics,
movement analysis, and receive intelligent summaries for athletes.
""")

uploaded_file = st.file_uploader("Upload a TG0 insole CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("CSV successfully loaded!")

    # Show raw data
    with st.expander("🔍 View raw data"):
        st.dataframe(df.head())

    # CapSense sensor plots
    st.subheader("📊 CapSense Pressure Sensors (First 5s)")
    capsense_cols = [col for col in df.columns if "CapSense" in col]
    fig, ax = plt.subplots(figsize=(12, 4))
    for col in capsense_cols:
        ax.plot(df[col][:500], label=col, alpha=0.5)
    ax.set_title("CapSense Sensor Readings")
    ax.set_ylabel("Pressure")
    ax.legend(ncol=6, fontsize=6)
    st.pyplot(fig)

    # Symmetry Index
    st.subheader("🦶 Pressure Symmetry Index")
    left = df["CapSense_0"] + df["CapSense_1"] + df["CapSense_2"]
    right = df["CapSense_10"] + df["CapSense_11"]
    symmetry = (right - left) / (right + left + 1e-5)
    st.line_chart(symmetry[:500])
    st.metric("Average Symmetry Index (R-L)", round(symmetry.mean(), 2))

    # Movement metrics
    st.subheader("🚀 Movement Summary (Accelerometer & Gyroscope)")
    st.line_chart(df[["Accel_X", "Accel_Y", "Accel_Z"]][:500])
    st.line_chart(df[["Gyro_Roll", "Gyro_Pitch", "Gyro_Yaw"]][:500])

    # Pressure heatmap
    st.subheader("🔥 Foot Pressure Map Snapshot")
    sample_index = 300
    pressure_vals = df.loc[sample_index, [f"CapSense_{i}" for i in range(12)]].astype(float).values
    grid = pressure_vals.reshape((4, 3))
    fig2, ax2 = plt.subplots(figsize=(4, 6))
    heat = ax2.imshow(grid, cmap="hot", interpolation="nearest", origin="lower")
    ax2.set_xticks([0, 1, 2])
    ax2.set_xticklabels(["Lateral", "Mid", "Medial"])
    ax2.set_yticks([0, 1, 2, 3])
    ax2.set_yticklabels(["Heel", "Midfoot", "Forefoot", "Toes"])
    plt.colorbar(heat, ax=ax2)
    ax2.set_title("Foot Pressure Map (Frame 300)")
    st.pyplot(fig2)

    # Basic summary
    st.subheader("🧠 Intelligent Summary")
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

    sym_label = "Right-dominant" if symmetry.mean() > 0.05 else "Left-dominant" if symmetry.mean() < -0.05 else "Balanced"
    st.info(f"**Posture Insight:** This frame shows a {sym_label} stance.")

else:
    st.info("Please upload a CSV file to begin.")
