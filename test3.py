# 圧縮ファイルをウェブからダウンロードし解凍 >> テキストファイルを保存
import os
import subprocess
import urllib
import re
from datetime import date, timedelta

import mojimoji as mojimoji
import numpy as np
import pandas as pd
import wget
from Tools.scripts.dutree import display
from lhafile import LhaFile
from pandas._testing import get_dtype


# 圧縮ファイルをウェブからダウンロードし解凍 >> テキストファイルを保存
def download_file(obj, date):
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
            with open(f'downloads/{obj}/{ymd}.txt', 'wb') as file:
                file.write(d)
            archive = None
            os.remove(f'downloads/{obj}/{ymd}.lzh')
        except urllib.request.HTTPError:
            print(f'There are no data for {date}')

def read_file(obj, date):
    """
    obj (str): 'racelists' or 'results'
    """
    date = str(pd.to_datetime(date).date())
    ymd = date.replace('-', '')
    f = open(f'downloads/{obj}/{ymd}.txt', 'r', encoding='cp932')
    Lines = [l.strip().replace('\u3000', '') for l in f]
    Lines = [mojimoji.zen_to_han(l, kana=False) for l in Lines][1:-1]
    lines_by_plc = {}
    for l in Lines:
        if 'BGN' in l:
            place_cd = int(l[:-4])
            lines = []
        elif 'END' in l:
            lines_by_plc[place_cd] = lines
        else:
            lines.append(l)
    return lines_by_plc

place_mapper = {
    1: '桐生', 2: '戸田', 3: '江戸川', 4: '平和島', 5: '多摩川',
    6: '浜名湖', 7: '蒲郡', 8: '常滑', 9: '津', 10: '三国',
    11: '琵琶湖', 12: '住之江', 13: '尼崎', 14: '鳴門', 15: '丸亀',
    16: '児島', 17: '宮島', 18: '徳山', 19: '下関', 20: '若松',
    21: '芦屋', 22: '福岡', 23: '唐津', 24: '大村'
}
def get_results(date):
    conv_racetime = lambda x: np.nan if x == '.' else\
        sum([w * float(v) for w, v in zip((60, 1, 1/10), x.split('.'))])
    info_cols = ['title', 'day', 'date', 'place_cd', 'place']
    race_cols = ['race_no', 'race_type', 'distance']
    keys = ['toban', 'name', 'moter_no', 'boat_no',
            'ET', 'SC', 'ST', 'RT', 'position']
    racer_cols = [f'{k}_{i}' for k in keys for i in range(1, 7)]
    res_cols = []
    for k in ('tkt', 'odds', 'poprank'):
        for type_ in ('1t', '1f1', '1f2', '2t', '2f',
                      'w1', 'w2', 'w3', '3t', '3f'):
            if (k == 'poprank') & (type_ in ('1t', '1f1', '1f2')):
                pass
            else:
                res_cols.append(f'{k}_{type_}')
    res_cols.append('win_method')
    cols = info_cols + race_cols + racer_cols + res_cols

    stack = []
    date = str(pd.to_datetime(date).date())
    for place_cd, lines in read_file('results', date).items():
        min_lines = 26
        if len(lines) < min_lines:
            continue
        title = lines[4]
        day = int(re.findall('第(\d)日', lines[6].replace(' ', ''))[0])
        place = place_mapper[place_cd]
        info = {k: v for k, v in zip(
            info_cols, [title, day, date, place_cd, place])}

        head_list = []
        race_no = 1
        for i, l in enumerate(lines[min_lines:]):
            if f'{race_no}R' in l:
                head_list.append(min_lines + i)
                race_no += 1
        for race_no, head in enumerate(head_list, 1):
            try:
                race_type = lines[head].split()[1]
                distance = int(re.findall('H(\d*)m', lines[head])[0])
                win_method = lines[head + 1].split()[-1]
                _, tkt_1t, pb_1t = lines[head + 10].split()
                _, tkt_1f1, pb_1f1, tkt_1f2, pb_1f2 = lines[head + 11].split()
                _, tkt_2t, pb_2t, _, pr_2t = lines[head + 12].split()
                _, tkt_2f, pb_2f, _, pr_2f = lines[head + 13].split()
                _, tkt_w1, pb_w1, _, pr_w1 = lines[head + 14].split()
                tkt_w2, pb_w2, _, pr_w2 = lines[head + 15].split()
                tkt_w3, pb_w3, _, pr_w3 = lines[head + 16].split()
                _, tkt_3t, pb_3t, _, pr_3t = lines[head + 17].split()
                _, tkt_3f, pb_3f, _, pr_3f = lines[head + 18].split()
                race_vals = [race_no, race_type, distance]
                res_vals = [
                    tkt_1t, tkt_1f1, tkt_1f2, tkt_2t, tkt_2f,
                    tkt_w1, tkt_w2, tkt_w3, tkt_3t, tkt_3f,
                    pb_1t, pb_1f1, pb_1f2, pb_2t, pb_2f,
                    pb_w1, pb_w2, pb_w3, pb_3t, pb_3f,
                    pr_2t, pr_2f, pr_w1, pr_w2, pr_w3,
                    pr_3t, pr_3f, win_method
                ]
                dic = info.copy()
                dic.update(dict(zip(race_cols, race_vals)))
                dic.update(dict(zip(res_cols, res_vals)))
                dic = {k: float(v) / 100 if 'odds' in k else v
                       for k, v in dic.items()}
                for i in range(6):
                    bno, *vals = lines[head + 3 + i].split()[1:10]
                    vals.append(i + 1)
                    keys = ['toban', 'name', 'moter_no', 'boat_no',
                            'ET', 'SC', 'ST', 'RT', 'position']
                    dic.update(zip([f'{k}_{bno}' for k in keys], vals))
                stack.append(dic)
            except IndexError:
                continue
            except ValueError:
                continue
    if len(stack) > 0:
        df = pd.DataFrame(stack)[cols].dropna(how='all')
        repl_mapper = {'K': np.nan, '.': np.nan}
        for i in range(1, 7):
            df[f'ET_{i}'] = df[f'ET_{i}'].replace(repl_mapper)
            df[f'ST_{i}'] = df[f'ST_{i}'].replace(repl_mapper)\
                .str.replace('F', '-').str.replace('L', '1')
            df[f'RT_{i}'] = df[f'RT_{i}'].map(conv_racetime)
        waku = np.array([('{}'*6).format(*v) for v in df[
            [f'SC_{i}' for i in range(1, 7)]].values])
        df['wakunari'] = np.where(waku == '123456', 1, 0)
        df = df.replace({'K': np.nan})
        df.to_csv(f'downloads/results_{date}.csv', index=False, encoding='cp932')
        return df
    else:
        return None

def date_range(start, stop, step = timedelta(1)):
    current = start
    while current < stop:
        yield current
        current += step

for date in date_range(date(2021, 1, 1), date(2021, 12, 31)):
    dstr = date.strftime("%Y-%m-%d")

download_file('results', dstr)
read_file('results', dstr)
get_results(dstr)



