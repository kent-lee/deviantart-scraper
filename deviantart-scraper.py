from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from html import unescape
import time
import requests
import re
import json
import os


def get_json(file_path):
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def get_unescape_html(session, url):
    response = session.get(url)
    if response.status_code != 200:
        return None
    return unescape(response.text)


def get_image_title(html):
    return re.search(r"<title>(.*) by .*</title>", html)[1]


def get_author_name(html):
    return re.search(r"<title>(.*)'s .*</title>", html)[1]


def create_directory(author_name, download_location):
    directory_path = download_location + "\\" + author_name
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return directory_path


def get_download_url(html):
    # get download button url
    try:
        image_url = re.search(r"data-download_url=\"(.*?)\"", html)[1]
        return re.sub(";", "&", image_url)
    # get enlarged image url
    except TypeError:
        try:
            return re.findall(r"<img collect_rid=\"1:\d+\" src=\"(.*?)\"", html)[1]
        except IndexError:
            return None


def get_file_name(response):
    # get name from the response of download button url
    try:
        file_name = response.headers['Content-Disposition']
        return re.search(r"''(.*)", file_name)[1]
    except KeyError:
        # get name from the response of enlarged image url
        try:
            return re.search(r".*wixmp.com/f/.*/(.*)\?token=", response.url)[1]
        # for url that is not image (e.g. gif, swf)
        except TypeError:
            return re.match(r"https://.*/(.*)", response.url)[1]


def get_driver():
    options = Options()
    # let Chrome run in the background
    options.headless = True
    # set log level to highest
    options.add_argument("log-level=3")
    return webdriver.Chrome(options=options)


def get_thumb_urls(session, author_id, url):
    html = get_unescape_html(session, url)
    offset = 0
    limit = 24
    pattern = r"href=\"(https://www.deviantart.com/" + author_id + r"/art/.*?)\""
    csrf = re.search(r"\"csrf\":\"(.*?)\"", html)[1]
    dapilid = re.search(r"\"requestid\":\"(.*?)\"", html)[1]
    
    while True:
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
        yield list(dict.fromkeys(found_urls))


def pass_age_gate(url):
    driver = get_driver()
    driver.get(url)

    driver.find_element_by_id("month").send_keys("01")
    driver.find_element_by_id("day").send_keys("01")
    driver.find_element_by_id("year").send_keys("1991")
    driver.find_element_by_class_name("tos-label").click()
    driver.find_element_by_class_name("submitbutton").click()
    time.sleep(1)

    image_url = get_download_url(driver.page_source)
    cookies = driver.get_cookies()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"])
    response = session.get(image_url)
    driver.quit()
    return response


def download_images(session, author_id, download_location):
    gallery_url = "https://www.deviantart.com/" + author_id + "/gallery/?catpath=/"
    gallery_html = get_unescape_html(session, gallery_url)
    if gallery_html is None:
        print("\nERROR: author id %s does not exist\n" % author_id)
        return
    author_name = get_author_name(gallery_html)
    directory_path = create_directory(author_name, download_location)

    print("\ndownload for author %s begins\n" %  author_name)
    for image_urls in get_thumb_urls(session, author_id, gallery_url):
        for url in image_urls:
            html = get_unescape_html(session, url)
            image_title = get_image_title(html)
            download_url = get_download_url(html)
            # if there is age restriction download_url cannot be found
            if download_url is None:
                response = pass_age_gate(url)
            else:
                response = session.get(download_url)

            file_name = get_file_name(response)
            file_path = directory_path + "\\" + file_name
            if os.path.isfile(file_path):
                print("author %s is up-to-date\n" % author_name)
                return
            print("download image: %s (%s)" % (image_title, file_name))
            with open(file_path, "wb") as f:
                f.write(response.content)
    print("\ndownload for author %s completed\n" % author_name)


def main():
    info = get_json("info.json")
    session = requests.Session()
    print("there are %d authors..." % len(info["author_ids"]))
    for id in info["author_ids"]:
        download_images(session, id, info["download_location"])


if __name__ == "__main__":
    main()