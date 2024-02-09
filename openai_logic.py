# note which revision of python, for example 3.9.6
from datasets import load_dataset
from openai import OpenAI
# import openai
from pinecone import Pinecone, ServerlessSpec
from tqdm.auto import tqdm
import ast
import os
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import sys
import json 
import numpy as np
import gradio as gr

#Global variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# get embeddings
def get_embeddings(query, model_emb):
   embedding = openai_client.embeddings.create(input = query, model=model_emb)
   print("Dimension of query embedding: ", len(embedding.data[0].embedding))
   return embedding

def create_embeddings(text, model_emb):   
    response = openai_client.embeddings.create(
        input=text,
        model=model_emb
    )
    embedding = response.data[0].embedding
    return embedding     

# create prompt for openai
def create_prompt(query, res):
    contexts = [ x['metadata']['text'] for x in res['matches']]
    prompt_start = ("Answer the question based on the context and sentiment of the question.\n\n" + "Context:\n") # also, do not discuss any Personally Identifiable Information.
    prompt_end = (f"\n\nQuestion: {query}\nAnswer:")
    prompt = (prompt_start + "\n\n---\n\n".join(contexts) + prompt_end)
    return prompt


def add_prompt_messages(role, content, messages):
    json_message = {
        "role": role, 
        "content": content
    }
    messages.append(json_message)
    return messages

def get_chat_completion_messages(messages, model_chat, temperature=0.0): 
    try:
        response = openai_client.chat.completions.create(
        model=model_chat,
        messages=messages,
        temperature=temperature,
    )
    except Exception as e:
        print(e)
        sys.exit()
    else:
        return response.choices[0].message.content

def create_system_prompt():
    system_prompt = f"""
    You are a customer service specialist at a multiple listing service that helps customers.
    """
    return system_prompt

