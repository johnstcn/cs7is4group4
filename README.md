# CS7IS4 2020 Group 4 Git Repository

This repository contains the source code and supporting material for the group project of CS7IS4 Group 4, 2020.

## Paper

Run the command `make` to build the paper.

In order to build the group contribution document, the authors' signatures need to be added to the `./signatures` folder. These are not available in the public version of this repository for obvious reasons.

## Supporting Data

Supporting data for the paper is available in both the `./data` and `./oldweather` folders.

* `./data/boards_mtcranium_forecast_2018.csv` contains extracted forecasts from `boards.ie`.
* `./data/met_forecast_waybackmachine_partial_2018.csv` contains extracted forecast data from archived snapshots of [the MET Eireann homepage](https://www.met.ie).
* `./data/forecasts_with_features.csv` contains the above data, annotated with semantic features.
* `./data/twitter_*.csv` contains extracted data from the Internet Archive's grab of the Twitter Spritzer, available [here](https://archive.org/details/twitterstream).
* `oldwea

## Data Processing

There are a number of scripts used to process both the weather and Twitter data:
* `./oldweather/munge_boards.py` extracts the weather forecasts from the print versions of the `boards.ie` weather thread, stored under `./oldweather/boards_mtcranium`. 
* `./oldweather/munge_met.py` extracts the weather forecasts from the stored snapshots of the Met Eireann homepage under `./oldweather/www.met.ie`.
* `./oldweather/weather_features.py` extracts a number of semantic categories from the output of the above two scripts. 
* `./twittermunger/main.go` is a Golang program used to extract Tweets matching particular criteria from the Twitter TAR archives. These are not included in this repository due to size limitations, but can be downloaded separately. 
* `./colab-notebook/TA_G4.ipynb` is a saved version of the Jupyter notebook used for performing more in-depth exploratory analysis on both the annotated weather forecast dataset and Twitter dataset.

## How To Run All Of This

### Jupyter Notebook

The Jupyter notebook can be uploaded to [Google Colaboratory](https://colab.research.google.com/) and viewed directly there.

### Weather Mungers
In the case of the Python scripts, or if you wish to run the Jupyter notebook locally, you need a Python 3 environment. If you don't have one set up, see [the Python website](https://python.org) for more information on doing so. 

Each of the Python scripts accepts a `--help` command-line argument which will provide documentation on the required arguments of the script. Both 

Example: to extract the Boards.ie forecast data from `118.html` and save it to `boards118.csv`:
```
./munge_boards.py boards_mtcranium/118.html | tee boards118.csv
```

The 

### Twitter Munger

In the case of the `twittermunger` program, a working Go toolchain (>=1.13) is required to build the program. Pre-built binaries (using [mitchellh/gox](https://github.com/mitchellh/gox)) for 64-bit Linux, MacOS and Windows are provided.

Example: to extract only Tweets posted in Iceland containing the string "Eyjafjallajökull" in the TAR archive `twitter.tar` and save them to iceland.csv:
```
twittermunger -country IS -searchexpr 'Eyjafjallajökull' twitter.tar | tee iceland.csv
```
