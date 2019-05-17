import collections, itertools
import os, shutil
import json
import time

def load_json(file_path, object_hook=None):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f, object_hook=object_hook)

def print_json(json_data):
    print(json.dumps(json_data, indent=4, ensure_ascii=False))

def write_json(json_data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

def make_dir(*args):
    dir_path = os.path.join(*args)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def file_names(*args, separator=" "):
    dir_path = os.path.join(*args)
    return {*[f.partition(separator)[0] for f in os.listdir(dir_path)]}

def sorted_file_names(*args, key="mtime"):
    dir_path = os.path.join(*args)
    if key == "mtime":
        key_function = lambda f: os.path.getmtime(os.path.join(dir_path, f))
    elif key == "size":
        key_function = lambda f: os.path.getsize(os.path.join(dir_path, f))
    return sorted(os.listdir(dir_path), key=key_function, reverse=True)

# set the access and modified times of files for sorting purpose
def set_files_mtime(file_names, dir_path):
    ts = time.time()
    for i, f in enumerate(file_names):
        file_path = os.path.join(dir_path, f)
        os.utime(file_path, (ts - i, ts - i))

def remove_dir(*args):
    dir_path = os.path.join(*args)
    shutil.rmtree(dir_path, ignore_errors=True)

def first_index(iterable, predicate, default=None):
    return next((i for i, v in enumerate(iterable) if predicate(v)), default)

def counter(listOfDicts):
    counter = collections.Counter()
    for d in reversed(listOfDicts):
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