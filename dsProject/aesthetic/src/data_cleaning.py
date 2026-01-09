import pandas as pd
import os
import re
from symspellpy import SymSpell, Verbosity

"""
data_cleaning.py

Main purpose:
    Data cleaning.

Input:
    data/raw/*.csv
        - Raw OCR-scanned data
        - Each file contains columns such as: Author, Title, Publication, Date, Place, Full_text, URL

Output:
    data/processed/processed_*.csv
        - Cleaned datasets ready for merging and analysis
        - New columns:
            * Full_text: cleaned text (after OCR cleaning + general data cleaning + spelling correction)
            * OCR_noise_ratio: ratio of out-of-vocabulary words
            * Year, Decade: extracted time information

------------------------------------------------------------
Pipeline overview:
    Step 1: OCR feature cleaning
        - Fix common OCR artifacts 
    Step 2: General text cleaning
        - Remove HTML tags, URLs, and non-English symbols
        - Preserve punctuation and lowercase text
    Step 3: Spelling correction (SymSpell)
        - Apply fast dictionary-based spelling correction
    Step 4: OCR noise ratio calculation
        - Compute fraction of unknown tokens (not in dictionary)
    Step 5: Metadata standardization
        - Fix swapped Publication/Date columns (Opera, Poetry)
        - Add Year and Decade columns
    Step 6: Save cleaned outputs

------------------------------------------------------------
Notes:
    - This script is part of the data preprocessing pipeline for the project:
        "Temporal Analysis of Criticism Language Evolution"
    - The next stage will merge all processed datasets (see data_merging.py)

Author: Xinyu Meng
Date: 2025-10-29
"""

# Path setting
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_PATH = os.path.join(project_root, 'data/raw')
PROCESSED_DATA_PATH = os.path.join(project_root, 'data/processed')
os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)

USE_SPELLING_CORRECTION = False

# used to fix OCR errors
def init_symspell(max_edit_distance_dictionary=2, prefix_length=7):
    sym_spell = SymSpell(max_edit_distance_dictionary, prefix_length)
    dict_path = os.path.join(os.path.dirname(__file__), "frequency_dictionary_en_82_765.txt")
    if not os.path.exists(dict_path):
        import urllib.request
        print("Downloading SymSpell dictionary...")
        url = "https://raw.githubusercontent.com/mammothb/symspellpy/master/symspellpy/frequency_dictionary_en_82_765.txt"
        urllib.request.urlretrieve(url, dict_path)
    sym_spell.load_dictionary(dict_path, term_index=0, count_index=1)
    return sym_spell


SYM_SPELL = init_symspell()
ENGLISH_VOCAB = set(SYM_SPELL.words.keys())


# Step 1: OCR feature cleaning
def fix_ocr_errors(text):
    if not isinstance(text, str):
        return ""
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl").replace("ﬀ", "ff")
    text = re.sub(r'(?<=\w)0(?=\w)', 'o', text)
    text = re.sub(r'(?<=\w)1(?=\w)', 'l', text)
    text = re.sub(r'\b1\b', 'I', text)
    text = re.sub(r'[¬\x0c\xad]', ' ', text)
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# Step 2: General text cleaning
def clean_full_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    # keep punctuation and hyphens
    text = re.sub(r"[^a-zA-ZÀ-ÖØ-öø-ÿ0-9'\-.,;:!?()\s]", ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()


# Step 3: SymSpell spelling correction
def correct_spelling(text, max_edit_distance=1):
    if not text.strip():
        return text
    corrected = []
    for token in text.split():
        suggestions = SYM_SPELL.lookup(token, Verbosity.CLOSEST, max_edit_distance)
        corrected.append(suggestions[0].term if suggestions else token)
    return ' '.join(corrected)


# Step 4: OCR noise ratio
def is_noisy_by_pattern(token: str) -> bool:
    """
    只根据“形态规则”判断 token 是否像 OCR 噪声：
    - 含有奇怪符号（除了字母、数字、- ' .，以及常见的拉丁重音字符）
    - 含有数字但不是简单数字/年份（2~4 位纯数字）
    - 长度 >= 5 且没有元音
    - 单字符但不是 a / i
    """
    # 去掉首尾空白 + 常见标点（中间的 - 和 ' 保留）
    t = token.strip().strip(".,;:!?()\"'“”’")
    if not t:
        return False

    # 1. 含有奇怪符号
    # 允许：英文字母 + 拉丁扩展 À-ÖØ-öø-ÿ + 数字 + - ' .
    if re.search(r"[^a-zA-ZÀ-ÖØ-öø-ÿ0-9\-'.]", t):
        return True

    # 2. 含有数字但不是简单数字/年份
    if any(ch.isdigit() for ch in t):
        # 纯数字且长度为 2~4（可能是年份/页码），放过
        if t.isdigit() and 2 <= len(t) <= 4:
            return False
        return True

    # 3. 全是字母，长度 >= 5，但没有元音，极可能是 OCR 残渣
    letters = re.sub(r"[^a-zA-ZÀ-ÖØ-öø-ÿ]", "", t)
    if len(letters) >= 5 and not re.search(r"[aeiouAEIOU]", letters):
        return True

    # 4. 单字符但不是 a / i
    if len(t) == 1 and t.lower() not in {"a", "i"}:
        return True

    return False


def is_noisy_token(token: str) -> bool:
    """
    先看 token 是否在现代词典中：
        - 在词典里 -> 一定不是噪声
        - 不在词典里 -> 再用 is_noisy_by_pattern 判断
    注意：这里会先去掉两端标点，再做词典匹配和形态判断。
    """
    # 统一做一次首尾清理（和 is_noisy_by_pattern 相同）
    t = token.strip().strip(".,;:!?()\"'“”’")
    if not t:
        return False

    # 0. 白名单：词典里的词一律视为“非噪声”
    if t.lower() in ENGLISH_VOCAB:
        return False

    # 1. 不在词典里，再用形态规则判断
    return is_noisy_by_pattern(t)


def ocr_noise_ratio(text: str) -> float:
    """
    OCR 噪声比例：
        噪声比例 = 噪声 token 数 / 总 token 数
    噪声 token 的判定逻辑：
        - 先去掉 token 两端标点
        - 如果在现代词典中 -> 不算噪声
        - 否则 -> 看形态是否“像噪声”
    """
    tokens = text.split()
    if not tokens:
        return 0.0
    noisy = sum(1 for t in tokens if is_noisy_token(t))
    return noisy / len(tokens)


# Step 5: Main pipeline
def run(raw_data_path=RAW_DATA_PATH, processed_data_path=PROCESSED_DATA_PATH):
    files = os.listdir(raw_data_path)
    for file in files:
        if file.startswith('.'):
            continue

        print(f"{file}: Start to clean data")
        file_name = os.path.join(raw_data_path, file)
        df = pd.read_csv(file_name)

        # Fix Publication/Date swap
        if "opera" in file.lower() or "poetry" in file.lower():
            tmp = df['Publication'].copy()
            df['Publication'] = df['Date']
            df['Date'] = tmp

        new_df = pd.DataFrame()
        new_df["Author"] = df["Author"].str.strip().str.title()
        new_df["Title"] = df["Title"].str.replace(r"[^a-zA-Z0-9\s]", "", regex=True).str.strip()
        new_df["Publication"] = df["Publication"].astype(str).str.strip().str.title()
        new_df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        new_df["Place"] = df["Place"].astype(str).str.strip().str.title()
        new_df["URL"] = df["URL"]

        # Text processing
        cleaned_texts = []
        noise_ratios = []
        # the processing order is OCR cleaning -> general cleaning -> fix wrong spelling
        for text in df["Full_text"].fillna(''):
            t = fix_ocr_errors(text)
            t = clean_full_text(t)
            if USE_SPELLING_CORRECTION:
                t = correct_spelling(t)
            cleaned_texts.append(t)
            noise_ratios.append(ocr_noise_ratio(t))

        new_df["Full_text"] = cleaned_texts
        new_df["OCR_noise_ratio"] = noise_ratios

        # Add year/decade
        new_df["Year"] = new_df["Date"].dt.year
        new_df["Decade"] = (new_df["Year"] // 10) * 10

        # Save
        new_file_name = f'processed_{file}'
        new_file_path = os.path.join(processed_data_path, new_file_name)
        new_df.to_csv(new_file_path, index=False)
        print(f"{file}: Data cleaning completed, saved to {new_file_path}")

    print("Data cleaning has been completed, you can process next step!")

if __name__ == "__main__":
    run()