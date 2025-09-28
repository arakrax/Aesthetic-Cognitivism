import pandas as pd
import os
import re
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(project_root, 'data/raw')
# used to store processed data
PROCESSED_DATA_PATH = os.path.join(project_root, 'data/processed')
os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)

# used to process full_text column
def clean_full_text(text):
    # remove all HTML tags
    text = re.sub(r'<.*?>', '', text)
    # remove HTTP links
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # remove non English and characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    # make all letters lowercase
    text = text.lower()
    # remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def run(raw_data_path=RAW_DATA_PATH, processed_data_path=PROCESSED_DATA_PATH):
    files = os.listdir(raw_data_path)
    for file in files:
        if file.startswith('.'):
            continue

        print(f"{file}: Start to clean data")
        file_name = f'{raw_data_path}/{file}'
        df = pd.read_csv(file_name)

        # There is a problem with the Publication and Date columns in these file, we need to modify
        if file in ["Operas_gale.csv", "Poetry_gale.csv"]:
            tmp = df['Publication'].copy()
            df['Publication'] = df['Date']
            df['Date'] = tmp

        # used to store processed data
        new_df = pd.DataFrame()
        # remove the leading and trailing spaces and convert to title format
        new_df["Author_cleaned"] = df["Author"].str.strip().str.title()
        # remove non English character
        new_df["Title_cleaned"] = df["Title"].str.replace(r"[^a-zA-Z0-9\s]", "", regex=True).str.strip()

        new_df["Publication_cleaned"] = df["Publication"].str.strip().str.title()

        # convert to '2006-01-14' format.
        new_df["Date_cleaned"] = pd.to_datetime(df["Date"], errors="coerce")

        new_df["Place_cleaned"] = df["Place"].str.strip().str.title()

        new_df["Full_text_cleaned"] = df["Full_text"].fillna('').apply(clean_full_text)

        new_df["URL"] = df["URL"]

        new_file_name = f'processed_{file}'
        new_file_path = os.path.join(processed_data_path, new_file_name)
        new_df.to_csv(new_file_path, index=False)

        print(f'{file}: Data cleaning completed')




