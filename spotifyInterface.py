# stratify: spotify interface module
# Methods: 
# Get recently played songs
# Determine beginning and end of these
# From URI get track info

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import json
import types
import dateutil.parser
from datetime import timedelta, datetime
import constants

token = util.prompt_for_user_token(
    username=os.environ['SPOTIFY_USERNAME']
    scope=os.environ['SPOTIFY_SCOPE']
    client_id=os.environ['SPOTIFY_CLIENT_ID']
    client_secret=os.environ['SPOTIFY_CLIENT_SECRET']
    redirect_uri=os.environ['SPOTIFY_REDIRECT_URL']
)

# ------------------------------------------------------------------- #
# convert (start, duration) to (start, end)
# also convert from time string to datetime object
def getEnd (startString, durationMS):
    startDate = dateutil.parser.parse(startString)
    duration = timedelta(milliseconds=durationMS)
    endDate = startDate + duration
    return startDate, endDate


# ------------------------------------------------------------------- #
# Get recently played songs from spotify. 
# Returns: list of (trackName:str, uri:str, start:datetime, end:datetime) tuples 

def getRecents(numberToGet):
    def recentlyPlayed(self, limit=numberToGet):
        return self._get('me/player/recently-played', limit=limit)


    spotify = spotipy.Spotify(auth=token)
    spotify.recentlyPlayed = types.MethodType(recentlyPlayed, spotify)

    recents = spotify.recentlyPlayed(limit=numberToGet)
    # out_file = open("canzonirecenti.json","w")
    # out_file.write(json.dumps(canzonirecenti, sort_keys=True, indent=2))
    # out_file.close()

    tracksList = []

    for track in recents['items']:
        artist = track['track']['artists'][0]['name']
        trackName = (track['track']['name'])
        uri = (track['track']['uri'])
        start = (track['played_at'])
        duration = track['track']['duration_ms']

        st, et = getEnd(start, duration)

        trackDict = {'trackName' : trackName, 'uri' : uri, 'st':st, 'et':et}
        tracksList.append(trackDict)

    return(tracksList)

# ------------------------------------------------------------------- #
# From a URI, get song
# returns tuple: (artist:str, trackname:str, uri:str)

def getSong(uri):
    id = uri.split(':')[2]
    spotify = spotipy.Spotify(auth=token)
    track = spotify.track(id)

    artist = track['artists'][0]['name']
    trackName = track['name']
    uri = track['uri']

    trackTuple = (artist, trackName, uri)
    return trackTuple

# ------------------------------------------------------------------- 
# unit testing 
def main():
 
    print('Testing Spotify interface\n')
    times = 25
    print('Printing {} most recent songs:'.format(times))
    print('-------------')
    tracklist = getRecents(times)
    for track in tracklist:
        print(track['trackName'])


if __name__ == "__main__":
   main()
    
