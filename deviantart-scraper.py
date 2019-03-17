from multiprocessing import Pool
from functools import partial
from html import unescape
import requests
import re
import json
import os


# read json file from file path
def get_json(file_path):
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


# get url response and return its html text
def get_unescape_html(session, url):
    response = session.get(url)
    if response.status_code != 200:
        return None
    return unescape(response.text)


# get image title from image url html
def get_image_title(html):
    return re.search(r"<title>(.*) by .*</title>", html)[1]


# get author name from image url html
def get_author_name(html):
    return re.search(r"<title>(.*)'s .*</title>", html)[1]


# create directory and name it using author name
def create_directory(author_name):
    download_location = get_json("info.json")["download_location"]
    directory_path = download_location + "\\" + author_name
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return directory_path


# get download url from image url html
def get_download_url(html):
    # get download button url
    try:
        return re.search(r"data-download_url=\"(.*?)\"", html)[1]
    # get enlarged image url
    except TypeError:
        return re.findall(r"<img collect_rid=\"1:\d+\" src=\"(.*?)\"", html)[1]


# get file name from download url response
def get_file_name(response):
    # get name from the response of download button url
    try:
        file_name = response.headers['Content-Disposition']
        return re.search(r"''(.*)", file_name)[1]
    except KeyError:
        # get name from the response of enlarged image url
        try:
            return re.search(r".*wixmp.com/f/.*/(.*)\?token=", response.url)[1]
        # get name from url that is not image (e.g. gif, swf)
        except TypeError:
            return re.match(r"https://.*/(.*)", response.url)[1]


# get all thumbnail image urls from a gallery url
def get_thumb_urls(session, author_id, url):
    html = get_unescape_html(session, url)
    offset = 0
    limit = 24
    pattern = r"href=\"(https://www.deviantart.com/" + author_id + r"/art/.*?)\""
    csrf = re.search(r"\"csrf\":\"(.*?)\"", html)[1]
    dapilid = re.search(r"\"requestid\":\"(.*?)\"", html)[1]
    
    # scroll to the bottom of the page
    while True:
        # mimic scrolling action request
        data = {
            "offset": str(offset),
            "limit": str(limit),
            "_csrf": csrf,
            "dapilid": dapilid
        }
        response = session.post(url, data=data)
        found_urls = re.findall(pattern, unescape(response.text))
        if not found_urls:
            break
        offset += limit
        # return n urls at a time (n = limit)
        yield list(dict.fromkeys(found_urls))


# download all images from a gallery url
def download_images(session, author_id):
    gallery_url = "https://www.deviantart.com/" + author_id + "/gallery/?catpath=/"
    gallery_html = get_unescape_html(session, gallery_url)
    if gallery_html is None:
        print("\nERROR: author id %s does not exist\n" % author_id)
        return
    author_name = get_author_name(gallery_html)
    directory_path = create_directory(author_name)

    # process urls by chunks to improve execution time and memory consumption
    for image_urls in get_thumb_urls(session, author_id, gallery_url):
        for url in image_urls:
            html = get_unescape_html(session, url)
            image_title = get_image_title(html)
            download_url = get_download_url(html)
            response = session.get(download_url)
            file_name = get_file_name(response)
            file_path = directory_path + "\\" + file_name
            if os.path.isfile(file_path):
                print("\nauthor %s is up-to-date\n" % author_name)
                return
            print("download image: %s (%s)" % (image_title, file_name))
            with open(file_path, "wb") as f:
                f.write(response.content)


def main():
    author_ids = get_json("info.json")["author_ids"]
    # need session for the download button to work
    session = requests.Session()
    # bypass age restriction check
    session.cookies["agegate_state"] = "1"
    print("\nthere are %d authors...\n" % len(author_ids))
    # use all available cores, otherwise specify the number as an argument
    with Pool() as pool:
        pool.map(partial(download_images, session), author_ids)


if __name__ == "__main__":
    main()