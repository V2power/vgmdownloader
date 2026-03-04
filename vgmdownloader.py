from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal
from urllib.parse import unquote, urljoin, urlparse

try:
    import requests
except ImportError:
    print("Missing dependency: requests. Install with: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    print("Missing dependency: beautifulsoup4. Install with: pip install beautifulsoup4")
    sys.exit(1)

try:
    import questionary
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except Exception as error:
    print(f"Import failure: {type(error).__name__}: {error}")
    sys.exit(1)

BASE_URL = "https://downloads.khinsider.com/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) "
    "Gecko/20100101 Firefox/140.0"
)
REQUEST_TIMEOUT = 30
DownloadFormat = Literal["mp3", "flac", "both"]
console = Console()


@dataclass(frozen=True)
class AlbumOption:
    name: str
    relative_url: str


def ui_header() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]VGM Downloader[/bold cyan]\n"
            "[dim]Modern interface for KHInsider OST downloads[/dim]",
            border_style="cyan",
        )
    )
    console.print("[dim]Created by V2[/dim]", justify="right")


def show_cancel_message() -> None:
    console.print()
    console.print(
        Panel.fit(
            "[bold yellow]Operation canceled[/bold yellow]\n"
            "[dim]Download interrupted by user (Ctrl + C).[/dim]",
            border_style="yellow",
        )
    )


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def sanitize_filename(value: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*]', "", value).strip()
    return sanitized.rstrip(".") or "untitled"


def strip_track_prefix(title: str) -> str:
    cleaned = title.strip()
    # Handles: "01 Name", "01. Name", "01 - Name", "01_Name", "01) Name".
    pattern = re.compile(r"^\s*\d{1,3}\s*(?:[-._)\]]\s*|\s+)")
    while True:
        next_cleaned = pattern.sub("", cleaned, count=1).strip()
        if next_cleaned == cleaned or not next_cleaned:
            break
        cleaned = next_cleaned
    return cleaned


def get_tag_attr_text(tag: Tag, attr_name: str) -> str:
    value = tag.get(attr_name)
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value).strip()
    return str(value).strip()


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
            clean_title = strip_track_prefix(raw_title)
            return sanitize_filename(clean_title or raw_title)

    return sanitize_filename(strip_track_prefix(fallback_title) or fallback_title)


def ask_game_query() -> str:
    while True:
        value = questionary.text("Enter the game name:").ask()
        if value is None:
            raise KeyboardInterrupt
        if value and value.strip():
            return value.strip()
        console.print("[yellow]Please enter a valid game name.[/yellow]")


def ask_download_format() -> DownloadFormat:
    selected = questionary.select(
        "Choose download format:",
        choices=[
            "MP3 only",
            "FLAC only",
            "Both MP3 and FLAC",
        ],
        default="MP3 only",
    ).ask()

    if selected == "FLAC only":
        return "flac"
    if selected == "Both MP3 and FLAC":
        return "both"
    return "mp3"


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
            if not isinstance(link, Tag):
                continue
            href = get_tag_attr_text(link, "href")
            if not href.startswith("/game-soundtracks/album/"):
                continue
            if href in seen:
                continue

            seen.add(href)
            album_name = href.removeprefix("/game-soundtracks/album/").replace("-", " ")
            options.append(AlbumOption(name=album_name, relative_url=href))

    return result_text, heading, options


def choose_album(options: list[AlbumOption], result_text: str) -> AlbumOption:
    table = Table(title=result_text or "Album Results", show_header=True, header_style="bold cyan")
    table.add_column("#", style="bold", width=4)
    table.add_column("Album")
    for index, option in enumerate(options, start=1):
        table.add_row(str(index), option.name)
    console.print(table)

    choices = [f"{idx:>3} | {opt.name}" for idx, opt in enumerate(options, start=1)]
    selected = questionary.select(
        "Select album:",
        choices=choices,
        use_shortcuts=False,
    ).ask()
    if not selected:
        raise RuntimeError("Album selection was cancelled.")

    selected_idx = int(selected.split("|", 1)[0].strip()) - 1
    return options[selected_idx]


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
        console.print(f"[dim]Searching for:[/dim] [cyan]{query}[/cyan]")
        search_soup = search_album_page(session, query)
        result_text, heading, options = parse_search_results(search_soup)

        if result_text == "Found 0 matching results.":
            console.print("[yellow]No albums found. Try another query.[/yellow]")
            continue

        if heading == "Search" and options:
            selected = choose_album(options, result_text)
            return get_soup(session, urljoin(BASE_URL, selected.relative_url))

        if heading:
            return get_soup(session, resolve_album_url(heading))

        console.print("[yellow]Unexpected search response. Try again.[/yellow]")


def prepare_directories(
    album_title: str,
    selected_format: DownloadFormat,
) -> tuple[Path, Path | None, Path | None]:
    parent = questionary.path(
        "Choose where to save downloads:",
        default=str(Path.home() / "Music"),
        only_directories=True,
    ).ask()
    if not parent:
        raise RuntimeError("No target directory selected.")

    parent_dir = Path(parent.replace("¥", "/")).expanduser()
    album_dir = parent_dir / sanitize_filename(album_title)
    mp3_dir: Path | None = None
    flac_dir: Path | None = None

    album_dir.mkdir(parents=True, exist_ok=True)
    if selected_format == "both":
        mp3_dir = album_dir / "MP3"
        flac_dir = album_dir / "FLAC"
        mp3_dir.mkdir(parents=True, exist_ok=True)
        flac_dir.mkdir(parents=True, exist_ok=True)

    console.print(
        Panel.fit(
            f"[green]Saving to:[/green] {album_dir}\n"
            f"[green]Format:[/green] {selected_format.upper()}",
            border_style="green",
        )
    )
    return album_dir, mp3_dir, flac_dir


def ask_download_images() -> bool:
    selected = questionary.confirm(
        "Download album images?",
        default=True,
    ).ask()
    if selected is None:
        raise KeyboardInterrupt
    return bool(selected)


def ask_download_another_album() -> bool:
    selected = questionary.confirm(
        "Download another album?",
        default=False,
    ).ask()
    if selected is None:
        raise KeyboardInterrupt
    return bool(selected)


def download_album_images(
    session: requests.Session,
    album_soup: BeautifulSoup,
    album_dir: Path,
) -> None:
    page_content = album_soup.find("div", {"id": "pageContent"})
    if not isinstance(page_content, Tag):
        console.print("[dim]No album images found.[/dim]")
        return

    image_urls: list[str] = []
    seen_urls: set[str] = set()
    # Some pages use class="albumImage" on <img>, others on the parent/link.
    image_tags = page_content.select("img.albumImage, .albumImage img")
    for image_tag in image_tags:
        if not isinstance(image_tag, Tag):
            continue
        src = get_tag_attr_text(image_tag, "src")
        if not src:
            continue

        image_url = urljoin(BASE_URL, src)
        parent = image_tag.parent
        if isinstance(parent, Tag) and parent.name == "a":
            href = get_tag_attr_text(parent, "href")
            href_path = urlparse(href).path.lower()
            if href and re.search(r"\.(jpg|jpeg|png|webp|gif|bmp)$", href_path):
                image_url = urljoin(BASE_URL, href)

        if image_url in seen_urls:
            continue
        seen_urls.add(image_url)
        image_urls.append(image_url)

    if not image_urls:
        console.print("[dim]No album images found.[/dim]")
        return

    console.print(f"[cyan]Downloading album images ({len(image_urls)})...[/cyan]")
    downloaded = 0
    for index, image_url in enumerate(image_urls, start=1):
        try:
            response = session.get(image_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as error:
            console.print(f"[yellow]Could not download image:[/yellow] {image_url} ({error})")
            continue

        original_name = unquote(Path(urlparse(image_url).path).name).strip()
        file_name = sanitize_filename(original_name) if original_name else f"Image {index:02d}.jpg"
        destination = ensure_unique_path(album_dir / file_name)
        destination.write_bytes(response.content)
        downloaded += 1

    if downloaded == 0:
        console.print("[yellow]No album images could be downloaded.[/yellow]")
    else:
        console.print(f"[green]Album images saved:[/green] {downloaded}")


def iter_song_pages(song_table: Tag) -> Iterable[str]:
    seen: set[str] = set()
    for link in song_table.find_all("a"):
        if not isinstance(link, Tag):
            continue
        href = get_tag_attr_text(link, "href")
        if not href:
            continue
        ext = detect_link_extension(href)
        if not ext:
            continue
        normalized = re.sub(r"\.(mp3|flac)$", "", href, flags=re.IGNORECASE)
        if normalized in seen:
            continue
        seen.add(normalized)
        yield href


def detect_link_extension(href: str) -> str | None:
    href_lower = href.lower().strip()
    parsed_path = urlparse(href_lower).path
    has_flac_token = re.search(r"(^|[\/._-])flac([\/._-]|$)", parsed_path) is not None
    has_mp3_token = re.search(r"(^|[\/._-])mp3([\/._-]|$)", parsed_path) is not None

    if parsed_path.endswith(".flac") or "format=flac" in href_lower or has_flac_token:
        return "flac"
    if parsed_path.endswith(".mp3") or "format=mp3" in href_lower or has_mp3_token:
        return "mp3"
    return None


def detect_album_formats(session: requests.Session, album_soup: BeautifulSoup) -> set[str]:
    page_content = album_soup.find("div", {"id": "pageContent"})
    if not isinstance(page_content, Tag):
        return set()

    song_table = page_content.find("table", {"id": "songlist"})
    if not isinstance(song_table, Tag):
        return set()

    formats: set[str] = set()
    song_page_candidates: list[str] = []
    seen_candidates: set[str] = set()

    for link in song_table.find_all("a"):
        if not isinstance(link, Tag):
            continue
        href = get_tag_attr_text(link, "href")
        if not href:
            continue

        ext = detect_link_extension(href)
        if ext:
            formats.add(ext)

        # Keep internal KHInsider pages as candidates to inspect per-track links.
        # Some albums expose one format in the table and the other inside track pages.
        if "/game-soundtracks/" in href and href not in seen_candidates:
            seen_candidates.add(href)
            song_page_candidates.append(href)

    if "mp3" in formats and "flac" in formats:
        return formats

    # Some album pages expose only one format in the table and the other
    # (usually FLAC) only inside each track page. Inspect a few track pages.
    for song_href in song_page_candidates[:20]:
        try:
            song_soup = get_soup(session, urljoin(BASE_URL, song_href))
        except requests.RequestException:
            continue

        song_content = song_soup.find("div", {"id": "pageContent"})
        if not isinstance(song_content, Tag):
            continue

        for file_link in song_content.find_all("a"):
            if not isinstance(file_link, Tag):
                continue
            file_href = get_tag_attr_text(file_link, "href")
            ext = detect_link_extension(file_href)
            if ext:
                formats.add(ext)

        if "mp3" in formats and "flac" in formats:
            break

    return formats


def choose_download_format_for_album(
    session: requests.Session,
    album_soup: BeautifulSoup,
) -> DownloadFormat:
    available_formats = detect_album_formats(session, album_soup)
    has_mp3 = "mp3" in available_formats
    has_flac = "flac" in available_formats

    if has_mp3 and has_flac:
        return ask_download_format()

    if has_mp3:
        console.print("[yellow]FLAC not available for this album. Using MP3.[/yellow]")
        return "mp3"

    if has_flac:
        console.print("[yellow]MP3 not available for this album. Using FLAC.[/yellow]")
        return "flac"

    # Fallback for unexpected pages.
    console.print("[yellow]No explicit audio format detected. Using MP3 by default.[/yellow]")
    return "mp3"


def parse_song_title(song_soup: BeautifulSoup, selected_format: DownloadFormat) -> str | None:
    content = song_soup.find("div", {"id": "pageContent"})
    if not isinstance(content, Tag):
        return None

    preferred = ["mp3", "flac"] if selected_format == "mp3" else ["flac", "mp3"]
    if selected_format == "both":
        preferred = ["flac", "mp3"]

    # Prefer extracting the track title from the download URL itself.
    for wanted_ext in preferred:
        for link in content.find_all("a"):
            if not isinstance(link, Tag):
                continue
            href = get_tag_attr_text(link, "href")
            ext = detect_link_extension(href)
            if not ext or ext != wanted_ext:
                continue
            return extract_title_from_download_url(href, "untitled", ext)

    bold_tags = content.find_all("b")
    if len(bold_tags) < 2:
        return None
    return strip_track_prefix(bold_tags[1].get_text(strip=True))


def download_song_files(
    session: requests.Session,
    song_soup: BeautifulSoup,
    song_title: str,
    album_dir: Path,
    mp3_dir: Path | None,
    flac_dir: Path | None,
    selected_format: DownloadFormat,
    track_index: int,
) -> int:
    page_content = song_soup.find("div", {"id": "pageContent"})
    if not isinstance(page_content, Tag):
        return 0

    downloaded = 0
    for link in page_content.find_all("a"):
        if not isinstance(link, Tag):
            continue
        href = get_tag_attr_text(link, "href")
        if "mp3" not in href and "flac" not in href:
            continue

        ext = detect_link_extension(href)
        if ext == "flac":
            extension = "flac"
            if selected_format == "both":
                if flac_dir is None:
                    continue
                target_dir = flac_dir
            else:
                target_dir = album_dir
        elif ext == "mp3":
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

        try:
            response = session.get(href, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as error:
            console.print(f"[red]Failed:[/red] {song_title} ({extension}) -> {error}")
            continue

        base_title = strip_track_prefix(extract_title_from_download_url(href, song_title, extension))
        numbered_title = f"{track_index:02d}. {base_title}"
        destination = ensure_unique_path(target_dir / f"{numbered_title}.{extension}")
        destination.write_bytes(response.content)
        output_name = f"{numbered_title}.{extension}"
        console.print(f"[green]Saved:[/green] {output_name}")
        downloaded += 1

    return downloaded


def download_album_tracks(
    session: requests.Session,
    album_soup: BeautifulSoup,
    album_dir: Path,
    mp3_dir: Path | None,
    flac_dir: Path | None,
    selected_format: DownloadFormat,
) -> int:
    page_content = album_soup.find("div", {"id": "pageContent"})
    if not isinstance(page_content, Tag):
        console.print("[red]Could not parse album page.[/red]")
        return 0

    song_table = page_content.find("table", {"id": "songlist"})
    if not isinstance(song_table, Tag):
        console.print("[red]No song list found for this album.[/red]")
        return 0

    total_downloaded = 0
    track_index = 1
    for song_href in iter_song_pages(song_table):
        try:
            song_soup = get_soup(session, urljoin(BASE_URL, song_href))
        except requests.RequestException as error:
            console.print(f"[yellow]Could not open song page:[/yellow] {song_href} ({error})")
            continue

        song_title = parse_song_title(song_soup, selected_format)
        if not song_title:
            console.print(f"[yellow]Could not identify title for:[/yellow] {song_href}")
            continue

        clean_song_title = strip_track_prefix(song_title)
        console.print(f"[cyan]Track:[/cyan] {clean_song_title}")
        downloaded_for_track = download_song_files(
            session,
            song_soup,
            clean_song_title,
            album_dir,
            mp3_dir,
            flac_dir,
            selected_format,
            track_index,
        )
        total_downloaded += downloaded_for_track
        if downloaded_for_track > 0:
            console.print()
        track_index += 1

    return total_downloaded


def main() -> None:
    ui_header()
    with build_session() as session:
        while True:
            album_soup = find_album_soup(session)
            selected_format = choose_download_format_for_album(session, album_soup)
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
            if ask_download_images():
                download_album_images(session, album_soup, album_dir)
            console.print(f"[bold cyan]Album:[/bold cyan] {album_title}\n")
            downloaded_count = download_album_tracks(
                session,
                album_soup,
                album_dir,
                mp3_dir,
                flac_dir,
                selected_format,
            )

            console.print(
                Panel.fit(
                    f"[bold green]Finished Album[/bold green]\n"
                    f"Downloaded files: [bold]{downloaded_count}[/bold]",
                    border_style="green",
                )
            )
            if not ask_download_another_album():
                break
            console.print()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        show_cancel_message()
        sys.exit(130)
    except RuntimeError as error:
        error_text = str(error).lower()
        if "cancel" in error_text or "no target directory selected" in error_text:
            show_cancel_message()
            sys.exit(130)
        raise
