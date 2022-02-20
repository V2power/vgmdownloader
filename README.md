### Features

- Download entire game music albums;
-  .mp3 and .flac formats;
- Search mechanism to find your exact game.

# VGMDownloader

![](https://github.com/V2power/vgmdownloader/blob/main/img/logo.png)


## About

This program uses web scraping with  [BeautifulSoap](https://beautiful-soup-4.readthedocs.io/en/latest/) to download OSTs (Original Sound Tracks) from [this site](https://downloads.khinsider.com).

## How to use it

First of all you are going to need [Python](https://www.python.org/) and two depedencies, [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) for the web scrapping and [urllib](https://pypi.org/project/urllib3/) to help us with the HTTP client.

```python
pip install beautifulsoup4
pip install urllib3
```
After installing those dependencies, you will need to change the **parent_dir** variable to the location that you want the files to be downloaded.

```python
parent_dir = "D:/Music/" # In my case the Music folder on my secondary drive.
# Please use "/" and avoid putting "C:\Music\".
```

Now that you're ready to run the program!

```python
python vgmdownloader.py
```


A little tip is to search the uncomplete name of the game or album you want to download, for example:
Search for **"Streets of"** and not the full game name like __"Streets of Rage"__. _(Trust me it will work better this way.)_

### Tips

Download a good music player, in my case I use [MusicBee](https://www.getmusicbee.com/)
![](https://github.com/V2power/vgmdownloader/blob/main/img/example.png)
Now you can enjoy those awesome tracks!

### To do list

   - Game search mechanism - ✅
   - Song download - ✅
   - Download with differents formats - ✅
   - Download the album image cover - ❌
   - Visual Interface - ❌
   - Save the files in a different location - ❌
   - Fix the duplicated download from the same song problem - ✅


### Info

This still a work in progress project. There is a lot of work to do, I'm doing this to practice my Python skills and to study about the art of web scraping.