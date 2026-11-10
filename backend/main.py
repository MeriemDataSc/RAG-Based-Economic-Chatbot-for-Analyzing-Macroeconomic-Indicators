from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import markdown  
from llm import generate_response  # Votre fonction clé

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    query: str

# Fonction pour formater la réponse et remplacer les \n par <br />
def format_response(answer: str) -> str:
    
    # Assurer que 'answer' est une chaîne de caractères
    if isinstance(answer, dict):  # Si c'est un dictionnaire, le convertir en chaîne
        answer = str(answer)  # Convertir en chaîne si nécessaire
    #return answer.replace("\n", "<br />")
 # Convertir le texte Markdown en HTML
    html_answer = markdown.markdown(answer)
    return html_answer

@app.post("/ask")
def ask_question(data: Question):
    question = data.query
    print(f"Question reçue : {question}")  # Debugging

    # Appeler la fonction generate_response
    try:
        answer = generate_response(question)  # Obtenir une réponse
    except Exception as e:
        print(f"Erreur lors de la génération de réponse : {e}")
        return {"answer": "Une erreur est survenue dans le backend."}

    # Vérifier si answer est un dictionnaire et extraire la partie texte si nécessaire
    if isinstance(answer, dict):
        # S'assurer qu'on prend la partie texte de la réponse (supposons que la clé 'answer' contient le texte)
        answer = answer.get('answer', '')  # Récupérer le texte sous la clé 'answer'

    # Formater la réponse avant de l'envoyer (remplacer \n par <br />)
    formatted_answer = format_response(answer)

    # Retourner la réponse formatée
    return {"answer": formatted_answer}
