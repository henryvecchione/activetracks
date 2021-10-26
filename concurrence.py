# concurrence.py
# Take a list of songs. Take a list of activities
# Return a list of songs during each activity. 

from sys import exit
import pytz
import dateutil.parser
from datetime import timedelta, datetime

number_of_activities = 5
number_of_songs = 50

def checkConcurrence(songs, activities):

    songEarliest = songs[-1]['st'].replace(tzinfo=None)
    songLatest = songs[0]['et'].replace(tzinfo=None)
    activityEarliest = activities[-1]['st'].replace(tzinfo=None)
    activityLatest = activities[0]['et'].replace(tzinfo=None)

    if songEarliest > activityLatest: 
        print('Error: Earliest song is more recent than latest activity: \n', 'song: ', songEarliest, '\n', 'actv: ', activityLatest)
        return None

    if songLatest < activityEarliest:
        print('Error: Earliest Activity is more recent than latest song: \n', 'song: ', songLatest, '\n', 'actv: ', activityEarliest)
        return None

    

    else:
        concurrenceList = []
        for activity in activities:
            if activity['et'] < songEarliest: continue
            concurrenceDict = {}
            concurrenceDict['id'] = activity['idNo']
            concurrenceDict['name'] = activity['name']
            concurrenceDict['kind'] = activity['kind']
            concurrenceDict['st'] = activity['st']
            concurrenceDict['et'] = activity['et']
            concurrenceDict['songList'] = []
            for song in songs:
                song['et'] = song['et'].replace(tzinfo=None)
                song['st'] = song['st'].replace(tzinfo=None)
                activity['st'] = activity['st'].replace(tzinfo=None)
                activity['et'] = activity['et'].replace(tzinfo=None)

                if (song['st'] > activity['st']) and (song['st'] < activity['et']):
                    concurrenceDict['songList'].append(song)
                elif (song['et'] > activity['st']) and (song['et'] < activity['et']):
                    concurrenceDict['songList'].append(song)
            concurrenceList.append(concurrenceDict)

    return concurrenceList

def checkConcurrenceSingle(songs, st, et):
    songEarliest = songs[-1]['st'].replace(tzinfo=None)
    songLatest = songs[0]['et'].replace(tzinfo=None)


    if songEarliest > et: 
        print('Error: Earliest song is more recent than latest activity: \n', 'song: ', songEarliest)
        return None

    if songLatest < st:
        print('Error: Earliest Activity is more recent than latest song: \n', 'song: ', songLatest)
        return None

    concurrenceList = []
    # if et < songEarliest: pass
    for song in songs:
        song['et'] = song['et'].replace(tzinfo=None)
        song['st'] = song['st'].replace(tzinfo=None)

        if (song['st'] > st) and (song['st'] < et):
            concurrenceList.append(song)
        elif (song['et'] > st) and (song['et'] < et):
            concurrenceList.append(song)

    return concurrenceList


# def main():

#     workouts = stravaInterface.getActivities(number_of_activities)
#     songs = spotifyInterface.getRecents(number_of_songs)

#     d = checkConcurrence(songs, workouts)
#     for k in d:
#         print('During ' + k +': ')
#         for v in d[k]:
#             print('\t' + v['trackName'])

# if __name__ == "__main__":
#     main()

