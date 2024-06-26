# 圧縮ファイルをウェブからダウンロードし解凍 >> テキストファイルを保存
import csv
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

def date_range(start, stop, step=timedelta(days=1)):
    current = start
    while current <= stop:
        yield current
        current += step

# 圧縮ファイルをウェブからダウンロードし解凍 >> テキストファイルを保存
def download_file(obj, date):
    date = str(pd.to_datetime(date).date())
    ymd = date.replace('-', '')
    S, s = ('K', 'k') if obj == 'results' else ('B', 'b')
    if os.path.exists(f'D:/BoatRace/result_txt/{obj}/{ymd}.txt'):
        return
    else:
        os.makedirs(f'D:/BoatRace/result_txt/{obj}', exist_ok=True)
        try:
            url_t = f'http://www1.mbrace.or.jp/od2/{S}/'
            url_b = f'{ymd[:-2]}/{s}{ymd[2:]}.lzh'
            wget.download(url_t + url_b, f'D:/BoatRace/result_txt/{obj}/{ymd}.lzh')
            archive = LhaFile(f'D:/BoatRace/result_txt/{obj}/{ymd}.lzh')
            d = archive.read(archive.infolist()[0].filename)
            with open(f'D:/BoatRace/result_txt/{obj}/{ymd}.txt', 'wb') as file:
                file.write(d)
            archive = None
            os.remove(f'D:/BoatRace/result_txt/{obj}/{ymd}.lzh')
        except urllib.request.HTTPError:
            print(f'There are no data for {date}')

def read_file(obj, date):
    """
    obj (str): 'racelists' or 'results'
    """
    date = str(pd.to_datetime(date).date())
    ymd = date.replace('-', '')
    f = open(f'D:/BoatRace/result_txt/{obj}/{ymd}.txt', 'r', encoding='cp932')
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
    race_cols = ['race_no', 'race_type', 'distance', 'weather', 'wind', 'wind_strength', 'wave']
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
                if "進入固定" in lines[head]:
                    weather = lines[head].split()[4]
                else:
                    weather = lines[head].split()[3]
                if "進入固定" in lines[head]:
                    wind = lines[head].split()[6]
                else:
                    wind = lines[head].split()[5]
                if "進入固定" in lines[head]:
                    wind_strength = lines[head].split()[7]
                else:
                    wind_strength = lines[head].split()[6]
                if "進入固定" in lines[head]:
                    wave = lines[head].split()[9]
                else:
                    wave = lines[head].split()[8]
                _, tkt_1t, pb_1t = lines[head + 10].split()
                _, tkt_1f1, pb_1f1, tkt_1f2, pb_1f2 = lines[head + 11].split()
                _, tkt_2t, pb_2t, _, pr_2t = lines[head + 12].split()
                _, tkt_2f, pb_2f, _, pr_2f = lines[head + 13].split()
                _, tkt_w1, pb_w1, _, pr_w1 = lines[head + 14].split()
                tkt_w2, pb_w2, _, pr_w2 = lines[head + 15].split()
                tkt_w3, pb_w3, _, pr_w3 = lines[head + 16].split()
                _, tkt_3t, pb_3t, _, pr_3t = lines[head + 17].split()
                _, tkt_3f, pb_3f, _, pr_3f = lines[head + 18].split()
                race_vals = [race_no, race_type, distance, weather, wind, wind_strength, wave]
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
        df['tkt_2t'] = df['tkt_2t'].apply(lambda x: f"'{x}")
        df['tkt_2f'] = df['tkt_2f'].apply(lambda x: f"'{x}")
        df['tkt_w1'] = df['tkt_w1'].apply(lambda x: f"'{x}")
        df['tkt_w2'] = df['tkt_w2'].apply(lambda x: f"'{x}")
        df['tkt_w3'] = df['tkt_w3'].apply(lambda x: f"'{x}")
        df['tkt_3t'] = df['tkt_3t'].apply(lambda x: f"'{x}")
        df['tkt_3f'] = df['tkt_3f'].apply(lambda x: f"'{x}")
        df['win_method_逃げ'] = df['win_method'].apply(lambda x: 1 if x == '逃げ' else 0)
        df['win_method_まくり'] = df['win_method'].apply(lambda x: 1 if x == 'まくり' else 0)
        df['win_method_まくり差し'] = df['win_method'].apply(lambda x: 1 if x == 'まくり差し' else 0)
        df['win_method_差し'] = df['win_method'].apply(lambda x: 1 if x == '差し' else 0)
        df['win_method_抜き'] = df['win_method'].apply(lambda x: 1 if x == '抜き' else 0)
        df['win_method_恵まれ'] = df['win_method'].apply(lambda x: 1 if x == '恵まれ' else 0)
        df['weather_晴'] = df['weather'].apply(lambda x: 1 if x == '晴' else 0)
        df['weather_曇り'] = df['weather'].apply(lambda x: 1 if x == '曇り' else 0)
        df['weather_雨'] = df['weather'].apply(lambda x: 1 if x == '雨' else 0)
        df['wind_東'] = df['wind'].apply(lambda x: 1 if x == '東' else 0)
        df['wind_西'] = df['wind'].apply(lambda x: 1 if x == '西' else 0)
        df['wind_南'] = df['wind'].apply(lambda x: 1 if x == '南' else 0)
        df['wind_北'] = df['wind'].apply(lambda x: 1 if x == '北' else 0)
        df['wind_南東'] = df['wind'].apply(lambda x: 1 if x == '南東' else 0)
        df['wind_南西'] = df['wind'].apply(lambda x: 1 if x == '南西' else 0)
        df['wind_北西'] = df['wind'].apply(lambda x: 1 if x == '北西' else 0)
        df['wind_北東'] = df['wind'].apply(lambda x: 1 if x == '北東' else 0)
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
        df.to_csv(f'D:/BoatRace/result/result_2023/result_{date}.csv', index=False, encoding='cp932')
        return df
    else:
        return None


# 開始日と終了日を指定
start_date = date(2020, 1, 19)
end_date = date(2020, 1, 19)

# date_range 関数を使用して日付を生成
for d in date_range(start_date, end_date):
    date_str = d.strftime("%Y-%m-%d")
    download_file('results', date_str)
    read_file('results', date_str)
    get_results(date_str)