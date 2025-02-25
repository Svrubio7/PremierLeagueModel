from curl_cffi import Curl, requests
import os
from pydantic import BaseModel
from rich import print

class SearchItem(BaseModel):
    name: str
    url: str
    description: str
    
class SearchResponse(BaseModel):
    results: list[SearchItem]
    
class ItemDetail(BaseModel):
    name: str
    url: str
    description: str
    price: str
    currency: str
    image: str
    
def new_session():
    session = requests.Session(impersonate_chrome=True)
    return session

def search_api(session: requests.Session, query: str, id: int) -> SearchResponse:
    url = f"https://api.reverse-api.com/search?q={query}&id={id}"
    resp = session.get(url)
    resp.raise_for_status()
    search = SearchResponse(**resp.json()['"raw"']["item_list"])
    return search

def detail_api(session: requests.Session, item: SearchItem) -> ItemDetail:
    url = f"https://api.reverse-api.com/detail?url={item.url}"
    resp = session.get(url)
    resp.raise_for_status()
    product = ItemDetail(**resp.json())
    return product

def main():
    session = new_session()
    search = search_api(session, "laptop", 1)
    for item in search.results:
        product = detail_api(session, item)
        print(product)