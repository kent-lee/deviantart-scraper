# DeviantArt Scraper

This is my personal project created to download images from [DeviantArt](https://www.deviantart.com/) website. The program will grab the highest resolution images and anything achieved in the download button from specified artists to specified download directory. In the download directory, the program will create and name subdirectories using the artist names, then save artworks to the corresponding subdirectories. For each artwork, the file modification time are set in order from newest to oldest, such that you can sort files by modified date. Lastly, the update information is stored for each artist, so the program will only download new uploads.

![alt text](doc/download.gif?raw=true "download")

![alt text](doc/result.png?raw=true "result")

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install `requests` library

    ```bash
    pip install --user requests
    ```

3. edit `config.json` file in `data` folder manually or via command line interface

    - `artists`: the artist name shown in URL
    - `save_directory`: the save directory path

## Usage

display help message

```bash
$ python main.py -h

usage: main.py [-h] [-f FILE] [-l] [-s SAVE_DIR] [-a  [ID ...]]
               [-d all [ID ...]] [-c all [ID ...]] [-t THREADS] [-r]

optional arguments:
  -h, --help       show this help message and exit
  -f FILE          set config file
  -l               list current settings
  -s SAVE_DIR      set save directory path
  -a  [ID ...]     add artist ids
  -d all [ID ...]  delete artist ids and their directories
  -c all [ID ...]  clear artists update info and their directories
  -t THREADS       set the number of threads
  -r               run program

```

run the program with current configuration (i.e. update artists' artworks)

```bash
python main.py
```

add artist IDs then run the program

```bash
python main.py -a wlop trungbui42 -r
```

load `temp.json` file in `data` folder then add artist IDs. Note that `temp.json` is only used for this instance and is not a replacement for the default `config.json` file

```bash
python main.py -f data/temp.json -a wlop trungbui42
```

clear update information (i.e. re-download artworks), set threads to 24, then run the program

```bash
python main.py -c all -t 24 -r
```


## Challenges

1. there are two ways to download an image: (1) download button URL. (2) direct image URL. The former is preferred because it grabs the highest image quality and other file formats including `gif`, `swf`, `abr`, and `zip`. However, this has a small problem. The URL contains a token that turns invalid if certain actions are performed, such as refreshing the page, reopening the browser, and exceeding certain time limit

    - Solution: use `session` to `GET` or `POST` all URLs

2. for direct image URL, the image quality is much lower than the original upload (the resolution and size of the original upload can be found in the right sidebar). This is not the case few years ago when the original image was accessible through right click, but on 2017, [Wix](https://www.wix.com/) acquired DeviantArt, and has been migrating the images to their own image hosting system from the original DeviantArt system. They linked most of the direct images to a stripped-down version of the original images; hence the bad image quality. Below are the three different formats of direct image URLs I found:

      - URL with `/v1/fill` inside: this means that the image went through Wix's encoding system and is modified to a specific size and quality. In this case, you remove `?token=` and its values, add `/intermediary` in front of `/f/` in the URL, and change the image settings right after `/v1/fill/` to `w_5100,h_5100,bl,q_100`. The definitions of the values can be found in [Wix's Image Service](https://support.wixmp.com/en/article/image-service-3835799), but basically, `w_5100,h_5100` requests the width and height of the image to be 5100x5100 pixels, `bl` requires the baseline JPEG version, and `q_100` sets the quality to 100% of the original. The reasons to have this dimension are: (1) 5100 pixels is the limit of the system; anything above it will result in `400 Bad Request`. (2) according to the Wix's API:

        > In case the required image is larger than the original, upscale should be enabled (lg_1) in order for a proportional upscale to be applied. If upscale is not enabled, **the returned image will maintain the original size**.

        Example: [original URL](https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/90b0cf78-3356-43b3-a7a2-8e6bf0e85ef1/dcbojon-68d45ef2-5ab7-408b-bf04-cf6d21aa16b5.jpg/v1/fill/w_1024,h_1280,q_70,strp/lantern_by_guweiz_dcbojon-fullview.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTI4MCIsInBhdGgiOiJcL2ZcLzkwYjBjZjc4LTMzNTYtNDNiMy1hN2EyLThlNmJmMGU4NWVmMVwvZGNib2pvbi02OGQ0NWVmMi01YWI3LTQwOGItYmYwNC1jZjZkMjFhYTE2YjUuanBnIiwid2lkdGgiOiI8PTEwMjQifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.-Gv_pRk6mqruJcBsg_kIpdAyRdWGzSzAI_YQT0Umh_A) vs [modified URL](https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/intermediary/f/90b0cf78-3356-43b3-a7a2-8e6bf0e85ef1/dcbojon-68d45ef2-5ab7-408b-bf04-cf6d21aa16b5.jpg/v1/fill/w_5100,h_5100,bl,q_100/lantern_by_guweiz_dcbojon-fullview.jpg). The original url has a file size of 153 KB and 1024x1280 resolution, while the modified URL has a file size of 2.03 MB and 2190x2738 resolution. The result is still not as good as the [original upload](https://www.deviantart.com/guweiz/art/Lantern-745215143) (4.2 MB and 2700×3375 resolution), but this is the closest I can get

        **UPDATE**: for new uploads, this trick no longer works. However, the image quality can still be changed. To do this, you keep everything in the image URL the same and change the part `q_\d+,strp` to `q_100`

      - URL with `/f/` but no `/v1/fill` inside: this is the original image, so just download it

      - URL with `https://img\d{2}` or `https://pre\d{2}`: this means that the image went through DeviantArt's system and is modified to a specific size. I could not figure out how to get the original image from these types of links, i.e. find `https://orig\d{2}` from them, so I just download the image as is

3. on the DeviantArt gallery website, you need to scroll to the bottom of the page to see all the contents

    - Solution 1: use `Selenium` with [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) to automate the scrolling action. This method works, but the execution time is too slow, especially for galleries containing hundreds of art works. The reasons for this are: (1) the driver itself is slow. (2) the driver needs to wait for the website's JavaScript to load whenever a scroll action is sent

    - Solution 2: send `POST` request to mimic the scrolling action. I found that whenever the website is revealing new contents during scrolling, there is always a `POST` request sent before anything. The request is for the scrolling action, and the form data can be found in the website page source

4. bypass the age restriction

    - Solution 1: use `Selenium` with [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) to fill the age confirmation form. This time, the execution time is acceptable because the filling process is much faster. However, I want to avoid using the driver as much as possible

    - Solution 2: I found that DeviantArt uses cookies to save the age check result. So, by setting the `session.cookies` to the appropriate value, there will be no age check

5. sometimes the `requests` module will close the program with errors `An existing connection was forcibly closed by the remote host` or `Max retries exceeded with url: (image url)`. I am not sure the exact cause, but it is most likely due to the high amount of requests sent from the same IP address in a short period of time; hence the server refuses the connection

    - Solution: use `HTTPAdapter` and `Retry` to retry `session.get` in case of `ConnectionError` exception

6. update mechanism

    - Attempt 1: download artworks from newest to oldest until an existing file is found on the disk. This does not work well with the multi-threading implementation, as it makes the program a lot more complicated in order to deal with thread stopping condition

    - Solution: record the last visited artwork information for each artist to check if update is needed. This does not work if the newest upload was deleted by the artist, as the stored information cannot be found in the retrieved HTML. One solution is to record a list of all downloaded artwork information for each artist, then compare it with the parsed data, but this wastes a lot of unnecessary space and memory

## Todo

- add more functionality (e.g. ranking)
