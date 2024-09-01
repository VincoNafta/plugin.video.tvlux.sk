# -*- coding: utf-8 -*-
# Module: default
# Author: Roman V. M.
# Created on: 28.11.2014
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib.parse import urlencode
from urllib.parse import parse_qsl

import xbmc
#from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import urllib3
from bs4 import BeautifulSoup


# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])


def search(page):
    user_agent = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"}
    http = urllib3.PoolManager(100, headers=user_agent)
    # Get the page content with the correct encoding to handle Unicode
    # response = http.request("GET","https://www.tvlux.sk/archiv/relacia/a-teraz-co/?id=a-teraz-co&relacia=300&iPage=1")
    # print(response.data.decode("utf-8"))
    return http.request("GET", page)


first_data = search("https://www.tvlux.sk/archiv/abecedne/vsetko")

bsObsah = BeautifulSoup(first_data.data, "html.parser")
def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def list_categories():
    """
    Create the list of video categories in the Kodi interface.
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(_handle, 'Videos')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')

    # Iterate through the div elements with video categories.
    div_content = bsObsah.findAll("div", class_="col-md-6 col-lg-3 rel-identification")
    for r in div_content:
        # Extract video information
        nazov = r.find("h3").text.strip()  # Title
        odkaz = r.find("a")["href"].strip()  # URL of the video
        obrazok = r.find("img")["src"].strip()  # Image URL
        zaner = r.find("div", class_="tag-blue").text.strip()

        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=nazov)

        # Ensure 'obrazok' is a valid string before passing it to setArt
        list_item.setArt({
            'thumb': obrazok,
            'icon': obrazok,
            'fanart': obrazok
        })

        # Set additional info for the list item.
        list_item.setInfo('video', {
            'title': nazov,
            'genre': zaner,
            'mediatype': 'video'
        })
        # Add the item to Kodi
        url = get_url(action='listing', category=nazov, url=odkaz)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def getVideoAdress(videoUrl):
    # html = http.request("GET", videoUrl)
    html = search(videoUrl)

    videoPageSrc = BeautifulSoup(html.data.decode("utf-8"), "html.parser")
    return videoPageSrc.find("source")["src"].strip()

def getVideoDescription(videoUrl):
    html = search(videoUrl)
    videoPageSrc = BeautifulSoup(html.data.decode("utf-8"), "html.parser")
    return videoPageSrc.find("p").text.strip()

def list_videos(category, url):
    """
    Create the list of playable videos in the Kodi interface.
    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name of the current section.
    xbmcplugin.setPluginCategory(_handle, category)
    # Set plugin content. It allows Kodi to select appropriate views for this type of content.
    xbmcplugin.setContent(_handle, 'videos')

    # Get the list of videos in the category.
    videos_raw_datas = search(url)
    videos = BeautifulSoup(videos_raw_datas.data.decode("utf-8"), "html.parser")

    # Find all video items
    video_list_content = videos.findAll("div", class_="archive-item")

    # Iterate through videos.
    for video in video_list_content:
        nazov = video.find("h4").text.strip()  # Title
        odkaz = video.find("a")["href"]  # Full URL of the video
        obrazok = video.find("img")["src"]  # Image URL
        datum = video.find("div", class_="tag dark").text.strip()
        list_item = xbmcgui.ListItem(label=nazov)

        # Set additional info for the list item.
        list_item.setInfo('video', {'title': nazov,
                                    'plot': getVideoDescription(odkaz),
                                    'mediatype': 'video'})
        # Set graphics for the list item.
        list_item.setArt({'thumb': obrazok, 'icon': obrazok, 'fanart': obrazok})
        # Set 'IsPlayable' property to 'true'.
        list_item.setProperty('IsPlayable', 'true')

        # Create a URL for the video playback
        url = get_url(action='play', video=getVideoAdress(odkaz))

        # Add the list item to Kodi directory
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_videos(params["category"], params['url'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['video'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_categories()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])