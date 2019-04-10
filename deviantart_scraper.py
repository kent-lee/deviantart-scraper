from multiprocessing.pool import ThreadPool
from functools import partial
from html import unescape
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import re
import json
import os


USER_FILE = "info.json"
THREADS = 24
MB_BYTES = 1048576
image_num = 0
total_size = 0


# get user info from json file
def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# update user info to json file
def write_json(user_info, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(user_info, f, indent=4, ensure_ascii=False)


def request(session, method, url, response="", headers={}, data={}, stream=False):
    if method == "GET":
        res = session.get(url, headers=headers, stream=stream)
    elif method == "POST":
        res = session.post(url, headers=headers, data=data)
    # check if request is successful
    res.raise_for_status()
    
    if response == "HTML":
        return unescape(res.text)
    elif response == "BINARY":
        return res.content
    elif response == "JSON":
        return res.json()
    else:
        return res


# create directory and name it using author name
def create_directory(download_location, author_name=""):
    dir_path = os.path.join(download_location, author_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


# get download url from image url html
def get_download_url(html, fail=False):
    # get download button url
    download_btn = re.search(r"data-download_url=\"(.*?)\"", html)
    if download_btn:
        return download_btn[1]
    # get direct image url with prefix /v1/fill/ inside
    direct_image = re.findall(r"<img collect_rid=\"1:\d+\" src=\"(.*?)\"", html)
    if direct_image and re.search("/v1/fill/", direct_image[1]):
        # only image quality is allowed to modify for new uploads
        if fail:
            return re.sub(r"q_\d+,strp", "q_100", direct_image[1])
        # set image properties. For more details, visit below link:
        # https://support.wixmp.com/en/article/image-service-3835799
        image_settings = "w_5100,h_5100,bl,q_100"
        direct_image = re.match(r"(.*?)\?token=", direct_image[1])[1]
        direct_image = re.sub("/f/", "/intermediary/f/", direct_image)
        direct_image = re.sub("/v1/fill/.*/", f"/v1/fill/{image_settings}/", direct_image)
        return direct_image
    # get direct image url with other prefixes like /f/ or https://img00
    else:
        return direct_image[1]


# get original file name from download url response
def get_file_name(response):
    # get name from the response of download button url
    if "Content-Disposition" in response.headers:
        file_name = response.headers["Content-Disposition"]
        return re.search(r"''(.*)", file_name)[1]
    # get name from response url with image settings
    if re.search("/v1/fill/", response.url):
        try:
            re.search(r"w_\d+,h_\d+,bl,q_100/(.*)", response.url)[1]
        except TypeError:
            re.search(r"w_\d+,h_\d+,q_100/(.*)", response.url)[1]
    # get name from response url without image settings
    try:
        return re.search(r".*wixmp.com/f/.*/(.*)\?token=", response.url)[1]
    # get name from response url that is not image (e.g. gif, swf)
    except TypeError:
        return re.match(r"https://.*/(.*)", response.url)[1]


# get the gallery info of an author
def get_gallery_info(session, author_id):
    url = f"https://www.deviantart.com/{author_id}/gallery/?catpath=/"
    html = request(session, "GET", url, "HTML")
    author_name = re.search(r"<title>(.*)'s .*</title>", html)[1]
    pattern = rf"\"(https://www.deviantart.com/{author_id}/art/.*?)\""
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
    author_id = gallery_info["author_id"]
    pattern = rf"\"(https://www.deviantart.com/{author_id}/art/.*?)\""

    if author_id in user_info["update_info"]:
        last_visit_url = user_info["update_info"][author_id]
    else:
        last_visit_url = ""
    user_info["update_info"][author_id] = gallery_info["newest_image_url"]

    # scroll to the bottom of the page
    while need_update:
        # mimic scrolling action request
        data = {
            "offset": str(offset),
            "limit": str(limit),
            "_csrf": gallery_info["csrf"],
            "dapilid": gallery_info["dapilid"]
        }
        html = request(session, "POST", gallery_info["url"], "HTML", data=data)
        found_urls = re.findall(pattern, html)
        found_urls, need_update = check_update(found_urls, last_visit_url)
        image_urls.extend(found_urls)
        offset += limit
    return image_urls


# download and save image to dir_path
def save_image(session, dir_path, url):
    html = request(session, "GET", url, "HTML")
    image_title = re.search(r"<title>(.*) by .*</title>", html)[1]
    try:
        download_url = get_download_url(html)
        res = request(session, "GET", download_url, stream=True)
    except requests.exceptions.HTTPError:
        download_url = get_download_url(html, True)
        res = request(session, "GET", download_url, stream=True)

    file_name = get_file_name(res)
    with open(os.path.join(dir_path, file_name), "wb") as f:
        for chunk in res.iter_content(chunk_size=MB_BYTES):
            f.write(chunk)
            global total_size
            total_size += len(chunk)
        global image_num
        image_num += 1
    print(f"download image: {image_title} ({file_name})")
    return file_name


# change file modification dates to allow sorting in File Explorer
def modify_files_dates(file_names, dir_path):
    current_time = time.time()
    # from oldest to newest
    file_names.reverse()
    for file_name in file_names:
        file_path = os.path.join(dir_path, file_name)
        os.utime(file_path, (current_time, current_time))
        current_time += 1


# download all images from a gallery url
def download_images(user_info, author_id):
    # declare session here to prevent remote host from closing connection
    session = requests.Session()
    # bypass age restriction check
    session.cookies["agegate_state"] = "1"
    # retry when exceed the max request number
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    gallery_info = get_gallery_info(session, author_id)
    if gallery_info is None:
        print(f"\nERROR: author id {author_id} does not exist\n")
        return
    author_name = gallery_info["author_name"]
    dir_path = create_directory(user_info["download_location"], author_name)

    print(f"download for author {author_name} begins\n")
    image_urls = get_image_urls(session, user_info, gallery_info)
    if not image_urls:
        print(f"author {author_name} is up-to-date\n")
        return
    # use all available cores if no arguments given
    with ThreadPool(THREADS) as pool:
        file_names = pool.map(partial(save_image, session, dir_path), image_urls)
    print(f"\ndownload for author {author_name} completed\n")

    modify_files_dates(file_names, dir_path)


def main():
    start_time = time.time()

    user_info = read_json(USER_FILE)
    print(f"\nthere are {len(user_info['author_ids'])} authors...\n")
    create_directory(user_info["download_location"])
    for id in user_info['author_ids']:
        download_images(user_info, id)
    write_json(user_info, USER_FILE)
    
    duration = time.time() - start_time
    size_mb = total_size / MB_BYTES
    print("\nSUMMARY")
    print("---------------------------------")
    print(f"time elapsed:\t{duration:.4f} seconds")
    print(f"total size:\t{size_mb:.4f} MB")
    print(f"total images:\t{image_num} images")
    print(f"download speed:\t{(size_mb / duration):.4f} MB/s")


if __name__ == "__main__":
    main()