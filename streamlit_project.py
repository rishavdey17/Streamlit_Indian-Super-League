import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
from mplsoccer.pitch import VerticalPitch
from scipy.spatial import ConvexHull
from natsort import natsorted

# Add custom CSS to hide GitHub link in top-right corner
if 'action_filter' not in st.session_state:
    st.session_state.action_filter = "All Actions"

st.title("Indian Super League 2024-25")
st.subheader("Actions and Heat Map of all players in the match.")

MATCHES_DIR = "Matches"  # Directory containing match CSV files
match_files = glob.glob(os.path.join(MATCHES_DIR, "*.csv"))
match_names = [os.path.basename(file).replace(".csv", "") for file in match_files]

if match_names:
    selected_match = st.selectbox("Select A Match -", sorted(match_names, reverse = True))
    st.write(f"Loaded data for: {selected_match}")

    file_path = os.path.join(MATCHES_DIR, f"{selected_match}.csv")
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        qualifier_id_cols = [col for col in df.columns if "/qualifierId" in col]
        qualifier_value_cols = [col.replace("/qualifierId", "/value") for col in qualifier_id_cols]
        
        df['end_x'] = np.nan
        df['end_y'] = np.nan
        
        for id_col, value_col in zip(qualifier_id_cols, qualifier_value_cols):
            df.loc[df[id_col] == 140, 'end_x'] = df[value_col]
            df.loc[df[id_col] == 141, 'end_y'] = df[value_col]
        
        teams = df['teamName'].unique()
        
        if len(teams) == 2:
            team1, team2 = teams
            selected_team = st.radio("Select Team -", [team1, team2])
            team_players = df[df['teamName'] == selected_team]['playerName'].dropna().sort_values().unique()
            player = st.selectbox(f"Select a Player from {selected_team} -", team_players)
            player_position = df[df['playerName'] == player]['Position'].iloc[0] if player else None

            st.write(f"**Selected Match:** {selected_match}")
            st.write(f"**Selected Team:** {selected_team}")
            st.write(f"**Selected Player:** {player}")

            filtered_data = df[df['playerName'] == player]

            action_filters = ["All Actions", "Heat Map & Passes", "Offensive Actions", "Defensive Actions", "Convex Hull"]
            col1, col2, col3, col4, col5 = st.columns(5)

            if col1.button("ALL ACTIONS IN THE MATCH"):
                st.session_state.action_filter = "ALL ACTIONS IN THE MATCH"
            if col2.button("PASSES & HEATMAP"):
                st.session_state.action_filter = "PASSES & HEATMAP"
            if col3.button("OFFENSIVE ACTIONS"):
                st.session_state.action_filter = "OFFENSIVE ACTIONS"
            if col4.button("DEFENSIVE ACTIONS"):
                st.session_state.action_filter = "DEFENSIVE ACTIONS"
            if col5.button("CONVEX HULL"):
                st.session_state.action_filter = "CONVEX HULL"

        pitch = VerticalPitch(pitch_type='opta', pitch_color='black', line_color='white', linewidth=3, corner_arcs=True)
        fig, ax = pitch.draw(figsize=(10, 10), constrained_layout=True, tight_layout=False)
        fig.set_facecolor('black')

        action_filter = st.session_state.action_filter

        if action_filter == "ALL ACTIONS IN THE MATCH":
            goal = filtered_data[filtered_data['typeId'] == 16]
            shot_miss = filtered_data[filtered_data['typeId'] == 13]
            shot_post = filtered_data[filtered_data['typeId'] == 14]
            shot_saved = filtered_data[filtered_data['typeId'] == 15]
                
            assist = filtered_data[filtered_data['assist'] == 1]
            chance = filtered_data[filtered_data['keyPass'] == 1]
            passes = filtered_data[filtered_data['typeId'] == 1]
            passes_successful = passes[(passes['outcome'] == 1) & ~(passes['eventId'].isin(chance['eventId']))]
            passes_unsuccessful = passes[passes['outcome'] == 0]
                
            recovery = filtered_data[filtered_data['typeId'] == 49]
            offside = filtered_data[filtered_data['typeId'] == 55]
            shield = filtered_data[filtered_data['typeId'] == 56]
                
            tackle = filtered_data[filtered_data['typeId'] == 7]
            succ_tackle = tackle[tackle['outcome'] == 1]
                
            interception = filtered_data[filtered_data['typeId'] == 8]
            block = filtered_data[filtered_data['typeId'] == 10]
            clearance = filtered_data[filtered_data['typeId'] == 12]
                
            foul = filtered_data[filtered_data['typeId'] == 4]
            foul_won = foul[foul['outcome'] == 1]
            foul_committed = foul[foul['outcome'] == 0]
                
            dribble = filtered_data[filtered_data['typeId'] == 3]
            succ_dribble = dribble[dribble['outcome'] == 1]
                
            aerial = filtered_data[filtered_data['typeId'] == 44]
            aerial_won = aerial[aerial['outcome'] == 1]
            aerial_lost = aerial[aerial['outcome'] == 0]

            dispossessed = filtered_data[filtered_data['typeId'] == 50]

            dribbled_past = filtered_data[filtered_data['typeId'] == 45]
                
            pickup = filtered_data[filtered_data['typeId'] == 52]
            punch = filtered_data[filtered_data['typeId'] == 41]

            for df_subset in [assist, chance, passes, passes_successful, passes_unsuccessful]:
                df_subset[['x', 'y', 'end_x', 'end_y']] = df_subset[['x', 'y', 'end_x', 'end_y']].astype(float)

            if player_position == 'Goalkeeper':
                de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')
                pitch.arrows(passes_successful.x, passes_successful.y, passes_successful.end_x, passes_successful.end_y, width=0.75, color='#00ff00', ax=ax, label='Completed Pass')
                pitch.arrows(passes_unsuccessful.x, passes_unsuccessful.y, passes_unsuccessful.end_x, passes_unsuccessful.end_y, width=0.75, color='red', ax=ax, label='Incomplete Pass')
                plt.scatter(block['y'], block['x'], s = 200, c = '#00ff00', marker = '*', edgecolor = '#000000', label ='Save')
                plt.scatter(punch['y'], punch['x'], s = 100, c = '#ffec00', marker = 'o', edgecolor = '#000000', label = 'Punch')
                plt.scatter(pickup['y'], pickup['x'], s = 120, c = '#dd571c', marker = '+', edgecolor = '#000000', label = 'Pick-Up')
                plt.scatter(recovery['y'], recovery['x'], s= 120, c = '#fcd200', marker = ',', edgecolor = '#000000', label = 'Ball Recovery')
                plt.scatter(tackle['y'], tackle['x'], s= 120,c = 'cyan', marker = ',', edgecolor = '#000000', label = 'Tackle')
                plt.scatter(interception['y'], interception['x'], s = 120, c = '#ff007f', marker = ',', edgecolor = '#000000', label = 'Interception')
                plt.scatter(clearance['y'], clearance['x'], s = 100, c = '#9999ff', marker = 'x', edgecolor = '#000000', label = 'Clearance')
                plt.scatter(offside['y'], offside['x'], s= 120, c = '#fcd200', marker = 'P', edgecolor = '#000000', label = 'Offside Provoked')
                plt.scatter(shield['y'], shield['x'], s = 50, c = '#dd571c', marker = 'D', edgecolor = '#000000', label = 'Shielding Ball Out')
                plt.scatter(succ_dribble['y'], succ_dribble['x'], s= 200, c = '#fc3900', marker = '*', edgecolor = '#000000', label = 'Dribble')
                plt.scatter(foul_won['y'], foul_won['x'], s= 120, c = '#008000', marker = 'X', edgecolor = '#000000', label = 'Foul Won')
                plt.scatter(foul_committed['y'], foul_committed['x'], s= 120, c = '#c21919', marker = 'X', edgecolor = '#000000', label = 'Foul Committed')
                plt.scatter(dispossessed['y'], dispossessed['x'], s = 100, c = '#cb0000', marker = 'p', edgecolor = '#000000', label = 'Dispossessed')
                plt.scatter(dribbled_past['y'], dribbled_past['x'], s = 50, c = '#cb0000', marker = 'x', edgecolor = '#000000', label = 'Dribbled Past')

                ax.legend(loc='upper left', bbox_to_anchor=(-0.19, 1.12), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')

                endnote = "Made by Rishav. Data Source: OPTA. Built Using: Python and Streamlit."
                plt.figtext(0.46, 0.115, endnote, ha="center", va="top", fontsize=13, color="white")
   
                if player or selected_team:
                    st.pyplot(fig)
                    plt.close(fig)

            else:
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

                ax.legend(loc='upper left', bbox_to_anchor=(-0.23, 1.17), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')

                endnote = "Made by Rishav. Data Source: OPTA. Built Using: Python and Streamlit."
                plt.figtext(0.53, 0.115, endnote, ha="center", va="top", fontsize=13, color="white")
                
                if player or selected_team:
                    st.pyplot(fig)
                    plt.close(fig)

        if action_filter == "PASSES & HEATMAP":
            passes = filtered_data[filtered_data['typeId'] == 1]
            passes_successful = passes[passes['outcome'] == 1]
            passes_unsuccessful = passes[passes['outcome'] == 0]
            assist = filtered_data[filtered_data['assist'] == 1]
            chance = filtered_data[filtered_data['keyPass'] == 1]

            for df_subset in [assist, chance, passes, passes_successful, passes_unsuccessful]:
                df_subset[['x', 'y', 'end_x', 'end_y']] = df_subset[['x', 'y', 'end_x', 'end_y']].astype(float)

            if player_position == 'Goalkeeper':
                de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')
                pitch.arrows(passes_successful.x, passes_successful.y, passes_successful.end_x, passes_successful.end_y, width=0.75, color='#00ff00', ax=ax, label='Completed Pass')
                pitch.arrows(passes_unsuccessful.x, passes_unsuccessful.y, passes_unsuccessful.end_x, passes_unsuccessful.end_y, width=0.75, color='red', ax=ax, label='Incomplete Pass')

                pitch.lines(assist.x, assist.y, assist.end_x, assist.end_y, color='#00ff00', comet = True, lw = 2.5, ax=ax, label='Assist')
                ax.scatter(assist['end_y'], assist['end_x'], s=50, c='black', edgecolor='#00ff00')

                pitch.lines(chance.x, chance.y, chance.end_x, chance.end_y, color='#ffea00', comet = True, lw = 2.5, ax=ax, label='Key Pass')
                ax.scatter(chance['end_y'], chance['end_x'], s=50, c='black', edgecolor='#ffea00')

                ax.legend(loc='upper left', bbox_to_anchor=(0.205, 1.06), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=2, edgecolor='#ffffff')
                st.pyplot(fig)

            else:
                de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')
                pitch.arrows(passes_successful.x, passes_successful.y, passes_successful.end_x, passes_successful.end_y, width=0.6, headwidth=5, headlength=5, color='#00ff00', ax=ax, label='Completed Pass')
                pitch.arrows(passes_unsuccessful.x, passes_unsuccessful.y, passes_unsuccessful.end_x, passes_unsuccessful.end_y, width=0.6, headwidth=5, headlength=5, color='red', ax=ax, label='Incomplete Pass')

                pitch.lines(assist.x, assist.y, assist.end_x, assist.end_y, color='#00ff00', comet = True, lw = 2.5, ax=ax, label='Assist')
                ax.scatter(assist['end_y'], assist['end_x'], s=50, c='black', edgecolor='#00ff00')

                pitch.lines(chance.x, chance.y, chance.end_x, chance.end_y, color='#ffea00', comet = True, lw = 2.5, ax=ax, label='Key Pass')
                ax.scatter(chance['end_y'], chance['end_x'], s=50, c='black', edgecolor='#ffea00')

                ax.legend(loc='upper left', bbox_to_anchor=(0.205, 1.06), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=2, edgecolor='#ffffff')
                st.pyplot(fig)

        if action_filter == "OFFENSIVE ACTIONS":
            goal = filtered_data[filtered_data['typeId'] == 16]
            shot_miss = filtered_data[filtered_data['typeId'] == 13]
            shot_post = filtered_data[filtered_data['typeId'] == 14]
            shot_saved = filtered_data[filtered_data['typeId'] == 15]
                
            assist = filtered_data[filtered_data['assist'] == 1]
            chance = filtered_data[filtered_data['keyPass'] == 1]
            passes = filtered_data[filtered_data['typeId'] == 1]

            dribble = filtered_data[filtered_data['typeId'] == 3]
            succ_dribble = dribble[dribble['outcome'] == 1]

            foul = filtered_data[filtered_data['typeId'] == 4]
            foul_won = foul[foul['outcome'] == 1]
            foul_committed = foul[foul['outcome'] == 0]
                
            aerial = filtered_data[filtered_data['typeId'] == 44]
            aerial_won = aerial[aerial['outcome'] == 1]
            aerial_lost = aerial[aerial['outcome'] == 0]

            dispossessed = filtered_data[filtered_data['typeId'] == 50]

            for df_subset in [assist, chance, dribble, succ_dribble]:
                df_subset[['x', 'y', 'end_x', 'end_y']] = df_subset[['x', 'y', 'end_x', 'end_y']].astype(float)

            if player_position == 'Goalkeeper':
                de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')
                ax.scatter(goal['y'], goal['x'], s=120, c='#00ff00', edgecolor='#000000', label='Goal')
                ax.scatter(shot_saved['y'], shot_saved['x'], s=120, c='#ff7c60', edgecolor='#000000', label='Saved/Blocked Shot')
                ax.scatter(shot_post['y'], shot_post['x'], s=120, c='w', edgecolor='#000000', label='Shot Off Woodwork')
                ax.scatter(shot_miss['y'], shot_miss['x'], s=120, c='r', edgecolor='#000000', label='Shot Off Target')

                pitch.lines(assist.x, assist.y, assist.end_x, assist.end_y, color='#00ff00', comet = True, lw = 2.5, ax=ax, label='Assist')
                ax.scatter(assist['end_y'], assist['end_x'], s=50, c='black', edgecolor='#00ff00')

                pitch.lines(chance.x, chance.y, chance.end_x, chance.end_y, color='#ffea00', comet = True, lw = 2.5, ax=ax, label='Key Pass')
                ax.scatter(chance['end_y'], chance['end_x'], s=50, c='black', edgecolor='#ffea00')

                plt.scatter(succ_dribble['y'], succ_dribble['x'], s= 200, c = '#fc3900', marker = '*', edgecolor = '#000000', label = 'Dribble')

                plt.scatter(foul_won['y'], foul_won['x'], s= 120, c = '#008000', marker = 'X', edgecolor = '#000000', label = 'Foul Won')
                plt.scatter(foul_committed['y'], foul_committed['x'], s= 120, c = '#c21919', marker = 'X', edgecolor = '#000000', label = 'Foul Committed')
                plt.scatter(aerial_won['y'], aerial_won['x'], s = 100, c = '#008000', marker = '^', edgecolor = '#000000', label = 'Aerial Won')
                plt.scatter(aerial_lost['y'], aerial_lost['x'], s = 100, c = '#c21919', marker = '^', edgecolor = '#000000', label = 'Aerial Lost')
                plt.scatter(dispossessed['y'], dispossessed['x'], s = 100, c = '#cb0000', marker = 'p', edgecolor = '#000000', label = 'Dispossessed')

                ax.legend(loc='upper left', bbox_to_anchor=(-0.2, 1.09), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')

                if player or selected_team:
                    st.pyplot(fig)

            else:
                de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')
                ax.scatter(goal['y'], goal['x'], s=120, c='#00ff00', edgecolor='#000000', label='Goal')
                ax.scatter(shot_saved['y'], shot_saved['x'], s=120, c='#ff7c60', edgecolor='#000000', label='Saved/Blocked Shot')
                ax.scatter(shot_post['y'], shot_post['x'], s=120, c='w', edgecolor='#000000', label='Shot Off Woodwork')
                ax.scatter(shot_miss['y'], shot_miss['x'], s=120, c='r', edgecolor='#000000', label='Shot Off Target')

                pitch.lines(assist.x, assist.y, assist.end_x, assist.end_y, color='#00ff00', comet = True, lw = 2.5, ax=ax, label='Assist')
                ax.scatter(assist['end_y'], assist['end_x'], s=50, c='black', edgecolor='#00ff00')

                pitch.lines(chance.x, chance.y, chance.end_x, chance.end_y, color='#ffea00', comet = True, lw = 2.5, ax=ax, label='Key Pass')
                ax.scatter(chance['end_y'], chance['end_x'], s=50, c='black', edgecolor='#ffea00')

                plt.scatter(succ_dribble['y'], succ_dribble['x'], s= 200, c = '#fc3900', marker = '*', edgecolor = '#000000', label = 'Dribble')
                plt.scatter(foul_won['y'], foul_won['x'], s= 120, c = '#008000', marker = 'X', edgecolor = '#000000', label = 'Foul Won')
                plt.scatter(foul_committed['y'], foul_committed['x'], s= 120, c = '#c21919', marker = 'X', edgecolor = '#000000', label = 'Foul Committed')
                plt.scatter(aerial_won['y'], aerial_won['x'], s = 100, c = '#008000', marker = '^', edgecolor = '#000000', label = 'Aerial Won')
                plt.scatter(aerial_lost['y'], aerial_lost['x'], s = 100, c = '#c21919', marker = '^', edgecolor = '#000000', label = 'Aerial Lost')
                plt.scatter(dispossessed['y'], dispossessed['x'], s = 100, c = '#cb0000', marker = 'p', edgecolor = '#000000', label = 'Dispossessed')

                ax.legend(loc='upper left', bbox_to_anchor=(-0.2, 1.09), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')

                if player or selected_team:
                    st.pyplot(fig)                  
                
        if action_filter == "DEFENSIVE ACTIONS":
            passes = filtered_data[filtered_data['typeId'] == 1]
                
            recovery = filtered_data[filtered_data['typeId'] == 49]
            offside = filtered_data[filtered_data['typeId'] == 55]
            shield = filtered_data[filtered_data['typeId'] == 56]
              
            tackle = filtered_data[filtered_data['typeId'] == 7]
            succ_tackle = tackle[tackle['outcome'] == 1]
                
            interception = filtered_data[filtered_data['typeId'] == 8]
            block = filtered_data[filtered_data['typeId'] == 10]
            clearance = filtered_data[filtered_data['typeId'] == 12]
                
            foul = filtered_data[filtered_data['typeId'] == 4]
            foul_won = foul[foul['outcome'] == 1]
            foul_committed = foul[foul['outcome'] == 0]
                
            aerial = filtered_data[filtered_data['typeId'] == 44]
            aerial_won = aerial[aerial['outcome'] == 1]
            aerial_lost = aerial[aerial['outcome'] == 0]

            dispossessed = filtered_data[filtered_data['typeId'] == 50]

            dribbled_past = filtered_data[filtered_data['typeId'] == 45]
               
            pickup = filtered_data[filtered_data['typeId'] == 52]
            punch = filtered_data[filtered_data['typeId'] == 41]

            for df_subset in [passes]:
                df_subset[['x', 'y', 'end_x', 'end_y']] = df_subset[['x', 'y', 'end_x', 'end_y']].astype(float)

            if player_position == 'Goalkeeper':
                de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')
                plt.scatter(block['y'], block['x'], s = 200, c = '#00ff00', marker = '*', edgecolor = '#000000', label ='Save')
                plt.scatter(punch['y'], punch['x'], s = 100, c = '#ffec00', marker = 'o', edgecolor = '#000000', label = 'Punch')
                plt.scatter(pickup['y'], pickup['x'], s = 120, c = '#dd571c', marker = '+', edgecolor = '#000000', label = 'Pick-Up')
                plt.scatter(recovery['y'], recovery['x'], s= 120, c = '#fcd200', marker = ',', edgecolor = '#000000', label = 'Ball Recovery')
                plt.scatter(tackle['y'], tackle['x'], s= 120,c = 'cyan', marker = ',', edgecolor = '#000000', label = 'Tackle')
                plt.scatter(interception['y'], interception['x'], s = 120, c = '#ff007f', marker = ',', edgecolor = '#000000', label = 'Interception')
                plt.scatter(clearance['y'], clearance['x'], s = 100, c = '#9999ff', marker = 'x', edgecolor = '#000000', label = 'Clearance')
                plt.scatter(shield['y'], shield['x'], s = 50, c = '#dd571c', marker = 'D', edgecolor = '#000000', label = 'Shielding Ball Out')
                plt.scatter(foul_won['y'], foul_won['x'], s= 120, c = '#008000', marker = 'X', edgecolor = '#000000', label = 'Foul Won')
                plt.scatter(foul_committed['y'], foul_committed['x'], s= 120, c = '#c21919', marker = 'X', edgecolor = '#000000', label = 'Foul Committed')
                plt.scatter(dispossessed['y'], dispossessed['x'], s = 100, c = '#cb0000', marker = 'p', edgecolor = '#000000', label = 'Dispossessed')
                plt.scatter(dribbled_past['y'], dribbled_past['x'], s = 50, c = '#cb0000', marker = 'x', edgecolor = '#000000', label = 'Dribbled Past')

                ax.legend(loc='upper left', bbox_to_anchor=(-0.13, 1.09), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')
                    
                if player or selected_team:
                    st.pyplot(fig)

            else:
                de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')
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

                ax.legend(loc='upper left', bbox_to_anchor=(-0.17, 1.12), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')

                if player or selected_team:
                    st.pyplot(fig)

        if action_filter == "CONVEX HULL":
                # Filter data and scatter plot
            filtered = filtered_data[~filtered_data['typeId'].isin([2, 17, 18, 19, 43])]
            pitch.scatter(filtered.x, filtered.y, color='#00FF00', s=80, edgecolors='#FFFFFF', linewidth=1, ax=ax)

            pitch.scatter(filtered.x, filtered.y, color='#00FF00', s=80, edgecolors='#FFFFFF', linewidth=1, ax=ax)

                # Creating an array of (x, y) coordinates for convex hull calculation
            points = np.column_stack((filtered.x, filtered.y))

                # Calculate the convex hull of the data points
            hull1 = pitch.convexhull(filtered.x, filtered.y)
            hull = ConvexHull(points)

                # Plot the edges of the convex hull
            for simplex in hull.simplices:
                pitch.plot(filtered.x.iloc[simplex], filtered.y.iloc[simplex], color='#00FFFF', linewidth=3, linestyle='dashed', ax=ax)

                # Create a polygon from the convex hull with a semi-transparent fill
            polygon = pitch.polygon(hull1, color='#00FFFF', alpha=0.2, ax=ax)

            if player or selected_team:
                st.pyplot(fig)

    else:
        st.error(f"File {selected_match}.csv not found.")
else:
    st.warning("No match files found in the 'Matches' folder.")
