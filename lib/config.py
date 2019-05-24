import os
from lib.deviantart import DeviantArtAPI
from lib import utils

class Config:

    api = DeviantArtAPI()

    def __init__(self, file_path):
        self.file_path = file_path
        self._data = utils.load_json(file_path)
        self._data["save_directory"] = os.path.normpath(self._data["save_directory"])

    def print(self):
        utils.print_json(self._data)

    def update(self):
        utils.write_json(self._data, self.file_path)

    @property
    def save_dir(self):
        return self._data["save_directory"]

    @save_dir.setter
    def save_dir(self, save_dir):
        save_dir = os.path.normpath(save_dir)
        self._data["save_directory"] = save_dir

    def update_artist(self, artist_id, value):
        self._data["artists"][artist_id] = value

    @property
    def artists(self):
        return self._data["artists"]

    def add_artists(self, artist_ids):
        for id in artist_ids:
            try:
                self.api.gallery(id)
                self.artists.setdefault(id, None)
            except:
                print(f"Artist {id} does not exist")

    def delete_artists(self, artist_ids):
        if "all" in artist_ids:
            artist_ids = self.artists.keys()
        for id in artist_ids:
            if id in self.artists.keys():
                self.artists.pop(id, None)
                artist_name = self.api.gallery(id)["artist_name"]
                utils.remove_dir(self.save_dir, artist_name)
            else:
                print(f"Artist {id} does not exist")

    def clear_artists(self, artist_ids):
        if "all" in artist_ids:
            artist_ids = self.artists.keys()
        for id in artist_ids:
            if id in self.artists.keys():
                self.artists[id] = None
                artist_name = self.api.gallery(id)["artist_name"]
                utils.remove_dir(self.save_dir, artist_name)
            else:
                print(f"Artist {id} does not exist")