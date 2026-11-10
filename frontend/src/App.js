import React, { useState } from "react";
import "./App.css";

function App() {
  // State pour la question et la réponse
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState("");
  const [chatHistory, setChatHistory] = useState([]);

  // Fonction pour gérer l'envoi du formulaire
  const handleSubmit = async (e) => {
    e.preventDefault(); // Empêche le rechargement de la page

    try {
      const res = await fetch("http://localhost:8001/ask", { // URL de l'API FastAPI
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: question }), // Envoi de la question au backend
      });

      if (!res.ok) {
        throw new Error("Erreur lors de la requête vers le backend");
      }

      const data = await res.json(); // Récupération de la réponse du backend
      setResponse(data.answer); // Mise à jour de l'état avec la réponse
      setChatHistory(prev => [...prev, { question, answer: data.answer }]);
    } catch (error) {
      console.error("Erreur :", error);
      setResponse("Un error has occured .please tray again."); // Message d'erreur utilisateur
    }
  };

  return (
    <div className="App">
      {/* En-tête */}
      <header className="header">
        <img src="/logo.jpg" alt="Logo ENS" className="school-logo" />
        <h2 className="school-name">
          École Nationale Supérieure de Statistique et d'Économie Appliquée
        </h2>
      </header>
  
      
{/* Conteneur principal : sidebar + main */}
<div className="chat-container">
  
  {/* Barre latérale gauche */}
  <aside className="chat-history">
    <h3>Chat History</h3>
    <ul>
       {chatHistory.map((item, index) => (
          <li
            key={index}
            onClick={() => setResponse(item.answer)}
            style={{ cursor: "pointer", marginBottom: "8px" }}
          >
              {item.question}
          </li>
        ))}
    </ul>
  </aside>

  {/* Section principale */}
  <main className="chat-main">
    <div className="ask-container">
      <img src="/chat_im.jpg" alt="chatbot" className="chatbot-icon" />
      <h1 className="ask-title"> Ask a question</h1>
    </div>

    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Enter your question here ..."
      />

      <button type="submit">Submit</button>

      <button
        type="button"
        onClick={() => setQuestion("")}
        className="reset-button"
        title="Réinitialiser la question"
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          padding: 0,
        }}
      >
        <img
          src="/trash.jpg"
          alt="Reset"
          className="reset-img"
          style={{ width: "24px", height: "24px" }}
        />
      </button>
    </form>

    <section className="response">
      <div
        style={{ whiteSpace: "pre-wrap" }}
        dangerouslySetInnerHTML={{ __html: response }}
      />
    </section>
  </main>
</div>



    </div>
  );
}

export default App;
