# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import sys
from urllib.parse import urlencode
from urllib.parse import parse_qsl


import xbmc
import xbmcgui
import xbmcplugin

from PageRequester import search
import ListRealtions as Lr
import ListVideos as Lv

_url = sys.argv[0]
_handle = int(sys.argv[1])


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

    live_header = "[COLOR FFEE0000]Živé vysielanie[/COLOR]"
    live_item = xbmcgui.ListItem(label=live_header)
    info_tag = live_item.getVideoInfoTag()
    info_tag.setTitle(live_header)
    info_tag.setMediaType('video')

    livestream = "https://stream.tvlux.sk/luxtv/luxtv-livestream/playlist.m3u8"

    get_url(action='play', video=livestream)
    xbmcplugin.addDirectoryItem(_handle, livestream, live_item, False)

    # Archív
    archive_header = "Archív"
    archive_item = xbmcgui.ListItem(label=archive_header)
    info_tag = archive_item.getVideoInfoTag()
    info_tag.setTitle(archive_header)
    archive_url = get_url(action='archive')
    xbmcplugin.addDirectoryItem(
        _handle, archive_url, archive_item, True
    )

    xbmcplugin.endOfDirectory(_handle)

def list_archive():
    xbmcplugin.setPluginCategory(_handle, 'Videos')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')

    for r in Lr.getRelationRawData():
        # Extract video information
        nazov = Lr.getRelationName(r)
        odkaz = Lr.getRelationLink(r)
        obrazok = Lr.getRelationImg(r)
        zaner = Lr.getRelationGenre(r)

        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=nazov)

        # Ensure 'obrazok' is a valid string before passing it to setArt
        list_item.setArt({
            'thumb': obrazok,
            'icon': obrazok,
            'fanart': obrazok
        })

        info_tag = list_item.getVideoInfoTag()
        info_tag.setTitle(nazov)
        info_tag.setGenres([zaner])
        info_tag.setMediaType('video')

        # Add the item to Kodi
        url = get_url(action='listing', category=nazov, url=odkaz)
        xbmcplugin.addDirectoryItem(_handle, url, list_item, True)
    xbmcplugin.endOfDirectory(_handle)




def list_videos(category, url):
    """
    Create the list of playable videos in the Kodi interface.
    :param category: Category name
    :type category: str
    :type url: address to page with video thumbnails
    """
    xbmcplugin.setPluginCategory(_handle, category)
    xbmcplugin.setContent(_handle, 'videos')
    archive_page_content = Lv.getVideoItems(url)

    for video in archive_page_content.find_all("div", class_="archive-item"):
        nazov = video.find("h4").text.strip()  # Title
        odkaz = video.find("a")["href"]  # Full URL of the video
        obrazok = video.find("img")["src"]  # Image URL
        parsed_date = video.find("div", class_="tag dark")
        list_item = xbmcgui.ListItem(label=nazov)

        video_page_src = Lv.get_video_page_src(odkaz)

        premier_date = Lv.convert_date(parsed_date)
        info_tag = list_item.getVideoInfoTag()

        info_tag.setTitle(nazov)
        info_tag.setPlot(Lv.get_video_description(video_page_src))
        info_tag.setMediaType('video')

        if premier_date:
            info_tag.setPremiered(premier_date)

        list_item.setArt({'thumb': obrazok, 'icon': obrazok, 'fanart': obrazok})
        list_item.setProperty('IsPlayable', 'true')

        url = get_url(action='play', video=Lv.get_video_adress(video_page_src))
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    pages = archive_page_content.find("ul", class_="a-list")
    if pages is not None:
        next_button = pages.find("a", class_="chevronRight")
        if next_button is not None:
            next_button_url = next_button.get("href")
            if next_button_url:
                list_item = xbmcgui.ListItem(label='Ďalšie Epizódy')
                info_tag = list_item.getVideoInfoTag()
                info_tag.setTitle('Ďalšie Epizódy')
                info_tag.setMediaType('video')

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
        elif params['action'] == 'archive':
            list_archive()
        elif params['action'] == 'play':
            play_video(params['video'])
        elif params['action'] == 'play_video':
            play_video(params['video'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2][1:])
