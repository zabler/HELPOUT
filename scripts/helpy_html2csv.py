'''helpy_html2csv.py'''

# %% IMPORTS
import pandas as pd
import io
import os
import yaml
from pathlib import Path
import time
import re

# %% LOGIC

def get_files_list(database_path, filetype='html'):
    # GET ALL RECORDINGS
    recording_paths = []
    for root, folders, files in os.walk(database_path):
        for name in files:
            if name.split('.')[1] == filetype:
                recording_paths.append(os.path.join(root, name))
    return recording_paths

# def convert_consistent_html_to_excel(html_input, output_folder):
#     try:
#         # 1. Parse the HTML
#         # If html_input is a file path, it reads the file. If it's a string, it wraps it.
#         if html_input.endswith('.html'):
#             with open(html_input, 'r', encoding='utf-8') as f:
#                 html_content = f.read()
#         else:
#             html_content = html_input

#         # read_html returns a list of dataframes
#         dfs = pd.read_html(io.StringIO(html_content)) #dfs = pd.read_html(io.StringIO(html_content), keep_default_na=False)
        
#         if not dfs:
#             print("No tables found.")
#             return

#         # Take the first table (since structure is consistent)
#         df = dfs[0]

#         # 1. FIXED DEPRECATION: Use .map instead of .applymap
#         # This cleans up whitespace and removes 'NaN'
#         df = df.map(lambda x: " ".join(str(x).split()) if pd.notnull(x) else "")

#         # 2. CONSISTENCY: Normalize Column Headers
#         # Removes hidden spaces or newlines in the header names themselves
#         df.columns = [" ".join(str(col).split()) for col in df.columns]

#         # Define output filename based on original stem but into the OUTPUT_HELPY folder
#         input_filename = Path(html_input).stem
#         output_filename = Path(output_folder) / f"{input_filename}.xlsx"

#         # Create output folder if it doesn't exist
#         output_filename.parent.mkdir(parents=True, exist_ok=True)

#         # 3. PROFESSIONAL FORMATTING
#         with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
#             df.to_excel(writer, index=False, sheet_name='Diary_Log')
            
#             worksheet = writer.sheets['Diary_Log']
            
#             for i, col in enumerate(df.columns):
#                 # Calculate width based on content or header
#                 max_content = df[col].astype(str).map(len).max()
#                 column_len = max(max_content, len(str(col))) + 3
                
#                 # Use a safer column indexer for tables wider than 'Z'
#                 col_letter = worksheet.cell(row=1, column=i+1).column_letter
#                 worksheet.column_dimensions[col_letter].width = min(column_len, 50) # Cap width at 50

#         print(f"Processed: {input_filename} -> {output_filename.name}")

#     except Exception as e:
#         print(f"An error occurred: {e}")

def convert_consistent_html_to_csv(html_input, output_folder):
    try:
        if html_input.endswith('.html'):
            with open(html_input, 'r', encoding='utf-8') as f:
                html_content = f.read()
        else:
            html_content = html_input

        # read_html is excellent for structural consistency
        dfs = pd.read_html(io.StringIO(html_content), keep_default_na=False)
        if not dfs: return
        df = dfs[0]

        # 1. CLEAN DATA & HEADERS
        # Using .map (Pandas 2.1+) to clean whitespace
        df = df.map(lambda x: " ".join(str(x).split()) if pd.notnull(x) else "")
        df.columns = [" ".join(str(col).split()) for col in df.columns]

        # 2. FIX DATUM: Ensure space between Year and Time
        if 'Datum' in df.columns:
            # Regex: Finds 4 digits (Year) followed by 2 digits: (Hour)
            # Result: 31/01/202612:47 -> 31/01/2026 12:47
            df['Datum'] = df['Datum'].apply(lambda x: re.sub(r'(\d{4})(\d{2}:\d{2})', r'\1 \2', str(x)))

        # 3. DEFINE FILENAME
        input_filename = Path(html_input).stem
        output_filename = Path(output_folder) / f"{input_filename}.csv"

        # 4. Create output folder if it doesn't exist
        output_filename.parent.mkdir(parents=True, exist_ok=True)

        # 5. SAVE TO CSV
        # utf-8-sig adds a 'BOM' so Excel recognizes the encoding automatically
        df.to_csv(output_filename, index=False, encoding='utf-8-sig', sep=';')

        print(f"Processed: {input_filename} -> {output_filename.name}")

    except Exception as e:
        print(f"Error processing {html_input}: {e}")
#  %% MAIN
if __name__ == "__main__":

    # Settings
    CONFIGS = yaml.safe_load(open("config.yaml", 'r'))
    FILENAME = os.path.splitext(os.path.basename(__file__))[0]
    ACTIVE = CONFIGS.get('configs', {}).get(CONFIGS.get('active'), {})
    CONFIG = ACTIVE.get('defaults', {}) | ACTIVE.get('scripts', {}).get(FILENAME, {})

    # Paths
    INPUT_HELPY = Path(os.path.expanduser(CONFIG['base']), CONFIG['input']).resolve()
    OUTPUT_FOLDER = Path(os.path.expanduser(CONFIG['base']), CONFIG['output'], str(time.strftime("%Y%m%d-%H%M%S")) + '_' + FILENAME) if CONFIG['dataout'] else None

    # Get list of HTML diary files
    html_diaries = get_files_list(INPUT_HELPY, filetype='html')
    for html_file_path in html_diaries:
        if CONFIG.get('dataout', False):
            convert_consistent_html_to_csv(html_file_path, OUTPUT_FOLDER)
    print("All done!")