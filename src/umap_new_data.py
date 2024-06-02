import torch
import torch.nn as nn
import torch.nn.functional as F
import joblib
import preprocess_pattern
import numpy as np
import re
import hashlib
import chardet

class CNNModel(nn.Module):
    def __init__(self, pattern_embedding_dim, input_size, max_sequence_len, max_level):
        super(CNNModel, self).__init__()
        self.note_embedding = nn.Embedding(input_size-2, pattern_embedding_dim, padding_idx=0)
        self.numeric_embedding = nn.Linear(1, pattern_embedding_dim)
        self.max_level = max_level
        
        self.layer1 = nn.Sequential(
            nn.Conv1d(pattern_embedding_dim * input_size, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=4)
        )
        
        self.layer2 = nn.Sequential(
            nn.Conv1d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=4)
        )
        
        self.layer3 = nn.Sequential(
            nn.Conv1d(128, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)
        )
        
        def conv_output_size(seq_len, kernel_size, padding, stride, max_pool_kernel_size):
            return ((seq_len - kernel_size + 2 * padding) // stride + 1) // max_pool_kernel_size
        
        self.output_size_after_layer1 = conv_output_size(max_sequence_len, 3, 1, 1, 4)
        self.output_size_after_layer2 = conv_output_size(self.output_size_after_layer1, 3, 1, 1, 4)
        self.output_size_after_layer3 = conv_output_size(self.output_size_after_layer2, 3, 1, 1, 2)

        self.fc1 = nn.Linear(64 * self.output_size_after_layer3, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, max_level)
        self.dropout = nn.Dropout(p=0.1)

    def forward(self, x, return_embeddings=False):
        note_part = x[:, :, :5].long()
        bpm_part = x[:, :, 5:6]
        stop_part = x[:, :, 6:]
        note_embed = self.note_embedding(note_part)
        bpm_embed = F.relu(self.numeric_embedding(bpm_part)).unsqueeze(2)
        stop_embed = F.relu(self.numeric_embedding(stop_part)).unsqueeze(2)
        input_embed = torch.cat((note_embed, bpm_embed, stop_embed), dim=2)
        
        x = input_embed.view(input_embed.size(0), input_embed.size(1), -1).transpose(1, 2)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        # 시각화를 위해 결과값으로 합치기 전의 임베딩 값 추출
        if return_embeddings:
            return x
        x = self.dropout(x)
        x = self.fc3(x)
        return x

def extract_data(uploaded_file):
    hash_md5 = hashlib.md5()
    uploaded_file.stream.seek(0)
    for chunk in iter(lambda: uploaded_file.stream.read(4096), b""):
        hash_md5.update(chunk)
    uploaded_file.stream.seek(0)
    
    raw_file = uploaded_file.stream.read()
    bms_data = raw_file.decode(chardet.detect(raw_file)['encoding'])
    uploaded_file.stream.seek(0)
    
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
        "md5": hash_md5.hexdigest(),
        "judge_rank": judge_rank,
        "total": total,
        "ln_obj_type": ln_obj_type,
        "is_random_exist": is_random_exist,
        "raw_bms_data": bms_data.replace('\r', '')
    }

def extract_metadata(uploaded_file):
    uploaded_file.stream.seek(0)
    raw_file = uploaded_file.stream.read()
    bms_data = raw_file.decode(chardet.detect(raw_file)['encoding'])
    uploaded_file.stream.seek(0)
    
    title = "None"
    artist = "None"
    
    main_title_match = re.search(r"#TITLE\s*(.*?)\n", bms_data)
    if main_title_match:
       title = main_title_match.group(1)
       
    sub_title_match = re.search(r"#SUBTITLE\s*(.*?)\n", bms_data)
    if sub_title_match:
       title = title + " " + sub_title_match.group(1)
       
    main_artist_match = re.search(r"#ARTIST\s*(.*?)\n", bms_data)
    if main_artist_match:
        artist = main_artist_match.group(1)
        
    sub_artist_match = re.search(r"#SUBARTIST\s*(.*?)\n", bms_data)
    if sub_artist_match:
        artist = artist + " " + sub_artist_match.group(1)
    
    return title, artist

def process_uploaded_data(uploaded_file):
    model_file_path = "./models/CE_with_md5_30.pth"
    reducer_file_path = "./models/umap_model.pkl"
    
    torch.backends.cudnn.enabled = False

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = "cpu"
    
    print('Device:', device)
    print('Current cuda device:', torch.cuda.current_device())
    print('Count of using GPUs:', torch.cuda.device_count())
    
    KEY_MODE = 5
    MAX_SEQ_LEN = 23606

    loaded_model = CNNModel(pattern_embedding_dim=4, input_size=KEY_MODE+2, max_sequence_len=MAX_SEQ_LEN, max_level=20).to(device)
    loaded_model.load_state_dict(torch.load(model_file_path))
    loaded_model.eval()

    loaded_reducer = joblib.load(reducer_file_path)
    
    infer_bms_data = extract_data(uploaded_file)
    infer_extracted_pattern = preprocess_pattern.extract_pattern_from_bms_data(infer_bms_data)
    infer_normalized_pattern = preprocess_pattern.normalize_extracted_pattern(infer_extracted_pattern)
    infer_pattern_seq = preprocess_pattern.pattern_to_seq(infer_normalized_pattern)
    
    pattern_seq = np.pad(infer_pattern_seq, ((0, MAX_SEQ_LEN - len(infer_pattern_seq)), (0, 0)), mode='constant')
    pattern_seq = torch.tensor(pattern_seq, dtype=torch.float).to(device)
    
    with torch.no_grad():
        embedding = loaded_model(pattern_seq.unsqueeze(0), return_embeddings=True)
        
        outputs = loaded_model(pattern_seq.unsqueeze(0))
        _, predicted_level = torch.max(outputs, 1)
        
    embedding = embedding.cpu().detach().numpy()
    embedding_2d = loaded_reducer.transform(embedding)
    
    title, artist = extract_metadata(uploaded_file)
    
    processed_result_json = {
        'title': str(title.replace('\r', '')),
        'artist': str(artist.replace('\r', '')),
        'level': int(predicted_level),
        'x': float(embedding_2d[:, 0][0]),
        'y': float(embedding_2d[:, 1][0])
    }
    
    return processed_result_json