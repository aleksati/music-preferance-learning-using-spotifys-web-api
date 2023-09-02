#!/usr/bin/env python
# coding: utf-8

# In[9]:

import spotipy
import pandas as pd
import json
import itertools
import numpy as np
import ast

CLIENT_ID = "280475d600d24f9ca046a87becb99130"
CLIENT_SECRET = "3ccb25a470d74c90afaee272f0fd7fad"
token = spotipy.oauth2.SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=token)


# In[10]:

def analyze_features(playlist):
    #variables specifying the features we want to extract and where to store them.
    playlist_features = {}
    playlist_features_list = ["track_name", 
                              "duration_ms", "energy", "danceability", "loudness", "valence", "tempo", "time_signature"]
    df_playlist = pd.DataFrame(columns = playlist_features_list)

    for track in playlist:
        #Basic metadata
        #playlist_features["artist"] = track["track"]["album"]["artists"][0]["name"]
        #playlist_features["album"] = track["track"]["album"]["name"]
        playlist_features["track_name"] = track["track"]["name"]

        audio_features = sp.audio_features(track["track"]["id"])[0]
        for feature in playlist_features_list[1:]:
            playlist_features[feature] = audio_features[feature]

        #store and concatonate in dataframes
        track_df = pd.DataFrame(playlist_features, index=[0])
        df_playlist = pd.concat([df_playlist, track_df], ignore_index=True)
        
    return df_playlist


# In[11]:


def analyze_analysis(playlist, df_features):
    #Dicts specifying the analysis features we want to extract, and a dict to store them in. 
    #The is dynamic so audio features can be added if wanted. Complete list avaliable at:
    #https://developer.spotify.com/documentation/web-api/reference/tracks/get-audio-analysis/
    analysis_features_gathered = {}
    analysis_feature_list = {
        "segments" : [
            "pitches",
            "timbre"
        ],
        "sections" : [
            "key",
            "mode"
        ]
    }

    #Colunm names and framwork for our final dataframe
    framework = []
    for i, (key, val) in enumerate(analysis_feature_list.items()):
        for idx in range(len(val)):
            framework.append(val[idx])
    df_framework = pd.DataFrame(columns=framework)

    for count, track in enumerate(playlist):
        #First store the track duration in milliseconds
        track_dur = df_features["duration_ms"][count]
        
        #gather the desired values (expressed in the analysis_feature_list) from each track 
        #and store them in our new analysis_features_gathered dictionary.
        audio_analysis = sp.audio_analysis(track["track"]["id"])
        for i, (key, val) in enumerate(analysis_feature_list.items()):
            for item in range(len(val)):
                #Initialize the key to the correct type. Always store within list.
                analysis_features_gathered[val[item]] = []  
                for x, (y, z) in enumerate(audio_analysis.items()):
                    if y == key:
                        for w in range(len(z)):
                            analysis_features_gathered[val[item]].append(z[w][val[item]])
                            
        #Now we want to configure and calculate different kinds of averages of the lists and numbers
        #we have gathered per segment and section of each track.
        for i, (key, val) in enumerate(analysis_features_gathered.items()):
            p = []
            if type(val[0]) == list: #and is therefore ONLY either timbre or pitch in the segment key. else it would be an int or float.
                for w in range(len(val[0])):
                    store = []
                    for item in val:
                        store.append(item[w])
                    p.append(round(sum(store) / len(store), 2))
                analysis_features_gathered[key] = []
                analysis_features_gathered[key].append(p)
            else:
                if key == "key":
                    #precentage value indicating how many key changes happen in the track, based on its duration.
                    val = [k for k, g in itertools.groupby(val)] #remove consecutive duplicate values.
                    ms_per_chord_change = track_dur/len(val) #how many miliseconds per chord change on average.
                    change_percentage = (100/track_dur)*ms_per_chord_change
                    p.append(abs(change_percentage-100)) #invert values for a more intuitive reading.
                    analysis_features_gathered[key] = p
                else:
                    p.append(round(sum(val)/len(val), 2))
                    analysis_features_gathered[key] = p

        #store and concatonate in dataframes
        df_analysis_features = pd.DataFrame(analysis_features_gathered)
        df_framework = pd.concat([df_framework, df_analysis_features], ignore_index=True)
    
    return df_framework


# In[12]:


def clean(df):
    #Convert dataset to np array
    features = df[['track_name','duration_ms','energy','danceability',
                    'loudness','valence','tempo','time_signature','pitch_avg', 
                    'timbre_avg','key_change_percentage','mode_avg']].to_numpy()
    
    # Substitute titles with integers
    for i in range(features.shape[0]):
        features[i][0] = i
    
    #convert the timbre and pitch vectors, which are actually strings in the dataset imported, to lists.
    for row in range(features.shape[0]):
        for col in range(features.shape[1]):
            if type(features[row][col]) == str:
                features[row][col] = ast.literal_eval(features[row][col])
                
    #The do a little "hack" to unpack the lists within the feature array,
    #and subesequently extent the coloumn size of the feature array.
    def flatten(x):
        for item in x:
            try:
                yield from flatten(item) #if x has a member (item) it means its a a list or array, therefore we feed the item back into the function.
            except TypeError: #so if x has no members to iterate on (i.e its a float or integer), we return it (yield)
                yield item
    
    #the list features are actually imported as string, so we need to convert them back
    array = np.empty([])
    for i in range(features.shape[0]):
        row = list(flatten(features[i]))
        row = [round(elem, 2) for elem in row]
        row = np.array(row)
        if i == 0:
            array = row
        else:
            array = np.vstack((array, row))
    
    return array


# In[13]:


def gather_features(username, pl_url):
    output = np.array([])
    
    #gather and process
    playlist = sp.user_playlist(username, pl_url)["tracks"]["items"]
    df_playlist_features = analyze_features(playlist)
    df_playlist_analysis = analyze_analysis(playlist, df_playlist_features)
    df_analysis_combined = pd.concat([df_playlist_features, df_playlist_analysis], ignore_index=False, axis=1)
    df_analysis_combined = df_analysis_combined.rename(columns = {"pitches": "pitch_avg", "timbre" : "timbre_avg", "key": "key_change_percentage","mode": "mode_avg"}, inplace=False)
    output = clean(df_analysis_combined)
    return output


# In[ ]:

def shoot(playlist_url, username):
    track = gather_features(username, playlist_url)
    if len(track.shape) > 1:
        pass
    else:
        track = np.resize(track, (1, track.size))
    return track


