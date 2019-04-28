from argparse import ArgumentParser
import sys
import os
import time
from lib.deviantart import DeviantArtAPI
from lib import utils

def load_config(file_path="data/config.json"):
    return utils.load_json(file_path)

def update_config(config, file_path="data/config.json"):
    utils.update_json(config, file_path)

def add_artists(config, artist_ids, api):
    for artist_id in artist_ids:
        config["artists"].setdefault(artist_id, None)
        artist_name = api.gallery(artist_id)["artist_name"]
        utils.make_dir(os.path.join(config["save_directory"], artist_name))

def delete_artists(config, artist_ids, api):
    if artist_ids[0] in "allAllALL":
        artist_ids = list(config["artists"])
    for artist_id in artist_ids:
        config["artists"].pop(artist_id, None)
        artist_name = api.gallery(artist_id)["artist_name"]
        utils.remove_dir(os.path.join(config["save_directory"], artist_name))

def clear_artists(config, artist_ids, api):
    if artist_ids[0] in "allAllALL":
        artist_ids = list(config["artists"])
    for artist_id in artist_ids:
        config["artists"][artist_id] = None
        artist_name = api.gallery(artist_id)["artist_name"]
        utils.remove_dir(os.path.join(config["save_directory"], artist_name))

def init_stats():
    stats = {
        "start_time": time.time(),
        "file_count": 0,
        "total_size": 0,
        "file_names": []
    }
    return stats

def update_stats(files, stats):
    stats["file_names"] = []
    for file in files:
        stats["file_count"] += file["count"]
        stats["total_size"] += file["size"]
        stats["file_names"].append(file["name"])

def print_stats(stats):
    duration = time.time() - stats["start_time"]
    size_mb = stats["total_size"] / 1048576
    print("\nSUMMARY")
    print("---------------------------------")
    print(f"time elapsed:\t{duration:.4f} seconds")
    print(f"total size:\t{size_mb:.4f} MB")
    print(f"total artworks:\t{stats['file_count']} artworks")
    print(f"download speed:\t{(size_mb / duration):.4f} MB/s")

def download_artists(api, config):
    stats = init_stats()
    print(f"\nthere are {len(config['artists'])} artists\n")
    save_dir = utils.make_dir(config["save_directory"])
    for artist_id, artwork_id in config["artists"].items():
        artist_name = api.gallery(artist_id)["artist_name"]
        dir_path = utils.make_dir(os.path.join(save_dir, artist_name))
        files = api.save_artist(artist_id, dir_path, stop=artwork_id)
        if not files:
            continue
        config["artists"][artist_id] = files[0]["url"]
        update_stats(files, stats)
        utils.set_files_mtime(stats["file_names"], dir_path)
    print_stats(stats)

def init_commands():
    parser = ArgumentParser()
    parser.add_argument("-l", action="store_true", dest="list", help="list current settings")
    parser.add_argument("-s", dest="save_dir", help="set save directory path")
    parser.add_argument("-a", nargs="+", dest="add", metavar=("", "ID"), help="add artist ids")
    parser.add_argument("-d", nargs="+", dest="delete", metavar=("all", "ID"), help="delete artist ids")
    parser.add_argument("-c", nargs="+", dest="clear", metavar=("all", "ID"), help="clear artists update info")
    parser.add_argument("-t", dest="threads", type=int, help="set the number of threads")
    parser.add_argument("-r", action="store_true", dest="run", help="run program")
    return parser.parse_args()

def main():
    config = load_config()
    api = DeviantArtAPI()
    args = init_commands()

    if not len(sys.argv) > 1:
        download_artists(api, config)
        update_config(config)
        return

    if args.list:
        utils.print_json(config)

    if args.save_dir:
        config["save_directory"] = args.save_dir

    if args.add:
        add_artists(config, args.add, api)

    if args.delete:
        delete_artists(config, args.delete, api)

    if args.clear:
        clear_artists(config, args.clear, api)

    if args.threads:
        api.threads = args.threads

    if args.run:
        download_artists(api, config)

    update_config(config)

if __name__ == "__main__":
    main()