import os
import subprocess
import urllib
import re
import mojimoji
import numpy as np
import pandas as pd
import wget
from Tools.scripts.dutree import display
from lhafile import LhaFile
from pandas._testing import get_dtype
from datetime import date, timedelta

def date_range(start, stop, step=timedelta(days=1)):
    current = start
    while current <= stop:
        yield current
        current += step

def download_file(obj, date):
    """
    obj (str): 'racelists' or 'results'
    """
    date = str(pd.to_datetime(date).date())
    ymd = date.replace('-', '')
    S, s = ('K', 'k') if obj == 'results' else ('B', 'b')
    if os.path.exists(f'D:/BoatRace/racelist_txt/{obj}/{ymd}.txt'):
        return
    else:
        os.makedirs(f'D:/BoatRace/racelist_txt/{obj}', exist_ok=True)
        try:
            url_t = f'http://www1.mbrace.or.jp/od2/{S}/'
            url_b = f'{ymd[:-2]}/{s}{ymd[2:]}.lzh'
            wget.download(url_t + url_b, f'D:/BoatRace/racelist_txt/{obj}/{ymd}.lzh')
            archive = LhaFile(f'D:/BoatRace/racelist_txt/{obj}/{ymd}.lzh')
            d = archive.read(archive.infolist()[0].filename)
            with open(f'D:/BoatRace/racelist_txt/{obj}/{ymd}.txt', 'wb') as file:
                file.write(d)
            archive = None
            os.remove(f'D:/BoatRace/racelist_txt/{obj}/{ymd}.lzh')
        except urllib.request.HTTPError:
            print(f'There are no data for {date}')

def read_file(obj, date):
    """
    obj (str): 'racelists' or 'results'
    """
    date = str(pd.to_datetime(date).date())
    ymd = date.replace('-', '')
    f = open(f'D:/BoatRace/racelist_txt/{obj}/{ymd}.txt', 'r', encoding='cp932')
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

# 出走表ファイルのフォーマットを解析し、いい感じにテーブルに変形して出力
place_mapper = {
    1: '桐生', 2: '戸田', 3: '江戸川', 4: '平和島', 5: '多摩川',
    6: '浜名湖', 7: '蒲郡', 8: '常滑', 9: '津', 10: '三国',
    11: '琵琶湖', 12: '住之江', 13: '尼崎', 14: '鳴門', 15: '丸亀',
    16: '児島', 17: '宮島', 18: '徳山', 19: '下関', 20: '若松',
    21: '芦屋', 22: '福岡', 23: '唐津', 24: '大村'
}

def get_racelists(date):
    info_cols = ['title', 'day', 'date', 'place_cd', 'place']
    race_cols = ['race_no', 'race_type', 'distance', 'deadline']
    keys = ['toban', 'name', 'area', 'class', 'age', 'weight',
            'glob_win', 'glob_in2', 'loc_win', 'loc_in2',
            'moter_no', 'moter_in2', 'boat_no', 'boat_in2']
    racer_cols = [f'{k}_{i}' for k in keys for i in range(1, 7)]
    cols = info_cols + race_cols + racer_cols

    stack = []
    date = str(pd.to_datetime(date).date())
    for place_cd, lines in read_file('racelists', date).items():
        min_lines = 11
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
                deadline = re.findall('電話投票締切予定(\d*:\d*)', lines[head])[0]
                arr = []
                for l in lines[head + 5: head + 11]:
                    split = re.findall('\d \d{4}.*\d\d\.\\d\d', l)[0].split()
                    bno = [0]
                    name, area, cls1 = [e for e in re.findall(
                        '[^\d]*', split[1]) if e != '']
                    toban, age, wght, cls2 = [e for e in re.findall(
                        '[\d]*', split[1]) if e != '']
                    tmp = [toban, name, area, cls1 + cls2, age, wght] + split[2:10]
                    if len(tmp) == 14:
                        arr.append(tmp)
                    else:
                        continue
                if len(arr) == 6:
                    dic = info.copy()
                    dic.update(zip(race_cols, [race_no, race_type, distance, deadline]))
                    dic.update(dict(zip(racer_cols, np.array(arr).T.reshape(-1))))
                    stack.append(dic)
            except IndexError:
                continue
            except ValueError:
                continue
    if len(stack) > 0:
        df = pd.DataFrame(stack)[cols].dropna()
        class_mapping = {'B2': 4, 'B1': 3, 'A2': 2, 'A1': 1, '群馬': 1, '埼玉': 2, '東京': 3, '静岡': 4, '愛知': 5, '三重': 6, '福井': 7, '滋賀': 8,
                         '大阪': 9, '兵庫': 10, '岡山': 11, '広島': 12, '山口': 13, '徳島': 14, '香川': 15,
                         '福岡': 16, '佐賀': 17, '長崎': 18}
        df['class_no_1'] = df['class_1'].map(class_mapping)
        df['class_no_2'] = df['class_2'].map(class_mapping)
        df['class_no_3'] = df['class_3'].map(class_mapping)
        df['class_no_4'] = df['class_4'].map(class_mapping)
        df['class_no_5'] = df['class_5'].map(class_mapping)
        df['class_no_6'] = df['class_6'].map(class_mapping)
        df['area_no_1'] = df['area_1'].map(class_mapping)
        df['area_no_2'] = df['area_2'].map(class_mapping)
        df['area_no_3'] = df['area_3'].map(class_mapping)
        df['area_no_4'] = df['area_4'].map(class_mapping)
        df['area_no_5'] = df['area_5'].map(class_mapping)
        df['area_no_6'] = df['area_6'].map(class_mapping)
        df.to_csv(f'D:/BoatRace/racelist/racelist_2022/racelist_{date}.csv', index=False, encoding='cp932')
        return df
    else:
        return None

start_date = date(2022, 1, 1)
end_date = date(2022, 12, 31)

# date_range 関数を使用して日付を生成
for d in date_range(start_date, end_date):
    date_str = d.strftime("%Y-%m-%d")
    download_file('racelists', date_str)
    read_file('racelists', date_str)
    get_racelists(date_str)




