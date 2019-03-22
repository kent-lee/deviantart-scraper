# DeviantArt Scraper

This is my personal project created to download images from [DeviantArt](https://www.deviantart.com/) website. The program will grab the highest resolution images and anything achieved in the download button from specified artists to specified download location, both of which can be edited in `info.json` file. In the download location, the program will create and name directories using the artist names, then download images to the corresponding directories. It stores update information for each artist, so it will only download new uploads.

The program uses threads to download images. The number of threads is declared at the beginning of the program; it can be edited based on your preference. With the default value of `24` threads, I am getting around `8 MB/s` download speed.

![alt text](doc/download.gif?raw=true "download")

![alt text](doc/result.png?raw=true "result")

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install `requests` library

        pip install --user requests

3. edit `info.json` file. Ignore field `update_info` as it is filled by the program for tracking update. Only edit `download_location` and `author_id`

4. go to root directory and run the program

        python pixiv-scraper.py

## Challenges

1. there are two ways to download an image: through download button URL or through the image URL. The former is preferred because it grabs the highest image quality and other file formats including `jpg`, `png`, `gif`, `swf`, `abr`, and `zip`. However, this has a small problem. The URL contains a token that turns invalid if certain actions are performed, such as refreshing the page, reopening the browser, and exceeding a certain time limit

    - Solution: use `session` to get or post all URLs

2. on the DeviantArt gallery website, you need to scroll to the bottom of the page to see all the contents

    - Solution 1: use `Selenium driver` to automate the scrolling action. This method works, but the execution time is too slow, especially for galleries containing hundreds of art works. The reasons for this are: 1. the driver itself is slow. 2. the driver needs to wait for the website's JavaScript to load whenever a scroll action is sent

    - Solution 2: send POST request to mimic the scrolling action. I found that whenever the website is revealing new contents during scrolling, there is always a POST request sent before anything. The request is for the scrolling action, and the form data can be found in the website page source

3. bypass the age restriction

    - Solution 1: use `Selenium driver` to fill the age confirmation form. This time, the execution time is acceptable because the filling process is much faster. However, I want to avoid using the driver as much as possible

    - Solution 2: I found that DeviantArt uses cookies to save the age check result. So, by setting the `session.cookies` to the appropriate value, there will be no age check

4. unstable connection

    - sometimes the requests module will close the program with the error: `connection forcibly closed by remote host`. I am not sure the exact cause, but it is most likely due to the high amount of data being transferred in a short period of time

    - Solution: use different `session` for each artist instead of using the same one for all

## Todo

- refactor code

- add more functionality (e.g. ranking)