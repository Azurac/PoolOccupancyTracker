import requests
from bs4 import BeautifulSoup

URL = "https://www.kravihora-brno.cz/kryta-plavecka-hala"


def fetch_occupancy() -> int | None:
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for p in soup.find_all("p"):
            text = p.get_text(strip=True).lower()

            if text.startswith("obsazenost"):
                strong = p.find("strong")
                if not strong:
                    continue

                value_text = strong.get_text(strip=True)  # e.g. "0 / 135"

                if "/" not in value_text:
                    return None

                current = int(value_text.split("/")[0].strip())
                return current

        return None

    except Exception as e:
        print(f"[SCRAPER ERROR] {e}")
        return None
