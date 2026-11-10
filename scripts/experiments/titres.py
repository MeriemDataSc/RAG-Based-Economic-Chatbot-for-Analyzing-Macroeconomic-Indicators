import pdfplumber
import pandas as pd
import re

all_data_json = []
pdf_file = 'stat2022.pdf'

def extract_year_from_title(title):
    # Cherche une année sur 4 chiffres entre 1900 et 2099 dans le titre
    match = re.search(r'\b(19|20)\d{2}\b', title)
    return match.group(0) if match else None

with pdfplumber.open(pdf_file) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        
        # Texte brut de la page pour détecter un éventuel titre
        page_text = page.extract_text()
        lines = page_text.split('\n') if page_text else []
        title = lines[0] if lines else ""
        
        # Cherche une année dans le titre
        year_from_title = extract_year_from_title(title)
        
        for table in tables:
            df = pd.DataFrame(table)
            
            if df.empty or df.shape[0] < 2:
                continue  # ignore tableaux vides ou sans contenu
            
            df.columns = df.iloc[0]
            df = df.iloc[1:]
            df = df.dropna(how='all')  # enlève les lignes complètement vides

            # Normalise les noms de colonnes
            df.columns = [str(col).strip().lower() for col in df.columns]

            # Cas 1 : année dans le titre → ajouter 'year' à chaque ligne
            if year_from_title and 'year' not in df.columns:
                df['year'] = year_from_title

            # Cas 2 : si colonne 'year' déjà présente → ne rien faire

            # Conversion en JSON
            data_json = df.to_dict(orient="records")
            all_data_json.extend(data_json)

# Affichage des données extraites
print("Nombre total d'enregistrements extraits :", len(all_data_json))
print(all_data_json)  # pour aperçu rapide des 3 premiers
