import multiprocessing
from multiprocessing.pool import ThreadPool
from functools import partial
from html import unescape
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os, re
from lib import utils

class DeviantArtAPI:

    threads = multiprocessing.cpu_count() * 3
    download_chunk_size = 1048576

    def __init__(self):
        self.session = requests.Session()
        # bypass age restriction check
        self.session.cookies["agegate_state"] = "1"
        # retry when exceed the max request number
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

    def request(self, method, url, **kwargs):
        if method == "GET":
            res = self.session.get(url, **kwargs)
        elif method == "POST":
            res = self.session.post(url, **kwargs)
        res.raise_for_status()
        return res

    def gallery(self, artist_id):
        url = f"https://www.deviantart.com/{artist_id}/gallery/?catpath=/"
        res = self.request("GET", url)
        html = unescape(res.text)
        data = {
            "url": url,
            "artist_id": artist_id,
            "artist_name": re.search(r"<title>(.*)'s .*</title>", html)[1],
            "latest_upload": re.search(rf"\"(https://www.deviantart.com/{artist_id}/art/.*?)\"", html)[1],
            "url_pattern": rf"\"(https://www.deviantart.com/{artist_id}/art/.+?)\"",
            "csrf": re.search(r"\"csrf\":\"(.*?)\"", html)[1]
        }
        return data

    def _scroll(self, gallery, offset, stop):
        data = {
            "offset": str(offset),
            "limit": "24",
            "_csrf": gallery["csrf"]
        }
        res = self.request("POST", gallery["url"], data=data)
        html = unescape(res.text)
        urls = re.findall(gallery["url_pattern"], html)
        urls = list(dict.fromkeys(urls))
        index = None
        if isinstance(stop, str):
            index = utils.first_index(urls, lambda v: v == stop)
        elif isinstance(stop, int) and stop - offset < 24:
            index = stop - offset
        return (urls[:index], False) if not urls or index is not None else (urls, True)

    def artist_artworks(self, artist_id, stop=None):
        gallery = self.gallery(artist_id)
        if isinstance(stop, str) and stop == gallery["latest_upload"]:
            return []
        artwork_urls = []
        offset = 0
        need_update = True
        while need_update:
            urls, need_update = self._scroll(gallery, offset, stop)
            artwork_urls.extend(urls)
            offset += 24
        return artwork_urls

    def download_url(self, artwork_html, retry=False):
        # download button url
        direct_download = re.search(r"data-download_url=\"(.*?)\"", artwork_html)
        if direct_download:
            return direct_download[1]
        # direct image url with prefix /v1/fill/ inside
        direct_image = re.findall(r"<img collect_rid=\"1:\d+\" src=\"(.*?)\"", artwork_html)
        if direct_image and "/v1/fill/" in direct_image[1]:
            # only image quality is allowed to modify for new uploads
            if retry:
                return re.sub(r"q_\d+,strp", "bl,q_100", direct_image[1])
            # set image properties. For more details, visit below link:
            # https://support.wixmp.com/en/article/image-service-3835799
            image_settings = "w_5100,h_5100,bl,q_100"
            direct_image = re.match(r"(.*?)\?token=", direct_image[1])[1]
            direct_image = re.sub("/f/", "/intermediary/f/", direct_image)
            direct_image = re.sub("/v1/fill/.*/", f"/v1/fill/{image_settings}/", direct_image)
            return direct_image
        # direct image url with other prefixes like /f/ or https://img00
        else:
            return direct_image[1]

    def file_name(self, response):
        # get name from the response of download button url
        if "Content-Disposition" in response.headers:
            file_name = response.headers["Content-Disposition"]
            return re.search(r"''(.*)", file_name)[1]
        # get name from response url with image settings
        if "/v1/fill/" in response.url:
            return re.search(r"w_\d+,h_\d+,bl,q_100/(.*?)($|\?token=.*)", response.url)[1]
        # get name from response url without image settings
        try:
            return re.search(r".*wixmp.com/f/.*/(.*)\?token=", response.url)[1]
        # get name from response url that is not image (e.g. gif, swf)
        except TypeError:
            return re.match(r"https://.*/(.*)", response.url)[1]

    def save_artwork(self, dir_path, artwork_url):
        file = {
            "title": [],
            "url": [],
            "name": [],
            "count": 0,
            "size": 0
        }
        res = self.request("GET", artwork_url)
        file["url"].append(res.url)
        html = unescape(res.text)
        image_title = re.search(r"<title>(.*) by .*</title>", html)[1]
        file["title"].append(image_title)
        try:
            download_url = self.download_url(html)
            res = self.request("GET", download_url, stream=True)
        except requests.exceptions.HTTPError:
            download_url = self.download_url(html, True)
            res = self.request("GET", download_url, stream=True)
        file_name = self.file_name(res)
        file["name"].append(file_name)
        with open(os.path.join(dir_path, file_name), "wb") as f:
            for chunk in res.iter_content(chunk_size=self.download_chunk_size):
                f.write(chunk)
                file["size"] += len(chunk)
            file["count"] += 1
        print(f"download image: {image_title} ({file_name})")
        return file

    def save_artist(self, artist_id, dir_path, stop=None):
        gallery = self.gallery(artist_id)
        artist_name = gallery["artist_name"]
        print(f"download for author {artist_name} begins\n")
        dir_path = utils.make_dir(dir_path, artist_name)
        artwork_urls = self.artist_artworks(artist_id, stop)
        if not artwork_urls:
            print(f"author {artist_name} is up-to-date\n")
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artwork_urls)
        print(f"\ndownload for author {artist_name} completed\n")
        combined_files = utils.counter(files)
        utils.set_files_mtime(combined_files["name"], dir_path)
        return combined_files