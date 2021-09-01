import hashlib
import time
from win10toast import ToastNotifier
from bs4 import BeautifulSoup
import download as dl

url = 'https://www.stadt-zuerich.ch/portal/de/index/politik_u_recht/amtliche_sammlung.html'

old_hash = ''
while True:
    content = dl.download_content(url)
    soup = BeautifulSoup(content, 'html.parser')
    as_list = soup.select_one('.mod_newsteaser')
    #print(as_list.prettify())
    new_hash = hashlib.sha256(str(as_list).encode('utf-8')).hexdigest()
    print(f"Hash: {new_hash}")
    if old_hash != new_hash:
        print(f"Hash changed!")
        toast = ToastNotifier()
        toast.show_toast("Amtliche Sammlung","Liste der letzten Einträge hat sich geändert", duration=20)
    old_hash = new_hash
    time.sleep(30)





