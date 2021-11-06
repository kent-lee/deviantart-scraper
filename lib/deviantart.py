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

    def _download_url(self, artwork, retry=False):
        baseUri = artwork['media']['baseUri']
        prettyName = artwork['media']['prettyName']
        token = artwork['media']['token'][0]
        url = ''
        for t in reversed(artwork['media']['types']):
            if t['r'] == 0:
                url = t['c']
            if url:
                break
        if not url:
            return ''
        url = url.replace('<prettyName>', prettyName)
        url = f'{baseUri}/{url}?token={token}'
        return url

    def _file_name(self, response, artwork):
        # get name from the response of download button url
        if 'Content-Disposition' in response.headers:
            file_name = response.headers['Content-Disposition']
            file_name = re.search(r"''(.*)", file_name)[1]
        else:
            _, file_extension = os.path.splitext(artwork['media']['baseUri'])
            file_name = artwork['media']['prettyName'] + file_extension
        suffix = artwork['deviationId']
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
        file_name = self._file_name(res, artwork)
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

    def save_users_artworks(self, user_ids, dir_path):
        print(f'\nthere are {len(user_ids)} users\n')
        result = []
        for user in user_ids:
            files = self.save_user_artworks(user, dir_path)
            if not files:
                continue
            result.append(files)
        return utils.counter(result)
