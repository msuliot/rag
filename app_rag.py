import os
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import gradio as gr
from utils.pinecone_logic import delete_pinecone_index, get_pinecone_index, upsert_data
from utils.data_prep import import_csv, clean_data_pinecone_schema, generate_embeddings_and_add_to_df
from utils.openai_logic import get_embeddings, create_prompt, add_prompt_messages, get_chat_completion_messages, create_system_prompt
import sys

# load environment variables
load_dotenv(find_dotenv())

# Function to extract information
def extract_info(data):
    extracted_info = []
    for match in data['matches']:
        source = match['metadata']['source']
        score = match['score']
        extracted_info.append((source, score))
    return extracted_info


# main function
def main(query):
    # https://platform.openai.com/docs/models  ## validate the model you want to use
    # https://platform.openai.com/api-keys ## sign up for an API key
    # https://www.pinecone.io ## sign up access and for an API key (serverless vector database)

    print("Start: Main function")
    
    model_for_openai_embedding="text-embedding-3-small"
    model_for_openai_chat="gpt-3.5-turbo"
    index_name = "demo-kb-index"
    csv_file = './data/kb.csv'
    # query = "This is where I put a question if I'm Testing?"

    ######## delete_pinecone_index(index_name)  # uncomment to delete index
    index, index_created = get_pinecone_index(index_name)
    
    # if index_created:
    df = pd.DataFrame(columns=['id', 'tiny_link', 'content'])
    df = import_csv(df, csv_file, max_rows=2000) 
    df = clean_data_pinecone_schema(df)
    df = generate_embeddings_and_add_to_df(df, model_for_openai_embedding)
    upsert_data(index, df)

    embed = get_embeddings(query, model_for_openai_embedding)
    res = index.query(vector=embed.data[0].embedding, top_k=3, include_metadata=True)
    
    # create system prompt and user prompt for openai chat completion
    messages = []
    system_prompt = create_system_prompt()
    prompt = create_prompt(query, res)
    messages = add_prompt_messages("system", system_prompt , messages)
    messages = add_prompt_messages("user", prompt , messages)
    response = get_chat_completion_messages(messages, model_for_openai_chat) 
    print('-' * 80)
    extracted_info = extract_info(res)
    validated_info = []
    for info in extracted_info:
        source, score = info
        validated_info.append(f"Source: {source}    Score: {score}")

    validated_info_str = "\n".join(validated_info)
    final_output = response + "\n\n" + validated_info_str
    print(final_output)
    print('-' * 80)
    return final_output


if __name__ == "__main__":
    main("hello, how are you?")


# #create Gradio interface for the chatbot
# gr.close_all()
# demo = gr.Interface(fn=main,
#                     inputs=[gr.Textbox(label="Hello, my name is Aiden, your customer service assistant, how can i help?", lines=1,placeholder=""),],
#                     outputs=[gr.Textbox(label="response", lines=30)],
#                     title="Customer Service Assistant",
#                     description="A question and answering chatbot that answers questions based on your confluence knowledge base.  Note: anything that was tagged internal_only has been removed",
#                     allow_flagging="never")
# demo.launch(server_name="localhost", server_port=8888)    