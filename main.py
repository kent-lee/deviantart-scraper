from argparse import ArgumentParser
import sys, os, time
from lib.deviantart import DeviantArtAPI
from lib.config import Config
from lib import utils, cmd
import re

def download_users(api, config, option, **kwargs):
    start_time = time.time()
    if option == 'artwork':
        result = api.save_users_artworks(config.users, config.save_dir)
    elif option == 'ranking':
        result = api.save_ranking_artworks(**kwargs)
    elif option == 'collections':
        result = api.save_collections_artworks(config.collections, **kwargs)
    duration = time.time() - start_time
    size_mb = result['size'] / 1048576
    print('\nSUMMARY')
    print('---------------------------------')
    print(f'time elapsed:\t{duration:.4f} seconds')
    print(f'total size:\t{size_mb:.4f} MB')
    print(f'total artworks:\t{result["count"]} artworks')
    print(f'download speed:\t{(size_mb / duration):.4f} MB/s')

def main():
    api = DeviantArtAPI()
    args = cmd.main_parser()
    config = Config(args.f)
    if args.l:
        config.print()
    if args.s:
        config.save_dir = args.s
    if args.t:
        api.threads = args.t
    if args.option == 'artwork':
        if args.a:
            config.add_users(args.a)
        if args.d:
            config.delete_users(args.d)
        if args.c:
            config.clear_users(args.c)
        download_users(api, config, args.option)
    elif args.option == 'ranking':
        params = {
            'order': args.order,
            'type': args.type,
            'content': args.content,
            'category': args.category,
            'limit': args.n,
            'dir_path': config.save_dir
        }
        download_users(api, config, args.option, **params)
    elif args.option == 'collections':
        params = {
            'dir_path': config.save_dir
        }
        download_users(api, config, args.option, **params)
    config.update()

if __name__ == "__main__":
    main()