import os, requests
from re import S
from urllib import response
from bs4 import BeautifulSoup

os.chdir("C:\\Users\\vitor\Music")
r = requests.get("https://downloads.khinsider.com/")
baseURL = str(r.url)
# zelda
gameName = str(input("Enter the game name: "))
# https://downloads.khinsider.com/search?search=zelda
gameName = gameName.replace(" ", "+").lower()
searchPage = requests.get(baseURL + "/search?search=" + gameName)
lista = []
searchSoup = BeautifulSoup(searchPage.text, "html.parser")
search = searchSoup.find("div", {"id": "EchoTopic"})
for link in search.find_all('a'):
    games = link.get('href')
    print(str(link.get('href')).strip().replace("/game-soundtracks/album/", "").replace("-", " "))
    lista.append(games)
n = int(input("Select the album number you want to download: "))
n = n - 1
gameLink = lista[n]
downres = requests.get(str(baseURL + gameLink))
downSoup = BeautifulSoup(downres.text, "html.parser")
print(downSoup)