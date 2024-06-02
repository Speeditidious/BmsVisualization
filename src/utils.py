import re
import math
import chardet
import json
import hashlib

def read_json_various_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        data = json.load(f)
    
    return data

def read_file_various_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        data = f.read()
        
    return data

def get_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
            
    return hash_md5.hexdigest()

def extract_data(file_path):
    md5_value = get_md5(file_path)
    bms_data = read_file_various_encoding(file_path)
    
    main_title_match = re.search(r"#TITLE\s*(.*?)\n", bms_data)
    if not main_title_match:
        # 메인 타이틀 없으면 아마 빈 파일 일 듯
        return None
    
    judge_rank = int(re.search(r"#RANK\s+(\d)", bms_data).group(1))
    
    total_match = re.search(r"#TOTAL\s+(\d)", bms_data)
    if total_match:
        total = float(total_match.group(1))
    else:
        total = 0
    
    ln_obj_match = re.search(r"#LNOBJ\s+(\S{2})\n", bms_data)
    if ln_obj_match:
        ln_obj_type = ln_obj_match.group(1)
    else:
        ln_obj_type_match = re.search(r"#LNTYPE\s+(\S+)\n", bms_data)
        ln_obj_type = int(ln_obj_type_match.group(1)) if ln_obj_type_match else 0
        
    random_match = re.search(r"#RANDOM\s+(\d)", bms_data)
    is_random_exist = False
    if random_match:
        is_random_exist = True
    
    '''
    md5: md5 hash value
    bpm: bpm (does not have bpm change information)
    judge_rank: judge rank. {0: VH, 1: H, 2: N, 3: E, 4: VE}
    ln_obj_type: ln_obj or ln_type. ln_type = {0: no ln, 1: ln_type 1, 2: ln_type 2}
    raw_bms_data: raw bms data that contains pattern data
    '''
    return {
        "md5": md5_value,
        "judge_rank": judge_rank,
        "total": total,
        "ln_obj_type": ln_obj_type,
        "is_random_exist": is_random_exist,
        "raw_bms_data": bms_data
    }

def extract_table_data_by_md5(table_file_path, md5):
    table_json_data_list = read_json_various_encoding(table_file_path)
    
    title = ""
    level = ""
    for table_json_data in table_json_data_list:
        table_md5 = table_json_data["md5"]
        if table_md5 == md5:
            title = table_json_data["title"]
            level = table_json_data["folder"]
    
    return {
        "title": title,
        "level": level
    }
    
def hexadecimal_to_decimal(hexadecimal):
    return int(hexadecimal, 16)

def lcm(a, b):
    return a * b // math.gcd(a, b)

def find_lcm_of_numbers_set(numbers_set):
    numbers_set_iter = iter(numbers_set)
    current_lcm = next(numbers_set_iter)
    for number in numbers_set_iter:
        current_lcm = lcm(current_lcm, number)
    return current_lcm

def insert_empty_notes(notes, notes_lcm):
    n = (notes_lcm / len(notes)) - 1
    new_list = []
    for item in notes:
        new_list.append(item)
        for _ in range(n):
            new_list.append("00")
    
    return new_list

def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True