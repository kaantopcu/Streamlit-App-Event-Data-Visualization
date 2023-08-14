import streamlit as st
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import seaborn as sns
import matplotlib.pyplot as plt
from mplsoccer import Pitch, Sbopen, VerticalPitch
import os

st.set_option('deprecation.showPyplotGlobalUse', False)


# radio button
team_name= st.radio(
    "Enter the team:",
    ('Team A', 'Team B'))

#team_name = st.text_input("Enter the team:")
#player_name = st.text_input("Enter the player:")

df = pd.read_csv('eventDataMasked.csv')

def generateCombinedShotMap(team1):
    team1_xg = generateTeamxGDataFrame(team1)
    #team2_xg = generateTeamxGDataFrame(team2)
    team1_shots = team1_xg[team1_xg.type_name=='Shot']
    #team2_shots = team2_xg[team2_xg.type_name=='Shot']
    pitch = Pitch(line_color='white',pitch_color='#02540b')
    fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,endnote_height=0.04, title_space=0, endnote_space=0)
    pitch.scatter(team1_shots.x, team1_shots.y, alpha = 0.3, s = team1_shots.shot_statsbomb_xg*5000, color = "red", ax=ax['pitch'],)
    #pitch.scatter(120-team2_shots.x, 80-team2_shots.y, alpha = 0.3, s = team2_shots.shot_statsbomb_xg*5000, color = "blue", ax=ax['pitch'],)
    #ax['pitch'].text(5, 5, team2 + ' shots',color='white',size=20)
    ax['pitch'].text(80, 5, team1 + ' shots',color='white',size=20)
    st.pyplot(fig=fig)
 
 
 # calling the function
#generateCombinedShotMap("Team A","Team B")

# to take a better look at player pass map
def generatePlayerPassMap(player_name):
    player_filter = (df.type_name == 'Pass') & (df.player_name == player_name)
    player_df = df.loc[player_filter, ['x', 'y', 'end_x', 'end_y']]

    pitch = Pitch(line_color='white',pitch_color='#02540b')
    fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,endnote_height=0.04, title_space=0, endnote_space=0)
    for i in player_df.index:
        x = player_df['x'][i]
        y = player_df['y'][i]
        dx = player_df['end_x'][i] - player_df['x'][i]
        dy = player_df['end_y'][i] - player_df['y'][i]
        if df['outcome_name'][i] != 'Incomplete':
            ax['pitch'].arrow(x,y,dx,dy,color='#0dff00',length_includes_head=True,head_width=1,head_length=0.8)
            pitch.scatter(player_df['x'][i],player_df['y'][i],color='#0dff00',ax=ax['pitch'])
        else:
            ax['pitch'].arrow(x,y,dx,dy,color='red',length_includes_head=True,head_width=1,head_length=0.8)
            pitch.scatter(player_df['x'][i],player_df['y'][i],color='red',ax=ax['pitch'])
    fig.suptitle(player_name+" passes", fontsize = 20)
    st.pyplot(fig=fig)

# we can do this for all players individually
#generatePlayerPassMap(player_name)



def generatePassingNetwork(team_name):
    #check for index of first sub
    sub = df.loc[df["type_name"] == "Substitution"].loc[df["team_name"] == team_name].iloc[0]["index"]
    #make df with successfull passes by Real Madrid until the first substitution
    rm_passes = (df.type_name == 'Pass') & (df.team_name == team_name) & (df.index < sub) & (df.outcome_name.isnull()) & (df.sub_type_name != "Throw-in")
    #taking necessary columns
    rm_pass = df.loc[rm_passes, ['x', 'y', 'end_x', 'end_y', "player_name", "pass_recipient_name"]]
    #adjusting that only the surname of a player is presented.
    rm_pass["player_name"] = rm_pass["player_name"].apply(lambda x: str(x).split()[-1])
    rm_pass["pass_recipient_name"] = rm_pass["pass_recipient_name"].apply(lambda x: str(x).split()[-1])
    
    scatter_df = pd.DataFrame()
    for i, name in enumerate(rm_pass["player_name"].unique()):
        passx = rm_pass.loc[rm_pass["player_name"] == name]["x"].to_numpy()
        recx = rm_pass.loc[rm_pass["pass_recipient_name"] == name]["end_x"].to_numpy()
        passy = rm_pass.loc[rm_pass["player_name"] == name]["y"].to_numpy()
        recy = rm_pass.loc[rm_pass["pass_recipient_name"] == name]["end_y"].to_numpy()
        scatter_df.at[i, "player_name"] = name
        #make sure that x and y location for each circle representing the player is the average of passes and receptions
        scatter_df.at[i, "x"] = np.mean(np.concatenate([passx, recx]))
        scatter_df.at[i, "y"] = np.mean(np.concatenate([passy, recy]))
        #calculate number of passes
        scatter_df.at[i, "no"] = rm_pass.loc[rm_pass["player_name"] == name].count().iloc[0]
    #adjust the size of a circle so that the player who made more passes 
    scatter_df['marker_size'] = (scatter_df["no"] / scatter_df["no"].max() * 1500)
    
    #counting passes between players
    rm_pass["pair_key"] = rm_pass.apply(lambda x: "_".join(sorted([x["player_name"], x["pass_recipient_name"]])), axis=1)
    lines_df = rm_pass.groupby(["pair_key"]).x.count().reset_index()
    lines_df.rename({'x':'pass_count'}, axis='columns', inplace=True)
    #setting a threshold. You can try to investigate how it changes when you change it.
    lines_df = lines_df[lines_df['pass_count']>2]
    
    #plot once again pitch and vertices
    pitch = Pitch(line_color='white',pitch_color='#02540b')
    fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,
                         endnote_height=0.04, title_space=0, endnote_space=0)
    pitch.scatter(scatter_df.x, scatter_df.y, s=scatter_df.marker_size, color='#2f5fed', edgecolors='grey', linewidth=1, alpha=1, ax=ax["pitch"], zorder = 3)
    for i, row in scatter_df.iterrows():
        pitch.annotate(row.player_name, xy=(row.x, row.y), c='black', va='center', ha='center', weight = "bold", size=16, ax=ax["pitch"], zorder = 4)
    for i, row in lines_df.iterrows():
            player1 = row["pair_key"].split("_")[0]
            player2 = row['pair_key'].split("_")[1]
            #take the average location of players to plot a line between them 
            player1_x = scatter_df.loc[scatter_df["player_name"] == player1]['x'].iloc[0]
            player1_y = scatter_df.loc[scatter_df["player_name"] == player1]['y'].iloc[0]
            player2_x = scatter_df.loc[scatter_df["player_name"] == player2]['x'].iloc[0]
            player2_y = scatter_df.loc[scatter_df["player_name"] == player2]['y'].iloc[0]
            num_passes = row["pass_count"]
            #adjust the line width so that the more passes, the wider the line
            line_width = (num_passes / lines_df['pass_count'].max() * 10)
            #plot lines on the pitch
            pitch.lines(player1_x, player1_y, player2_x, player2_y,
                            alpha=1, lw=line_width, zorder=2, color="#2f5fed", ax = ax["pitch"])
    fig.suptitle(team_name+"'s Passing Network", fontsize = 20)
    st.pyplot(fig=fig)
    
def generateTeamxGDataFrame(team_name):
    xg = df[['team_name','minute','type_name','shot_statsbomb_xg','x','y']]
    team_xg = xg[xg['team_name']==team_name].reset_index()
    return team_xg
    
def generatexGPlot(team_name):
    team_xg = generateTeamxGDataFrame(team_name)
    #xg_events[xg_events.shot_statsbomb_xg.isna()==False]
    plt.clf()
    sns.lineplot(data=team_xg,x='minute',y='shot_statsbomb_xg',ci=None)
    plt.xlabel("Minutes")
    plt.ylabel("xG")
    plt.title("xG/Minute for "+ team_name)
    plt.show()
    st.pyplot()	    

def generatePlayerHeatmapGrid(team_name):
    # filtering to passes by team_name players
    team_passes = (df.type_name == 'Pass') & (df.team_name == team_name) & (df.sub_type_name != "Throw-in")
    # selecting only relevant columsn for the pass map
    team_passes = df.loc[team_passes, ['x', 'y', 'end_x', 'end_y', 'player_name','outcome_name']]
    #get the list of all players who made a pass
    names = team_passes['player_name'].unique()
    #draw 4x4 pitches
    pitch = Pitch(line_color='white',pitch_color='#02540b')
    fig, axs = pitch.grid(ncols = 4, nrows = 4, grid_height=0.85, title_height=0.06, axis=False,endnote_height=0.04, title_space=0.04, endnote_space=0.01)
    plt.figure(figsize=(14,10))
    
    
    #for each player
    for name, ax in zip(names, axs['pitch'].flat[:len(names)]):
        #take only passes by this player
        player_df = team_passes.loc[team_passes["player_name"] == name]
        #put player name over the plot
        ax.text(60, -10, name.split()[-1],ha='center', va='center', fontsize=14)
        #Create the heatmap
        pitch.kdeplot(
            x=player_df['x'],
            y=player_df['y'],
            shade = True,
            shade_lowest=False,
            alpha=.5,
            n_levels=10,
            cmap = 'plasma',
            ax=ax
        )
    #We have more than enough pitches - remove them
    for ax in axs['pitch'][-1, 25 - len(names):]:
        ax.remove(ax)
    
    #Another way to set title using mplsoccer
    axs['title'].text(0.5, 0.5, team_name+" Heatmaps", ha='center', va='center', fontsize=20)
    st.pyplot(fig=fig)
    
def generatePlayerPassMapsGrid(team_name):
    # filtering to passes by team_name players
    team_passes = (df.type_name == 'Pass') & (df.team_name == team_name) & (df.sub_type_name != "Throw-in")
    # selecting only relevant columsn for the pass map
    team_passes = df.loc[team_passes, ['x', 'y', 'end_x', 'end_y', 'player_name','outcome_name']]
    #get the list of all players who made a pass
    names = team_passes['player_name'].unique()
    #draw 4x4 pitches
    pitch = Pitch(line_color='white',pitch_color='#02540b',pad_top=20)
    fig, axs = pitch.grid(ncols = 4, nrows = 4, grid_height=0.85, title_height=0.06, axis=False,endnote_height=0.04, title_space=0.04, endnote_space=0.01)
    plt.figure(figsize=(50,10))
    #for each player
    for name, ax in zip(names, axs['pitch'].flat[:len(names)]):
        #take only passes by this player
        player_df = team_passes.loc[team_passes["player_name"] == name]
        #put player name over the plot
        ax.text(60, -10, name.split()[0]+":"+str(len(player_df))+" passes",ha='center', va='center', fontsize=14)
        #scatter -  plots the player position with 0.2 alpha(visibility)
        #pitch.scatter(player_df.x, player_df.y, alpha = 0.2, s = 50, color = "blue", ax=ax)
        #plot pass arrows
        #pitch.arrows(player_df.x, player_df.y,player_df.end_x, player_df.end_y, color = "blue", ax=ax, width=1)
        # plotting arrows one by one, red or green based on if its incomplete or not
        for i in player_df.index:
            x=player_df['x'][i]
            y = player_df['y'][i]
            dx = player_df['end_x'][i] - player_df['x'][i]
            dy = player_df['end_y'][i] - player_df['y'][i]
            if df['outcome_name'][i] != 'Incomplete':
                ax.arrow(x,y,dx,dy,color='#0dff00',length_includes_head=True,head_width=1,head_length=0.8)
                pitch.scatter(player_df['x'][i],player_df['y'][i],color='#0dff00',ax=ax)
            else:
                ax.arrow(x,y,dx,dy,color='red',length_includes_head=True,head_width=1,head_length=0.8)
                pitch.scatter(player_df['x'][i],player_df['y'][i],color='red',ax=ax)


    #We have more than enough pitches - remove them
    for ax in axs['pitch'][-1, 25 - len(names):]:
        ax.remove(ax)

    #Another way to set title using mplsoccer
    axs['title'].text(0.5, 0.5, team_name+" pass maps", ha='center', va='center', fontsize=20)
    st.pyplot(fig=fig)
    

    
# calling the function
generateCombinedShotMap((team_name))
generatePlayerPassMapsGrid(team_name)
generatePassingNetwork(team_name)
generatePlayerHeatmapGrid(team_name)
generatexGPlot(team_name)

#generatePassingNetwork("Team B")
