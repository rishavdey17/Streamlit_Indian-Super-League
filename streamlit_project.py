import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

from mplsoccer.pitch import Pitch, VerticalPitch

st.title("Indian Super League 2024-25")
st.subheader("Actions and Heat Map of all players in the match.")

# Get the absolute path of the Matches directory
MATCHES_DIR = os.path.join(os.getcwd(), "Matches")  # Adjust if needed

# List available match files
match_files = glob.glob(os.path.join(MATCHES_DIR, "*.csv"))

# Extract match names
match_names = [os.path.basename(file).replace(".csv", "") for file in match_files]

if match_names:
    selected_match = st.selectbox("Select A Match", match_names)
    
    file_path = os.path.join(MATCHES_DIR, f"{selected_match}.csv")  # Correct path

    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding="latin-1")
        st.write(f"Loaded data for: {selected_match}")

        # Extract columns containing '/qualifierId' and '/value'
        qualifier_id_cols = [col for col in df.columns if "/qualifierId" in col]
        qualifier_value_cols = [col.replace("/qualifierId", "/value") for col in qualifier_id_cols]

        # Create new columns for end_x and end_y if they don't exist already
        df['end_x'] = df.get('end_x', np.nan)
        df['end_y'] = df.get('end_y', np.nan)

        # Iterate through the qualifier ID columns and update 'end_x' and 'end_y' values
        for id_col, value_col in zip(qualifier_id_cols, qualifier_value_cols):
            df['end_x'] = df.apply(lambda row: row[value_col] if row[id_col] == 140 else row['end_x'], axis=1)
            df['end_y'] = df.apply(lambda row: row[value_col] if row[id_col] == 141 else row['end_y'], axis=1)

        # Proceed with player selection
        player = st.selectbox("Select A Player", df['playerName'].sort_values().unique())

        def filter_data(df, player):
            if player:
                df = df[df['playerName'] == player]

            return df

        filtered_data = filter_data(df, player)

        pitch = VerticalPitch(pitch_type='opta', pitch_color='#09075a', line_color='#c7d5cc')
        fig, ax = pitch.draw(figsize=(10, 10), constrained_layout=True, tight_layout=False)
        fig.set_facecolor('#09075a')

        # Call plot_actions function here...
        plot_actions(filtered_data, ax, pitch)

        endnote = "Made by Rishav. Data Source: OPTA. Built Using: Python and Streamlit."
        plt.figtext(0.515, 0.11, endnote, ha="center", va="top", fontsize=13, color="white")

        st.pyplot(fig)

    else:
        st.error(f"File not found: {file_path}")
else:
    st.warning("No match files found in the 'Matches' folder.")
