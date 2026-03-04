from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://downloads.khinsider.com/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) "
    "Gecko/20100101 Firefox/140.0"
)
REQUEST_TIMEOUT = 30
DownloadFormat = Literal["mp3", "flac", "both"]


@dataclass(frozen=True)
class AlbumOption:
    name: str
    relative_url: str


def print_banner() -> None:
    print(" __      _______ __  __ _____                      _                 _           ")
    print(" \\ \\    / / ____|  \\/  |  __ \\                    | |               | |          ")
    print("  \\ \\  / / |  __| \\  / | |  | | _____      ___ __ | | ___   __ _  __| | ___ _ __ ")
    print("   \\ \\/ /| | |_ | |\\/| | |  | |/ _ \\ \\ /\\ / / '_ \\| |/ _ \\ / _` |/ _` |/ _ \\ '__|")
    print("    \\  / | |__| | |  | | |__| | (_) \\ V  V /| | | | | (_) | (_| | (_| |  __/ |   ")
    print("     \\/   \\_____|_|  |_|_____/ \\___/ \\_/\\_/ |_| |_|_|\\___/ \\__,_|\\__,_|\\___|_|   ")
    print("                                                                  created by V2\n")


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def sanitize_filename(value: str) -> str:
    # Remove characters forbidden in Windows file names.
    sanitized = re.sub(r'[<>:"/\\|?*]', "", value).strip()
    return sanitized.rstrip(".") or "untitled"


def ensure_unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem} ({counter}){path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def extract_title_from_download_url(href: str, fallback_title: str, extension: str) -> str:
    file_name = Path(urlparse(href).path).name
    decoded_name = unquote(file_name)
    suffix = f".{extension}"

    if decoded_name.lower().endswith(suffix):
        raw_title = decoded_name[: -len(suffix)]
        if raw_title.strip():
            # Remove common track-number prefixes like "02 - ", "2. ", "02_".
            clean_title = re.sub(r"^\s*\d+\s*[-._)]\s*", "", raw_title).strip()
            return sanitize_filename(clean_title or raw_title)

    return sanitize_filename(fallback_title)


def ask_game_query() -> str:
    return input("Enter the game name: ").strip()


def ask_download_format() -> DownloadFormat:
    while True:
        print("\nChoose download format:")
        print("1) MP3 only")
        print("2) FLAC only")
        print("3) Both MP3 and FLAC")
        choice = input("Select an option (1-3) [default: 1]: ").strip()
        if choice in ("", "1"):
            return "mp3"
        if choice == "2":
            return "flac"
        if choice == "3":
            return "both"
        print("Invalid option. Please try again.")


def search_album_page(session: requests.Session, query: str) -> BeautifulSoup:
    url = f"{BASE_URL}search?search={query.replace(' ', '+').lower()}"
    return get_soup(session, url)


def parse_search_results(search_soup: BeautifulSoup) -> tuple[str, str, list[AlbumOption]]:
    result_text_tag = search_soup.find("p", {"align": "left"})
    heading_tag = search_soup.find("h2")
    album_table = search_soup.find("table", {"class": "albumList"})

    result_text = result_text_tag.get_text(strip=True) if isinstance(result_text_tag, Tag) else ""
    heading = heading_tag.get_text(strip=True) if isinstance(heading_tag, Tag) else ""
    options: list[AlbumOption] = []

    if isinstance(album_table, Tag):
        seen: set[str] = set()
        for link in album_table.find_all("a"):
            href = (link.get("href") or "").strip()
            if not href.startswith("/game-soundtracks/album/"):
                continue
            if href in seen:
                continue

            seen.add(href)
            album_name = href.removeprefix("/game-soundtracks/album/").replace("-", " ")
            options.append(AlbumOption(name=album_name, relative_url=href))

    return result_text, heading, options


def choose_album(options: list[AlbumOption], result_text: str) -> AlbumOption:
    print(result_text)
    print()
    for index, option in enumerate(options, start=1):
        print(f"{index}) {option.name}")

    while True:
        print("\n=======================================================")
        choice_raw = input("Select the album number you want to download: ").strip()
        print("=======================================================")
        if not choice_raw.isdigit():
            print("Please enter a valid number.")
            continue

        choice = int(choice_raw) - 1
        if 0 <= choice < len(options):
            return options[choice]

        print("Invalid option. Please try again.")


def resolve_album_url(heading: str) -> str:
    album_slug = (
        heading.replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
        .lower()
    )
    return urljoin(BASE_URL, f"game-soundtracks/album/{album_slug}")


def find_album_soup(session: requests.Session) -> BeautifulSoup:
    while True:
        query = ask_game_query()
        search_soup = search_album_page(session, query)
        result_text, heading, options = parse_search_results(search_soup)

        if result_text == "Found 0 matching results.":
            print("No albums found! Please try again...\n")
            continue

        if heading == "Search" and options:
            selected = choose_album(options, result_text)
            return get_soup(session, urljoin(BASE_URL, selected.relative_url))

        if heading:
            return get_soup(session, resolve_album_url(heading))

        print("Unexpected search response. Please try again.\n")


def prepare_directories(
    album_title: str,
    selected_format: DownloadFormat,
) -> tuple[Path, Path | None, Path | None]:
    parent_raw = input(
        "Choose where you want to download "
        "(Example: C:/Users/V2/Music/): "
    ).strip()
    parent_dir = Path(parent_raw.replace("¥", "/")).expanduser()
    album_dir = parent_dir / sanitize_filename(album_title)
    mp3_dir: Path | None = None
    flac_dir: Path | None = None

    album_dir.mkdir(parents=True, exist_ok=True)
    if selected_format == "both":
        mp3_dir = album_dir / "MP3"
        flac_dir = album_dir / "FLAC"
        mp3_dir.mkdir(parents=True, exist_ok=True)
        flac_dir.mkdir(parents=True, exist_ok=True)

    print("=======================================================\n")
    print(f"Saving downloaded files to: {album_dir}")
    return album_dir, mp3_dir, flac_dir


def download_album_cover(
    session: requests.Session,
    album_soup: BeautifulSoup,
    album_dir: Path,
) -> None:
    image_tag = album_soup.find("img")
    if not isinstance(image_tag, Tag):
        print("No album covers found...")
        return

    image_src = image_tag.get("src")
    if not image_src:
        print("No album covers found...")
        return

    try:
        print("Downloading album cover...")
        response = session.get(urljoin(BASE_URL, image_src), timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        (album_dir / "Cover.jpg").write_bytes(response.content)
        print("Done downloading the album cover!\n")
    except requests.RequestException as error:
        print(f"Could not download album cover: {error}")


def iter_song_pages(song_table: Tag) -> Iterable[str]:
    seen: set[str] = set()
    for link in song_table.find_all("a"):
        href = (link.get("href") or "").strip()
        if not href or href in seen:
            continue
        if "mp3" not in href and "flac" not in href:
            continue
        seen.add(href)
        yield href


def parse_song_title(song_soup: BeautifulSoup) -> str | None:
    content = song_soup.find("div", {"id": "pageContent"})
    if not isinstance(content, Tag):
        return None

    bold_tags = content.find_all("b")
    if len(bold_tags) < 2:
        return None
    return bold_tags[1].get_text(strip=True)


def download_song_files(
    session: requests.Session,
    song_soup: BeautifulSoup,
    song_title: str,
    album_dir: Path,
    mp3_dir: Path | None,
    flac_dir: Path | None,
    selected_format: DownloadFormat,
) -> None:
    page_content = song_soup.find("div", {"id": "pageContent"})
    if not isinstance(page_content, Tag):
        return

    for link in page_content.find_all("a"):
        href = (link.get("href") or "").strip()
        if "mp3" not in href and "flac" not in href:
            continue

        href_lower = href.lower()
        if ".flac" in href_lower or "flac" in href_lower:
            extension = "flac"
            if selected_format == "both":
                if flac_dir is None:
                    continue
                target_dir = flac_dir
            else:
                target_dir = album_dir
        elif ".mp3" in href_lower or "mp3" in href_lower:
            extension = "mp3"
            if selected_format == "both":
                if mp3_dir is None:
                    continue
                target_dir = mp3_dir
            else:
                target_dir = album_dir
        else:
            continue

        if selected_format != "both" and extension != selected_format:
            continue

        print(f"Downloading from this URL: {href}")
        try:
            response = session.get(href, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as error:
            print(f"ERROR, song could not be downloaded: {error}\n")
            continue

        base_title = extract_title_from_download_url(href, song_title, extension)
        destination = ensure_unique_path(target_dir / f"{base_title}.{extension}")
        destination.write_bytes(response.content)
        print(f"Done downloading: {destination.name}\n")


def download_album_tracks(
    session: requests.Session,
    album_soup: BeautifulSoup,
    album_dir: Path,
    mp3_dir: Path | None,
    flac_dir: Path | None,
    selected_format: DownloadFormat,
) -> None:
    page_content = album_soup.find("div", {"id": "pageContent"})
    if not isinstance(page_content, Tag):
        print("Could not parse album page.")
        return

    song_table = page_content.find("table", {"id": "songlist"})
    if not isinstance(song_table, Tag):
        print("No song list found for this album.")
        return

    for song_href in iter_song_pages(song_table):
        try:
            song_soup = get_soup(session, urljoin(BASE_URL, song_href))
        except requests.RequestException as error:
            print(f"Could not open song page {song_href}: {error}")
            continue

        song_title = parse_song_title(song_soup)
        if not song_title:
            print(f"Could not identify title for: {song_href}")
            continue

        print(f"Download this song: {song_title}")
        download_song_files(
            session,
            song_soup,
            song_title,
            album_dir,
            mp3_dir,
            flac_dir,
            selected_format,
        )
        print("Selecting the next song\n")


def main() -> None:
    print_banner()
    with build_session() as session:
        selected_format = ask_download_format()
        album_soup = find_album_soup(session)
        page_content = album_soup.find("div", {"id": "pageContent"})
        if not isinstance(page_content, Tag):
            raise RuntimeError("Album page does not contain expected content.")

        album_title_tag = page_content.find("h2")
        album_title = (
            album_title_tag.get_text(strip=True)
            if isinstance(album_title_tag, Tag)
            else "Unknown Album"
        )

        album_dir, mp3_dir, flac_dir = prepare_directories(album_title, selected_format)
        download_album_cover(session, album_soup, album_dir)
        download_album_tracks(
            session,
            album_soup,
            album_dir,
            mp3_dir,
            flac_dir,
            selected_format,
        )

    print("No more songs found!\n")
    print("Thanks for using this program!")
    time.sleep(5)


if __name__ == "__main__":
    main()
