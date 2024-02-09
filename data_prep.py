import pandas as pd
import json
from tqdm.auto import tqdm
from openai_logic import create_embeddings
import os, sys

# Function to get dataset
def import_csv(df, csv_file, max_rows):
    print("Start: Getting dataset")

    # Check if file exists
    if not os.path.exists(csv_file):
        return "Error: CSV file does not exist."
    
    try:
        # Attempt to read the CSV file
        df = pd.read_csv(csv_file, usecols=['id', 'tiny_link', 'content'], nrows=max_rows)
    except FileNotFoundError:
        return "Error: CSV file not found."
    except PermissionError:
        return "Error: Permission denied when accessing the CSV file."
    except Exception as e:
        return f"Error: An unexpected error occurred while reading the CSV file. ({e})"
    
    # Check if DataFrame is empty
    if df.empty:
        return "Error: No data found in the CSV file."
    
    return df
    

def clean_data_pinecone_schema(df):
    # Ensure necessary columns are present
    required_columns = {'id', 'tiny_link', 'content'}
    if not required_columns.issubset(df.columns):
        missing_columns = required_columns - set(df.columns)
        return f"Error: CSV file is missing required columns: {missing_columns}"
    
    # Filter out rows where 'content' is empty
    df = df[df['content'].notna() & (df['content'] != '')]
    
    if df.empty:
        return "Error: No valid data found in the CSV file after filtering empty content."
    
    # Proceed with the function's main logic
    df['id'] = df['id'].astype(str)
    df.rename(columns={'tiny_link': 'source'}, inplace=True)
    df['metadata'] = df.apply(lambda row: json.dumps({'source': row['source'], 'text': row['content']}), axis=1)
    df = df[['id', 'metadata']]
    # print(df.head())
    print("Done: Dataset retrieved")
    return df


# Function to generate embeddings and add to DataFrame
def generate_embeddings_and_add_to_df(df, model_emb):
    print("Start: Generating embeddings and adding to DataFrame")
    # Check if the DataFrame and the 'metadata' column exist
    if df is None or 'metadata' not in df.columns:
        print("Error: DataFrame is None or missing 'metadata' column.")
        return None
    
    
    df['values'] = None

    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        try:
            content = row['metadata']
            meta = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for row {index}: {e}")
            continue  # Skip to the next iteration

        text = meta.get('text', '')
        if not text:
            print(f"Warning: Missing 'text' in metadata for row {index}. Skipping.")
            continue

        try:
            response = create_embeddings(text, model_emb)
            embedding = response   # .data[0].embedding -- Embedding Error? this may be it  # Each in bedding format may be different
            df.at[index, 'values'] = embedding
        except Exception as e:
            print(f"Error generating embedding for row {index}: {e}")

    print("Done: Generating embeddings and adding to DataFrame")
    return df

