# SPDX-License-Identifier: CC0-1.0

import requests
import urllib
from bs4 import BeautifulSoup
import sys
import time
import traceback

WEBSITES = ["radio-free-asia", "rfa-mandarin", "rfa-cantonese", "rfa-korean", "rfa-khmer", "rfa-uyghur", "rfa-vietnamese", "rfa-lao", "rfa-burmese", "rfa-tibetan"]
OLD_WEBSITES = ["burmese", "lao", "tibetan"]
# https://www.rfa.org/burmese/story_archive/ https://www.rfa.org/lao/story_archive/ https://www.rfa.org/tibetan/story_archive/ don't use the API. The API still exists for them, though, and this script will use it.

printed_thumbnail_urls = set()
printed_article_urls = set()
printed_misc_urls = set()

pagination_urls_web_api = open("www.rfa.org_pagination_urls_web_api.txt", "w")
pagination_urls_full_api = open("www.rfa.org_pagination_urls_full_api.txt", "w")
article_urls = open("www.rfa.org_article_urls.txt", "w")
thumbnail_urls = open("www.rfa.org_thumbnail_urls.txt", "w")
misc_urls = open("www.rfa.org_misc_urls.txt", "w")

THUMBNAIL_HOST = "https://cloudfront-us-east-1.images.arcpublishing.com/radiofreeasia/"

def recurse_blob(blob):
    if isinstance(blob, dict):
        for k, v in blob.items():
            if k == "website_url" or k == "canonical_url" or k == "short_url":
                if v != "":
                    assert v.startswith("/")
                    url = "https://www.rfa.org" + v
                    if url not in printed_article_urls:
                        print(url, file=article_urls)
                        printed_article_urls.add(url)
            elif k == "url":
                if "auth" in blob:
                    assert isinstance(blob["auth"], dict)
                    assert blob["auth"].keys() == {"1"}
                    # print thumbnail. Remove THUMBNAIL_HOST if present, but other hosts get URL-encoded
                    # https://www.rfa.org/resizer/v2/https%3A%2F%2Fd2m6nhhu3fh4n6.cloudfront.net%2F05-06-2025%2Ft_bb98cbc226a44195ba0a11c093133a99_name_file_540x960_1600_v4_.jpg?auth=ea49415f135c31b61177785c034e51a96640afecbd50d80608ebb90a8780884d&smart=true&width=500&height=375
                    # https://www.rfa.org/resizer/v2/AXITKZE75IGUZUOFFPOPX32T6Q.jpg?auth=d3c54fa459666c2a93498d5471e30a391585581ce022ee4d26a659a285667e41&smart=true&width=500&height=375
                    thumbnail_name = v
                    if thumbnail_name.startswith(THUMBNAIL_HOST):
                        thumbnail_name = thumbnail_name[len(THUMBNAIL_HOST):]
                    thumbnail_name = urllib.parse.quote(thumbnail_name, safe='')
                    url = f'https://www.rfa.org/resizer/v2/{thumbnail_name}?auth={blob["auth"]["1"]}&smart=true&width=500&height=375'
                    if url not in printed_thumbnail_urls:
                        print(url, file=thumbnail_urls)
                        printed_thumbnail_urls.add(url)
            recurse_blob(v)
    elif isinstance(blob, list):
        for v in blob:
            recurse_blob(v)
    elif isinstance(blob, str):
        if blob.startswith("http"):
            if blob not in printed_misc_urls:
                print(blob, file=misc_urls)
                printed_misc_urls.add(blob)

def get_json(url):
    r = None
    try:
        r = requests.get(url, timeout=60)
        assert r.status_code == 200, r.status_code
        data = r.json()
    except Exception as e:
        print(f"  Exception retrieving {url}: {e}; retrying", file=sys.stderr)
        if r != None:
            print(f"  Status code: {r.status_code}; Content-Type: {r.headers.get('content-type')}", file=sys.stderr)
        else:
            print(f"  Response was None", file=sys.stderr)
        if not isinstance(e, requests.exceptions.ReadTimeout):
            traceback.print_exception(e)
        if isinstance(e, KeyboardInterrupt):
            raise
        time.sleep(300)  # avoid cached errors
        r = requests.get(url, timeout=300)
        assert r.status_code == 200, r.status_code
        data = r.json()
    recurse_blob(data)
    return data

def recurse_stories_0(site, date_range, use_filter_param):
    filter_param = ''
    if use_filter_param:
        filter_param = f'&%7Bcontent_elements%7B_id%2Ccredits%7Bby%7Badditional_properties%7Boriginal%7Bbyline%7D%7D%2Cname%2Ctype%2Curl%7D%7D%2Cdescription%7Bbasic%7D%2Cdisplay_date%2Cheadlines%7Bbasic%7D%2Clabel%7Bbasic%7Bdisplay%2Ctext%2Curl%7D%7D%2Cowner%7Bsponsored%7D%2Cpromo_items%7Bbasic%7B_id%2Cauth%7B1%7D%2Ctype%2Curl%7D%2Clead_art%7Bpromo_items%7Bbasic%7B_id%2Cauth%7B1%7D%2Ctype%2Curl%7D%7D%2Ctype%7D%7D%2Ctype%2Cwebsites%7B{site}%7Bwebsite_section%7B_id%2Cname%7D%2Cwebsite_url%7D%7D%7D%2Ccount%2Cnext%7D'
    data = {"next": 0}
    while "next" in data:
        url = f'https://www.rfa.org/pf/api/v3/content/fetch/story-feed-query?query=%7B%22feature%22%3A%22results-list%22%2C%22offset%22%3A{data["next"]}%2C%22query%22%3A%22display_date%3A{date_range}%22%2C%22size%22%3A20%7D{filter_param}&d=105&_website={site}'
        if use_filter_param:
            print(url, file=pagination_urls_web_api)
        else:
            print(url, file=pagination_urls_full_api)
        data = get_json(url)
    print(f'{site} {date_range} had {data["count"]} articles', file=sys.stderr)

def recurse_stories(site):
    for year in range(1998, 2025+1):
        recurse_stories_0(site, f"%5B{year}-01-01%2BTO%2B{year}-12-31%5D", False)
        recurse_stories_0(site, f"%5B{year}-01-01%2BTO%2B{year}-12-31%5D", True)
        for month in range(1, 12+1):
            # The site always assumes 31 days, including for February
            recurse_stories_0(site, f"%5B{year}-{month:02}-01%2BTO%2B{year}-{month:02}-31%5D", False)
            recurse_stories_0(site, f"%5B{year}-{month:02}-01%2BTO%2B{year}-{month:02}-31%5D", True)

def print_old_stories(site, year):
    if year != None:
        start = f'https://www.rfa.org/{site}/story_archive?year={year}'
        page_prefix = f'https://www.rfa.org/{site}/story_archive?year={year}&b_start:int='
    else:
        start = f'https://www.rfa.org/{site}/story_archive'
        page_prefix = f'https://www.rfa.org/{site}/story_archive?b_start:int='

    print(start, file=pagination_urls_web_api)
    text = requests.get(start).text

    soup = BeautifulSoup(text, 'html.parser')
    next_list = soup.find_all(attrs={"class":"next"})
    if len(next_list) == 0:
        # https://www.rfa.org/burmese/story_archive?year=1998 has nothing
        print(f'{start} had no pagination', file=sys.stderr)
        print(f'{page_prefix}0', file=pagination_urls_web_api)
        return
    else:
        assert len(next_list) == 1

    last_list = soup.find_all(attrs={"class":"last"})
    if len(last_list) == 0:
        # https://www.rfa.org/burmese/story_archive?year=2004 has 1/2/3 and next but no last
        pagination_list = soup.find_all(attrs={"class":"pagination"})
        assert len(pagination_list) == 1
        pages = pagination_list[0].find_all("a")
        print(f'{page_prefix}0', file=pagination_urls_web_api)
        # will include the next button as well as pages, which means one duplicated URL, meh
        for page in pages:
            print(page.get("href"), file=pagination_urls_web_api)
        print(f'{start} had only {len(pages)} pages', file=sys.stderr)
        return
    else:
        assert len(last_list) == 1

    next_page = next_list[0].find("a").get("href")
    last_page = last_list[0].find("a").get("href")

    assert next_page.startswith(page_prefix)
    next_offset = int(next_page[len(page_prefix):])
    assert last_page.startswith(page_prefix)
    last_offset = int(last_page[len(page_prefix):])

    for offset in range(0, last_offset+next_offset, next_offset):
        print(f'{page_prefix}{offset}', file=pagination_urls_web_api)

    print(f'{start} had {last_offset} entries at {next_offset} per page', file=sys.stderr)

for site in OLD_WEBSITES:
    print_old_stories(site, None)
    for year in range(1998, 2025+1):
        print_old_stories(site, year)

for site in WEBSITES:
    for heirarchy_url in [
        "https://www.rfa.org/pf/api/v3/content/fetch/site-service-hierarchy?query=%7B%22feature%22%3A%22footer%22%2C%22hierarchy%22%3A%22footer%22%2C%22sectionId%22%3A%22%22%7D&filter=%7Bchildren%7B_id%2Cchildren%7B_id%2Cdisplay_name%2Cname%2Cnode_type%2Curl%7D%2Cdisplay_name%2Cname%2Cnode_type%2Curl%7D%7D&d=105&_website=",
        "https://www.rfa.org/pf/api/v3/content/fetch/site-service-hierarchy?query=%7B%22feature%22%3A%22footer%22%2C%22hierarchy%22%3A%22footer%22%7D&filter=%7Bchildren%7B_id%2Cchildren%7B_id%2Cdisplay_name%2Cname%2Cnode_type%2Curl%7D%2Cdisplay_name%2Cname%2Cnode_type%2Curl%7D%7D&d=105&_website=",
        "https://www.rfa.org/pf/api/v3/content/fetch/site-service-hierarchy?query=%7B%22feature%22%3A%22header-nav-chain%22%2C%22hierarchy%22%3A%22hamburger-menu%22%7D&filter=%7Bchildren%7B_id%2Cchildren%7B_id%2Cdisplay_name%2Cname%2Cnode_type%2Curl%7D%2Cdisplay_name%2Cname%2Cnode_type%2Curl%7D%7D&d=105&_website=",
        "https://www.rfa.org/pf/api/v3/content/fetch/site-service-hierarchy?query=%7B%22feature%22%3A%22links-bar%22%2C%22hierarchy%22%3A%22links-bar%22%7D&filter=%7Bchildren%7B_id%2Cdisplay_name%2Cname%2Cnode_type%2Curl%7D%7D&d=105&_website="
    ]:
        print(heirarchy_url + site, file=pagination_urls_web_api)
        get_json(heirarchy_url + site)
    recurse_stories(site)
