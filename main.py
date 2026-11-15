from ollama import chat, embeddings
import chromadb
import time
from pathlib import Path
import sys
import os
from dotenv import load_dotenv
import re

load_dotenv()
DATABASE_PATH = os.getenv('DATABASE_PATH')

#getting the embeddings
client = chromadb.PersistentClient(path=DATABASE_PATH)
collection = client.get_collection(name='my_docs')

history = []
MODEL = 'qwen3:4b'

def rewrite(query):

    if not history:
        return query

    recent = '\n'.join(f'{chat['role']} : {chat['content']}' for chat in history[-4:]) #last 4 conversation
    response = chat(model=MODEL,think=False,options={'num_ctx':2048,'num_predict':60},
                    messages=[{'role':'user','content':                
                            f"Chat so far:\n{recent}\n\nRewrite the last question as a standalone question. "
                            f"Output only the question.\nQuestion: {query}"}])
    
    return response.message.content or query

def conversation(query):
    standalone = rewrite(query)
    query_res = embeddings(model='nomic-embed-text',prompt=f"search_query: {standalone}")
    query_emb = query_res.embedding
    result = collection.query(query_embeddings=[query_emb],n_results=3)

    #context
    context = '\n\n'.join(f"page : {meta['page']}\n {doc}" for doc,meta in zip(result['documents'][0],result['metadatas'][0]))

    messages = [{"role": "system", "content":
                "You are a concise assistant. Look previous conversation for Answers."
                "If no answer in previous conversation then look into the provided context"
                "If it isn't there, say so. Format: one short bullet per item, "}]
    messages += history[-6:]
    messages.append({"role" : "user","content" : f"Context : {context}.\n\n Query : {query}"})
    #counter
    start = time.perf_counter()
    cpu_start = time.process_time()

    response = chat(model=MODEL,
                    messages=messages,
                    think=False,
                    keep_alive='30m',
                    options={'num_ctx':8000,'num_predict':800}) #  Sets the maximum number of tokens the model can generate in a single response.


    end = time.perf_counter()
    cpu_end = time.process_time()

    #model final output
    answer  = re.sub(r'^[\s\S]*?<\/think>',"",response.message.content,flags=re.S).strip()

    history.append({"role": "user", "content": query})       
    history.append({"role": "assistant", "content": answer})
    print(response.prompt_eval_count, response.eval_count)
    print('time elapsed : ',end - start)
    print('time CPU : ',cpu_end - cpu_start)
    return(answer)

while True:
    query = input("Enter the Query...Press Enter to exit : ")
    if not query:
        break

    answer = conversation(query)
    print(answer)
    