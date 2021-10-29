# stravify.py

from flask import Flask, request, make_response, redirect, url_for
from flask import render_template, Markup, flash, session, jsonify, abort
import spotipy
from spotipy import oauth2
import stravalib
import json
import dateutil.parser
from datetime import timedelta, datetime
from concurrence import checkConcurrence, checkConcurrenceSingle
import pytz
import requests
import urllib3
import stravaMethods
import os
import psycopg2
import database as db
import base64

DATABASE_URL = os.environ['DATABASE_URL']

# conn = psycopg2.connect(DATABASE_URL, sslmode='require')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TEMPLATE_DIR = './templates'
STATIC_DIR = './static'

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.secret_key = os.environ['secret_key']
app.config['SECRET_KEY'] = app.secret_key

client = stravalib.Client()


STRAVA_CLIENT_ID = os.environ['STRAVA_CLIENT_ID']
STRAVA_CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
STRAVA_REDIRECT_URI = os.environ['STRAVA_REDIRECT_URI']

SPOTIPY_CLIENT_ID = os.environ['SPOTIPY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = os.environ['SPOTIPY_CLIENT_SECRET']
SPOTIPY_REDIRECT_URI = os.environ['SPOTIPY_REDIRECT_URI']
SCOPE = os.environ['SCOPE']
CACHE = os.environ['CACHE']

sp_oauth = oauth2.SpotifyOAuth( SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET,SPOTIPY_REDIRECT_URI,scope=SCOPE, cache_path=CACHE )


# -------------------------------------------------------------------- #
# take the start time of Spotify song, the duration, and return the start
# and end as datetime objects
def getEnd (startString, durationMS):
    startDate = dateutil.parser.parse(startString)
    duration = timedelta(milliseconds=durationMS)
    endDate = startDate + duration
    return startDate, endDate



# -------------------------------------------------------------------- #
# Takes a strava user ID and activity number and returns a JSON dictionary
# of that activity, if a valid activity is returned. If an error is returned
# return None.
def getActivityByID(userID, activityID):
    activity_url = 'https://www.strava.com/api/v3/activities/'
    activity_url = activity_url + str(activityID)
    auth_url = "https://www.strava.com/oauth/token"

    # pull the refresh token of the athlete 
    refresh_token = db.getUserInfoStrava(userID)[2]
    payload = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'grant_type': "refresh_token",
        'refresh_token': refresh_token,
    }
    # refresh the access token and refresh token
    res = requests.post(auth_url, data=payload)
    access_token = res.json()['access_token']
    refresh_token = res.json()['refresh_token']
    # add the new tokens to DB
    db.updateUserStrava(userID, access_token, refresh_token)
    header = {'Authorization': 'Bearer ' + access_token}
    # request the activity
    res = requests.get(activity_url, headers=header)
    out = res.json()
    if 'errors' in out.keys(): return None
    return(out)


# -------------------------------------------------------------------- #
# THis is where the magic happens.
# Route that is hit when a authenitcated user makes a webhook event.
# If it's a "create" or "update" of an activity, pull the user's recent songs
# and editActivity() with songs in the description
@app.route('/webhook', methods=['POST'])
def webhookPOST():
    info = request.json
    print("webhook event received\n", info)
    # dont do anything if the webhook is an object being deleted, or if 
    # it isnt an activity (eg a post).
    if info['aspect_type'] == 'delete': return make_response(info)
    if info['object_type'] != 'activity': return make_response(info)
    
    activityID = info['object_id']
    userID = info['owner_id']

    # get the activity 
    activity = getActivityByID(userID, activityID)
    if activity: # if it's a valid one
        if activity['manual']: return make_response(info) # if manual the time might not be accurate, so do nothing
        print('Activity: \n' , activity['name']) # console log for testing
        # get the interval 
        start, end = getEnd(activity['start_date'], (activity['elapsed_time']*1000))
        # get the songs in that interval
        songs = songsForDesc(userID, start, end)
        if songs:
            # make the description to be appended
            newDesc = 'Listened to:\n'
            for song in reversed(songs):
                newDesc = newDesc + '- ' + song['name'] + ' -- ' + song['artist'] + '\n'

            newDesc = newDesc + "(from activetracks.herokuapp.com)"
            editActivity(userID, activityID, newDesc)
    else: 
        print("error getting activity in webhookPOST(). user may be private.")
    
    return make_response(info)


# -------------------------------------------------------------------- #
# this is used to verify the webhook subscription with strava
@app.route('/webhook', methods=['GET'])
def webhookGET():
    VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
    mode = request.args.get('hub.mode')
    print('SUGMA')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if (mode and token):
        if (mode == 'subscribe' and token == VERIFY_TOKEN):
            print('Webhook verfied')
            return make_response(json.loads('{"hub.challenge":"'+challenge+'"}'))


# -------------------------------------------------------------------- #
# render index, about, and spotify Login pages
@app.route('/', methods=['GET'])
def index():
    html = render_template('index.html')
    return make_response(html)

@app.route('/about', methods=['GET'])
def about():
    html = render_template('about.html')
    return make_response(html)

def htmlForLoginButton():
    auth_url = getSPOauthURI()
    htmlLoginButton =  auth_url
    return htmlLoginButton

def getSPOauthURI():
    auth_url = sp_oauth.get_authorize_url()
    return auth_url

@app.route('/spotifyLogin', methods=['GET'])
def spotifyLogin():
    html = render_template('spotifyLogin.html', loginURL=htmlForLoginButton())
    return make_response(html)

# -------------------------------------------------------------------- #
# route for authenticating spotify account 
# significant help came from https://github.com/perelin/spotipy_oauth_demo/blob/master/spotipy_oauth_demo.py

@app.route("/spotifyAuth", methods=['GET'])
def spotifyAuth():

    auth_url = "https://accounts.spotify.com/authorize"
    token_url = "https://accounts.spotify.com/api/token"
    user_url = "https://api.spotify.com/v1/me"
    rp_url = 'https://api.spotify.com/v1/me/player/recently-played?limit=50'

    access_token = ""

    # token_info = sp_oauth.get_cached_token()

    # if token_info:
    #     print("Found cached token!")
    #     access_token = token_info['access_token']
    code = request.args.get('code')

    if code == None:
        payload = {
            'client_id' : SPOTIPY_CLIENT_ID,
            "response_type" : 'code',
            'redirect_uri' : SPOTIPY_REDIRECT_URI,
            'scope': SCOPE
        }
        res = requests.get(auth_url, data=payload)

    else:
        payload = {
            'grant_type' : 'authorization_code',
            'code' : code,
            'redirect_uri' : SPOTIPY_REDIRECT_URI
        }
        authStr = SPOTIPY_CLIENT_ID +':'+ SPOTIPY_CLIENT_SECRET
        authStrB64 = base64.urlsafe_b64encode(authStr.encode()).decode()
        header = {'Authorization': 'Basic ' + authStrB64}
        res = requests.post(token_url, headers=header, data=payload)
        access_token = res.json()['access_token']
        refresh_token = res.json()['refresh_token']

    if access_token:
        print("Access token available! Trying to get user information...")
        header = {'Authorization': 'Bearer ' + access_token}
        user = requests.get(user_url, headers=header)
        results = requests.get(rp_url , headers=header)
        userID = user.json()['id']

        # if the user is not in the database, add them to it
        if db.getUserInfoSpotify(userID) is None:
            db.addNewUser('-1', '-1', '-1', access_token, refresh_token, userID)
        # if they are, update their row with the new tokens
        else:
            db.updateUserSpotify(userID, access_token, refresh_token)
        
        # get the tracks they listened to 
        tracksList = []
        for track in results.json()['items']:
            artist = track['track']['artists'][0]['name']
            trackName = (track['track']['name'])
            uri = (track['track']['uri'])
            start = (track['played_at'])
            duration = track['track']['duration_ms']

            st, et = getEnd(start, duration)
            st, et = st.replace(tzinfo=None), et.replace(tzinfo=None)

            trackDict = {'name' : trackName, 'artist' : artist, 'uri' : uri, 'st':st, 'et':et}
            tracksList.append(trackDict)


        session['recentlyPlayed'] = tracksList
        session['spotify_user'] = userID
        url = client.authorization_url(client_id=STRAVA_CLIENT_ID, redirect_uri=STRAVA_REDIRECT_URI, scope=['read_all', 'profile:read_all', 'activity:read_all','activity:write'  ])
        if len(tracksList) == 0: 
            tracksList = [{'name' : 'None', 'artist' : 'None'}]
        html = render_template('stravaLogin.html', loginURL=url, lastSong = tracksList[0])
        response = make_response(html)
        return response 
    
    else:
        html = render_template('spotifyLogin.html', loginURL=htmlForLoginButton())
        return make_response(html)



# -------------------------------------------------------------------- #
# Route for authenticating Strava account
@app.route('/stravaAuthed', methods=['GET'])
def stravaAuthed():
    code = request.args.get('code')

    access_token = client.exchange_code_for_token(client_id=STRAVA_CLIENT_ID,
                                                    client_secret=STRAVA_CLIENT_SECRET, code=code)

    client.access_token = access_token

    auth_url = "https://www.strava.com/oauth/token"
    activites_url = "https://www.strava.com/api/v3/athlete/activities"
    athlete_url = "https://www.strava.com/api/v3/athlete"

    payload = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': access_token['refresh_token'],
        'grant_type': "refresh_token",
        'f': 'json'
    }
    # get the access and refresh tokens
    print("Requesting Token...\n")
    res = requests.post(auth_url, data=payload, verify=False)
    access_token = res.json()['access_token']
    refresh_token = res.json()['refresh_token']
    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 50, 'page': 1}
    
    # get the activities
    activities_data = requests.get(activites_url, headers=header, params=param).json()
    res = requests.get(athlete_url, headers=header).json()
    athleteID = res['id']
    athleteName = res['firstname'] + ' ' + res['lastname']

    spotify_user = session['spotify_user']

    # if they're new to the DB, add them by the key of the spotify user logged in previously
    if db.getUserInfoStrava(athleteID) is None:
        db.updateUserStravaBySpotify(spotify_user, athleteID, access_token, refresh_token)
    else:
        db.updateUserStrava(athleteID,access_token,refresh_token)


    if 'recentlyPlayed' in session:
        tracksList = session['recentlyPlayed']
    else:
        print('NO TRACKLIST')
        
    # get their recent activities 
    activitiesList = []
    for activity in activities_data:
        name = activity['name']
        idNo = activity['id']
        kind = activity['type']
        st, et = getEnd(activity['start_date'], (activity['elapsed_time']*1000))
        st, et = st.replace(tzinfo=None), et.replace(tzinfo=None)

        acDict = {'name' : name, 'idNo' : idNo, 'kind' : kind, 'st' :st, 'et' : et}
        activitiesList.append(acDict)

    # compare the track list with the activity list to get songs played during the activities
    concurrence = checkConcurrence(tracksList, activitiesList)

    if not concurrence:
        html = render_template('bothAuthed.html', lastActivity=activitiesList[0]['name'], noData=True)
        response = make_response(html)
        return response
    else:
        concurrence = stravaMethods.getSongIndices(concurrence)


    # code for more complex data analysis, future feature
    
    # f = open('streams.txt', 'w')

    # for activity in concurrence:
    #     streams_url = "https://www.strava.com/api/v3/activities/" + str(activity['id']) + "/streams?keys=velocity_smooth,time&key_by_type="
    #     streams = requests.get(streams_url, headers=header, params=param).json()
    #     streamDict = {}
    #     for stream in streams:
    #         streamDict[stream['type']] = stream['data']
    #         f.write(stream['type'] + str(len(stream['data'])) + '\n' + str(stream['data']) + '\n')

    #     for song in activity['songList']:
    #         averageSpeed = stravaMethods.averageBetweenSeconds(streamDict['time'], streamDict['velocity_smooth'],song['begOffset'], song['endOffset'])
    #         print('During ' + song['name']+ ', average was ' + str(averageSpeed))
    # f.close()

    html = render_template('bothAuthed.html', lastActivity=activitiesList[0]['name'], noData=False)
    response = make_response(html)
    return response

# -------------------------------------------------------------------- #
# edits the description of a strava activity
def editActivity(userID, activityID, newDescription): 
    activity_url = 'https://www.strava.com/api/v3/activities/'
    activity_url = activity_url + str(activityID)
    auth_url = "https://www.strava.com/oauth/token"

    refresh_token = db.getUserInfoStrava(userID)[2]
    payload = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'grant_type': "refresh_token",
        'refresh_token': refresh_token,
    }
    # authenticate the user 
    res = requests.post(auth_url, data=payload)
    access_token = res.json()['access_token']
    refresh_token = res.json()['refresh_token']
    header = {'Authorization': 'Bearer ' + access_token}
    db.updateUserStrava(userID, access_token, refresh_token)

    # get the old description: we are adding to it rather than changing wholesale
    oldDescription = requests.get(activity_url, headers=header).json()['description']
    if oldDescription == None: oldDescription = ''
    else: oldDescription = oldDescription +'\n'
    if 'from activetracks.herokuapp.com' not in oldDescription:
        updatedActivity = {
            'description':  oldDescription + newDescription,
        }
        # make the PUT to update the activity with the new info
        updateActivity = requests.put(activity_url, headers=header, data=updatedActivity, verify=False)
        return updateActivity
    else: 
        return None  

def songsForDesc(strava_user, activity_start, activity_end):
    auth_url = 'https://accounts.spotify.com/api/token'
    refresh_token = db.getUserInfoStrava(strava_user)[4]
    payload = {
        'grant_type' : 'refresh_token',
        'refresh_token' : refresh_token
    }
    # authenticate spotify user
    authStr = SPOTIPY_CLIENT_ID +':'+ SPOTIPY_CLIENT_SECRET
    authStrB64 = base64.urlsafe_b64encode(authStr.encode()).decode()
    header = {'Authorization': 'Basic ' + authStrB64}
    res = requests.post(auth_url, data=payload, headers=header)
    access_token = res.json()['access_token']

    # update database information 
    spotify_user = db.getUserInfoStrava(strava_user)[5]
    db.updateUserSpotify(spotify_user, access_token, refresh_token)
    
    # get the recently played songs 
    sp = spotipy.Spotify(access_token)
    userID = sp.current_user()['id']
    results = sp.current_user_recently_played(limit=50)
    
    tracksList = []
    for track in results['items']:
        artist = track['track']['artists'][0]['name']
        trackName = (track['track']['name'])
        uri = (track['track']['uri'])
        start = (track['played_at'])
        duration = track['track']['duration_ms']

        st, et = getEnd(start, duration)
        st, et = st.replace(tzinfo=None), et.replace(tzinfo=None)

        trackDict = {'name' : trackName, 'artist' : artist, 'uri' : uri, 'st':st, 'et':et}
        tracksList.append(trackDict)

    activity_start = activity_start.replace(tzinfo=None)
    activity_end = activity_end.replace(tzinfo=None)
    # return the songs played between activity_start and activity_end
    songs = checkConcurrenceSingle(tracksList, activity_start, activity_end)
    return songs

# test code
if __name__ == "__main__":
    userID = 2987820
    activityID = 6097750589
    activity = getActivityByID(userID, activityID)
    print('activity:: ' ,activity)
    print(db.getUserInfoStrava(userID))
    # start, end = getEnd(activity['start_date'], (activity['elapsed_time']*1000))
    # songs = songsForDesc(userID, start, end)
    # editActivity(userID, activityID, songs)
    # print(songs)
