import html
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["PAGESPEED_API_KEY"]
URL = "https://aireadypage.com"
ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def get_page_title(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    match = re.search(r"<title[^>]*>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
    return html.unescape(match.group(1).strip()) if match else None


def main():
    response = requests.get(
        ENDPOINT,
        params={
            "url": URL,
            "strategy": "mobile",
            "key": API_KEY,
        },
    )
    response.raise_for_status()
    data = response.json()

    score = data["lighthouseResult"]["categories"]["performance"]["score"]
    title = get_page_title(URL)

    print(f"Performance score: {round(score * 100)}")
    print(f"Page title: {title}")


if __name__ == "__main__":
    main()
