#!/usr/bin/env python3

import argparse
import csv
import datetime
import re
import sys

from lxml import etree

class BoardsMunger(object):
    def __init__(self, writer, fnames):
        super().__init__()
        self.writer = writer
        self.fnames = fnames

    def process(self):
        for fname in self.fnames:
            with open(fname) as f:
                self.process_file(f)

    def process_file(self, f):
        contents = f.read()
        et = etree.HTML(contents)
        nodes = et.cssselect("table.tborder td.page")
        for node in nodes:
            text = etree.tostring(node, method="text", encoding=str).strip()
            if not text.lower().startswith("m.t. cranium"):
                continue
            self.munge(text)

    def munge(self, raw_text):
        date_expr = re.compile(r"(?is)^.*?(\d+-\d+-\d+)")
        today_expr = re.compile(r"(?is)^.*?(today\s.+?)\stonight")
        post_date = "".join(date_expr.findall(raw_text)).strip()
        today_forecast = "".join(today_expr.findall(raw_text)).strip()
        if not (post_date and today_forecast):
            return

        parsed_date = datetime.datetime.strptime(post_date, "%d-%m-%Y")
        self.to_csv([parsed_date.strftime("%Y-%m-%d"), "boards", today_forecast])

    def to_csv(self, row):
        self.writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, nargs="+")
    args = parser.parse_args()

    writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    writer.writerow(["date", "source", "forecast"])
    munger = BoardsMunger(writer, args.input)
    munger.process()


if __name__ == "__main__":
    main()

