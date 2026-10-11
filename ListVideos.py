from dateutil.parser import parse
from PageRequester import search
from bs4 import BeautifulSoup

def getVideoItems(url):
    return BeautifulSoup(search(url).data.decode("utf-8"), "html.parser")

def get_video_adress(page_src):
    return page_src.find("source")["src"].strip()


def get_video_description(page_src):
    return page_src.find("p").text.strip()


def convert_date(str_date):
    date_text = str_date.get_text(strip=True)
    t_date = parse(date_text, dayfirst=True).date()
    return t_date.isoformat()


def get_video_page_src(video_page_url):
    return BeautifulSoup(search(video_page_url).data.decode("utf-8"), "html.parser")