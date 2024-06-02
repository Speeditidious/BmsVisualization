'''
로컬 폴더에서 bms 파일들 다운로드
'''

import os
import shutil
from tqdm import tqdm
import json

# 폴더 지정
'''
SOURCE_FOLDER_PATH: 어디에 있는 파일들 가져올 것인지
TARGET_FOLDER_PATH: 어디에다가 추출할 것인지
TABLE_JSON_PATH: 난이도표 data.json 경로
'''
# ------------------------------------------------------------
SOURCE_FOLDER_PATH = "/mnt/c/Users/jhjh3/Desktop/Desktop/Games/BMS/Songs/Aery5Key/"
TARGET_FOLDER_PATH = "./pattern_dataset/"
TABLE_JSON_PATH = "./aery_table/data.json"
# ------------------------------------------------------------

valid_extension_tuple = (".bms", ".bme", ".bml", ".BMS")

print("Removing existing BMS data...")
for filename in os.listdir(TARGET_FOLDER_PATH):
    file_path = os.path.join(TARGET_FOLDER_PATH, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f'Failed to delete {file_path}. Reason: {e}')

print("Extracting BMS data...")
for i, (foldername, subfolders, filenames) in enumerate(tqdm(list(os.walk(SOURCE_FOLDER_PATH)), desc="directory")):
    for filename in filenames:
        if filename.endswith(valid_extension_tuple):
            file_path = os.path.join(foldername, filename)
            destination_path = os.path.join(TARGET_FOLDER_PATH, f'{i}_{filename}')
            shutil.copy(file_path, destination_path)
            
file_num = 0
for foldername, subfolders, filenames in tqdm(list(os.walk(TARGET_FOLDER_PATH)), desc="directory"):
    for filename in filenames:
        file_num += 1

print("Done extracting...")
print("총 추출한 파일 개수:", file_num)

with open(TABLE_JSON_PATH, "r") as f:
    aery_table_json = json.load(f)

print("난이도표에 등록된 데이터 개수:", len(aery_table_json))