import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os

from mplsoccer.pitch import VerticalPitch

# Add custom CSS to hide GitHub link in top-right corner
st.markdown(
    """
    <style>
    /* Hide the entire footer */
    footer {display: none;}

    /* Or, if you just want to hide the GitHub icon specifically */
    .css-14xtw13 {display: none;}
    </style>
    """, unsafe_allow_html=True
)


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
    selected_match = st.selectbox("Select A Match - ", match_names)
    st.write(f"Loaded data for: {selected_match}")

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

       # Identify unique teams in the match
    teams = df['teamName'].unique()

    if len(teams) == 2:  # Ensure there are two teams
        team1, team2 = teams

# Create dropdowns for team selection
        selected_team = st.radio("Select Team -", [team1, team2])

# Filter players based on selected team
        team_players = df[df['teamName'] == selected_team]['playerName'].sort_values().unique()

# Player selection based on team
        player = st.selectbox(f"Select a Player from {selected_team} -", team_players, index=None)

# Now filter data based on the selected player
        filtered_data = df[df['playerName'] == player]


        # Player selection
        # Filter data based on selected player
        def filter_data(df, player):
            if player:
                df = df[df['playerName'] == player]
            return df

        filtered_data = filter_data(df, player)

        # Create pitch
        pitch = VerticalPitch(pitch_type='opta', pitch_color='black', line_color='white', linewidth = 3, corner_arcs = True)
        fig, ax = pitch.draw(figsize=(10, 10), constrained_layout=True, tight_layout=False)
        fig.set_facecolor('black')

        # Function to plot actions on the pitch
        def plot_actions(df, ax, pitch):
            goal = df[df['typeId'] == 16]
            shot_miss = df[df['typeId'] == 13]
            shot_post = df[df['typeId'] == 14]
            shot_saved = df[df['typeId'] == 15]
            
            assist = df[df['assist'] == 1]
            chance = df[df['keyPass'] == 1]
            passes = df[df['typeId'] == 1]
            passes_successful = passes[(passes['outcome'] == 1) & ~(passes['eventId'].isin(chance['eventId']))]
            passes_unsuccessful = passes[passes['outcome'] == 0]
            
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
                         headwidth=5, headlength=5, color='#dc6601', edgecolor='#000000', ax=ax, label='Key Pass')

            pitch.arrows(passes_successful.x, passes_successful.y, passes_successful.end_x, passes_successful.end_y, width=0.75,
                         headwidth=5, headlength=5, color='#00ff00', ax=ax, label='Completed Pass')

            pitch.arrows(passes_unsuccessful.x, passes_unsuccessful.y, passes_unsuccessful.end_x, passes_unsuccessful.end_y, width=0.75,
                         headwidth=5, headlength=5, color='red', ax=ax, label='Incomplete Pass')

            plt.scatter(succ_dribble['y'], succ_dribble['x'], s= 120, c = '#dc6601', marker = 'X', edgecolor = '#000000', label = 'Dribble')
            plt.scatter(foul_won['y'], foul_won['x'], s= 120, c = '#009afd', marker = 'X', edgecolor = '#000000', label = 'Foul Won')
            plt.scatter(tackle['y'], tackle['x'], s= 100,c = 'w', marker = ',', edgecolor = '#000000', label = 'Tackle')
            plt.scatter(recovery['y'], recovery['x'], s= 100, c = '#ffea00', marker = ',', edgecolor = '#000000', label = 'Ball Recovery')
            plt.scatter(interception['y'], interception['x'], s = 100, c = '#ff007f', marker = ',', edgecolor = '#000000', label = 'Interception')
            plt.scatter(block['y'], block['x'], s = 100, c = '#008080', marker = ',', edgecolor = '#000000', label ='Block')
            plt.scatter(clearance['y'], clearance['x'], s = 120, c = '#00ffff', marker = '^', edgecolor = '#000000', label = 'Clearance')
            plt.scatter(aerial_won['y'], aerial_won['x'], s = 100, c = '#9999ff', marker = '^', edgecolor = '#000000', label = 'Aerial Won')
            plt.scatter(offside['y'], offside['x'], s= 120, c = 'r', marker = 'P', edgecolor = '#000000', label = 'Offside Provoked')
            plt.scatter(shield['y'], shield['x'], s = 120, c = '#dd571c', marker = 'H', edgecolor = '#000000', label = 'Shielding Ball Out')
            plt.scatter(punch['y'], punch['x'], s = 100, c = '#ff007f', marker = '^', edgecolor = '#000000', label = 'Keeper Punch')
            ax.scatter(pickup['y'], pickup['x'], s = 120, c = '#dd571c', marker = 'P', edgecolor = '#000000', label = 'Keeper Pick-Up')

            ax.legend(loc='upper left', bbox_to_anchor=(-0.2, 1.15), framealpha=0.9, ncol=4, edgecolor='#000000')

        # Plot the selected match data
        plot_actions(filtered_data, ax, pitch)

        # Add a footer to the figure
        endnote = "Made by Rishav Dey. Data Source: OPTA. Built Using: Python and Streamlit."
        plt.figtext(0.515, 0.115, endnote, ha="center", va="top", fontsize=13, color="white")

        st.pyplot(fig)
    else:
        st.error(f"File {selected_match}.csv not found.")
else:
    st.warning("No match files found in the 'Matches' folder.")
