import os
import re
from math import ceil
from itertools import chain

from selenium import webdriver
import requests
from tqdm import tqdm

MAX_WAIT = 5


class Downloader:
    def __init__(self, wait=3):
        self.driver = webdriver.Chrome(executable_path='./chromedriver')
        self.driver.implicitly_wait(wait)

    def download(self, cell_id, outdir='.'):
        url = f'https://cildata.crbs.ucsd.edu/media/images/{cell_id}/{cell_id}.tif'
        resp = requests.get(url, stream=True)
        total = int(resp.headers.get('content-length', 0))
        fname = f'{outdir}/{cell_id}.tif'
        if os.path.isfile(fname):
            "already done"
            if total == os.stat(fname).st_size:
                print(f'Skipping CIL:{cell_id}')
                return
            else:
                os.remove(fname)
        print(f'Downloading CIL:{cell_id} to {fname}')
        with open(fname, 'wb') as file, tqdm(
                desc=fname,
                total=total,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)

    def run(self, keyword):
        try:
            os.mkdir(keyword)
        except:
            pass
        query = keyword.replace(" ", "+")
        base_url = f'http://cellimagelibrary.org/images?k={query}&simple_search=Search'
        page_url = 'http://cellimagelibrary.org/images?k={query}&simple_search=Search&page={page}&per_page=100'
        self.driver.get(base_url)
        self.driver.find_element_by_xpath('//*[@id="browse_header"]/div[1]/div')
        result_text = self.driver.find_element_by_xpath('//*[@id="browse_header"]/div[1]/div').text
        result_cnt = int(re.search(r'\d+', result_text.split('\n')[1])[0])
        print(f'Found {result_cnt} results.')

        for page_num in range(ceil(result_cnt / 100)):
            print(f'Collecting data from page<{page_num+1}>')
            self.driver.get(page_url.format(query=query, page=page_num))
            rows = self.driver.find_elements_by_xpath('/html/body/div[5]/div')[2:-1]
            cell_ids = list(chain.from_iterable([re.findall(r'(?<=CIL:)\d+', row.text) for row in rows]))
            for i, _id in enumerate(cell_ids):
                print(f'[{page_num*100+i+1}/{result_cnt}]', end='')
                self.download(cell_id=_id, outdir=keyword)


if __name__ == '__main__':
    d = Downloader(MAX_WAIT)
    d.run(keyword='phase contrast')
    d.driver.close()
