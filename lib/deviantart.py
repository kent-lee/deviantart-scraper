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
        self.session.cookies['agegate_state'] = '1'
        # retry when exceed the max request number
        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def request(self, method, url, **kwargs):
        if method == 'GET':
            res = self.session.get(url, **kwargs)
        elif method == 'POST':
            res = self.session.post(url, **kwargs)
        res.raise_for_status()
        return res

    def user(self, user_id):
        url = 'https://www.deviantart.com/_napi/da-deviation/shared_api/user/info?'
        payload = {
            'username': user_id,
            'expand': 'user.stats,user.profile,user.watch'
        }
        res = self.request('GET', url, params=payload)
        return res.json()

    def artwork(self, artwork_id):
        url = 'https://www.deviantart.com/_napi/da-user-profile/shared_api/deviation/extended_fetch?'
        payload = {
            'deviationid': str(artwork_id),
            'type': 'art',
        }
        res = self.request('GET', url, params=payload)
        return res.json()['deviation']

    def user_artworks(self, user_id, dir_path=None):
        url = 'https://www.deviantart.com/_napi/da-user-profile/api/gallery/contents?'
        artworks = []
        offset = 0
        # list of artwork ids
        file_names = utils.file_names(dir_path, pattern=r'-(\d+)\.(.+)$') if dir_path else []
        while True:
            payload = {
                'username': user_id,
                'offset': str(offset),
                'limit': '24',
                'all_folder': 'true',
                'mode': 'newest'
            }
            json = self.request('GET', url, params=payload).json()
            for a in json['results']:
                if str(a['deviation']['deviationId']) in file_names:
                    return artworks
                artworks.append(a['deviation'])
            if not json['hasMore']:
                break
            offset += 24
        return artworks

    def ranking_artworks(self, order='popular-1-month', type='visual-art', content='all', category='all', limit=30, dir_path=None):
        '''
        available orders: ['whats-hot', 'undiscovered', 'most-recent', 'popular-24-hours', 'popular-1-week', 'popular-1-month', 'popular-all-time']
        available types: ['visual-art', 'video', 'literature']
        available contents: ['all', 'original-work', 'fan-art', 'resource', 'tutorial', 'da-related']
        available categories: ['all', 'animation', 'artisan-crafts', 'tattoo-and-body-art', 'design', 'digital-art', 'traditional', 'photography', 'sculpture', 'street-art', 'mixed-media', 'poetry', 'prose', 'screenplays-and-scripts', 'characters-and-settings', 'action', 'adventure', 'abstract', 'comedy', 'drama', 'documentary', 'horror', 'science-fiction', 'stock-and-effects', 'fantasy', 'adoptables', 'events', 'memes', 'meta']
        '''
        url = 'https://www.deviantart.com/_napi/da-browse/api/faceted?'
        artworks = []
        offset = 0
        while True:
            payload = {
                'offset': str(offset),
                'limit': '24',
                'page_type': 'deviations',
                'order': order,
                'facet_type': type,
                'facet_content': content,
                'facet_category': category
            }
            json = self.request('GET', url, params=payload).json()
            for i, a in enumerate(json['deviations']):
                if i + offset == limit:
                    return artworks
                artworks.append(a)
            if not json['hasMore']:
                break
            offset += 24
        return artworks

    def collection_metadata(self, collection):
        # e.g. shemetz/favourites/77974139/deviantart-wallpapers
        username, kind_place, folderid, lowercase_name = collection.split("/")
        assert kind_place
        url = f'https://www.deviantart.com/_napi/da-user-profile/api/init/{kind_place}'
        params = {
            "username": username,
            "deviations_limit": 0,
        }
        json = self.request('GET', url, params=params).json()
        folders = json["sectionData"]["modules"][0]["moduleData"]["folders"]["results"]
        for folder in folders:
            if str(folder["folderId"]) == folderid:
                return folder
        raise ValueError(f'Did not find collection {folderid} ({lowercase_name}).')

    def collection_artworks(self, collection, dir_path=None):
        # e.g. shemetz/favourites/77974139/deviantart-wallpapers
        username, kind_place, folderid, lowercase_name = collection.split("/")
        if kind_place == "favourites":
            kind = "collection"
        elif kind_place == "gallery":
            kind = "gallery"
        else:
            raise ValueError(f'Expected "favourites" or "gallery" instead of "{kind_place}", in {collection}')
        url = f'https://www.deviantart.com/_napi/da-user-profile/api/{kind}/contents'
        artworks = []
        offset = 0
        file_names = utils.file_names(dir_path, pattern=r'-(\d+)\.(.+)$') if dir_path else []
        while True:
            payload = {
                'username': username,
                'folderid': folderid,
                'offset': str(offset),
                'limit': '24',
            }
            json = self.request('GET', url, params=payload).json()
            for a in json['results']:
                if str(a['deviation']['deviationId']) in file_names:
                    return artworks
                artworks.append(a['deviation'])
            if not json['hasMore']:
                break
            offset += 24
        return artworks

    def _download_url(self, artwork, retry=False):
        # download button
        if artwork['isDownloadable']:
            res = self.request('GET', artwork['url'])
            html = unescape(res.text)
            return re.search(r'href="(https://www.deviantart.com/download/.+?)"', html)[1]
        url = next(a['src'] for a in artwork['files'] if a['type']=='fullview')
        # direct image url with other prefixes like /f/ or https://img00
        if '/v1/fill/' not in url:
            return url
        # in case for new uploads where only image quality is allowed to modify
        if retry:
            return re.sub(r'(q_\d+,strp|strp)', 'q_100', url)
        # set image properties. For more details, visit below link:
        # https://support.wixmp.com/en/article/image-service-3835799
        a = self.artwork(artwork['deviationId'])
        w = a['extended']['originalFile']['width']
        h = a['extended']['originalFile']['height']
        url = re.match(r'(.+?)\?token=', url)[1]
        url = re.sub('/f/', '/intermediary/f/', url)
        url = re.sub('/v1/fill/.*/', f'/v1/fill/w_{w},h_{h},q_100/', url)
        return url

    def _file_name(self, response, suffix):
        # get name from the response of download button url
        if 'Content-Disposition' in response.headers:
            file_name = response.headers['Content-Disposition']
            file_name = re.search(r"''(.*)", file_name)[1]
        # get name from response url with image settings
        elif '/v1/fill/' in response.url:
            file_name = re.search(r'w_\d+,h_\d+,q_100/(.*?)($|\?token=.*)', response.url)[1]
        else:
            # get name from response url without image settings
            try:
                file_name = re.search(r'.*wixmp.com/f/.*/(.*)\?token=', response.url)[1]
            # get name from response url that is not image (e.g. gif, swf)
            except TypeError:
                file_name = re.match(r'https://.*/(.*)', response.url)[1]
        return re.sub(r'\.(.+)$', rf'-{suffix}.\1', file_name)

    def save_artwork(self, dir_path, artwork):
        file = {
            'title': [],
            'url': [],
            'name': [],
            'count': 0,
            'size': 0
        }
        try:
            download_url = self._download_url(artwork)
            res = self.request('GET', download_url, stream=True)
        except requests.exceptions.HTTPError:
            download_url = self._download_url(artwork, True)
            res = self.request('GET', download_url, stream=True)
        image_title = artwork['title']
        file['title'].append(image_title)
        file['url'].append(download_url)
        file_name = self._file_name(res, artwork['deviationId'])
        file['name'].append(file_name)
        with open(os.path.join(dir_path, file_name), 'wb') as f:
            for chunk in res.iter_content(chunk_size=self.download_chunk_size):
                f.write(chunk)
                file['size'] += len(chunk)
            file['count'] += 1
        print(f'download image: {image_title} ({file_name})')
        return file

    def save_user_artworks(self, user_id, dir_path):
        print(f'download artworks for user {user_id}\n')
        dir_path = utils.make_dir(dir_path, user_id)
        artworks = self.user_artworks(user_id, dir_path)
        if not artworks:
            print(f'user {user_id} is up-to-date\n')
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artworks)
        print(f'\ndownload for user {user_id} completed\n')
        combined_files = utils.counter(files)
        utils.set_files_mtime(combined_files['name'], dir_path)
        return combined_files

    def save_ranking_artworks(self, dir_path, order='popular-1-month', type='visual-art', content='all', category='all', limit=30):
        print(f'download {order} {content} {category} ranking\n')
        dir_path = utils.make_dir(dir_path, f'{order} {content} {category} ranking')
        artworks = self.ranking_artworks(order, type, content, category, limit, dir_path)
        if not artworks:
            print(f'{order} {content} {category} ranking is up-to-date\n')
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artworks)
        print(f'\ndownload for {order} {content} {category} ranking completed\n')
        combined_files = utils.counter(files)
        utils.set_files_mtime(combined_files['name'], dir_path)
        return combined_files

    def save_collection_artworks(self, collection, dir_path):
        collection_metadata = self.collection_metadata(collection)
        collection_name = collection_metadata["name"]
        collection_owner = collection_metadata["owner"]["username"]
        amount = collection_metadata["size"]
        print(f'download {amount} artworks for collection {collection_name} by {collection_owner}\n')
        dir_path = utils.make_dir(dir_path, collection_name)
        artworks = self.collection_artworks(collection, dir_path)
        if not artworks:
            print(f'collection {collection_name} is up-to-date\n')
            return
        with ThreadPool(self.threads) as pool:
            files = pool.map(partial(self.save_artwork, dir_path), artworks)
        print(f'\ndownload for collection {collection_name} completed\n')
        combined_files = utils.counter(files)
        utils.set_files_mtime(combined_files['name'], dir_path)
        return combined_files

    def save_users_artworks(self, user_ids, dir_path):
        print(f'\nthere are {len(user_ids)} users\n')
        result = []
        for user in user_ids:
            files = self.save_user_artworks(user, dir_path)
            if not files:
                continue
            result.append(files)
        return utils.counter(result)

    def save_collections_artworks(self, collections, dir_path):
        result = []
        for collection in collections:
            files = self.save_collection_artworks(collection, dir_path)
            if not files:
                continue
            result.append(files)
        return utils.counter(result)