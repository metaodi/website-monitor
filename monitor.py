import hashlib
import time
import logging
from win10toast import ToastNotifier
from bs4 import BeautifulSoup
import download as dl

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

url = 'https://www.stadt-zuerich.ch/portal/de/index/politik_u_recht/amtliche_sammlung.html'

old_hash = ''
while True:
    content = dl.download_content(url)
    soup = BeautifulSoup(content, 'html.parser')
    as_list = soup.select_one('.mod_newsteaser')
    log.debug(as_list.prettify())
    new_hash = hashlib.sha256(str(as_list).encode('utf-8')).hexdigest()
    log.info(f"Hash: {new_hash}")
    if old_hash != new_hash:
        log.info(f"Hash changed!")
        toast = ToastNotifier()
        toast.show_toast("Amtliche Sammlung","Liste der letzten Einträge hat sich geändert", duration=20)
    old_hash = new_hash
    time.sleep(30)





