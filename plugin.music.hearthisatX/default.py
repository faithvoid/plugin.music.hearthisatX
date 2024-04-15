import urllib2
import json
import sys
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItem, endOfDirectory
from xbmc import Keyboard

BASE_URL = 'https://api-v2.hearthis.at'
LATEST_URL = BASE_URL + '/feed/?type=new&page=1&count=20'
POPULAR_URL = BASE_URL + '/feed/?type=popular&page=1&count=20'
EXPLORE_URL = BASE_URL + '/feed/?page=1&count=20'
LIVE_URL = BASE_URL + '/feed/?type=live&page=1&count=20'

def fetch_tracks(url):
    """ Fetches tracks based on the URL provided """
    try:
        response = urllib2.urlopen(url)
        data = json.load(response)
        return data
    except Exception as e:
        print("Error retrieving data: %s" % str(e))
        return None

def list_tracks(tracks):
    """ Lists tracks in the XBMC/Kodi GUI """
    if tracks:
        for track in tracks:
            # Ensure both username and title are encoded as UTF-8 to handle non-ASCII characters
            user = track['user']['username'].encode('utf-8') if isinstance(track['user']['username'], unicode) else track['user']['username']
            title = track['title'].encode('utf-8') if isinstance(track['title'], unicode) else track['title']
            display_title = "{} - {}".format(user, title)
            li = ListItem(display_title, iconImage='DefaultAudio.png', thumbnailImage=track.get('artwork_url', ''))
            li.setInfo(type='Music', infoLabels={'Title': title, 'Artist': user})
            addDirectoryItem(handle=int(sys.argv[1]), url=track['stream_url'], listitem=li, isFolder=False)
    else:
        Dialog().ok('Error', 'Failed to retrieve tracks')
    endOfDirectory(int(sys.argv[1]))

def main_menu():
    """ Main menu providing choices for Popular, Latest Tracks, and Genres """
    base_url = sys.argv[0]
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=latest', listitem=ListItem('Latest Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=popular', listitem=ListItem('Popular Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=explore', listitem=ListItem('Explore', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=genres', listitem=ListItem('Genres', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=search', listitem=ListItem('Search Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    endOfDirectory(int(sys.argv[1]))

def search_tracks(query):
    search_url = BASE_URL + '/search?t=' + urllib2.quote(query)
    tracks = fetch_tracks(search_url)
    list_tracks(tracks)


def initiate_search():
    """ Initiates a search by asking user input through a keyboard dialog """
    keyboard = Keyboard('', 'Enter search query')
    keyboard.doModal()
    if keyboard.isConfirmed():
        query = keyboard.getText()
        search_tracks(query)


def fetch_genres():
    """ Fetches available genres from HearThis.At """
    genres_url = BASE_URL + '/categories/'
    try:
        response = urllib2.urlopen(genres_url)
        genres = json.load(response)
        return genres
    except Exception as e:
        print("Error retrieving genres: %s" % str(e))
        return None

def list_genres():
    """ Lists available genres in the XBMC/Kodi GUI """
    genres = fetch_genres()
    if genres:
        for genre in genres:
            li = ListItem(genre['name'], iconImage='DefaultFolder.png')
            url = '%s?mode=genre&genre_id=%s' % (sys.argv[0], genre['id'])
            addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)
    else:
        Dialog().ok('Error', 'Failed to retrieve genres')
    endOfDirectory(int(sys.argv[1]))

def get_params():
    """ Parse parameters passed to the plugin """
    param_string = sys.argv[2]
    params = {}
    if len(param_string) >= 2:
        pairs = param_string[1:].split('&')
        params = {pair.split('=')[0]: pair.split('=')[1] for pair in pairs if len(pair.split('=')) == 2}
    return params

if __name__ == '__main__':
    params = get_params()
    mode = params.get('mode', None)
    if mode == 'latest':
        tracks = fetch_tracks(LATEST_URL)
        list_tracks(tracks)
    elif mode == 'popular':
        tracks = fetch_tracks(POPULAR_URL)
        list_tracks(tracks)
    elif mode == 'live':
        tracks = fetch_tracks(LIVE_URL)
        list_tracks(tracks)
    elif mode == 'explore':
        tracks = fetch_tracks(EXPLORE_URL)
        list_tracks(tracks)
    elif mode == 'genres':
        list_genres()
    elif mode == 'genre':
        genre_id = params.get('genre_id', '')
        genre_tracks_url = BASE_URL + '/categories/' + genre_id + '/?type=tracks&count=20'
        tracks = fetch_tracks(genre_tracks_url)
        list_tracks(tracks)
    elif mode == 'search':
        initiate_search()
    else:
        main_menu()
