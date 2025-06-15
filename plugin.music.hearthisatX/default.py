import urllib2
import json
import sys
from xbmcgui import ListItem, Dialog
from xbmcplugin import addDirectoryItem, endOfDirectory
from xbmc import Keyboard
import re
import ssl

## URLs for API-V2 ##
# Base URL for API requests
BASE_URL = 'https://api-v2.hearthis.at'

# URLs for different feeds
POPULAR_URL = BASE_URL + '/feed?type=popular&page={page}&count=20'
FEATURED_URL = BASE_URL + '/feed?page={page}&count=20'
LATEST_URL = BASE_URL + '/feed?type=new&page={page}&count=20'
LIVE_URL = BASE_URL + '/feed?type=live&page={page}&count=20'

# SSL
try:
    SSL_CONTEXT = ssl.create_default_context()
except Exception:
    SSL_CONTEXT = ssl._create_unverified_context()

# Common headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'
}

# Function to fetch tracks from a given URL
def fetch_tracks(url, page=1):
    url = url.format(page=page)
    try:
        request = urllib2.Request(url, headers=HEADERS)
        response = urllib2.urlopen(request, context=SSL_CONTEXT)
        data = json.load(response)
        if isinstance(data, list):  # Ensure the response is a list
            return data
        else:
            print("Unexpected data format:", data)
            return []
    except Exception as e:
        print("Error retrieving data: %s" % str(e))
        return []

# Function to add pagination controls to the list
def add_pagination_controls(url, current_page, mode):
    current_page = int(current_page)
    base_url = sys.argv[0]
    next_page = ListItem('Next Page >>', iconImage='DefaultFolder.png')
    prev_page = ListItem('<< Previous Page', iconImage='DefaultFolder.png')
    if current_page > 1:
        addDirectoryItem(handle=int(sys.argv[1]), url='{0}?mode={1}&page={2}'.format(base_url, mode, current_page - 1), listitem=prev_page, isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url='{0}?mode={1}&page={2}'.format(base_url, mode, current_page + 1), listitem=next_page, isFolder=True)

# Function to list tracks as ListItems in XBMC
def list_tracks(tracks):
    if not tracks or not isinstance(tracks, list):
        Dialog().ok('Error', 'Failed to retrieve tracks!')
        endOfDirectory(int(sys.argv[1]))
        return

    for track in tracks:
        if not isinstance(track, dict):
            continue

        # Extract metadata directly from the API
        user = track.get('user', {}).get('username', 'Unknown')
        title = track.get('title', 'Untitled')
        stream_url = track.get('stream_url')
        thumb = track.get('artwork_url', '') or track.get('thumb', '')
        genre = track.get('genre', 'Unknown')
        duration = int(track.get('duration', 0))

        # Safe unicode handling (for Python 2)
        try:
            user = user.encode('utf-8') if isinstance(user, unicode) else user
            title = title.encode('utf-8') if isinstance(title, unicode) else title
        except NameError:
            pass  # Python 3

        display_title = "{} - {}".format(user, title)

        li = ListItem(display_title, iconImage='DefaultAudio.png', thumbnailImage=thumb)
        li.setInfo(type='Music', infoLabels={
            'Title': title,
            'Artist': user,
            'Genre': genre,
            'Duration': duration
        })

        addDirectoryItem(handle=int(sys.argv[1]), url=stream_url, listitem=li, isFolder=False)

    endOfDirectory(int(sys.argv[1]))

# Main menu
def main_menu():
    base_url = sys.argv[0]
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=popular', listitem=ListItem('Popular Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=featured', listitem=ListItem('Featured Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=latest', listitem=ListItem('Latest Tracks', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=live', listitem=ListItem('Livestreams', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=genres', listitem=ListItem('Genres', iconImage='DefaultFolder.png'), isFolder=True)
    addDirectoryItem(handle=int(sys.argv[1]), url=base_url + '?mode=search', listitem=ListItem('Search', iconImage='DefaultFolder.png'), isFolder=True)
    endOfDirectory(int(sys.argv[1]))

# Function to choose search type
def choose_search_type():
    dialog = Dialog()
    types = ['Tracks']
    chosen = dialog.select('Search Type:', types)
    if chosen == -1:
        return None  # User cancelled the dialog
    return types[chosen]

def search_tracks(query, search_type, page=1):
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

# Function to initiate search
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

# Function to fetch genres
def fetch_genres():
    genres_url = BASE_URL + '/categories/'
    try:
        request = urllib2.Request(genres_url, headers=HEADERS)
        response = urllib2.urlopen(request, context=SSL_CONTEXT)
        genres = json.load(response)
        return genres
    except Exception as e:
        print("Error retrieving genres: %s" % str(e))
        return None

# Function to list genres as ListItems in XBMC
def list_genres():
    genres = fetch_genres()
    if genres:
        for genre in genres:
            # Check if the genre name is neither "Livestreams" nor "Replays"
            if genre['name'] not in ["", "Replays"]:
                li = ListItem(genre['name'], iconImage='DefaultFolder.png')
                url = '%s?mode=genre&genre_id=%s' % (sys.argv[0], genre['id'])
                addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)
    else:
        Dialog().ok('Error', 'Failed to retrieve genres')
    endOfDirectory(int(sys.argv[1]))

# Function to parse parameters passed to the plugin
def get_params():
    param_string = sys.argv[2]
    params = {}
    if len(param_string) >= 2:
        pairs = param_string[1:].split('&')
        params = {pair.split('=')[0]: pair.split('=')[1] for pair in pairs if len(pair.split('=')) == 2}
    return params

# Function to handle API responses
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

# Main Function
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
        query = params.get('query', '')  # Get query parameter, default to empty string
        initiate_search('Tracks', query, page)  # Initiate search with query
    else:
        main_menu()
