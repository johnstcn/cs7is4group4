#!/usr/bin/env python3

import argparse
import datetime
import logging
import os
import os.path
import pathlib
import re
import time
import urllib.request

DEFAULT_URLS = [
    'https://www.met.ie/Open_Data/xml/xConnacht.xml',
    'https://www.met.ie/Open_Data/xml/xMunster.xml',
    'https://www.met.ie/Open_Data/xml/xLeinster.xml',
    'https://www.met.ie/Open_Data/xml/xUlster.xml',
    'https://www.met.ie/Open_Data/xml/xDublin.xml',
]


def fetch(url: str, dest: str):
    with urllib.request.urlopen(url) as resp:
        body = resp.read()
        fpath = pathlib.Path(dest)
        fpath.touch(exist_ok=True)
        with open(fpath, 'wb') as f:
            f.write(body)
            f.flush()

class DailyReportDownloader(object):
    def __init__(self, basedir: str, logger: logging.Logger, interval: int, urls=DEFAULT_URLS):
        super().__init__()
        self.urls = urls
        self.basedir = basedir
        self.logger = logger
        self.interval = interval

    def loop_once(self):
        for url in self.urls:
            try:
                dest_start = url.split('/')[-1].replace('.xml', '')
                dest_end = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                dest = dest_start + '_' + dest_end + '.xml'
                dest_full = os.path.join(self.basedir, dest)
                fetch(url, dest_full)
                self.logger.info('successfully fetched %s -> %s', url, dest_full)
            except Exception as e:
                self.logger.error('fetch %s: %s', url, e, exc_info=1)

    def loop(self):
        while True:
            self.loop_once()
            next_fetch_time = datetime.datetime.now() + datetime.timedelta(seconds=self.interval)
            self.logger.info('next fetch at %s', next_fetch_time.strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(self.interval)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--basedir', default='out', help='path to save fetched data')
    parser.add_argument('--interval', default=3600, help='interval between fetches in seconds')
    parser.add_argument('--log', default='forecast.log', help='path to log file')
    args = parser.parse_args()

    if not os.path.exists(args.basedir):
        os.mkdir(args.basedir)

    logger = logging.getLogger('DailyReportDownloader')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(args.log)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)

    basedir_full = str(pathlib.Path(args.basedir).resolve())

    dl = DailyReportDownloader(
        basedir_full,
        logger,
        args.interval,
    )

    try:
        dl.loop()
    except KeyboardInterrupt:
        raise SystemExit


if __name__ == '__main__':
    main()
