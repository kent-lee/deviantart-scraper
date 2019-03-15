# DeviantArt Scraper

This is my personal project created to download images from [DeviantArt](https://www.deviantart.com/) website. The program will download all original images, including `jpg`, `png`, `gif` and `swf` file formats, from specified artists to specified download location, both of which can be edited in `info.json` file. In the download location, the program will create and name directories using the artist names, then download images to the corresponding directories. It checks on artist new uploads, so it will only download new images if the directory already exists.

![alt text](doc/result.png?raw=true "result")

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install `requests` library

        pip install --user requests

3. edit `info.json` file

4. go to root directory and run the program

        python pixiv-scraper.py

## Notes

I encountered 3 main difficulties in this project:

1. there are 2 ways to download an image: through download button URL or through the image URL. The former is preferred because it grabs the highest image quality. However, this has a small problem. The URL contains a token that turns invalid if certain actions are performed, such as refreshing the page, reopening the browser, and exceeding a certain time limit

    - Solution: use `session` to get or post all URLs

2. on the DeviantArt gallery website, you need to scroll to the bottom of the page to see all the contents

    - Solution 1: use `Selenium driver` to automate the scrolling action. I tried this initially, as it was the most popular method on Stack Overflow. The result, however, was not satisfying. The program execution time was too slow, especially for galleries containing hundreds of art works, due to 2 main reasons: 1. the driver itself was slow. 2. the driver needed to wait for the website's JavaScript to load whenever a scroll action was sent

    - Solution 2: send POST request to mimic the scrolling action. I found that whenever the website was revealing new contents during scrolling, there was always a POST request sent before anything. The request was for the scrolling action, which contained form data that can be found in the website page source, as well as values like `offset` that indicate the relative position and the number of visible elements

3. bypass the age restriction

    - Solution 1: use `Selenium driver` to fill the age confirmation form. This time, the execution time was acceptable because the filling process was much faster. However, I wanted to avoid using the driver as much as possible

    - Solution 2: I found that DeviantArt used cookies to save the age check result. So, by setting the `session.cookies` to the appropriate value, there would be no age check

## Todo

- refactor code

- add more functionality (e.g. ranking)

- use threads to make the download process faster