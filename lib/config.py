import os
from lib.deviantart import DeviantArtAPI
from lib import utils

class Config:

    api = DeviantArtAPI()

    def __init__(self, file_path):
        self.file_path = file_path
        self._data = utils.load_json(file_path)
        self._data['save_directory'] = os.path.normpath(self._data['save_directory'])
        self._data['users'] = list(dict.fromkeys(self._data['users']))

    def print(self):
        utils.print_json(self._data)

    def update(self):
        utils.write_json(self._data, self.file_path)

    @property
    def save_dir(self):
        return self._data['save_directory']

    @save_dir.setter
    def save_dir(self, save_dir):
        save_dir = os.path.normpath(save_dir)
        self._data['save_directory'] = save_dir

    def update_artist(self, artist_id, value):
        self._data['artists'][artist_id] = value

    @property
    def users(self):
        return self._data['users']

    def add_users(self, user_ids):
        for id in user_ids:
            if id in self.users:
                print(f'User ID {id} already exists in config file')
            elif 'error' in self.api.user(id).keys():
                print(f'User ID {id} does not exist')
            else:
                self.users.append(id)

    def delete_users(self, user_ids):
        if 'all' in user_ids:
            user_ids = self.users.copy()
        for id in user_ids:
            if id not in self.users:
                print(f'User ID {id} does not exist in config file')
            else:
                self.users.remove(id)
                utils.remove_dir(self.save_dir, str(id))

    def clear_users(self, user_ids):
        if 'all' in user_ids:
            user_ids = self.users.copy()
        for id in user_ids:
            if id not in self.users:
                print(f'User ID {id} does not exist in config file')
            else:
                utils.remove_dir(self.save_dir, str(id))
