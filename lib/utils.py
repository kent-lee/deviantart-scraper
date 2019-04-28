import collections, itertools
import os, shutil
import json
import time

def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def print_json(json_data):
    print(json.dumps(json_data, indent=4, ensure_ascii=False))

def update_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def make_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def remove_dir(dir_path):
    shutil.rmtree(dir_path, ignore_errors=True)

def counter(listOfDicts):
    counter = collections.Counter()
    for d in listOfDicts:
        counter.update(d)
    return counter

# https://docs.python.org/3/library/itertools.html#itertools-recipes
def consume(iterator, n=None):
    if n is None:
        collections.deque(iterator, maxlen=0)
    else:
        next(itertools.islice(iterator, n, n), None)

# https://docs.python.org/3/library/itertools.html#itertools-recipes
def flatten(listOfLists):
    return itertools.chain.from_iterable(listOfLists)

# set the access and modified times of files for sorting purpose
def set_files_mtime(file_names, dir_path):
    ts = time.time()
    for i,f in enumerate(file_names):
        file_path = os.path.join(dir_path, f)
        os.utime(file_path, (ts - i, ts - i))