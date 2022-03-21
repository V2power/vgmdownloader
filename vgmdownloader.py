import os
import requests
from bs4 import BeautifulSoup

r = requests.get("https://downloads.khinsider.com/")
baseURL = str(r.url)
# Exemplo: zelda
print(" __      _______ __  __ _____                      _                 _           ")
print(" \ \    / / ____|  \/  |  __ \                    | |               | |          ")
print("  \ \  / / |  __| \  / | |  | | _____      ___ __ | | ___   __ _  __| | ___ _ __ ")
print("   \ \/ /| | |_ | |\/| | |  | |/ _ \ \ /\ / / '_ \| |/ _ \ / _` |/ _` |/ _ \ '__|")
print("    \  / | |__| | |  | | |__| | (_) \ V  V /| | | | | (_) | (_| | (_| |  __/ |   ")
print("     \/   \_____|_|  |_|_____/ \___/ \_/\_/ |_| |_|_|\___/ \__,_|\__,_|\___|_|   ")
print("                                                                  created by V2\n")

a = 1
while(a == 1):
    gameName = str(input("Enter the game name: "))
    # https://downloads.khinsider.com/search?search=zelda
    gameName = gameName.replace(" ", "+").lower()
    searchPage = requests.get(baseURL + "/search?search=" + gameName)
    lista = []
    searchSoup = BeautifulSoup(searchPage.text, "html.parser")
    results = searchSoup.find("p", {"align": "left"}).string
    search = searchSoup.find("div", {"id": "EchoTopic"})
    searchExist = search.find("h2").string
    if (results == "Found 0 matching results."):
        print("No albuns found! Please try again...\n")
    else:
        a = 0

# Apresentando as opções de álbuns para download
if (searchExist == "Search"):
    i = 0
    print(results + "\n")
    for link in search.find_all('a'):
        games = link.get('href')
        gameSelection = str(i+1) + ") " + str(link.get('href')).strip().replace("/game-soundtracks/album/", "").replace("-", " ")
        print(gameSelection)
        lista.append(games)
        i += 1
    print("")
    print("=======================================================")
    n = int(input("Select the album number you want to download: "))
    print("=======================================================")
    n = n - 1
    gameLink = lista[n]

    # Entrando na página do álbum selecionado
    downres = requests.get(str(baseURL + gameLink))
    downSoup = BeautifulSoup(downres.text, "html.parser")
else:
    # baseURL = https://downloads.khinsider.com/
    # https://downloads.khinsider.com/game-soundtracks/album/b-wings-nes
    # B-Wings (NES)
    gameLink = searchExist.replace(" ", "-").replace("(","").replace(")","").lower()
    downres = requests.get(str(baseURL + "game-soundtracks/album/" + gameLink))
    downSoup = BeautifulSoup(downres.text, "html.parser")

echoTopic = downSoup.find("div", {"id": "EchoTopic"})
songList = echoTopic.find("table", {"id": "songlist"}) # Lista das músicas para download

# Criando uma pasta com o título do álbum para salvar as músicas
albumTitle = echoTopic.find("h2").string
directory = albumTitle
parent_dir = input("Choose where you want to download (Example: D:/Music/): ").replace("\\", "/")
print("=======================================================\n")
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

# Baixando a arte do álbum
try:
    imageCover = downSoup.find("img").get("src")
    print("Downloading album cover...")
    coverResponse = requests.get(str(imageCover))
    with open("Cover.jpg", 'wb') as f:
        f.write(coverResponse.content)
        print("Done downloading the album cover!\n")
except:
    print("No album covers found...") # Quando não há imagens para baixar.
finally:
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
                        print("Done downloading!\n")
                else:
                    os.chdir(mp3Directory)
                    with open(songTitle+ ".mp3", 'wb') as f:
                        f.write(download.content)
                        print("Done downloading!\n")
            else:
                print("ERROR, song could not be downloaded!\n")
        print("Selecting the next song\n")
print("No more songs found!\n")
print("Thanks for using this program!")