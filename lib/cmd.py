import argparse
import os

def artwork_parser(subparsers):
    artwork = subparsers.add_parser("artwork", help="download artworks from user IDs specified in \"users\" field")
    artwork.add_argument("-a", metavar=("", "ID"), nargs="+", help="add user IDs")
    artwork.add_argument("-d", metavar=("all", "ID"), nargs="+", help="delete user IDs and their directories")
    artwork.add_argument("-c", metavar=("all", "ID"), nargs="+", help="clear directories of user IDs")

def ranking_parser(subparsers):
    orders = ['whats-hot', 'undiscovered', 'most-recent', 'popular-24-hours', 'popular-1-week', 'popular-1-month', 'popular-all-time']
    types = ['visual-art', 'video', 'literature']
    contents = ['all', 'original-work', 'fan-art', 'resource', 'tutorial', 'da-related']
    categories = ['all', 'animation', 'artisan-crafts', 'tattoo-and-body-art', 'design', 'digital-art', 'traditional', 'photography', 'sculpture', 'street-art', 'mixed-media', 'poetry', 'prose', 'screenplays-and-scripts', 'characters-and-settings', 'action', 'adventure', 'abstract', 'comedy', 'drama', 'documentary', 'horror', 'science-fiction', 'stock-and-effects', 'fantasy', 'adoptables', 'events', 'memes', 'meta']
    ranking = subparsers.add_parser("ranking", help="download top N ranking artworks based on given conditions")
    ranking.add_argument("-order", metavar="ORDER", choices=orders, default='popular-1-week', help="orders: {%(choices)s} (default: %(default)s)")
    ranking.add_argument("-type", metavar="TYPE", choices=types, default='visual-art', help="types: {%(choices)s} (default: %(default)s)")
    ranking.add_argument("-content", metavar="CONTENT", choices=contents, default='all', help="contents: {%(choices)s} (default: %(default)s)")
    ranking.add_argument("-category", metavar="CATEGORY", choices=categories, default='all', help="categories: {%(choices)s} (default: %(default)s)")
    ranking.add_argument("-n", metavar="N", type=int, default=30, help="get top N artworks (default: %(default)s)")

def collections_parser(subparsers):
    subparsers.add_parser("collections", help="download artworks from collections specified in \"collections\" field")

def main_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", metavar=("FILE"), default=os.path.join("data", "config.json"), help="load file for this instance (default: %(default)s)")
    parser.add_argument("-l", action="store_true", help="list current settings")
    parser.add_argument("-s", metavar=("SAVE_DIR"), help="set save directory path")
    parser.add_argument("-t", metavar=("THREADS"), type=int, help="set number of threads for this instance")
    subparsers = parser.add_subparsers(dest="option")
    artwork_parser(subparsers)
    ranking_parser(subparsers)
    collections_parser(subparsers)
    return parser.parse_args()
