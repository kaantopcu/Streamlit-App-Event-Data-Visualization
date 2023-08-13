import streamlit as st
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import seaborn as sns
import matplotlib.pyplot as plt
from mplsoccer import Pitch, Sbopen, VerticalPitch
import os

st.set_option('deprecation.showPyplotGlobalUse', False)


# radio button
#team_name= st.radio(
#    "Enter the team:",
#    ('Team A', 'Team B'))

#team_name = st.text_input("Enter the team:")
player_number = st.text_input("Enter a player number between 1-28:")
player_name = "Player" + player_number 

df = pd.read_csv('eventDataMasked.csv')


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

def generatePlayerHeatMap(player_name):
    player_filter = (df.type_name == 'Pass') & (df.player_name == player_name)
    player_df = df.loc[player_filter, ['x', 'y', 'end_x', 'end_y']]

    pitch = Pitch(line_color='white',pitch_color='#02540b')
    fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False,endnote_height=0.04, title_space=0, endnote_space=0)
    #Create the heatmap
    pitch.kdeplot(
        x=player_df['x'],
        y=player_df['y'],
        shade = True,
        shade_lowest=False,
        alpha=.5,
        n_levels=10,
        cmap = 'plasma',
        ax=ax['pitch']
        )
    fig.suptitle(player_name+" Heatmap", fontsize = 20)
    st.pyplot(fig=fig)



generatePlayerPassMap(player_name)
generatePlayerHeatMap(player_name)

