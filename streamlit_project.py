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
    footer {display: none;}
    .css-14xtw13 {display: none;}
    </style>
    """, unsafe_allow_html=True
)

st.title("Indian Super League 2024-25")
st.subheader("Actions and Heat Map of all players in the match.")

# Directory where CSV files are stored
MATCHES_DIR = "Matches"  # Ensure this folder contains CSV files

# Get a list of all CSV files in the Matches folder
match_files = glob.glob(os.path.join(MATCHES_DIR, "*.csv"))
match_names = [os.path.basename(file).replace(".csv", "") for file in match_files]

if match_names:
    selected_match = st.selectbox("Select A Match - ", sorted(match_names, reverse = True))
    st.write(f"Loaded data for: {selected_match}")

    # Load the match data
    file_path = os.path.join(MATCHES_DIR, f"{selected_match}.csv")

    if os.path.exists(file_path):
        df = pd.read_csv(file_path)

        # Extract end_x, end_y from qualifiers
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

        # Identify teams
        teams = df['teamName'].unique()
        if len(teams) == 2:
            team1, team2 = teams
            selected_team = st.radio("Select Team -", [team1, team2])

            # Filter players based on selected team
            team_players = df[df['teamName'] == selected_team]['playerName'].dropna().sort_values().unique()
            player = st.selectbox(f"Select a Player from {selected_team} -", team_players, index=None)

            # Filter data for selected player
            def filter_data(df, player):
                return df[df['playerName'] == player] if player else df

            filtered_data = filter_data(df, player)

            # Create Pitch
            pitch = VerticalPitch(pitch_type='opta', pitch_color='black', line_color='white', linewidth=3, corner_arcs=True)
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
                foul_committed = foul[foul['outcome'] == 0]
                
                dribble = df[df['typeId'] == 3]
                succ_dribble = dribble[dribble['outcome'] == 1]
                
                aerial = df[df['typeId'] == 44]
                aerial_won = aerial[aerial['outcome'] == 1]
                aerial_lost = aerial[aerial['outcome'] == 0]

                dispossessed = df[df['typeId'] == 50]

                dribbled_past = df[df['typeId'] == 45]
                
                pickup = df[df['typeId'] == 52]
                punch = df[df['typeId'] == 41]

                # Convert necessary columns to float
                for df_subset in [assist, chance, passes, passes_successful, passes_unsuccessful]:
                    df_subset[['x', 'y', 'end_x', 'end_y']] = df_subset[['x', 'y', 'end_x', 'end_y']].astype(float)

                de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')

                ax.scatter(goal['y'], goal['x'], s=120, c='#00ff00', edgecolor='#000000', label='Goal')
                ax.scatter(shot_saved['y'], shot_saved['x'], s=120, c='#ff7c60', edgecolor='#000000', label='Saved/Blocked Shot')
                ax.scatter(shot_post['y'], shot_post['x'], s=120, c='w', edgecolor='#000000', label='Shot Off Woodwork')
                ax.scatter(shot_miss['y'], shot_miss['x'], s=120, c='r', edgecolor='#000000', label='Shot Off Target')

                pitch.lines(assist.x, assist.y, assist.end_x, assist.end_y, color='#00ff00', comet = True, lw = 2.5, ax=ax, label='Assist')
                ax.scatter(assist['end_y'], assist['end_x'], s=50, c='black', edgecolor='#00ff00')

                pitch.lines(chance.x, chance.y, chance.end_x, chance.end_y, color='#ffea00', comet = True, lw = 2.5, ax=ax, label='Key Pass')
                ax.scatter(chance['end_y'], chance['end_x'], s=50, c='black', edgecolor='#ffea00')

                pitch.arrows(passes_successful.x, passes_successful.y, passes_successful.end_x, passes_successful.end_y, width=0.6, headwidth=5, headlength=5, color='#00ff00', ax=ax, label='Completed Pass')

                pitch.arrows(passes_unsuccessful.x, passes_unsuccessful.y, passes_unsuccessful.end_x, passes_unsuccessful.end_y, width=0.6, headwidth=5, headlength=5, color='red', ax=ax, label='Incomplete Pass')

                plt.scatter(succ_dribble['y'], succ_dribble['x'], s= 200, c = '#fc3900', marker = '*', edgecolor = '#000000', label = 'Dribble')
                plt.scatter(recovery['y'], recovery['x'], s= 120, c = '#fcd200', marker = ',', edgecolor = '#000000', label = 'Ball Recovery')
                plt.scatter(tackle['y'], tackle['x'], s= 120,c = 'cyan', marker = ',', edgecolor = '#000000', label = 'Tackle')
                plt.scatter(block['y'], block['x'], s = 120, c = '#009afd', marker = ',', edgecolor = '#000000', label ='Block')
                plt.scatter(interception['y'], interception['x'], s = 120, c = '#ff007f', marker = ',', edgecolor = '#000000', label = 'Interception')
                plt.scatter(clearance['y'], clearance['x'], s = 100, c = '#9999ff', marker = 'x', edgecolor = '#000000', label = 'Clearance')
                plt.scatter(offside['y'], offside['x'], s= 120, c = '#fcd200', marker = 'P', edgecolor = '#000000', label = 'Offside Provoked')
                plt.scatter(shield['y'], shield['x'], s = 50, c = '#dd571c', marker = 'D', edgecolor = '#000000', label = 'Shielding Ball Out')
                plt.scatter(foul_won['y'], foul_won['x'], s= 120, c = '#008000', marker = 'X', edgecolor = '#000000', label = 'Foul Won')
                plt.scatter(foul_committed['y'], foul_committed['x'], s= 120, c = '#c21919', marker = 'X', edgecolor = '#000000', label = 'Foul Committed')
                plt.scatter(aerial_won['y'], aerial_won['x'], s = 100, c = '#008000', marker = '^', edgecolor = '#000000', label = 'Aerial Won')
                plt.scatter(aerial_lost['y'], aerial_lost['x'], s = 100, c = '#c21919', marker = '^', edgecolor = '#000000', label = 'Aerial Lost')
                plt.scatter(dispossessed['y'], dispossessed['x'], s = 100, c = '#cb0000', marker = 'p', edgecolor = '#000000', label = 'Dispossessed')
                plt.scatter(dribbled_past['y'], dribbled_past['x'], s = 50, c = '#cb0000', marker = 'x', edgecolor = '#000000', label = 'Dribbled Past')

                plt.scatter(punch['y'], punch['x'], s = 100, c = '#ffec00', marker = 'o', edgecolor = '#000000', label = 'Keeper Punch')
                plt.scatter(pickup['y'], pickup['x'], s = 120, c = '#dd571c', marker = 'P', edgecolor = '#000000', label = 'Keeper Pick-Up')

                ax.legend(loc='upper left', bbox_to_anchor=(-0.2, 1.18), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')

                ax.legend(loc='upper left', bbox_to_anchor=(-0.2, 1.15), framealpha=0.9, ncol=4, edgecolor='#000000')

            # Plot player actions
            plot_actions(filtered_data, ax, pitch)

            # Add footer text
            endnote = "Made by Rishav Dey. Data Source: OPTA. Built Using: Python and Streamlit."
            plt.figtext(0.515, 0.115, endnote, ha="center", va="top", fontsize=13, color="white")

            # Display plot in Streamlit
            st.pyplot(fig)
