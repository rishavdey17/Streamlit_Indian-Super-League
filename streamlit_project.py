import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

from mplsoccer.pitch import VerticalPitch

st.title("Indian Super League 2024-25")
st.subheader("Actions and Heat Map of all players in the match.")

# Directory where CSV files are stored
MATCHES_DIR = "Matches"  # Ensure this is the folder where CSV files are stored

# Get a list of all CSV files in the Matches folder
match_files = glob.glob(os.path.join(MATCHES_DIR, "*.csv"))

# Extract the match names (file names without extension)
match_names = [os.path.basename(file).replace(".csv", "") for file in match_files]

if match_names:
    # Allow user to select a match
    selected_match = st.selectbox("Select A Match", match_names)

    # Load the selected match's data
    file_path = os.path.join(MATCHES_DIR, f"{selected_match}.csv")
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)

        # Process the data
        qualifier_id_cols = [col for col in df.columns if "/qualifierId" in col]
        qualifier_value_cols = [col.replace("/qualifierId", "/value") for col in qualifier_id_cols]

        df['end_x'] = None
        df['end_y'] = None

        for id_col, value_col in zip(qualifier_id_cols, qualifier_value_cols):
            df['end_x'] = df.apply(
                lambda row: row[value_col] if row[id_col] == 140 else row['end_x'], axis=1
            )
            df['end_y'] = df.apply(
                lambda row: row[value_col] if row[id_col] == 141 else row['end_y'], axis=1
            )

        # Player selection
        player = st.selectbox("Select A Player", df['playerName'].sort_values().unique(), index = None)

        # Filter data based on selected player
        def filter_data(df, player):
            if player:
                df = df[df['playerName'] == player]
            return df

        filtered_data = filter_data(df, player)

        # Create pitch
        pitch = VerticalPitch(pitch_type='opta', pitch_color='#09075a', line_color='#c7d5cc')
        fig, ax = pitch.draw(figsize=(10, 10), constrained_layout=True, tight_layout=False)
        fig.set_facecolor('#09075a')

        # Function to plot actions on the pitch
        def plot_actions(df, ax, pitch):
            goal = df[df['typeId'] == 16]
            shot_miss = df[df['typeId'] == 13]
            shot_post = df[df['typeId'] == 14]
            shot_saved = df[df['typeId'] == 15]
            recovery = df[df['typeId'] == 49]
            offside = df[df['typeId'] == 55]
            shield = df[df['typeId'] == 56]
            tackle = df[df['typeId'] == 7]
            succ_tackle = tackle[tackle['outcome'] == 1]
            interception = df[df['typeId'] == 8]
            block = df[df['typeId'] == 10]
            clearance = df[df['typeId'] == 12]
            foul = df[df['typeId'] == 4]
            foul_won = foul[foul['outcome'] == 1]
            dribble = df[df['typeId'] == 3]
            succ_dribble = dribble[dribble['outcome'] == 1]
            aerial = df[df['typeId'] == 44]
            aerial_won = aerial[aerial['outcome'] == 1]
            assist = df[df['assist'] == 1]
            chance = df[df['keyPass'] == 1]
            passes = df[df['typeId'] == 1]
            passes_successful = passes[passes['outcome'] == 1]
            passes_unsuccessful = passes[passes['outcome'] == 0]
            pickup = df[df['typeId'] == 52]
            punch = df[df['typeId'] == 41]

            assist[['x', 'y', 'end_x', 'end_y']] = assist[['x', 'y', 'end_x', 'end_y']].astype(float)
            chance[['x', 'y', 'end_x', 'end_y']] = chance[['x', 'y', 'end_x', 'end_y']].astype(float)
            passes[['x', 'y', 'end_x', 'end_y']] = passes[['x', 'y', 'end_x', 'end_y']].astype(float)
            passes_successful[['x', 'y', 'end_x', 'end_y']] = passes_successful[['x', 'y', 'end_x', 'end_y']].astype(float)
            passes_unsuccessful[['x', 'y', 'end_x', 'end_y']] = passes_unsuccessful[['x', 'y', 'end_x', 'end_y']].astype(float)

            # Plot actions on the pitch
            kde = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.5, n_levels=10, cmap='magma')

            ax.scatter(goal['y'], goal['x'], s=120, c='#00ff00', edgecolor='#000000', label='Goal')
            ax.scatter(shot_saved['y'], shot_saved['x'], s=120, c='#ffea00', edgecolor='#000000', label='Saved/Blocked Shot')
            ax.scatter(shot_post['y'], shot_post['x'], s=120, c='w', edgecolor='#000000', label='Shot Off Woodwork')
            ax.scatter(shot_miss['y'], shot_miss['x'], s=120, c='r', edgecolor='#000000', label='Shot Off Target')

            pitch.arrows(assist.x, assist.y, assist.end_x, assist.end_y, width=2,
                         headwidth=5, headlength=5, color='#00ff00', edgecolor='#000000', ax=ax, label='Assist')
            pitch.arrows(chance.x, chance.y, chance.end_x, chance.end_y, width=2,
                         headwidth=5, headlength=5, color='#ffea00', edgecolor='#000000', ax=ax, label='Key Pass')

            # Add other actions like pass, tackle, dribble, etc.

            ax.legend(loc='upper left', bbox_to_anchor=(-0.2, 1.15), framealpha=0.6, ncol=4, edgecolor='#000000')

        # Plot the selected match data
        plot_actions(filtered_data, ax, pitch)

        # Add a footer to the figure
        endnote = "Made by Rishav. Data Source: OPTA. Built Using: Python and Streamlit."
        plt.figtext(0.515, 0.11, endnote, ha="center", va="top", fontsize=13, color="white")

        st.pyplot(fig)
    else:
        st.error(f"File {selected_match}.csv not found.")
else:
    st.warning("No match files found in the 'Matches' folder.")
