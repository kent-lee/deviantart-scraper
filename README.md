# DeviantArt Scraper

This is my personal project created to download images from [DeviantArt](https://www.deviantart.com/) website. The program will download the highest resolution images and anything achieved in the download button from specified users to specified download directory. Note that this program only works for the new [DeviantArt Eclipse](https://www.deviantarteclipse.com/) design and is only tested on Windows 10.

![alt text](doc/download.gif?raw=true "download")

![alt text](doc/result.png?raw=true "result")

## Overview

For people who had used this program before - the format of the config file has changed and you will need to re-download everything due to the new update mechanism. I apologize for the inconvenience.

- the program is multi-threaded; the default number of threads is `your cpu cores * 3`. You can temporarily change the number via the command line interface, or permanently change the number via the source code (in `lib/deviantart.py` at line 13)
- each artwork filename is appended with its artwork ID at the end for update validation purpose. The program downloads artworks for a user from newest to oldest until an existing file is found on the disk
- downloaded artworks are categorized by user and ranking mode
- modification time of each artwork is set according to upload order such that you can sort files by modified date
- ranking will overwrites existing files

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install `requests` library

    ```bash
    pip install --user requests
    ```

3. edit `config.json` file in `data` folder manually or via command line interface

    - `save directory`: the save directory path
    - `users`: the username shown on website or in URL

## Usage

display help message

```bash
$ python main.py -h

usage: main.py [-h] [-f FILE] [-l] [-s SAVE_DIR] [-t THREADS]
               {artwork,ranking} ...

positional arguments:
  {artwork,ranking}
    artwork          download artworks from user IDs specified in "users"
                     field
    ranking          download top N ranking artworks based on given conditions

optional arguments:
  -h, --help         show this help message and exit
  -f FILE            load file for this instance (default: data\config.json)
  -l                 list current settings
  -s SAVE_DIR        set save directory path
  -t THREADS         set number of threads for this instance
```

display `artwork` help message

```bash
$ python main.py artwork -h

usage: main.py artwork [-h] [-a  [ID ...]] [-d all [ID ...]] [-c all [ID ...]]

optional arguments:
  -h, --help       show this help message and exit
  -a  [ID ...]     add user IDs
  -d all [ID ...]  delete user IDs and their directories
  -c all [ID ...]  clear directories of user IDs
```

display `ranking` help message

```bash
usage: main.py ranking [-h] [-order ORDER] [-type TYPE] [-content CONTENT]
                       [-category CATEGORY] [-n N]

optional arguments:
  -h, --help          show this help message and exit
  -order ORDER        orders: {whats-hot, undiscovered, most-recent,
                      popular-24-hours, popular-1-week, popular-1-month,
                      popular-all-time} (default: popular-1-week)
  -type TYPE          types: {visual-art, video, literature} (default: visual-
                      art)
  -content CONTENT    contents: {all, original-work, fan-art, resource,
                      tutorial, da-related} (default: all)
  -category CATEGORY  categories: {all, animation, artisan-crafts, tattoo-and-
                      body-art, design, digital-art, traditional, photography,
                      sculpture, street-art, mixed-media, poetry, prose,
                      screenplays-and-scripts, characters-and-settings,
                      action, adventure, abstract, comedy, drama, documentary,
                      horror, science-fiction, stock-and-effects, fantasy,
                      adoptables, events, memes, meta} (default: all)
  -n N                get top N artworks (default: 30)

```

download artworks from user IDs stored in config file; update users' artworks if directories already exist

```bash
python main.py artwork
```

download the top `30 (default)` artworks that are `popular-1-month`, of type `visual-art (default)`, of content `original-work`, and of category `digital-art`

```bash
python main.py ranking -order popular-1-month -content original-work -category digital-art
```

delete user IDs and their directories (IDs in `users` field + artwork directories), then download / update artworks for remaining IDs in config file

```bash
python main.py artwork -d wlop trungbui42
```

add user IDs then download / update bookmark artworks for newly added IDs + IDs in config file

```bash
python main.py artwork -a wlop trungbui42
```

use `temp.json` file in `data` folder as the config file (only for this instance), add user IDs to that file, then download / update artworks to directory specified in that file

```bash
python main.py artwork -f data/temp.json -a wlop trungbui42
```

clear directories for all user IDs in config file, set threads to 24, then download artworks (i.e. re-download artworks)

```bash
python main.py artwork -c all -t 24
```

## Challenges

1. there are two ways to download an image: (1) download button URL. (2) direct image URL. The former is preferred because it grabs the highest image quality and other file formats including `gif`, `swf`, `abr`, and `zip`. However, this has a small problem. The URL contains a token that turns invalid if certain actions are performed, such as refreshing the page, reopening the browser, and exceeding certain time limit

    - Solution: use `session` to `GET` or `POST` all URLs

2. for direct image URL, the image quality is much lower than the original upload (the resolution and size of the original upload can be found in the right sidebar). This is not the case few years ago when the original image was accessible through right click, but on 2017, [Wix](https://www.wix.com/) acquired DeviantArt, and has been migrating the images to their own image hosting system from the original DeviantArt system. They linked most of the direct images to a stripped-down version of the original images; hence the bad image quality. Below are the three different formats of direct image URLs I found:

      - URL with `/v1/fill` inside: this means that the image went through Wix's encoding system and is modified to a specific size and quality. There are two cases for this format:
        - **old uploads**: remove `?token=` and the following values, add `/intermediary` in front of `/f/` in the URL, and change the image settings right after `/v1/fill/` to `w_{width},h_{height},q_100`. The `width` and `height` used to have a maximum limit of `5100` where (1) the system results in `400 Bad Request` if exceeds the value, and (2) the original size will be returned if the required image is larger than the original. However, this has been changed recently. Now there is no input limit for the size, so you can request any dimension for the image, which may results in disproportional image if the given dimension is incorrect. In this case, I use the original resolution specified by the artist as the `width` and `height`
        - **new uploads**: the width and height of the image cannot be changed, but the quality can still be improved by replacing `(q_\d+,strp|strp)` with `q_100`

        Example: [original URL](https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/90b0cf78-3356-43b3-a7a2-8e6bf0e85ef1/dcbojon-68d45ef2-5ab7-408b-bf04-cf6d21aa16b5.jpg/v1/fill/w_1024,h_1280,q_70,strp/lantern_by_guweiz_dcbojon-fullview.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTI4MCIsInBhdGgiOiJcL2ZcLzkwYjBjZjc4LTMzNTYtNDNiMy1hN2EyLThlNmJmMGU4NWVmMVwvZGNib2pvbi02OGQ0NWVmMi01YWI3LTQwOGItYmYwNC1jZjZkMjFhYTE2YjUuanBnIiwid2lkdGgiOiI8PTEwMjQifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.-Gv_pRk6mqruJcBsg_kIpdAyRdWGzSzAI_YQT0Umh_A) vs [incorrect dimension URL](https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/intermediary/f/90b0cf78-3356-43b3-a7a2-8e6bf0e85ef1/dcbojon-68d45ef2-5ab7-408b-bf04-cf6d21aa16b5.jpg/v1/fill/w_5100,h_5100,q_100/lantern_by_guweiz_dcbojon-fullview.jpg) vs [modified URL](https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/intermediary/f/90b0cf78-3356-43b3-a7a2-8e6bf0e85ef1/dcbojon-68d45ef2-5ab7-408b-bf04-cf6d21aa16b5.jpg/v1/fill/w_2190,h_2738,q_100/lantern_by_guweiz_dcbojon-fullview.jpg). The original url has a file size of 153 KB and 1024x1280 resolution, while the modified URL has a file size of 4.64 MB and 2700×3375 resolution.

      - URL with `/f/` but not `/v1/fill`: this is the original image, so just download it

      - URL with `https://img\d{2}` or `https://pre\d{2}`: this means that the image went through DeviantArt's system and is modified to a specific size. I could not figure out how to get the original image from these types of links, i.e. find `https://orig\d{2}` from them, so I just download the image as is

3. DeviantArt randomizes the `div` and `class` elements in HTML in an attempt to prevent scrapping, so parsing plain HTML will not work

    - Solution: DeviantArt now uses XHR requests to send data between client and server, meaning one can simulate the requests to extract and parse data from the JSON response. The XHR requests and responses can be found in browsers' developer tools under Network tab. You can simply go to the request URL to see the response object

4. age restriction

    - Solution: I found that DeviantArt uses cookies to save the age check result. So, by setting the `session.cookies` to the appropriate value, there will be no age check

5. sometimes the `requests` module will close the program with errors `An existing connection was forcibly closed by the remote host` or `Max retries exceeded with url: (image url)`. I am not sure the exact cause, but it is most likely due to the high amount of requests sent from the same IP address in a short period of time; hence the server refuses the connection

    - Solution: use `HTTPAdapter` and `Retry` to retry `session.get` in case of `ConnectionError` exception

## Todo

- add more functionality (e.g. user bookmarks)

