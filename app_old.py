from pinecone import Pinecone
import os
import pandas as pd
from openai import OpenAI
import re
import streamlit as st
import requests
import json
import time
from PIL import Image
import base64
import io


def add_logo(logo_path, width, height):
    """Read and return a resized logo"""
    logo = Image.open(logo_path)
    modified_logo = logo.resize((width, height))
    return modified_logo

st.image(add_logo(logo_path="./logo.PNG", width=200, height=100)) 

st.title("📝 Sabic Products Chatbot ") 

if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Mention your queries!"}
    ]
  
api_key=st.secrets.pinecone_api_key
openai_api_key=st.secrets.openai_api_key

client=OpenAI(api_key=openai_api_key)

pc = Pinecone(api_key=api_key)
index=pc.Index('genai-petro4')
supporting_data=pd.read_csv('./supporting_data_website.csv')

url = "http://172.206.0.44/rts/api/v1/services/newupdated/pinecone_version_streamlit"
username = 'demo_rapidminer'
password = 'demo_rapidminer'

def create_embeddings(text):
    MODEL = 'text-embedding-ada-002'
    res = client.embeddings.create(input=[text], model=MODEL)
    return dict(dict(res)['data'][0])['embedding']

def index_query(index_name,query,supporting_df,top_k_retrieves=3):
    ids=[]
    ret_text=""
    rets=index_name.query(
        vector=create_embeddings(query),
        top_k=top_k_retrieves,
        include_metadata=True)
    
    for i in range(len(rets['matches'])):
        ids.append(rets['matches'][i]['id'])
    for i in ids:
        ret_text=ret_text + str(supporting_df['text'][[supporting_df.index[supporting_df['ids'] == str(i)]][0][0]])
    return ret_text


def response_generator(response):
    comp = response
    if '\n' in comp:
      for line in comp.split('\n'):
        for word in line.split():
            yield word + " "
            time.sleep(0.05)
        yield "\n"
    else:
      for word in comp.split():
          yield word + " "
          time.sleep(0.05)

# def reset_conversation():
#   st.session_state.messages=st.session_state.messages = [{"role": "assistant", "content": "Mention your queries!"}]
# with st.sidebar:
#   st.button("Clear Chat",on_click=reset_conversation)

if query :=st.text_input("How can i help you today?",placeholder="Your query here"):
  st.session_state.messages.append({"role": "user", "content": str(query)})
  ret_text=index_query(index,query,supporting_data,3)
  system="""Answer the user's query with the help of the information provided by the user.
    Provide a structured and organized answer to the query.Answer in points if required.Form the answer considering the guidelines in the system prompt using the given information.
    It's important to consistently convey positive information about the organization. 
    Even if the user seeks insights into potential drawbacks or negatives, emphasize a 
    positive outlook and encourage them to explore various use cases or other topics of interest for a more comprehensive discussion.
    Do not provide your own opinions or perspectives.Answer only from the user provided information and nothing else.
    Say you dont know the answer if you dont know.The information:"""+str(ret_text)
  prompt="My query:"+str(query)
  myinput = {"data":[{"prompt":prompt,"system":system}]}

  
# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = requests.post(url, auth=(username, password),json=myinput)
            response_dict = json.loads(response.text)
            s=response_dict['data']
            response2=s[0]['response']
            response=st.write(response_generator(response2))
            # message = {"role": "assistant", "content": response}
            # st.session_state.messages.append(message)
