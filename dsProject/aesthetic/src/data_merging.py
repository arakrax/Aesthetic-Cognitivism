import pandas as pd
import os
import spacy

"""
data_merging.py

Main purpose: 
    1. Merging data. In this task, the goal is to explore how the language and focus of criticism evolved over time.
    Since the datasets come from the same source and share similar structure and linguistic style, 
    merging them provides a larger and more continuous corpus across years.

    2. Lemmatization
        - Perform lemmatization on 'Full_text' and save result as 'Processed_text'
        - Remove stopwords and punctuation
        - Keep only alphabetic tokens

Input:
    data/processed/*.csv
        - Data cleaned after data_cleaning.py

Output:
    data/merged_data.csv
        - Combine all input data into a file
        - Add the 'genre' column according to the input file name
        - Perform lemmatization on the 'Full_text', store in 'Processed_text'
"""

# Path setting
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DATA_PATH = os.path.join(project_root, 'data/processed')
MERGED_DATA_PATH = os.path.join(project_root, 'data')


def lemmatize_texts(texts, nlp):
    """
    对文本列表执行词形还原：
    - 去除停用词、标点
    - 保留字母型 token
    - 返回词形化后的字符串
    """
    processed = []
    for doc in nlp.pipe(texts, disable=["ner", "parser"]):
        lemmas = [
            token.lemma_.lower()
            for token in doc
            if token.is_alpha and not token.is_stop
        ]
        processed.append(" ".join(lemmas))
    return processed


def run(data_path1=PROCESSED_DATA_PATH, data_path2=MERGED_DATA_PATH):
    total_processed_data = []
    for file in os.listdir(data_path1):
        if file.endswith('.csv'):
            print(f"Start to process {file}")
            file_path = os.path.join(data_path1, file)
            df = pd.read_csv(file_path)
            # add the 'genre' column according to the file name
            genre = file.removeprefix("processed_").removesuffix("_gale.csv").lower()
            df["genre"] = genre
            total_processed_data.append(df)

    merged_df = pd.concat(total_processed_data, ignore_index=True)
    merged_df = merged_df.sort_values(by="Year")

    # Lemmatization
    print("Loading spaCy model...")
    try:
        nlp = spacy.load("en_core_web_md", disable=["ner", "parser"])
    except OSError:
        print("Model 'en_core_web_md' not found. Installing...")
        os.system("python -m spacy download en_core_web_md")
        nlp = spacy.load("en_core_web_md", disable=["ner", "parser"])
    print("Performing lemmatization on 'Full_text'...")

    # only perform lemmatization on 'Full_text'
    merged_df["Full_text"] = merged_df["Full_text"].astype(str).fillna("")
    merged_df["Processed_text"] = lemmatize_texts(merged_df["Full_text"].tolist(), nlp)

    print("Lemmatization completed! Added column 'Processed_text'.")

    # Save
    new_file_path = os.path.join(data_path2, "merged_data.csv")
    if os.path.exists(new_file_path):
        raise ValueError("File already exists! Please remove it or change its name!")
    else:
        merged_df.to_csv(new_file_path, index=False)
        print(f"Data merging has been completed! The size of merging data is {merged_df.shape}")


if __name__ == "__main__":
    run()