# database.py

from dbURLParse import parse
from psycopg2 import connect, Binary
import os

DATABASE_URL = os.environ['DATABASE_URL']


creds = parse(DATABASE_URL)

def connectClean(creds):
    return connect(host = creds['host'], port = creds['port'], user = creds['user'], password = creds['password'], database = creds['database'])


# def createTable():
#     try:
#         stmt = 'CREATE TABLE credentials (strava_user varchar(255), strava_access varchar(255), strava_refresh varchar(255), spotify_access varchar(255), spotify_refresh varchar(255));'

#         connection = connect(host = creds['host'], port = creds['port'], user = creds['user'], password = creds['password'], database = creds['database'])
#         cursor = connection.cursor()
#         cursor.execute(stmt)
#         cursor.close()
#         connection.commit()
#         connection.close()
#     except Exception as e:
#         print(e)

# def testConnection():
#     stmt = """ALTER TABLE credentials ADD spotify_user varchar(255);"""
#     connection = connect(host = creds['host'], port = creds['port'], user = creds['user'], password = creds['password'], database = creds['database'])
#     cursor = connection.cursor()
#     cursor.execute(stmt)
#     cursor.close()
#     connection.commit()
#     connection.close()


def addNewUser(strava_user, strava_access, strava_refresh, spotify_access, spotify_refresh, spotify_user):
    try:
        stmt = """INSERT INTO credentials VALUES (%s, %s, %s, %s, %s, %s);"""
        conn = connectClean(creds)
        cur = conn.cursor()
        cur.execute(stmt, (strava_user, strava_access, strava_refresh, spotify_access, spotify_refresh, spotify_user))
        conn.commit()
        cur.close()
        conn.close()
        print('New user added: ', strava_user, strava_access, strava_refresh, spotify_access, spotify_refresh, spotify_user)
    except Exception as e:
        print(e)

def getUserInfoStrava(strava_user):
    try:
        stmt = """SELECT * FROM credentials WHERE strava_user=%s;"""
        conn = connectClean(creds)
        cur = conn.cursor()
        cur.execute(stmt, (str(strava_user),))
        row = cur.fetchone()
        cur.close()
        conn.close()

        return row

    except Exception as e:
        print(e)
def getUserInfoSpotify(spotify_user):
    try:
        stmt = """SELECT * FROM credentials WHERE spotify_user=%s;"""
        conn = connectClean(creds)
        cur = conn.cursor()
        cur.execute(stmt, (spotify_user,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        return row

    except Exception as e:
        print(e)

def updateUserStrava(strava_user, strava_access, strava_refresh):
    try:
        stmt = """UPDATE credentials SET strava_access=%s, strava_refresh=%s WHERE strava_user=%s;"""
        conn = connectClean(creds)
        cur = conn.cursor()
        cur.execute(stmt,  (strava_access, strava_refresh, (str(strava_user))))
        conn.commit()
        cur.close()
        conn.close()
        print('Strava info updated: ', strava_user, strava_access, strava_refresh)
    except Exception as e:
        print(e)

def updateUserStravaBySpotify(spotify_user, strava_user, strava_access, strava_refresh):
    try:
        stmt = """UPDATE credentials SET strava_access=%s, strava_refresh=%s, strava_user=%s WHERE spotify_user=%s;"""
        conn = connectClean(creds)
        cur = conn.cursor()
        cur.execute(stmt, (strava_access, strava_refresh, str(strava_user), spotify_user))
        conn.commit()
        cur.close()
        conn.close()
        print('Strava info updated for Spotify user: ' + spotify_user + ' : ' + str(strava_user))
    except Exception as e:
        print(e)

def updateUserSpotify(spotify_user, spotify_access, spotify_refresh):
    try:
        stmt = """UPDATE credentials SET spotify_access=%s, spotify_refresh=%s WHERE spotify_user=%s;"""
        conn = connectClean(creds)
        cur = conn.cursor()
        cur.execute(stmt, (spotify_access, spotify_refresh, spotify_user))
        conn.commit()
        cur.close()
        conn.close()
        print('Spotify info updated for Spotify user: ' + spotify_user)
    except Exception as e:
        print(e)

def wildcard():
    try:
        stmt = """ALTER TABLE credentials DROP COLUMN strava_name"""
        conn = connectClean(creds)
        cur = conn.cursor()
        cur.execute(stmt)
        conn.commit()
        cur.close()
        conn.close()
        print('wildcard run')
    except Exception as e:
        print(e)

if __name__ == "__main__":
    # testConnection()
    wildcard();
