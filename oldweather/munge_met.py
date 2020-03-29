#!/usr/bin/env python3

import argparse
import csv
import datetime
import re
import sys

import lxml.html
import lxml.etree as etree

class MetMunger(object):
    def __init__(self, writer, fnames):
        super().__init__()
        self.writer = writer
        self.fnames = fnames

    def process(self):
        for fname in self.fnames:
            with open(fname, encoding="latin1") as f:
                self.process_file(f)

    def process_file(self, f):
        contents = f.read()
        et = etree.HTML(contents)
        nodes = et.cssselect("td.maincontent")
        for node in nodes:
            text = etree.tostring(node, method="text", encoding=str).strip()
            self.munge(text)

    def munge(self, raw_text):
        date_expr = re.compile(r"(?is)^.*?(\S+, \d+ \S+ \d{4})")
        today_expr = re.compile(r"(?is)^.*?(today\s.+?)\smore")
        post_date = "".join(date_expr.findall(raw_text)).strip()
        today_forecast = "".join(today_expr.findall(raw_text)).strip()
        today_forecast = today_forecast.replace("Tonight", "Tonight ")
        if not (post_date and today_forecast):
            return

        parsed_date = datetime.datetime.strptime(post_date.strip(), "%A, %d %B %Y")
        self.to_csv([parsed_date.strftime("%Y-%m-%d"), "met", today_forecast])

    def to_csv(self, row):
        self.writer.writerow(row)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, nargs="+")
    args = parser.parse_args()

    writer = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    writer.writerow(["date", "source", "forecast"])
    munger = MetMunger(writer, args.input)
    munger.process()


if __name__ == "__main__":
    main()

