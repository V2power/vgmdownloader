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
songList = echoTopic.find("table", {"id": "songlist"}) # Lista das músicas para download

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

# Criando a pasta MP3, dentro da pasta principal (sempre haverá os arquivos MP3).
try:
    mp3_directory = "MP3"
    mp3_parent_dir = fullDirectory
    path = os.path.join(mp3_parent_dir, mp3_directory)
    os.makedirs(path, mode)
    print("Folder MP3 created inside of '% s'" % fullDirectory)
    mp3Directory = mp3_parent_dir + "/" + mp3_directory

except OSError as error:
    print(error)

# Inicia as variaveis
mp3 = lastMp3 = "mp3"
flac = lastFlac = "flac"

# Selecionando as músicas para baixar
for link in songList.find_all('a'):
    # Verifica se a música escolhida já foi baixada
    songs = link.get('href')
    if songs == lastMp3 or songs == lastFlac:
        continue
    else:
        if mp3 in songs:
            lastMp3 = songs
        else:
            lastFlac = songs
            
    # Identificando a música e seu titulo e preparando-a para baixar
    response = requests.get(str(baseURL+songs))
    songSoup = BeautifulSoup(response.text, "html.parser")
    songDown = songSoup.find("div", {"id": "EchoTopic"})
    songNamePlace = songDown.find_next("p", {"align": "left"})
    songNameTruePlace = songNamePlace.find_next("p", {"align": "left"})
    songName = songNameTruePlace.find_next('b')
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
            print("Downloading from this URL: " + songLink)
            print(status)
            print("Downloading... ")
            download = req.get(href)
            if download.status_code == 200:
                if flac in href:
                    os.chdir(fullDirectory)
                    with open(songTitle+ ".flac", 'wb') as f:
                        f.write(download.content)
                        print("Done downloading!")
                else:
                    os.chdir(mp3Directory)
                    with open(songTitle+ ".mp3", 'wb') as f:
                        f.write(download.content)
                        print("Done downloading!")
            else:
                print("ERROR, song could not be downloaded!")
        print("Selecting the next song")
print("No more songs found!")
print("Thanks for using this program!")