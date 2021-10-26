# dbURLParse.py



# parse relevant information from the heroku DATABASE_URL config var
def parse(url):
    url = url.split('/')
    database = url[3]  ### 
    rest = url[2] 
    rest = rest.split(':')
    user = rest[0] ###
    port = rest[2] ###
    rest = rest[1] 
    rest = rest.split('@')
    password = rest[0] ###
    host = rest[1] ###
    
    creds = {}
    creds['host'] = host
    creds['port'] = port
    creds['user'] = user
    creds['password'] = password
    creds['database'] = database

    return creds


