import multiprocessing
from multiprocessing.pool import ThreadPool
from functools import partial
from html import unescape
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os, re

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
        artist_name = re.search(r"<title>(.*)'s .*</title>", html)[1]
        latest_artwork = re.search(rf"\"(https://www.deviantart.com/{artist_id}/art/.*?)\"", html)[1]
        csrf = re.search(r"\"csrf\":\"(.*?)\"", html)[1]
        dapilid = re.search(r"\"requestid\":\"(.*?)\"", html)[1]
        data = {
            "url": url,
            "artist_id": artist_id,
            "artist_name": artist_name,
            "latest_artwork": latest_artwork,
            "csrf": csrf,
            "dapilid": dapilid
        }
        return data

    def _update(self, found_urls, offset, stop):
        # remove duplicates
        found_urls = list(dict.fromkeys(found_urls))
        index = None
        if isinstance(stop, str):
            index = next((i for i,v in enumerate(found_urls) if v == stop), None)
        elif isinstance(stop, int) and stop - offset < 24:
            index = stop - offset
        return (found_urls[:index], False) if index is not None or not found_urls else (found_urls, True)

    def artist_artworks(self, artist_id, start=1, stop=None):
        gallery = self.gallery(artist_id)
        offset = start - 1 if isinstance(start, int) else 0
        limit = 24
        pattern = rf"\"(https://www.deviantart.com/{artist_id}/art/.*?)\""
        artwork_urls = []
        need_update = True

        while need_update:
            # simulate scrolling action request
            data = {
                "offset": str(offset),
                "limit": str(limit),
                "_csrf": gallery["csrf"],
                "dapilid": gallery["dapilid"]
            }
            res = self.request("POST", gallery["url"], data=data)
            html = unescape(res.text)
            found_urls = re.findall(pattern, html)
            found_urls, need_update = self._update(found_urls, offset, stop)
            artwork_urls.extend(found_urls)
            offset += limit
        start = artwork_urls.index(start) if isinstance(start, str) else start - 1
        return artwork_urls[start:]

    def download_url(self, artwork_html, retry=False):
        # download button url
        direct_download = re.search(r"data-download_url=\"(.*?)\"", artwork_html)
        if direct_download:
            return direct_download[1]
        # direct image url with prefix /v1/fill/ inside
        direct_image = re.findall(r"<img collect_rid=\"1:\d+\" src=\"(.*?)\"", artwork_html)
        if direct_image and re.search("/v1/fill/", direct_image[1]):
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
        if re.search("/v1/fill/", response.url):
            return re.search(r"w_\d+,h_\d+,bl,q_100/(.*?)($|\?token=.*)", response.url)[1]
        # get name from response url without image settings
        try:
            return re.search(r".*wixmp.com/f/.*/(.*)\?token=", response.url)[1]
        # get name from response url that is not image (e.g. gif, swf)
        except TypeError:
            return re.match(r"https://.*/(.*)", response.url)[1]

    def save_artwork(self, dir_path, artwork_url):
        file_info = {
            "title": "",
            "url": "",
            "name": "",
            "count": 0,
            "size": 0
        }
        res = self.request("GET", artwork_url)
        file_info["url"] = res.url
        html = unescape(res.text)
        image_title = re.search(r"<title>(.*) by .*</title>", html)[1]
        file_info["title"] = image_title
        try:
            download_url = self.download_url(html)
            res = self.request("GET", download_url, stream=True)
        except requests.exceptions.HTTPError:
            download_url = self.download_url(html, True)
            res = self.request("GET", download_url, stream=True)
        file_info["name"] = self.file_name(res)
        with open(os.path.join(dir_path, file_info["name"]), "wb") as f:
            for chunk in res.iter_content(chunk_size=self.download_chunk_size):
                f.write(chunk)
                file_info["size"] += len(chunk)
            file_info["count"] += 1
        print(f"download image: {image_title} ({file_info['name']})")
        return file_info

    def save_artist(self, artist_id, dir_path, start=1, stop=None):
        gallery = self.gallery(artist_id)
        artist_name = gallery["artist_name"]
        print(f"download for author {artist_name} begins\n")
        artworks = self.artist_artworks(artist_id, start, stop)
        if not artworks:
            print(f"author {artist_name} is up-to-date\n")
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artworks)
        print(f"\ndownload for author {artist_name} completed\n")
        return files