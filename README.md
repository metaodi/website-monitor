website-monitor
===============

A small script to monitor the contents of a website and get a notification if there are changes.

## Installation

1. Clone this repository
1. Run the `setup.sh` script.sh or install manually the dependencies:

```
source env/bin/activate
pip install -r requirements.py
```

Alternatively 

## Usage

```bash
$ python monitor.py --help
Usage:
  monitor.py --url <url-of-website> [--selector <css-selector>] [--wait <number-of-seconds>] [--verbose] [--no-verify]
  monitor.py (-h | --help)
  monitor.py --version
Options:
  -h, --help                     Show this screen.
  --version                      Show version.
  -u, --url <url-of-website>     URL of the website to monitor.
  -s, --selector <css-selector>  CSS selector to check for changes [default: body].
  -w, --wait <number-of-seconds> Number of seconds to wait until the URL is checked again [default: 30].
  --verbose                      Option to enable more verbose output.
  --no-verify                    Option to disable SSL verification for requests.
```

## Examples

Watch «Amtliche Sammlung» of the City of Zurich:
```bash
python monitor.py --url https://www.stadt-zuerich.ch/portal/de/index/politik_u_recht/amtliche_sammlung.html --selector .mod_newsteaser
```

Ignore SSL certificate errors:
```bash
python monitor.py --url https://metaodi.ch --selector div.content --no-verify
```

Verbose output:
```bash
python monitor.py -u https://www.wikidata.org/wiki/Special:Random --selector span.wikibase-title-label --verbose
```

Check every 5 seconds:
```bash
python monitor.py -u https://www.wikidata.org/wiki/Special:Random --selector span.wikibase-title-label --wait 5
```
