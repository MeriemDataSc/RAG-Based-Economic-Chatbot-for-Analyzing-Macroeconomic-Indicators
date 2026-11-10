import os
from dotenv import load_dotenv
from langchain.document_loaders import PyPDFLoader
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

import pandas as pd
import numpy as np
import re

import requests
import json
from groq import Groq 

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

# Define directories
pdf_directory = r"C:\Users\DELL\Desktop\essais\doc_pdf\temp" 
persist_directory = "./chroma_store"

# Initialize embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

#--------- functions-----------------------------------
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

#---------------------------------------------------------

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

#------------------------------------------------------
# Load (or initialize) the persistent Chroma vector store
if os.path.exists(os.path.join(persist_directory, "chroma.sqlite")):
    print("Base Chroma existante trouvée, chargement...")
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)
else:
    print("Aucune base trouvée, création d'une nouvelle...")
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embedding_model)

# Document splitter
book_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
report_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


# Loop through each PDF and add incrementally
for filename in os.listdir(pdf_directory):
    pdf_path = os.path.join(pdf_directory, filename)
    
    # the file is a book or a report ? 
    if filename.startswith("stat"):   #-------- a report ----------------
        print(f"report Processing: {filename}")
        
        last_title = " "
        text_generated_doc= [] # initialisation
        
        
        # use pdfplumber to extract tables
        with pdfplumber.open(pdf_path) as pdf:
        #-----------------------------------------------------------
            for page in pdf.pages:  # verifier que page non vide 
                all_data_json = []   # init
                # extraire tables ------- si pas de tables aller a la page suivante
                tables = page.extract_tables()
                if not tables:
                    continue
                
                # bornes superieurs des tableaux :------------------------------------------------------
                table_boxes = page.find_tables()
                top_side_table=[]
                for i, table_obj in enumerate(table_boxes):    # bors sup de ts les tableaux
                    x0, top, x1, bottom = table_obj.bbox
                    print(table_obj.bbox)
                    top_side_table.append(top)
                print('top_side_table:',top_side_table)   #liste bors sup de ts les tableaux
                
                # les titres ---------------------------------------------------------------------------
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
                    
                    actual_title=" "      # initialiser actual_title -----------------------------------------
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
                # end of page processing
                last_title=actual_title  # actualiser la valeur du dernier titre (memoire)
                
                # transformer les tableau de cette page en text par llm(groq)
                client = Groq(api_key=api_key)
                messages = [
                    {    "role": "system",
                        "content": "You are an assistant that converts JSON tables into structured text."
                    },
                    {
                        "role": "user",
                        "content": f"""Transform all these data into a smooth structured text, do not summarize or ommit informations.Replace the letter (e) beforme numerical value by the word estimated. If the year is not mentioned in the data do not make any assumptions about the year. *If year is mentionned in the data use it every time it is mentionned (Don't mention it just at the beginning of the generated text; mention it for each piece of information provided,
                                Don't condense the information; generate a complete and accurate response without leaving anything out: {json.dumps(all_data_json, indent=1)}"""
                    }]
                
                try:
                    completion = client.chat.completions.create(
                    model="llama3-8b-8192",messages=messages,
                    temperature=0.5,max_completion_tokens=8192,
                    top_p=1,stream=False    ) 
                    
                    texte_genere_par_llm_page=completion.choices[0].message.content
                    text_generated_doc.append(texte_genere_par_llm_page)
                except Exception as e:
                    print(f"Erreur lors de l'appel Groq sur la page {page.page_number} : {e}")    
        
        #---- fin covertion tables en text : text_generated_doc ----------------------------------------------
        print("End of conversion of report")
        # Split documents according to the file type
        docs = [Document(page_content=texte) for texte in text_generated_doc]
        chunks = report_splitter.split_documents(docs)

        # Add chunks to vector store and persist
        vector_store.add_documents(chunks)
        vector_store.persist()
        print(f"Added and persisted: {filename}")
        
    else:        #---------- a book -------------------------------------
        print(f"Book Processing: {filename}")
        # Load text with PyPDFLoader
        loader = PyPDFLoader(pdf_path)
        text_docs = loader.load()

        # Split documents according to the file type
        chunks = book_splitter.split_documents(text_docs)

        # Add chunks to vector store and persist
        vector_store.add_documents(chunks)
        vector_store.persist()
        print(f"Added and persisted: {filename}")



# # ------------------------------- retrieval --------------------------------------------------
# retriever = vector_store.as_retriever(search_kwargs={"k": 3})
# result = retriever.get_relevant_documents("what is algeria's volume of import in 2020? ")
# #print(result)

# #--------- Interrogation du LLM avec le contexte extrait (RAG complet) -----------------------

# # Étape 1 : Préparer la question
# question = "what is algeria thiopia's volume of import in 2020?"

# # Étape 2 : Construire le contexte à partir des documents récupérés
# context = "\n\n".join([doc.page_content for doc in result])

# # Étape 3 : Construire le prompt pour Groq LLM
# messages_rag = [
#     {
#         "role": "system",
#         "content": ("You are a precise but flexible assistant that extracts economic indicators from tabular or textual data. "
#                     "You understand that years may be implied from context (e.g., title of a table or section)."
#                     )
#     },
#     {
#         "role": "user",
#         "content": (f"You are an assistant that extracts economic data from provided data. "
#                     f"You are an assistant that extracts economic data (e.g., GDP, trade, inflation, etc.) from tables or text sections.\n"
#                     f"Your goal is to provide a clear and relevant answer to the question, based on the provided context.\n"
#                     f"If the year is not explicitly stated in the value but mentioned in the table title or section, you can assume it applies to the data. "
#                     f"Don't say 'not mentioned' if the value is visible. Provide the value in a short, precise format.\n\n"
#                     f"Write a short and coherent answer, directly addressing the question, including the value and the appropriate unit.\n\n"
#                     f"{context}\n\n"

#                     f"Question: {question}\n\n"

#                     f"Answer:"
#                     ) 
#     }
# ]

# # Étape 4 : Appeler le LLM
# completion_rag = client.chat.completions.create(
#     model="llama3-8b-8192",
#     messages=messages_rag,
#     temperature=0.3,
#     max_completion_tokens=512
# )

# # Étape 5 : Afficher la réponse finale
# final_answer = completion_rag.choices[0].message.content
# print("\n========= FINAL ANSWER (LLM with RAG) =========\n")
# print(final_answer)