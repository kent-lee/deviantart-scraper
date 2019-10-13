# File Structure Design

## current version

download all artworks of specified users, i.e. download everything in gallery folder `All`

```bash
save directory
├── user A
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── image3.jpg
│   ...
├── user B
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── image3.jpg
│   ...
├── ranking A
...
```

## version 1

In addition to current version, add folders to store artworks of given collections

**problem**: collection names can be identical. For example, these two links, [link A](https://www.deviantart.com/noahbradley/gallery/37091608/magic-the-gathering) and [link B](https://www.deviantart.com/reddragonshadow/favourites/60479378/magic-the-gathering), have the same collection name. In such case, the collection folder `Magic the Gathering` will contain files from two different users, which may cause the update validation to fail.

Suppose there exists two collections, `A` from `user A` and `B` from `user B`, where the collection names are the same. `A` contains files `[1.jpg, 2.jpg, 3.jpg]` and `B` contains files `[4.jpg, 2.jpg, 6.jpg, 8.jpg, ...]`. After the program downloaded everything from `A` and begins downloading for `B`, it will stop at `2.jpg` because it has detected that the file already exists on the disk and thus assume that the folder is up-to-date.

**potential solution**:

- add prefix or suffix to the collection folder names
- disable update and overwrite everything whenever downloading collections (like ranking). This is not a good solution because you will be re-downloading the same files most of the time

```bash
save directory
├── user A
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── image3.jpg
│   ...
├── user B
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── image3.jpg
│   ...
├── collection A
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── image3.jpg
│   ...
├── collection B
│   ├── image1.jpg
│   ├── image2.jpg
│   ...
├── ranking A
...
```

## version 2

In addition to current version, add sub-folders in each user folder to store the artworks of the user's collections

**note**: some user folders will only contain collection folders and no gallery artworks because the users simply have no artworks or you just want the collections.

```bash
save directory
├── user A
│   ├── collection A
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ├── collection B
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── image3.jpg
│   ...
├── user B
│   ├── collection A
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ├── image1.jpg
│   ├── image2.jpg
│   ├── image3.jpg
│   ...
├── ranking A
...
```

## version 3

download specific gallery / collection folders of specified users. For example, instead of downloading everything in gallery folder `All`, you select which one to download (e.g. `Featured`)

**problem**: need to have a new way to store / input `users` in `config.json` file, which is going to take a long time to implement as it affects some of the the core functionalities

```bash
save directory
├── user A
│   ├── gallery A
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ├── gallery B
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ├── collection A
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ...
├── user B
│   ├── gallery A
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ├── collection A
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ...
├── ranking A
...
```

## version 4

An alternative structure of version 3.

**problem**: need to have a new way to store / input `users` in `config.json` file, which is going to take a long time to implement as it affects some of the the core functionalities

```bash
save directory
├── gallery
│   ├── user A gallery A
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ├── user A gallery B
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ...
├── favourites
│   ├── user A collection A
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ├── user A collection B
│   │   ├── image1.jpg
│   │   ├── image2.jpg
│   │   ├── image3.jpg
│   │   ...
│   ...
└── ranking
    ├── ranking A
    │   ├── image1.jpg
    │   ├── image2.jpg
    │   ├── image3.jpg
    │   ...
    ├── ranking B
    │   ├── image1.jpg
    │   ├── image2.jpg
    │   ├── image3.jpg
    │   ...
    ...
```