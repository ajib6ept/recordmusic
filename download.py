import datetime
import os

import lxml.html
import requests
from cachelib import FileSystemCache
from dotenv import load_dotenv
from yandex_music import Client

load_dotenv()


TRACKS_URL = (
    "https://www.radiorecord.fm/playlist.php?date=%s&limit=1000"
    % datetime.datetime.now().strftime("%Y-%m-%d")
)

MUSIC_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "music"
)

CACHE_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".cache"
)

EXEPTION_WORDS = ("Record Club", "Солнце Монако")

MAX_MP3_DURATION = 1000 * 60 * 4  # in ms

YANDEX_MUSIC_TOKEN = os.getenv("YA_KEY")


def download_url(url: str) -> str:
    cache = FileSystemCache(cache_dir=CACHE_FOLDER)
    html = cache.get(url)
    if html is None:
        r = requests.get(url)
        html = r.content
        cache.set(url, r.content)
    return html


def get_tracks_from_url(url: str) -> list:
    html = download_url(url)
    doc = lxml.html.fromstring(html)
    title = doc.xpath('//div[@class="artist"]')
    tracks = ["".join(el.itertext()).strip() for el in title]
    return tracks


def normalize_file_name(name: str) -> str:
    return name.replace("/", "-") + ".mp3"


def download_track_from_yamusic(client, track: str) -> None:
    mp3_full_file_name = os.path.join(MUSIC_FOLDER, normalize_file_name(track))
    if not os.path.exists(mp3_full_file_name):
        search_result = client.search(text=track)
        try:
            best = search_result.best.result
            duration = best.to_dict().get("duration_ms")
            if duration and duration < MAX_MP3_DURATION:
                best.download(filename=mp3_full_file_name)
            else:
                print(f"AAAAA - {track}")
        except AttributeError:
            print(f"Error - {track}")


def filter_tracks(tracks: list) -> list:
    new_tracks = list(set(tracks))
    for item in EXEPTION_WORDS:
        new_tracks = [
            track.replace('"', "").replace("'", "")
            for track in new_tracks
            if item not in track
        ]
    return sorted(new_tracks)


def create_music_dir(path) -> None:
    if not os.path.exists(path):
        os.mkdir(path)


def main() -> None:

    create_music_dir(MUSIC_FOLDER)
    tracks = get_tracks_from_url(TRACKS_URL)
    tracks = filter_tracks(tracks)
    client = Client(token=YANDEX_MUSIC_TOKEN).init()
    for track in tracks:
        download_track_from_yamusic(client, track)


if __name__ == "__main__":
    main()
