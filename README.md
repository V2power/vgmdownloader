### Features

- Download entire game music albums;
-  .mp3 and .flac formats;
- Search mechanism to find your exact game.

# VGMDownloader

![](https://github.com/V2power/vgmdownloader/blob/main/img/logo.png)


## About

This program uses web scraping with  [BeautifulSoap](https://beautiful-soup-4.readthedocs.io/en/latest/) to download OSTs (Original Sound Tracks) from [this site](https://downloads.khinsider.com).

## How to compile it

First of all you are going to need [Python](https://www.python.org/) and two depedencies, [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) for the web scrapping and [Requests](https://docs.python-requests.org/en/latest/user/install/#install) to help us with the HTTP requests.

```python
pip install beautifulsoup4
pip install requests
```

Now you're ready to run the program!

```python
python vgmdownloader.py
```


A little tip is to search the uncomplete name of the game or album you want to download, for example:
Search for **"Streets of"** and not the full game name like __"Streets of Rage"__. _(Trust me it will work better this way.)_

### Tips

Download a good music player, in my case I use [MusicBee](https://www.getmusicbee.com/).

![](https://github.com/V2power/vgmdownloader/blob/main/img/example.png)

Check out my YouTube playlist: [V2's Amazing OSTs Collection](https://www.youtube.com/playlist?list=PLCEnyc2Sz_q6FHjfDSATEsal-UvEjslo_).

I've choose only the best of the bests. There is some bangers in this collection, I hope you like it!

Now enjoy those old but awesome tracks! 😄

### To do list

   - Game search mechanism - ✅
   - Song download - ✅
   - Download with differents formats - ✅
   - Download the album image cover - ✅
   - Fix the duplicated download from the same song problem - ✅
   - Save the files in a different location - ✅
   - Fix the error when the folder already exists - ✅
   - Fix the error when there is no album cover to download - ❌
   - Visual Interface - ❌


### Info

This still a work in progress project. There is a lot of work to do, I'm doing this to practice my Python skills and to study about the art of web scraping.