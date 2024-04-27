import urllib2
import json
import sys
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItem, endOfDirectory
from xbmc import Keyboard

## URLs for API-V2 ##

BASE_URL = 'https://api-v2.hearthis.at'
POPULAR_URL = BASE_URL + '/feed?type=popular&page={page}&count=20'
FEATURED_URL = BASE_URL + '/feed?page={page}&count=20'
LATEST_URL = BASE_URL + '/feed?type=new&page={page}&count=20'
LIVE_URL = BASE_URL + '/feed?type=live&page={page}&count=20'

def fetch_tracks(url, page=1):
    url = url.format(page=page)
    try:
        response = urllib2.urlopen(url)
        data = json.load(response)
        if isinstance(data, list):  # Ensure the response is a list
            return data
        else:
            print("Unexpected data format:", data)
            return []
    except Exception as e:
        print("Error retrieving data: %s" % str(e))
        return []

def add_pagination_controls(url, current_page, mode):
    """ Adds pagination controls to the list """
    current_page = int(current_page)
    base_url = sys.argv[0]
    next_page = ListItem('Next Page >>', iconImage='DefaultFolder.png')
    prev_page = ListItem('<< Previous Page', iconImage='DefaultFolder.png')
    if current_page > 1:
        addDirectoryItem(handle=int(sys.argv[1]), url='{0}?mode={1}&page={2}'.format(base_url, mode, current_page - 1), listitem=prev_page, isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url='{0}?mode={1}&page={2}'.format(base_url, mode, current_page + 1), listitem=next_page, isFolder=True)

def list_tracks(tracks):
    if tracks and isinstance(tracks, list):
        for track in tracks:
            if isinstance(track, dict) and 'user' in track and 'username' in track['user']:
                user = track['user']['username'].encode('utf-8') if isinstance(track['user']['username'], unicode) else track['user']['username']
                title = track['title'].encode('utf-8') if isinstance(track['title'], unicode) else track['title']
                display_title = "{} - {}".format(user, title)
                li = ListItem(display_title, iconImage='DefaultAudio.png', thumbnailImage=track.get('artwork_url', ''))
                li.setInfo(type='Music', infoLabels={'Title': title, 'Artist': user})
                addDirectoryItem(handle=int(sys.argv[1]), url=track['stream_url'], listitem=li, isFolder=False)
    else:
        Dialog().ok('Error', 'Failed to retrieve tracks!')
    endOfDirectory(int(sys.argv[1]))



def main_menu():
    """ Main menu providing choices for Popular, Latest Tracks, and Genres """
    base_url = sys.argv[0]
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=popular', listitem=ListItem('Popular Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=featured', listitem=ListItem('Featured Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=latest', listitem=ListItem('Latest Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=genres', listitem=ListItem('Genres', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=search', listitem=ListItem('Search', iconImage='DefaultFolder.png'), isFolder=True)
    endOfDirectory(int(sys.argv[1]))

def choose_search_type():
    """ Asks user to select the type of search. """
    dialog = Dialog()
    types = ['Tracks']
    chosen = dialog.select('Search Type:', types)
    if chosen == -1:
        return None  # User cancelled the dialog
    return types[chosen]

def search_tracks(query, search_type, page=1):
    """ Perform search based on the type and query provided """
    if search_type == 'Tracks':
        search_url = BASE_URL + '/search?type=tracks&t=' + urllib2.quote(query) + '&page={}&count=20'.format(page)
    elif search_type == 'Playlists':
        search_url = BASE_URL + '/search?type=playlists&t=' + urllib2.quote(query) + '&page={}&count=20'.format(page)
    else:
        return  # Unknown search type

    tracks = fetch_tracks(search_url)
    if search_type == 'Playlists':
        list_playlists(tracks)  # Handle playlist differently
    else:
        list_tracks(tracks)
    add_pagination_controls(search_url, page, 'search&query={}&search_type={}'.format(urllib2.quote(query), search_type))

def initiate_search(search_type=None, query=None, page=1):
    if not search_type:
        search_type = choose_search_type()
        if not search_type:
            return  # User cancelled the selection
    
    if not query:
        keyboard = Keyboard('', 'Search')
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
        else:
            return  # User cancelled input

    search_tracks(query, search_type, page)

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
            # Check if the genre name is neither "Livestreams" nor "Replays"
            if genre['name'] not in ["Livestreams", "Replays"]:
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

def handle_api_response(data):
    try:
        # Example of processing and validating API response
        username = data.get('username', 'N/A')  # Using .get for safer access
        permalink = data.get('permalink', 'N/A')
        # Process other fields
        print("Username: %s, Permalink: %s" % (username, permalink))
        # Further code to use this data
    except KeyError as e:
        print("Missing key in data: %s" % e)
    except TypeError as e:
        print("Type error in processing data: %s" % e)


if __name__ == '__main__':
    params = get_params()
    mode = params.get('mode', None)
    page = int(params.get('page', 1))  # Default to page 1 if not specified

    if mode in ['latest', 'popular', 'featured', 'live']:
        url_map = {
            'latest': LATEST_URL,
            'popular': POPULAR_URL,
            'featured': FEATURED_URL,
            'live': LIVE_URL
        }
        tracks = fetch_tracks(url_map[mode], page)
        list_tracks(tracks)
        add_pagination_controls(url_map[mode], page, mode)
    elif mode == 'genres':
        list_genres()
    elif mode == 'genre':
        genre_id = params.get('genre_id', '')
        genre_tracks_url = BASE_URL + '/categories/' + genre_id + '/?type=tracks&count=20&page={0}'.format(page)
        tracks = fetch_tracks(genre_tracks_url)
        list_tracks(tracks)
        add_pagination_controls(genre_tracks_url, page, 'genre&genre_id=' + genre_id)
    elif mode == 'search':
        initiate_search('Tracks', query, page)
    else:
        main_menu()
