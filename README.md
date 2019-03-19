# DeviantArt Scraper

This is my personal project created to download images from [DeviantArt](https://www.deviantart.com/) website. The program will download all highest resolution images, including `jpg`, `png`, `gif` ,`swf`, and `zip` file formats, from specified artists to specified download location, both of which can be edited in `info.json` file. In the download location, the program will create and name directories using the artist names, then download images to the corresponding directories. It stores update information for each artist, so it will only download new uploads.

The program retrieves request responses in chunks and uses threads to download images. The chunk size and the number of threads are declared at the beginning of the program; they can be edited based on your preference. The default values are `1 MB` chunk size and `24` threads. With this setting on my computer, I usually get around `8.5 MB/s` download speed.

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

I encountered 3 main difficulties in this project:

1. there are 2 ways to download an image: through download button URL or through the image URL. The former is preferred because it grabs the highest image quality. However, this has a small problem. The URL contains a token that turns invalid if certain actions are performed, such as refreshing the page, reopening the browser, and exceeding a certain time limit

    - Solution: use `session` to get or post all URLs

2. on the DeviantArt gallery website, you need to scroll to the bottom of the page to see all the contents

    - Solution 1: use `Selenium driver` to automate the scrolling action. This method works, but the execution time is too slow, especially for galleries containing hundreds of art works. The reasons for this are: 1. the driver itself is slow. 2. the driver needs to wait for the website's JavaScript to load whenever a scroll action is sent

    - Solution 2: send POST request to mimic the scrolling action. I found that whenever the website is revealing new contents during scrolling, there is always a POST request sent before anything. The request is for the scrolling action, which contains form data that can be found in the website page source, as well as values like `offset` and `limit` that control the relative position and the number of visible elements

3. bypass the age restriction

    - Solution 1: use `Selenium driver` to fill the age confirmation form. This time, the execution time is acceptable because the filling process is much faster. However, I want to avoid using the driver as much as possible

    - Solution 2: I found that DeviantArt uses cookies to save the age check result. So, by setting the `session.cookies` to the appropriate value, there will be no age check

## Todo

- refactor code

- add more functionality (e.g. ranking)