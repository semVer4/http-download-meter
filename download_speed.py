import argparse
import http.client
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024


def download(url):
    request = Request(url, headers={"Accept-Encoding": "identity"})
    size = 0
    started = time.perf_counter()
    with urlopen(request, timeout=30) as response:
        while chunk := response.read(CHUNK_SIZE):
            size += len(chunk)

        # При чтении блоками преждевременный EOF может выглядеть как конец файла.
        expected = response.headers.get("Content-Length")
        if (response.status != 204 and expected is not None
                and "Transfer-Encoding" not in response.headers
                and size != int(expected)):
            raise OSError(f"неполный ответ: ожидалось {expected} байт, получено {size}")

    return size, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser(description="Измеряет скорость загрузки по HTTP(S)")
    parser.add_argument("url", help="прямая ссылка на файл")
    args = parser.parse_args()
    try:
        parts = urlsplit(args.url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise ValueError
    except ValueError:
        parser.error("укажите полный адрес с http:// или https://")

    total_bytes = 0
    total_seconds = 0.0
    for number in range(1, REQUEST_COUNT + 1):
        try:
            size, seconds = download(args.url)
        except HTTPError as error:
            print(f"Запрос {number}: HTTP {error.code} ({error.reason})", file=sys.stderr)
            return 1
        except (URLError, OSError, http.client.HTTPException, ValueError) as error:
            print(f"Запрос {number}: {error}", file=sys.stderr)
            return 1
        total_bytes += size
        total_seconds += seconds
        print(f"{number}/{REQUEST_COUNT}: {size} байт за {seconds:.3f} с")

    mbps = total_bytes * 8 / total_seconds / 1_000_000
    print(f"Среднее время запроса: {total_seconds / REQUEST_COUNT:.3f} с")
    print(f"Всего скачано: {total_bytes} байт")
    print(f"Скорость скачивания: {mbps:.2f} Мбит/с")
    return 0


if __name__ == "__main__":
    sys.exit(main())
