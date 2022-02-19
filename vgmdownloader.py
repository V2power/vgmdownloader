import os, requests
from re import S
from urllib import response
import urllib.request
from bs4 import BeautifulSoup

os.chdir("D:/Music")
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
i = 0
for link in search.find_all('a'):
    games = link.get('href')
    print(str(i+1) + ") " + str(link.get('href')).strip().replace("/game-soundtracks/album/", "").replace("-", " "))
    lista.append(games)
    i += 1
n = int(input("Select the album number you want to download: "))
n = n - 1
gameLink = lista[n]
downres = requests.get(str(baseURL + gameLink))
downSoup = BeautifulSoup(downres.text, "html.parser")
echoTopic = downSoup.find("div", {"id": "EchoTopic"})
songList = echoTopic.find("table", {"id": "songlist"})
for link in songList.find_all('a'):
    # songName = link.string
    songs = link.get('href')
    response = requests.get(str(baseURL+songs))
    songSoup = BeautifulSoup(response.text, "html.parser")
    songDown = songSoup.find("div", {"id": "EchoTopic"})
    songNamePlace = songDown.find_next("p", {"align": "left"})
    songNamePlace2 = songNamePlace.find_next("p", {"align": "left"})
    songName = songNamePlace2.find_next('b')
    songName2 = songName.find_next('b').string
    print(songName2)
    songFile = songDown.find_all("a", {"style": "color: #21363f;"})
    with requests.Session() as req:
        for link in songFile:
            songs2 = link.get('href')
            href = songs2
            response2 = requests.get(str(baseURL+songs2))
            mp3 = "mp3"
            flac = "flac"
            print(songs2)
            print(response2)
            print("Downloading song... please wait...")
            download = req.get(href)
            if download.status_code == 200:
                if flac in href:
                    with open(songName2+ ".flac", 'wb') as f:
                        f.write(download.content)
                        print("Done downloading!")
                else:
                    with open(songName2+ ".mp3", 'wb') as f:
                        f.write(download.content)
                        print("Done downloading!")
            else:
                print("ERROR, song could not be downloaded!")