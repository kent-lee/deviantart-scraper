from multiprocessing.pool import ThreadPool
from functools import partial
from html import unescape
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import timeit
import re
import json
import os


USER_FILE = "info.json"
THREADS = 24
image_num = 0
total_size = 0


# get user info from json file
def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# update user info to json file
def update_json(user_info, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(user_info, f, indent=4, ensure_ascii=False)


# get url response and return its html text
def get_unescape_html(session, url):
    response = session.get(url)
    if response.status_code != 200:
        return None
    return unescape(response.text)


# create directory and name it using author name
def create_directory(author_name, download_location):
    dir_path = download_location + "\\" + author_name
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


# get download url from image url html
def get_download_url(html):
    # get download button url
    try:
        return re.search(r"data-download_url=\"(.*?)\"", html)[1]
    # get enlarged image url
    except TypeError:
        return re.findall(r"<img collect_rid=\"1:\d+\" src=\"(.*?)\"", html)[1]


# get original file name from download url response
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


# get the gallery info of an author
def get_gallery_info(session, author_id):
    url = "https://www.deviantart.com/" + author_id + "/gallery/?catpath=/"
    html = get_unescape_html(session, url)
    if html is None:
        return None
    author_name = re.search(r"<title>(.*)'s .*</title>", html)[1]
    pattern = r"\"(https://www.deviantart.com/%s/art/.*?)\"" % author_id
    newest_image_url = re.search(pattern, html)[1]
    csrf = re.search(r"\"csrf\":\"(.*?)\"", html)[1]
    dapilid = re.search(r"\"requestid\":\"(.*?)\"", html)[1]
    data = {
        "url": url,
        "author_id": author_id,
        "author_name": author_name,
        "newest_image_url": newest_image_url,
        "csrf": csrf,
        "dapilid": dapilid
    }
    return data


# flag update and return urls up to last_visit_url in found_urls
def check_update(found_urls, last_visit_url):
    urls = list(dict.fromkeys(found_urls))
    # find index of first matched element
    index = next((i for i, url in enumerate(urls) if url == last_visit_url), None)
    if (not urls) or (index is not None):
        return urls[:index], False
    else:
        return urls, True


# get all unvisited thumbnail image urls from a gallery
def get_image_urls(session, user_info, gallery_info):
    need_update = True
    image_urls = []
    offset = 0
    limit = 24
    pattern = r"\"(https://www.deviantart.com/%s/art/.*?)\"" % gallery_info["author_id"]
    author_id = gallery_info["author_id"]
    newest_image_url = gallery_info["newest_image_url"]

    if author_id not in user_info["update_info"]:
        last_visit_url = ""
    else:
        last_visit_url = user_info["update_info"][author_id]
    user_info["update_info"][author_id] = newest_image_url

    # scroll to the bottom of the page
    while need_update:
        # mimic scrolling action request
        data = {
            "offset": str(offset),
            "limit": str(limit),
            "_csrf": gallery_info["csrf"],
            "dapilid": gallery_info["dapilid"]
        }
        response = session.post(gallery_info["url"], data=data)
        found_urls = re.findall(pattern, unescape(response.text))
        found_urls, need_update = check_update(found_urls, last_visit_url)
        image_urls.extend(found_urls)
        offset += limit
    return image_urls


# download and save image to dir_path
def save_image(session, dir_path, url):
    html = get_unescape_html(session, url)
    image_title = re.search(r"<title>(.*) by .*</title>", html)[1]
    download_url = get_download_url(html)
    response = session.get(download_url)
    file_name = get_file_name(response)
    file_path = dir_path + "\\" + file_name
    print("download image: %s (%s)" % (image_title, file_name))
    global image_num
    image_num += 1
    with open(file_path, "wb") as f:
        f.write(response.content)
        global total_size
        total_size += len(response.content)


# download all images from a gallery url
def download_images(session, user_info, id):
    gallery_info = get_gallery_info(session, id)
    if gallery_info is None:
        print("\nERROR: author id %s does not exist\n" % id)
        return
    author_name = gallery_info["author_name"]
    dir_path = create_directory(author_name, user_info["download_location"])

    print("download for author %s begins\n" % author_name)
    image_urls = get_image_urls(session, user_info, gallery_info)
    if not image_urls:
        print("author %s is up-to-date\n" % author_name)
        return
    # use all available cores, otherwise specify the number as an argument
    with ThreadPool(THREADS) as pool:
        pool.map(partial(save_image, session, dir_path), image_urls)
    print("\ndownload for author %s completed\n" % author_name)


def main():
    start_time = timeit.default_timer()
    # need session for the download button to work
    session = requests.Session()
    # bypass age restriction check
    session.cookies["agegate_state"] = "1"
    # retry when exceed the max request number
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    user_info = read_json(USER_FILE)
    print("\nthere are %d authors...\n" % len(user_info["author_ids"]))
    for id in user_info["author_ids"]:
        download_images(session, user_info, id)
    update_json(user_info, USER_FILE)
    
    duration = timeit.default_timer() - start_time
    size_mb = total_size / 1048576
    print("\nSUMMARY")
    print("---------------------------------")
    print("time elapsed:\t%.4f seconds" % duration)
    print("total size:\t%.4f MB" % size_mb)
    print("total images:\t%d images" % image_num)
    print("download speed:\t%.4f MB/s" % (size_mb / duration))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()