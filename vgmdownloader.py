import os
import time
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"
}

r = requests.get("https://downloads.khinsider.com/", headers=headers)
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
    searchPage = requests.get(baseURL + "/search?search=" + gameName, headers=headers)
    lista = []
    searchSoup = BeautifulSoup(searchPage.text, "html.parser")
    results = searchSoup.find("p", {"align": "left"}).string
    search = searchSoup.find("table", {"class": "albumList"})
    searchExist = searchSoup.find("h2").string
    if (results == "Found 0 matching results."):
        print("No albuns found! Please try again...\n")
    else:
        a = 0

# Apresentando as opções de álbuns para download
if (searchExist == "Search"):
    i = 0
    oldGameSelection = "a" #Só para iniciar a variável e fazer a verificação para pular repitidos
    gameSelection = "b"

    print(results + "\n")
    for link in search.find_all('a'):
        games = link.get('href')
        gameSelection = str(link.get('href')).strip().replace("/game-soundtracks/album/", "").replace("-", " ")
        indexGameSelection = str(i+1) + ") " + gameSelection
        if (oldGameSelection == gameSelection or "/" in gameSelection):
            continue
        else:
            print(indexGameSelection)
            lista.append(games)
            i += 1
        oldGameSelection = gameSelection

    print("")
    print("=======================================================")
    n = int(input("Select the album number you want to download: "))
    print("=======================================================")
    n = n - 1
    gameLink = lista[n]

    # Entrando na página do álbum selecionado
    downres = requests.get(str(baseURL + gameLink), headers=headers)
    downSoup = BeautifulSoup(downres.text, "html.parser")
else:
    # baseURL = https://downloads.khinsider.com/
    # https://downloads.khinsider.com/game-soundtracks/album/b-wings-nes
    # B-Wings (NES)
    gameLink = searchExist.replace(" ", "-").replace("(","").replace(")","").lower()
    downres = requests.get(str(baseURL + "game-soundtracks/album/" + gameLink), headers=headers)
    downSoup = BeautifulSoup(downres.text, "html.parser")

echoTopic = downSoup.find("div", {"id": "pageContent"})
songList = echoTopic.find("table", {"id": "songlist"}) # Lista das músicas para download

# Criando uma pasta com o título do álbum para salvar as músicas
albumTitle = echoTopic.find("h2").string
directory = albumTitle.replace(":", "")
parent_dir = input("Choose where you want to download (Example: C:/Users/V2/Music/): ").replace("\\", "/").replace("¥", "/")
if not (parent_dir.endswith("/")):
    parent_dir = parent_dir + "/"
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
    coverResponse = requests.get(str(imageCover), headers=headers)
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
    response = requests.get(str(baseURL+songs), headers=headers)
    songSoup = BeautifulSoup(response.text, "html.parser")
    songDown = songSoup.find("div", {"id": "pageContent"})
    songNamePlace = songDown.find_next("p", {"align": "left"})
    songNameTruePlace = songNamePlace.find_next("p", {"align": "left"})
    songName = songNameTruePlace.find_next('b')
    songTitle = songName.find_next('b').string
    print("Download this song: " + songTitle)
    songFile = songTitle.find_all_next("a")

    # Deixando a conexão aberta para downloads multiplos
    with requests.Session() as req:
        # Selecionando os links para entrar na música
        for link in songFile:
            songLink = link.get('href')
            href = songLink
            status = requests.get(str(baseURL+songLink), headers=headers)
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
time.sleep(5)