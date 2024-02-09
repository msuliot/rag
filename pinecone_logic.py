from pinecone import Pinecone, ServerlessSpec
from tqdm.auto import tqdm
import ast
import os

#Global variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pinecone = Pinecone(api_key=PINECONE_API_KEY)

# delete index
def delete_pinecone_index(index_name):
    print(f"Deleting index '{index_name}' if it exists.")
    try:
        pinecone.delete_index(index_name)
        print(f"Index '{index_name}' successfully deleted.")
    except Exception as e:
        print(f"index '{index_name}' not found no action taken.")


# create index if needed
def get_pinecone_index(index_name):
    print(f"Checking if index {index_name} exists.")
    index_created = False
    if index_name in [index.name for index in pinecone.list_indexes()]:
        print(f"Index {index_name} already exists, good to go.")
        index = pinecone.Index(index_name)
    else:
        print(f"Index {index_name} does not exist, need to create it.")
        index_created = True
        pinecone.create_index(
            name=index_name, 
            dimension=1536, 
            metric='cosine', 
            spec=ServerlessSpec(cloud='aws', region='us-west-2'))
            
        print(f"Index {index_name} created.")

        index = pinecone.Index(index_name)
    return index, index_created


# Function to upsert data
def upsert_data(index, df):
    print("Start: Upserting data to Pinecone index")
    prepped = []

    for i, row in tqdm(df.iterrows(), total=df.shape[0]):
        meta = ast.literal_eval(row['metadata'])
        prepped.append({'id': row['id'], 
                        'values': row['values'],
                        'metadata': meta})
        if len(prepped) >= 200: # batching upserts
            index.upsert(prepped)
            prepped = []

    # Upsert any remaining entries after the loop
    if len(prepped) > 0:
        index.upsert(prepped)
    
    print("Done: Data upserted to Pinecone index")
    return index

