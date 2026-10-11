from bs4 import BeautifulSoup
from PageRequester import search


def getRelationRawData():
    return (BeautifulSoup(search("https://www.tvlux.sk/archiv/abecedne/vsetko").data, "html.parser").
               find_all("div", class_="col-md-6 col-lg-3 rel-identification"))


def getRelationName(relation_raw_data):
    return relation_raw_data.find("h3").text.strip()  # Title
def getRelationLink(relation_raw_data):
    return "https://www.tvlux.sk" + relation_raw_data.find("a")["href"].strip()  # URL of the video
def getRelationImg(relation_raw_data):
    return relation_raw_data.find("img")["src"].strip()  # Image URL
def getRelationGenre(relation_raw_data):
    return relation_raw_data.find("div", class_="tag-blue").text.strip()