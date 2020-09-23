#!/usr/bin/python3

import json
import datetime
import re
import sys
import os
from urllib.request import urlopen
from urllib.parse import urlparse

from bs4 import BeautifulSoup


def get_parsedhtml_soup(url, parser='lxml'):
    if hasattr(url, 'read'):
        soup = BeautifulSoup(url, parser)
    elif 'http' in urlparse(url).scheme:
        with urlopen(url) as file:
            soup = BeautifulSoup(file, parser)
    else:
        with open(url, 'r') as file:
            soup = BeautifulSoup(file, parser)
    return soup


def get_domain(soup):
    url = urlparse(soup.find('meta',  property='og:url')['content'])
    return f'{url.scheme}://{url.netloc}'


def get_listofrounds_links(soup):
    domain = get_domain(soup)
    selector = 'h3 + ul + ol > li > a[href*="/forum"]'
    return [domain + link.get('href').replace(domain, '') for link in soup.select(selector)]


def main():
    url = 'https://retropie.org.uk/forum/topic/9011/mame-row-rules-and-list-of-rounds'
    #url = 'https _retropie.org.uk_forum_topic_9011_mame-row-rules-and-list-of-rounds.html'
    start = 0  # 0=first page
    stop = 0  # 0=all
    d_today = str(datetime.datetime.utcnow().date())
    output = f'{os.path.basename(__file__)}-{d_today}.json'
    output_roms = output.replace('.json', '_roms.txt')
    input = output

    if os.path.exists(input):
        with open(input, 'r') as file:
            data = json.loads(file.read())
    else:
        data = []
    data_roms = []

    listofrounds = get_listofrounds_links(get_parsedhtml_soup(url))
    if stop == 0:
        stop = len(listofrounds)
    listofrounds = listofrounds[start:stop]

    for url in listofrounds:
        soup = get_parsedhtml_soup(url)
        page = []
        meta = {
            'title': soup.find('title').text,
            'url': soup.find('meta',  property='og:url')['content'],
            'published': soup.find('meta',  property='article:published_time')['content']
        }

        pass_url = False
        for page_item in data:
            if page_item[0]['url'] == meta['url']:
                print('pass:', meta['url'])
                pass_url = True
                break
        if pass_url == True:
            continue
        print('add:', meta['url'])
        page.append(meta)

        winner = meta['title'].lower()
        winner = re.sub(r'.+#\d+\s*[:-]\s*', '', winner)
        winner = re.sub(r'-\s*retropie forum', '', winner)
        winner = winner.replace(' ', '').strip()

        for element in soup.select('div[class="content"]')[0]:
            game = {}
            if element.name == 'p' and 'Game Name:' in element.text:
                for match in re.findall(r'.+', element.text):
                    if match.isdigit():
                        game['id'] = match.strip()
                    elif 'Game Name:' in match:
                        game['name'] = match.replace('Game Name:', '').strip()
                    elif 'Company:' in match:
                        game['company'] = match.replace('Company:', '').strip()
                    elif 'Year:' in match:
                        game['year'] = match.replace('Year:', '').strip()
                    elif 'ROM file name:' in match:
                        game['romname'] = match.replace('ROM file name:', '').strip()
                    elif 'BIOS:' in match:
                        bios = match.replace('BIOS:', '').strip()
                        if '.zip' not in bios and '-' not in bios:
                            bios += '.zip'
                        game['bios'] = bios
                try:
                    if winner in game['name'].lower().replace(' ', '').strip():
                        game['winner'] = True
                        data_roms.append(game['romname'])
                        if game['bios'] != '-' and game['bios'] is not None:
                            data_roms.append(game['bios'])
                except Exception:
                    pass
                page.append(game)
        data.append(page)

    with open(output, 'w') as file:
        file.write(json.dumps(data, sort_keys=False, indent=4))
        file_path = os.path.abspath(file.name)

    if data_roms:
        with open(output_roms, 'w') as file:
            data_roms = list(set(data_roms))
            data_roms = sorted(data_roms)
            file.write('\n'.join(data_roms))
            file_path = os.path.abspath(file.name)

    return 0

if __name__ == '__main__':
    # Check exit code in Linux shell with (0=success): echo $?
    sys.exit(main())
