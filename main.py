from argparse import ArgumentParser
import sys, os, time
from lib.deviantart import DeviantArtAPI
from lib.config import Config
from lib import utils
import re

def download_artists(api, config):
    start_time = time.time()
    print(f"\nthere are {len(config.artists)} artists\n")
    result = []
    for artist_id, artwork_url in config.artists.items():
        files = api.save_artist(artist_id, config.save_dir, artwork_url)
        if not files:
            continue
        config.update_artist(artist_id, files["url"][0])
        result.append(files)
    result = utils.counter(result)
    duration = time.time() - start_time
    size_mb = result["size"] / 1048576
    print("\nSUMMARY")
    print("---------------------------------")
    print(f"time elapsed:\t{duration:.4f} seconds")
    print(f"total size:\t{size_mb:.4f} MB")
    print(f"total artworks:\t{result['count']} artworks")
    print(f"download speed:\t{(size_mb / duration):.4f} MB/s")

def commands():
    parser = ArgumentParser()
    parser.add_argument("-f", dest="file", default=os.path.join("data", "config.json"), help="set config file")
    parser.add_argument("-l", action="store_true", dest="list", help="list current settings")
    parser.add_argument("-s", dest="save_dir", help="set save directory path")
    parser.add_argument("-a", nargs="+", dest="add", metavar=("", "ID"), help="add artist ids")
    parser.add_argument("-d", nargs="+", dest="delete", metavar=("all", "ID"), help="delete artist ids")
    parser.add_argument("-c", nargs="+", dest="clear", metavar=("all", "ID"), help="clear artists update info")
    parser.add_argument("-t", dest="threads", type=int, help="set the number of threads")
    parser.add_argument("-r", action="store_true", dest="run", help="run program")
    return parser.parse_args()

def main():
    args = commands()
    api = DeviantArtAPI()
    config = Config(args.file)

    if args.list:
        config.print()
    if args.save_dir:
        config.save_dir = args.save_dir
    if args.add:
        config.add_artists(args.add)
    if args.delete:
        config.delete_artists(args.delete)
    if args.clear:
        config.clear_artists(args.clear)
    if args.threads:
        api.threads = args.threads
    if len(sys.argv) == 1 or args.run:
        download_artists(api, config)
    config.update()

if __name__ == "__main__":
    main()