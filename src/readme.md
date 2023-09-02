# How to use

The dataset and target values are already gathered and lies in the dataset folder. Simply open the spotify-model-Regressor.ipynb file and go through the steps.

## To evalute the dataset gathering
- Install Spotipy python package:
	- pip install spotipy
- Create an account/sign in to spotify developers page to get the CLIENT_ID and CLIENT_SECRET keys necessary for the feature extraction
    - https://developer.spotify.com/dashboard/login
- Copy the last string behind playlists URL's into the playlist dictionary in the spotify-feature-extraction.ipynb
- For More info:
    - https://spotipy.readthedocs.io/en/2.16.0/