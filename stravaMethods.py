# stravaMethods.py
import numpy as np


def getSongIndices(concurrenceList):
    for activity in concurrenceList:
        for song in activity['songList']:
            begOffset = (song['st'] - activity['st']).total_seconds()
            endOffset = (song['et'] - activity['st']).total_seconds()
            song['begOffset'] = begOffset
            song['endOffset'] = endOffset

    return concurrenceList
            
def averageBetweenSeconds(timeStream, veloStream, start, end):
    startIndex = np.argmin(np.abs(np.array(timeStream)-start))
    endIndex = np.argmin(np.abs(np.array(timeStream)-end))
    duration = veloStream[startIndex:endIndex+1]
    average = sum(duration) / len(duration)
    return average


