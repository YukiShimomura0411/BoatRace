import os
import subprocess
import urllib
import re

import mojimoji as mojimoji
import numpy as np
import pandas as pd
import wget
from Tools.scripts.dutree import display
from lhafile import LhaFile, lhafile
from pandas._testing import get_dtype

def download_file(obj, date):
    """
    obj (str): 'racelists' or 'results'
    """
    date = str(pd.to_datetime(date).date())
    ymd = date.replace('-', '')
    S, s = ('K', 'k') if obj == 'results' else ('B', 'b')
    if os.path.exists(f'downloads/{obj}/{ymd}.txt'):
        return
    else:
        os.makedirs(f'downloads/{obj}', exist_ok=True)
        try:
            url_t = f'http://www1.mbrace.or.jp/od2/{S}/'
            url_b = f'{ymd[:-2]}/{s}{ymd[2:]}.lzh'
            wget.download(url_t + url_b, f'downloads/{obj}/{ymd}.lzh')
            archive = LhaFile(f'downloads/{obj}/{ymd}.lzh')
            d = archive.read(archive.infolist()[0].filename)
            u = open(f'downloads/{obj}/{ymd}.txt', 'wb')
            u.close()
            os.remove(f'downloads/{obj}/{ymd}.lzh')
        except urllib.request.HTTPError:
            print(f'There are no data for {date}')

download_file('racelists', '2023-11-04')