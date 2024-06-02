import os
import re
import utils
import json
from collections import Counter
from tqdm import tqdm

def split_pattern_by_keysound(pattern):
    return [pattern[i:i+2] for i in range(0, len(pattern), 2)]

def preprocess_note_pattern_type_obj(extracted_pattern_by_bar, ln_obj_type):
    is_drawing_ln_list = [False for i in range(5)]
    for pattern_per_bar in extracted_pattern_by_bar[::-1]:
        bar_index = extracted_pattern_by_bar.index(pattern_per_bar)
        for pattern_line in pattern_per_bar:
            if re.match(r"#\d{3}1\d:", pattern_line):
                line_index = pattern_per_bar.index(pattern_line)
                key_num = int(pattern_line[5])
                pattern_split_by_keysound = split_pattern_by_keysound(pattern_line.split(":")[1])
                for i in range(len(pattern_split_by_keysound) - 1, -1, -1):
                    if is_drawing_ln_list[key_num - 1]:
                        if pattern_split_by_keysound[i] == "00":
                            pattern_split_by_keysound[i] = '2'
                        else:
                            pattern_split_by_keysound[i] = '3'
                            is_drawing_ln_list[key_num - 1] = False
                    else:
                        if pattern_split_by_keysound[i] == "00":
                            pattern_split_by_keysound[i] = '0'
                        elif pattern_split_by_keysound[i] == ln_obj_type:
                            is_drawing_ln_list[key_num - 1] = True
                            pattern_split_by_keysound[i] = '4'
                        else:
                            pattern_split_by_keysound[i] = '1'
                extracted_pattern_by_bar[bar_index][line_index] = pattern_line.split(":")[0] + ":" + "".join(pattern_split_by_keysound)

    return extracted_pattern_by_bar
                    
def preprocess_note_pattern_type_1(extracted_pattern_by_bar):
    is_drawing_ln_list = [False for i in range(5)]
    for pattern_per_bar in extracted_pattern_by_bar[::-1]:
        bar_index = extracted_pattern_by_bar.index(pattern_per_bar)
        for line_index, pattern_line in enumerate(pattern_per_bar):
            if re.match(r"#\d{3}1\d:", pattern_line):
                pattern_split_by_keysound = split_pattern_by_keysound(pattern_line.split(":")[1])
                extracted_pattern_by_bar[bar_index][line_index] = pattern_line.split(":")[0] + ":" + "".join(['0' if keysound == '00' else '1' for keysound in pattern_split_by_keysound])
            elif re.match(r"#\d{3}5\d:", pattern_line):
                key_num = int(pattern_line[5])
                pattern_split_by_keysound = split_pattern_by_keysound(pattern_line.split(":")[1])
                for i in range(len(pattern_split_by_keysound) - 1, -1, -1):
                    if is_drawing_ln_list[key_num - 1]:
                        if pattern_split_by_keysound[i] == "00":
                            pattern_split_by_keysound[i] = '2'
                        else:
                            pattern_split_by_keysound[i] = '3'
                            is_drawing_ln_list[key_num - 1] = False
                    else:
                        if pattern_split_by_keysound[i] == "00":
                            pattern_split_by_keysound[i] = '0'
                        else:
                            pattern_split_by_keysound[i] = '4'
                            is_drawing_ln_list[key_num - 1] = True
                extracted_pattern_by_bar[bar_index][line_index] = pattern_line.split(":")[0] + ":" + "".join(pattern_split_by_keysound)
                        
    return extracted_pattern_by_bar

def insert_omit_key_pattern(extracted_pattern_by_bar, mode="note"):
    if mode == "note":
        re_pattern = r"#\d{3}1\d:"
        obj_str = "1"
    elif mode == "ln":
        re_pattern = r"#\d{3}5\d:"
        obj_str = "5"
    
    last_note_pattern_bar_num = "-1"
    for bar_index, pattern_per_bar in enumerate(extracted_pattern_by_bar):
        previous_key_num = 0
        last_note_pattern_index = -1
        for line_index, pattern_line in enumerate(pattern_per_bar):
            if re.match(re_pattern, pattern_line):
                key_num = int(pattern_line[5])
                last_note_pattern_bar_num = pattern_line[1:4]
                last_note_pattern_index = line_index
                for i in range(key_num - previous_key_num - 1, 0, -1):
                    omit_key_pattern_to_insert = pattern_line[:5] + str((i + previous_key_num)) + ":00"
                    extracted_pattern_by_bar[bar_index].insert(line_index, omit_key_pattern_to_insert)
                    last_note_pattern_index += 1
                previous_key_num = key_num

        if previous_key_num != 5:
            if previous_key_num == 0:
                last_note_pattern_bar_num = "{:03}".format(int(last_note_pattern_bar_num) + 1)
            for i in range(5 - previous_key_num, 0, -1):
                omit_key_pattern_to_insert = "#" + last_note_pattern_bar_num + obj_str + str(i + previous_key_num) + ":00"
                extracted_pattern_by_bar[bar_index].insert(last_note_pattern_index + 1, omit_key_pattern_to_insert)
            if previous_key_num != 0:
                last_note_pattern_bar_num = "{:03}".format(int(last_note_pattern_bar_num) + 1)
             
    return extracted_pattern_by_bar

def insert_omit_bar(extracted_pattern_by_bar, mode="note"):
    if mode == "note":
        re_pattern = r"#\d{3}1\d:"
        obj_str = "1"
    elif mode == "ln":
        re_pattern = r"#\d{3}5\d:"
        obj_str = "5"
    
    previous_note_pattern_bar_num = "-1"
    for bar_index, pattern_per_bar in enumerate(extracted_pattern_by_bar):
        found_note_pattern = False
        for line_index, pattern_line in enumerate(pattern_per_bar):
            if re.match(re_pattern, pattern_line):
                current_note_pattern_bar_num = pattern_line[1:4]
                found_note_pattern = True
        
        if found_note_pattern:
            for i in range(int(current_note_pattern_bar_num) - int(previous_note_pattern_bar_num) - 1, 0, -1):
                bar_num_to_insert = "{:03}".format(int(previous_note_pattern_bar_num) + i)
                empty_note_pattern = ["#" + bar_num_to_insert + obj_str + str(key + 1) + ":00" for key in range(5)]
                extracted_pattern_by_bar.insert(bar_index, empty_note_pattern)
                
            previous_note_pattern_bar_num = current_note_pattern_bar_num
        
    return extracted_pattern_by_bar

def normalize_pattern_to_lcm(pattern, lcm):
    normalized_pattern = []
    
    base_gap_size = (lcm - len(pattern)) // len(pattern)
    
    for i in range(len(pattern)):
        normalized_pattern.append(pattern[i])
        
        if pattern[i] == '2' or pattern[i] == '3':
            normalized_pattern.extend('2' * base_gap_size)
        else:
            normalized_pattern.extend('0' * base_gap_size)
    
    return normalized_pattern

def normalize_bpm_to_lcm(bpm_pattern, lcm):
    normalized_pattern = []
    
    base_gap_size = (lcm - len(bpm_pattern)) // len(bpm_pattern)
    
    for i in range(len(bpm_pattern)):
        normalized_pattern.append(bpm_pattern[i])
        
        normalized_pattern.extend([bpm_pattern[i]] * base_gap_size)
    
    return normalized_pattern

def merge_note_ln(extracted_pattern_by_bar):
    merged_extracted_pattern_by_bar = extracted_pattern_by_bar.copy()
    indices_to_remove = []
    for bar_index, pattern_per_bar in enumerate(extracted_pattern_by_bar):
        for line_index, pattern_line in enumerate(pattern_per_bar):
            if re.match(r"#\d{3}5\d:", pattern_line):
                key_num = int(pattern_line[5])
                for target_note_line_index, target_note_pattern_line in enumerate(pattern_per_bar):
                    if re.match(r"#\d{3}1\d:", target_note_pattern_line):
                        target_note_key_num = int(target_note_pattern_line[5])
                        if key_num == target_note_key_num:
                            ln_pattern = pattern_line.split(":")[1]
                            target_note_pattern = target_note_pattern_line.split(":")[1]
                            lcm = utils.lcm(len(ln_pattern), len(target_note_pattern))
                            normalized_ln_pattern = normalize_pattern_to_lcm(ln_pattern, lcm)
                            normalized_target_note_pattern = normalize_pattern_to_lcm(target_note_pattern, lcm)
                            
                            for i in range(len(normalized_target_note_pattern)):
                                # 몇몇 패턴 겹노트 이슈 있음. 플레이 할 땐 지장 없는 듯
                                if int(normalized_target_note_pattern[i]) == 1 and int(normalized_ln_pattern[i]) == 3:
                                    normalized_target_note_pattern[i] = str(3)
                                elif int(normalized_target_note_pattern[i]) != 0 and int(normalized_ln_pattern[i]) != 0:
                                    print("FATAL ERROR")
                                    print(pattern_line)
                                    print(ln_pattern)
                                    print(target_note_pattern)
                                    print(normalized_ln_pattern)
                                    print(normalized_target_note_pattern)
                                    return None
                                else:
                                    normalized_target_note_pattern[i] = str(int(normalized_target_note_pattern[i]) + int(normalized_ln_pattern[i]))

                            merged_extracted_pattern_by_bar[bar_index][target_note_line_index] = target_note_pattern_line.split(":")[0] + ':' + ''.join(normalized_target_note_pattern)

                indices_to_remove.append((bar_index, line_index))
    
    indices_to_remove.sort(reverse=True, key=lambda x: (x[0], x[1]))
    for bar_index, line_index in indices_to_remove:
        del merged_extracted_pattern_by_bar[bar_index][line_index]
        
    return merged_extracted_pattern_by_bar

def preprocess_bpm_stop_pattern(pattern, info_dict):
    bpm_stop_pattern_split_by_channel = [pattern[i:i+2] for i in range(0, len(pattern), 2)]
    bpm_stop_list = []
    for channel in bpm_stop_pattern_split_by_channel:
        if channel == "0":
            continue
        elif channel != "00":
            bpm_stop_list.append(info_dict[channel])

    return ",".join(bpm_stop_list)

def preprocess_bpm_channel(pattern):
    bpm_pattern_list = [pattern[i:i+2] for i in range(0, len(pattern), 2)]
    bpm_list = []
    last_bpm = 0
    for bpm_pattern in bpm_pattern_list:
        current_bpm = int(bpm_pattern, 16)
        if current_bpm == 0:
            bpm_list.append(str(last_bpm))
        else:
            bpm_list.append(str(current_bpm))
            last_bpm = current_bpm
    
    return ",".join(bpm_list)

def merge_bpm_channels(extracted_pattern_by_bar):
    merged_extracted_pattern_by_bar = extracted_pattern_by_bar.copy()
    indices_to_remove = []
    for bar_index, pattern_per_bar in enumerate(extracted_pattern_by_bar):
        is_bpm03_exist = False
        is_bpm08_exist = False
        bpm_03_index = -1
        bpm_08_index = -1
        for line_index, pattern_line in enumerate(pattern_per_bar):
            if "BPM03" in pattern_line:
                is_bpm03_exist = True
                bpm_03_index = line_index
                merged_extracted_pattern_by_bar[bar_index][bpm_03_index] = merged_extracted_pattern_by_bar[bar_index][bpm_03_index].replace("BPM03", "BPM")
            if "BPM08" in pattern_line:
                is_bpm08_exist = True
                bpm_08_index = line_index
                merged_extracted_pattern_by_bar[bar_index][bpm_08_index] = merged_extracted_pattern_by_bar[bar_index][bpm_08_index].replace("BPM08", "BPM")
                
        if is_bpm03_exist and is_bpm08_exist:
            bpm_03_list = extracted_pattern_by_bar[bar_index][bpm_03_index].split(":")[-1].split(",")
            bpm_08_list = extracted_pattern_by_bar[bar_index][bpm_08_index].split(":")[-1].split(",")
            lcm = utils.lcm(len(bpm_03_list), len(bpm_08_list))
            normalized_bpm_03_list = normalize_bpm_to_lcm(bpm_03_list, lcm)
            normalized_bpm_08_list = normalize_bpm_to_lcm(bpm_08_list, lcm)
            
            merged_bpm_list = []
            appending_03 = False    # True: 03, False: 08
            if normalized_bpm_08_list[0] == '0':
                appending_03 = True
            else:
                appending_03 = False
                
            for i in range(lcm):
                if i > 0 and ((not appending_03 and normalized_bpm_03_list[i] != normalized_bpm_03_list[i-1]) or (appending_03 and normalized_bpm_08_list[i] != normalized_bpm_08_list[i-1])):
                    appending_03 = not appending_03
                
                if appending_03:
                    merged_bpm_list.append(normalized_bpm_03_list[i])
                else:
                    merged_bpm_list.append(normalized_bpm_08_list[i])
                    
            merged_bpm_line = "BPM:" + ','.join(merged_bpm_list)
                    
            indices_to_remove.append((bar_index, bpm_03_index))
            indices_to_remove.append((bar_index, bpm_08_index))
            merged_extracted_pattern_by_bar[bar_index].append(merged_bpm_line)
            
    indices_to_remove.sort(reverse=True, key=lambda x: (x[0], x[1]))
    for bar_index, line_index in indices_to_remove:
        del merged_extracted_pattern_by_bar[bar_index][line_index]
                        
    return merged_extracted_pattern_by_bar

def fill_bpm_stop_channel(extracted_pattern_by_bar):
    for bar_index, pattern_per_bar in enumerate(extracted_pattern_by_bar):
        for line_index, pattern_line in enumerate(pattern_per_bar):
            if "BPM" in pattern_line or "STOP" in pattern_line:
                pattern_content_list = pattern_line.split(':')[-1].split(',')
                for i, pattern_content in enumerate(pattern_content_list):
                    if pattern_content == '0':
                        pattern_content_list[i] = pattern_content_list[i - 1]
                filled_pattern_line = pattern_line.split(':')[0] + ':' + ','.join(pattern_content_list)
                extracted_pattern_by_bar[bar_index][line_index] = filled_pattern_line
    
    return extracted_pattern_by_bar
                    
def extract_pattern_from_bms_data(bms_data):
    ln_obj_type = bms_data["ln_obj_type"]
    
    extracted_pattern_by_bar = []
    initial_bpm = "0"
    bpm_change_info_dict = {}
    stop_info_dict = {}
    
    previous_bar_num = 0
    current_bar_pattern = []
    for line in bms_data["raw_bms_data"].split('\n'):
        if re.match(r"#BPM \d", line):
            initial_bpm = line[5:]
            
        if re.match(r"#BPM[A-Z0-9]{2}", line):
            bpm_channel = line[4:6]
            bpm = line.split(" ")[-1]
            bpm_change_info_dict[bpm_channel] = bpm
        elif re.match(r"#STOP[A-Z0-9]{2}", line):
            stop_channel = line[5:7]
            stop = line.split(" ")[-1]
            stop_info_dict[stop_channel] = stop

        is_pattern_line = True
        if re.match(r"#\d{3}02:", line):
            pattern_to_append = line
        elif re.match(r"#\d{3}03:", line):
            pattern_to_append = "BPM03:" + preprocess_bpm_channel(line.split(":")[1])
        elif re.match(r"#\d{3}08:", line):
            pattern_to_append = "BPM08:" + preprocess_bpm_stop_pattern(line.split(":")[1], bpm_change_info_dict)
        elif re.match(r"#\d{3}09:", line):
            pattern_to_append = "STOP:" + preprocess_bpm_stop_pattern(line.split(":")[1], stop_info_dict)
        # 롱노트 오브젝트 정해져 있는데 NoneType 처럼 넣은 경우. 잘못 넣었으니까 그냥 없는 걸로 치기
        elif re.match(r"#\d{3}5\d:", line) and (ln_obj_type not in [0, 1, 2]):
            is_pattern_line = False
        elif re.match(r"#\d{3}1\d:", line) or re.match(r"#\d{3}5\d:", line):
            # 롱노트 때문에 리스트에 다 붙이고 나서 건드려야 함
            pattern_to_append = line
        else:
            is_pattern_line = False
        
        if is_pattern_line:
            current_bar_num = int(line[1:4])

            if current_bar_num - previous_bar_num > 0:
                extracted_pattern_by_bar.append(current_bar_pattern)
                current_bar_pattern = [pattern_to_append]
            else:
                current_bar_pattern.append(pattern_to_append)
            
            previous_bar_num = current_bar_num
    
    if current_bar_pattern:
        extracted_pattern_by_bar.append(current_bar_pattern)
    
    # 한 마디 동안 특정 키에 노트 없으면 아예 표시 안됨. empty 표시 해주기
    extracted_pattern_by_bar = insert_omit_key_pattern(extracted_pattern_by_bar, mode="note")
    # 빈 마디에 빈 노트 패턴 넣기
    extracted_pattern_by_bar = insert_omit_bar(extracted_pattern_by_bar, mode="note")
    # BPM 03, 08 채널 둘 다 쓰는 경우 합쳐주기
    extracted_pattern_by_bar = merge_bpm_channels(extracted_pattern_by_bar)
    
    # 롱노트도 빈 노트 및 빈 마디 넣기
    if ln_obj_type == 1 or ln_obj_type == 0:
        extracted_pattern_by_bar = insert_omit_key_pattern(extracted_pattern_by_bar, mode="ln")
        extracted_pattern_by_bar = insert_omit_bar(extracted_pattern_by_bar, mode="ln")
    
    # 노트 파트 처리 (롱노트 + 노트)
    # .bml의 경우 ln_obj_type이 안적혀져 있는 듯 => 0
    if ln_obj_type == 1 or ln_obj_type == 0:
        extracted_pattern_by_bar = preprocess_note_pattern_type_1(extracted_pattern_by_bar)
        # 노트 합치기 추가
    elif ln_obj_type == 2:
        assert "지원하지 않는 LN_OBJ_TYPE 2"
    else:
        extracted_pattern_by_bar = preprocess_note_pattern_type_obj(extracted_pattern_by_bar, ln_obj_type)
    
    # 롱놋, 단놋 합치기
    extracted_pattern_by_bar = merge_note_ln(extracted_pattern_by_bar)
    if extracted_pattern_by_bar == None:
        return None

    # BPM 및 STOP 패턴 처리
    extracted_pattern = []
    previous_bpm = initial_bpm
    for pattern_per_bar in extracted_pattern_by_bar:
        extracted_pattern_per_bar = []
        is_bpm_exist = False
        is_stop_exist = False
        bpm_info_list = []
        stop_info_list = []
        for pattern_line in pattern_per_bar:         
            if "BPM" in pattern_line:
                bpm_info_list.append(pattern_line)
                is_bpm_exist = True
            elif "STOP" in pattern_line:
                stop_info_list.append(pattern_line)
                is_stop_exist = True
            else:
                extracted_pattern_per_bar.append(pattern_line)
        
        if is_bpm_exist:
            for bpm_info in bpm_info_list:
                extracted_pattern_per_bar.append(bpm_info)
                previous_bpm = bpm_info.split(":")[-1].split(",")[-1]
        else:
            extracted_pattern_per_bar.append("BPM:" + previous_bpm)
                
        if is_stop_exist:
            for stop_info in stop_info_list:
                extracted_pattern_per_bar.append(stop_info)

        extracted_pattern.append(extracted_pattern_per_bar)
        
    # BPM 이나 STOP 채널에 0 있는 거 채워주기
    extracted_pattern = fill_bpm_stop_channel(extracted_pattern)

    return extracted_pattern

def pattern_len_based_on_bpm(bpm):
    pattern_len = 128
    if bpm >= 900:
        pattern_len = 16
    elif bpm >= 450:
        pattern_len = 32 
    elif bpm >= 200:
        pattern_len = 64
    elif bpm >= 100:
        pattern_len = 128
    elif bpm > 0:
        pattern_len = 256
    else:
        pattern_len = 128
        
    return pattern_len

def find_representative_bpm(longest_key_part, bpm_list):
    lcm = utils.lcm(len(longest_key_part), len(bpm_list))
    
    # 너무 긴 거 예외 처리
    if lcm > 10000:
        filtered_bpm_list = [bpm for bpm in bpm_list if bpm != '0']
        filtered_bpm_list.sort()
        
        n = len(filtered_bpm_list)
        mid = n // 2
        
        if float(filtered_bpm_list[mid]) > 999:
            return float(filtered_bpm_list[0])
        else:
            return float(filtered_bpm_list[mid])
    
    normalized_longest_key_part = normalize_pattern_to_lcm(longest_key_part, lcm)
    normalized_bpm_list = normalize_bpm_to_lcm(bpm_list, lcm)
    
    valid_bpm_list = []
    for i in range(lcm):
        if normalized_longest_key_part[i] == '1' or normalized_longest_key_part[i] == '3':
            valid_bpm_list.append(normalized_bpm_list[i])
    
    if valid_bpm_list == []:
        representative_bpm = float(normalized_bpm_list[i])
    else:
        valid_bpm_counter = Counter(valid_bpm_list)
        representative_bpm = float(valid_bpm_counter.most_common(1)[0][0])

    return representative_bpm

def normalize_pattern_to_target_len(pattern, target_len):
    pattern_id = pattern.split(':')[0]
    pattern_content = pattern.split(':')[-1]
    
    if re.match(r"#\d{3}1\d:", pattern):
        if len(pattern_content) == target_len:
            return pattern_id + ":" + ','.join(pattern_content)
    else:
        if len(pattern_content.split(',')) == target_len:
            return pattern
    
    normalized_pattern_content = ['0'] * target_len
    # note pattern
    if re.match(r"#\d{3}1\d:", pattern):
        scale_factor = len(pattern_content) / target_len
        important_elements = [(int(i / scale_factor), elem) for i, elem in enumerate(pattern_content) if elem in {'1', '3', '4'}]
        for new_idx, elem in important_elements:
            normalized_pattern_content[new_idx] = elem
        
        start_ln_idx_list = []
        end_ln_idx_list = []
        is_ln_body_exist = False
        for i in range(len(pattern_content)):
            if pattern_content[i] == '2':
                is_ln_body_exist = True
        for i in range(target_len):
            if normalized_pattern_content[i] == '3':
                start_ln_idx_list.append(i)
            elif normalized_pattern_content[i] == '4':
                end_ln_idx_list.append(i)
        
        if is_ln_body_exist and start_ln_idx_list == [] and end_ln_idx_list == []:
            normalized_pattern_content = ['2'] * target_len
        else:
            min_len = min(len(start_ln_idx_list), len(end_ln_idx_list))
            for i in range(min_len):
                start_ln_idx = start_ln_idx_list[i]
                end_ln_idx = end_ln_idx_list[i]
                normalized_pattern_content[start_ln_idx+1:end_ln_idx] = ['2'] * (end_ln_idx - start_ln_idx - 1)
            
            if len(start_ln_idx_list) > len(end_ln_idx_list):
                for i in range(min_len, len(start_ln_idx_list)):
                    start_ln_idx = start_ln_idx_list[i]
                    normalized_pattern_content[start_ln_idx+1:] = ['2'] * (target_len - start_ln_idx - 1)
            elif len(start_ln_idx_list) < len(end_ln_idx_list):
                for i in range(min_len, len(end_ln_idx_list)):
                    end_ln_idx = end_ln_idx_list[i]
                    normalized_pattern_content[:end_ln_idx] = ['2'] * end_ln_idx
    # bpm or stop pattern
    else:
        pattern_content_list = pattern_content.split(',')
        scale_factor = len(pattern_content_list) / target_len
        important_elements = [(int(i / scale_factor), elem) for i, elem in enumerate(pattern_content_list) if i == 0 or pattern_content_list[i] != pattern_content_list[i - 1]]
        for new_idx, elem in important_elements:
            normalized_pattern_content[new_idx] = elem
        
        for i in range(target_len):
            if normalized_pattern_content[i] == '0':
                normalized_pattern_content[i] = normalized_pattern_content[i - 1]
                
    return pattern_id + ":" + ','.join(normalized_pattern_content)

def normalize_extracted_pattern(pattern):
    normalized_pattern = []
    for pattern_per_bar in pattern:
        normalized_pattern_per_bar = []
        
        key_part_list = []
        bpm_list = []
        bar_multiplication = 1
        
        pattern_seg_list = []
        for pattern_line in pattern_per_bar:
            if re.match(r"#\d{3}1\d:", pattern_line):
                key_part_list.append(pattern_line.split(':')[-1])
                pattern_seg_list.append(pattern_line)
            elif re.match(r"#\d{3}02:", pattern_line):
                bar_multiplication = float(pattern_line.split(':')[-1])
            elif "BPM" in pattern_line:
                bpm_list = pattern_line.split(':')[-1].split(',')
                pattern_seg_list.append(pattern_line)
            elif "STOP" in pattern_line:
                pattern_seg_list.append(pattern_line)

        if key_part_list == []:
            continue
        
        longest_key_part = max(key_part_list, key=len)
        representative_bpm = find_representative_bpm(longest_key_part, bpm_list)
        target_pattern_len = max(1, int(bar_multiplication * pattern_len_based_on_bpm(representative_bpm)))
        
        for pattern_seg in pattern_seg_list:
            normalized_pattern_seg = normalize_pattern_to_target_len(pattern_seg, target_pattern_len)
            normalized_pattern_per_bar.append(normalized_pattern_seg)
        
        normalized_pattern.append(normalized_pattern_per_bar)
        
    return normalized_pattern

def pattern_to_seq(pattern, key_num=5):
    seq = []  
    for pattern_per_bar in pattern:
        key_pattern_per_bar = []
        bpm = -1
        stop = -1
        for pattern_line in pattern_per_bar:
            if re.match(r"#\d{3}1\d:", pattern_line):
                key_pattern_per_bar.append([int(key_pattern) for key_pattern in pattern_line.split(":")[-1].split(",")])
            elif "BPM" in pattern_line:
                bpm = [float(bpm_str) for bpm_str in pattern_line.split(":")[-1].split(",")]
            elif "STOP" in pattern_line:
                stop = [float(stop_str) for stop_str in pattern_line.split(":")[-1].split(",")]
        
        if bpm == -1:
            assert "No BPM found."
        if len(key_pattern_per_bar) != key_num:
            assert "Length of key pattern not matching with Key Mode."
            
        if stop == -1:
            stop = [0] * len(bpm)
        
        for i in range(len(bpm)):
            seq.append([key_pattern[i] for key_pattern in key_pattern_per_bar] + [bpm[i]] + [stop[i]])
        
            if len([key_pattern[i] for key_pattern in key_pattern_per_bar] + [bpm[i]] + [stop[i]]) != 7:
                print('seq len does not match')
                print(pattern_per_bar)
                return None
        
    return seq

def filter_bms_data_and_append_metadata(data_folder_path, table_data_path):
    filtered_bms_data_list = []
    random_cnt = 0
    level_filter_cnt = 0
    for filename in tqdm(os.listdir(data_folder_path)):
        bms_data_file_path = os.path.join(data_folder_path, filename)
        bms_data = utils.extract_data(bms_data_file_path)
        table_data = utils.extract_table_data_by_md5(table_data_path, bms_data["md5"])
        level = table_data["level"]
        
        if bms_data["is_random_exist"]:
            random_cnt += 1
            continue
        
        if level != "" and level != "OLD CHARTS" and level != "LEVEL DUMMY":
            title = table_data["title"]
            pre_level = int(level.split()[-1])
            filtered_bms_data_list.append({**bms_data, "title": title, "level": pre_level})
        else:
            level_filter_cnt += 1
    
    print(f"OLD CHARTS 및 LEVEL DUMMY 등 레벨 필터링: {level_filter_cnt}개 제외")
    print(f"RANDOM 함수 있는 건 제외: {random_cnt}개 제외")
    print(f"최종 데이터 개수: {filtered_bms_data_list}개")
            
    return filtered_bms_data_list

def main():
    SOURCE_BMS_DATA_FOLDER = "./pattern_dataset/"
    TABLE_DATA_FILE_PATH = "./aery_table/data.json"
    SAVE_FILE_PATH = './data/test_preprocessed_pattern.json'

    filtered_bms_data_list = filter_bms_data_and_append_metadata(SOURCE_BMS_DATA_FOLDER, TABLE_DATA_FILE_PATH)
    
    print("Preprocessing Dataset...")
    
    filtered_bms_data_with_pattern_list = []
    for filtered_bms_data in tqdm(filtered_bms_data_list):
        extracted_pattern = extract_pattern_from_bms_data(filtered_bms_data)
        normalized_pattern = normalize_extracted_pattern(extracted_pattern)
        pattern_seq = pattern_to_seq(normalized_pattern)
        if pattern_seq == None:
            print(filtered_bms_data)
            break
        filtered_bms_data_with_pattern_list.append({**filtered_bms_data, "pattern_seq": pattern_seq})
    
    print("Saving Preprocessed Dataset...")
    
    with open(SAVE_FILE_PATH, 'w', encoding="utf-8") as f:
        json.dump(filtered_bms_data_with_pattern_list, f, indent=4, ensure_ascii=False)
        
    print(f"Saved Dataset To {SAVE_FILE_PATH}")
        
if __name__ == "__main__":
    main()