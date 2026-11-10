
from dotenv import load_dotenv
import os
import pdfplumber
import pandas as pd
import numpy as np
import re

all_data_json = []
pdf_file='stat2021_removed.pdf'

def detect_header_row_count(table):
    """
    Détecte dynamiquement le nombre de lignes d'en-tête en examinant la première colonne.
    On compte combien de lignes (à partir de la 2e) ont None ou '' comme valeur.
    """
    count = 1  # on suppose que la 1ère ligne est toujours une entête
    for row in table[1:]:
        if row[0] is None or str(row[0]).strip().lower() == 'none' or str(row[0]).strip() == '':
            count += 1
        else:
            break
    return count



def fill_none_with_previous(header_rows):
    filled = []
    for row in header_rows:
        new_row = []
        last_val = ''
        for cell in row:
            if cell is None or str(cell).strip().lower() == 'none' or str(cell).strip() == '':
                new_row.append(last_val)
            else:
                last_val = str(cell).strip()
                new_row.append(last_val)
        filled.append(new_row)
    return filled

#----------------------------------------------------------------------------------------------------------------
#------------------ fonction principale ------------------------------------------------------------------------
last_title = " "
with pdfplumber.open(pdf_file) as pdf:
    
    for page in pdf.pages:  # verifier que page non vide ______________________________________________________
        page_text = page.extract_text()    # revoir 
        if not page_text:
            continue
    
            
        # bornes superieurs des tableaux :------------------------------------------------------
        table_boxes = page.find_tables()
        top_side_table=[]
        for i, table_obj in enumerate(table_boxes):    # bors sup de ts les tableaux
            x0, top, x1, bottom = table_obj.bbox
            print(table_obj.bbox)
            top_side_table.append(top)
        print('top_side_table:',top_side_table)   #liste bors sup de ts les tableaux
        
        # les titres -------------------------------------------------------------------------
        tables = page.extract_tables()
        titles=[]
        if tables:  # ya des tables ds la page actuelle
            words = page.extract_words()   # mot et tt ces coordonés 
            for i, word in enumerate(words):   # word est le dict (text+ coordonnes)
                if "Table" in word["text"]:
                    line_top = word["top"]
                    line_words = [w["text"] for w in words if abs(w["top"] - line_top) < 10]
                    title_text = ' '.join(line_words)        
                    titles.append({"text": title_text,"top": line_top})
        print('titles:', titles)
        top_titles= [item["top"] for item in titles]   # top_titles contient que les cordonnés des titres
        n_titles=len(titles)
        
        #Contenu de chaque tableau --------------------------------------------------------------
        tables_cont=page.extract_tables()
        # affectation  des titres 
        offset=0
        for index,table in enumerate(tables):
            current_index=index-offset
            if len(table)<2: # c'est pas un tableau (c une entete) , il faut l'eliminer et eliminer ses coord
                top_side_table.remove(min(top_side_table)) # ignorer cette barre et eliminer sa coord
                offset +=1
                continue
            
            
            # quelle est son titre :
            if len(titles)==0:     # si on pas de titres
                actual_title=last_title   # on affecte au tableau le dernier titre de la page precedante
                
            elif len(titles)==1:     # si un seul titre detecté
                print ("on a rentré")
                actual_title=titles[0]["text"]    # on l' affecte a tous les tableaux
            
            else:    # on a plusieur titres , on cherche celui qui corespond au tableau   
                
                distance=top_side_table[current_index]-np.array(top_titles)   # c'est un vecteur
                     # indice de min positif de distance
                positives = [(i, val) for i, val in enumerate(distance) if val > 0]
                min_index, min_value = min(positives, key=lambda item: item[1])  # min_index : indice titre convenable
                actual_title=titles[min_index]["text"]
       
            #------------------------------------------------------
            header_row_count = detect_header_row_count(table)
            header_rows = fill_none_with_previous(table[:header_row_count])
            # Concatène les valeurs verticalement pour chaque colonne (multi-rows header)
            full_headers = [' '.join(col).strip() for col in zip(*header_rows)]

            # Crée DataFrame avec données après les lignes d'entête
            df = pd.DataFrame(table[header_row_count:], columns=full_headers)
            df = df.dropna(how='all')  # supprime les lignes complètement vides  
            data_json = df.to_dict(orient="records")
            for row in data_json:
               row["title"] = actual_title  # Ajoute le titre à chaque ligne
            all_data_json.extend(data_json)
            
        last_title=actual_title  # actualiser la valeur du dernier titre (memoire)

  
  
  
  
                
#print(all_data_json)            
        
           

# #---------- functions -------------------------------------------------------------------------------
# def clean_cell(cell):
#     return None if cell is None or str(cell).strip().lower() in ('', 'none') else str(cell).strip()


  
import requests
import json
from groq import Groq 

 
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

messages = [
    {
        "role": "system",
        "content": "You are an assistant that converts JSON tables into structured text."
    },
    {
        "role": "user",
        "content": f"Transform all these data into a smooth structured text, do not summarize or ommit informations.Replace the letter (e) beforme numerical value by the word estimated. If the year is not mentioned in the data do not make any assumptions about the year. If year is mentionned in the data use it everu time it is mentionned: {json.dumps(all_data_json, indent=2)}"
    }
]

completion = client.chat.completions.create(
    model="llama3-8b-8192",
    messages=messages,
    temperature=0.5,
    max_completion_tokens=8192,
    top_p=1,
    stream=False  # False si tu veux la réponse complète d'un coup
)
texte_genere_par_llm=completion.choices[0].message.content
print(texte_genere_par_llm)


# #----------- RAG ------------------------------------------------------------------------------------------
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# initialisation 
# model embedding
embedding_model= HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# splitter
splitter=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50)

#------- Application  ----------------------------------------------------------------------------------------
# Encapsuler le texte dans un objet Document
doc = Document(page_content=texte_genere_par_llm)

# Chunking correctement
text_splitted = splitter.split_documents([doc])   # chunking

# afficher les chunks :
for idx, chunk in enumerate(text_splitted):
    print(f"Chunk {idx + 1}: {chunk.page_content}")
vectorstore = Chroma.from_documents(documents=text_splitted, embedding=embedding_model, persist_directory="chroma_store")

retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
result = retriever.get_relevant_documents("total population of North Macedonia in 2020?")
print("---------------------------------------------------------------------------------------")
print("---------------------------------------------------------------------------------------")

#print(result)

#--------- Interrogation du LLM avec le contexte extrait (RAG complet) -----------------------

# Étape 1 : Préparer la question
question = "total population of North Macedonia in 2020 ?"

# Étape 2 : Construire le contexte à partir des documents récupérés
context = "\n\n".join([doc.page_content for doc in result])

# Étape 3 : Construire le prompt pour Groq LLM
messages_rag = [
    {
        "role": "system",
        "content": "You are a helpful assistant. Answer the user's question using only the provided context. Be clear and concise. Do not make up any information."
    },
    {
        "role": "user",
        "content": f"""Context:Answer the question using only the data provided. Do not include any external information. Your response should be coherent and well-structured.you can add relative information to the answer using always data provided.


{context}

Question: {question}

Answer:"""
    }
]

# Étape 4 : Appeler le LLM
completion_rag = client.chat.completions.create(
    model="llama3-8b-8192",
    messages=messages_rag,
    temperature=0.5,
    max_completion_tokens=512
)

# Étape 5 : Afficher la réponse finale
final_answer = completion_rag.choices[0].message.content
print("\n========= FINAL ANSWER (LLM with RAG) =========\n")
print(final_answer)


