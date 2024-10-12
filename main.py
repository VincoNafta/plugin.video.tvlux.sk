# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib.parse import urlencode
from urllib.parse import parse_qsl
from dateutil.parser import parse

import xbmc
import xbmcgui
import xbmcplugin
import urllib3
from bs4 import BeautifulSoup

_url = sys.argv[0]
_handle = int(sys.argv[1])


def search(page):
    user_agent = {'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"}
    http = urllib3.PoolManager(1, headers=user_agent)
    return http.request("GET", page)


def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def get_video_page_src(video_page_url):
    return BeautifulSoup(search(video_page_url).data.decode("utf-8"), "html.parser")


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

    live_header = "[COLOR FFEE0000]Živé vysielanie[/COLOR]"
    live_item = xbmcgui.ListItem(label=live_header)
    live_item.setInfo('video', {'title': live_header,
                                'mediatype': 'video'})
    livestream = "https://stream.tvlux.sk/lux/ngrp:lux.stream_all/chunklist_b2652000.m3u8"

    get_url(action='play', video=livestream)
    xbmcplugin.addDirectoryItem(_handle, livestream, live_item, False)

    first_data = search("https://www.tvlux.sk/archiv/abecedne/vsetko")
    div_content = (BeautifulSoup(first_data.data, "html.parser").
                   findAll("div", class_="col-md-6 col-lg-3 rel-identification"))
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
    xbmcplugin.endOfDirectory(_handle)


def get_video_adress(page_src):
    return page_src.find("source")["src"].strip()


def get_video_description(page_src):
    return page_src.find("p").text.strip()

def convert_date(str_date):
    date_text = str_date.get_text(strip=True)
    t_date = parse(date_text, dayfirst=True).date()
    return t_date.isoformat()

def list_videos(category, url):
    """
    Create the list of playable videos in the Kodi interface.
    :param category: Category name
    :type category: str
    :type url: address to page with video thumbnails
    """
    xbmcplugin.setPluginCategory(_handle, category)
    xbmcplugin.setContent(_handle, 'videos')
    archive_page_content = (BeautifulSoup(search(url).data.decode("utf-8"), "html.parser"))

    for video in archive_page_content.findAll("div", class_="archive-item"):
        nazov = video.find("h4").text.strip()  # Title
        odkaz = video.find("a")["href"]  # Full URL of the video
        obrazok = video.find("img")["src"]  # Image URL
        parsed_date = video.find("div", class_="tag dark")
        list_item = xbmcgui.ListItem(label=nazov)

        video_page_src = get_video_page_src(odkaz)

        premier_date = convert_date(parsed_date)
        info_labels = {'title': nazov,
                       'plot': get_video_description(video_page_src),
                       'mediatype': 'video'}
        if premier_date:
            info_labels['premiered'] = premier_date

        list_item.setInfo('video', info_labels)

        list_item.setArt({'thumb': obrazok, 'icon': obrazok, 'fanart': obrazok})
        list_item.setProperty('IsPlayable', 'true')

        url = get_url(action='play', video=get_video_adress(video_page_src))
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    pages = archive_page_content.find("ul", class_="a-list")
    if pages is not None:
        next_button = pages.find("a", class_="chevronRight")
        if next_button is not None:
            next_button_url = next_button.get("href")
            if next_button_url:
                list_item = xbmcgui.ListItem(label='Ďalšie Epizódy')
                list_item.setInfo('video', {
                    'title': 'Ďalšie Epizódy',
                    'mediatype': 'video'
                })
                url = get_url(action='listing', category=category, url=next_button_url.strip())
                xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    # xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    play_item = xbmcgui.ListItem(path=path)
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
    if params:
        if params['action'] == 'listing':
            list_videos(params["category"], params['url'])
        elif params['action'] == 'play':
            play_video(params['video'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2][1:])
