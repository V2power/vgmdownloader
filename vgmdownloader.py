import os, requests
from urllib import response
from bs4 import BeautifulSoup

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

# Apresentando as opções de álbuns para download
i = 0
for link in search.find_all('a'):
    games = link.get('href')
    print(str(i+1) + ") " + str(link.get('href')).strip().replace("/game-soundtracks/album/", "").replace("-", " "))
    lista.append(games)
    i += 1
n = int(input("Select the album number you want to download: "))
n = n - 1
gameLink = lista[n]

# Entrando na página do álbum selecionado
downres = requests.get(str(baseURL + gameLink))
downSoup = BeautifulSoup(downres.text, "html.parser")
echoTopic = downSoup.find("div", {"id": "EchoTopic"})
songList = echoTopic.find("table", {"id": "songlist"})

# Criando uma pasta com o título do álbum para salvar as músicas
albumTitle = echoTopic.find("h2").string
directory = albumTitle
parent_dir = "D:/Music/"
path = os.path.join(parent_dir, directory)
mode = 0o666
try:
    os.mkdir(path, mode)
    print("Folder '% s' created" % directory)
    print("Salving the downloaded song in this folder!")
    fullDirectory = parent_dir + directory
    os.chdir(fullDirectory)
except OSError as error:
    print(error)

# Selecionando as músicas para baixar
for link in songList.find_all('a'):
    songs = link.get('href')
    response = requests.get(str(baseURL+songs))
    songSoup = BeautifulSoup(response.text, "html.parser")
    songDown = songSoup.find("div", {"id": "EchoTopic"})
    songNamePlace = songDown.find_next("p", {"align": "left"})
    songNamePlace2 = songNamePlace.find_next("p", {"align": "left"})
    songName = songNamePlace2.find_next('b')
    songTitle = songName.find_next('b').string
    print("Download this song: " + songTitle)
    songFile = songDown.find_all("a", {"style": "color: #21363f;"})

    # Deixando a conexão aberta para downloads multiplos
    with requests.Session() as req:
        # Selecionando os links para entrar na música
        for link in songFile:
            songLink = link.get('href')
            href = songLink
            status = requests.get(str(baseURL+songLink))
            mp3 = "mp3"
            flac = "flac"
            print("Downloading from this URL: " + songLink)
            print(status)
            print("Downloading... ")
            download = req.get(href)
            if download.status_code == 200:
                if flac in href:
                    with open(songTitle+ ".flac", 'wb') as f:
                        f.write(download.content)
                        print("Done downloading!")
                else:
                    with open(songTitle+ ".mp3", 'wb') as f:
                        f.write(download.content)
                        print("Done downloading!")
            else:
                print("ERROR, song could not be downloaded!")
        print("Selecting the next song")
    print("No more songs found!")
print("Thanks for using this program!")