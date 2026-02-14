website-monitor
===============

## GitHub Action to monitor a list of websites

This repository contains CSVs in the `csv` directory, which are used to define a list of websites to monitor.
The files is parsed on a regular basis (see the workflow file for details) and a notification is sent via Telegram if a change has been detected.

### WireGuard VPN Support

The GitHub Action supports routing requests through a WireGuard VPN connection. This is useful for monitoring websites that are only accessible from specific geographic regions (e.g., geo-restricted content).

To use WireGuard with the website monitor:

1. **Prepare your WireGuard configuration file** (`.conf` file from your VPN provider, e.g., ProtonVPN)
2. **Encode the configuration file to base64**:
   ```bash
   base64 -w 0 your-config.conf
   ```
3. **Add the following secret to your repository**:
   - `WIREGUARD_CONFIG`: The base64-encoded WireGuard configuration file

4. **Pass the secret to the workflow**:
   ```yaml
   jobs:
     notify_websites:
       uses: metaodi/website-monitor/.github/workflows/check_websites.yml@main
       with:
         csv-path: csv/your-sites.csv
       secrets:
         TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
         TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_TO }}
         TELEGRAM_ERROR_CHAT_ID: ${{ secrets.TELEGRAM_ERROR_CHAT_ID }}
         WIREGUARD_CONFIG: ${{ secrets.WIREGUARD_CONFIG }}
   ```

The VPN connection will be established before checking websites and terminated after all checks are complete.

### CSV format

The CSV must have the following structure:

```
label,active,error_count,url,selector,type,proxy,hash
```

* `label`: a label or title of the website
* `active`: used to enable or disable this entry, use values `yes` or `no`
* `error_count`: The number of times an error has occured for this entry
* `url`: the actual URL of the website
* `selector`: as CSS selector for elements on the website
* `type`: determines the type of the website, use `static` for static websites or `dynamic` for websites, that load most of their contant at runtime. Dynamic websites will be parsed using Selenium. Use `static` as a default.
* `proxy`: used to enable or disable the proxy, use values `yes` or `no`
* `hash`: The hash of the previous run. Make sure to always provide a value (use a dummy value for new entries)

Example:

| `label`              | `active` | `error_count` | `url`                                         | `selector`       | `type` | `hash`                                                           |
|----------------------|----------|---------------|-----------------------------------------------|------------------|--------|------------------------------------------------------------------|
| "Thalwil informiert" | yes      | 0             | https://www.thalwil.ch/aktuellesinformationen | #informationList | static | db60b21849b715eb4c12d75f285d460de6dfbc17b9429f8f0bfcc78fca76cb2e |

## Script to watch for changes in website (`monitor.py`)
A small script to monitor the contents of a website and get a notification if there are changes.

### Installation

1. Clone this repository
1. Run the `setup.sh` script.sh or install manually the dependencies:

```
source env/bin/activate
pip install -r requirements.py
``` 

### Usage

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

### Examples

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
