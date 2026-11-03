# StudyMate Presentation Cheat Sheet

## Quick Pitch

**StudyMate** turns a student's PDF into a study workspace for document-based questions, quizzes, and flashcards. It finds relevant passages from the active PDF and uses an AI model to create concise, grounded study help.

## Feature Words

| Short label | Explain it like this |
|---|---|
| PDF Upload | Add a study PDF and process it for questions. |
| Text Extraction | Read selectable text from each PDF page. |
| Smart Chunks | Split text into overlapping pieces for better retrieval. |
| Embeddings | Convert text and questions into vectors that capture meaning. |
| Vector Search | Find PDF chunks that are semantically related to a question. |
| PDF Scope | Keep retrieval tied to the latest uploaded PDF. |
| AI Chat | Ask questions and receive answers grounded in retrieved notes. |
| Provider Fallback | Try Groq first, then Gemini if the request fails. |
| AI Quiz | Generate multiple-choice questions from the active PDF. |
| Flashcards | Generate front-and-back cards from the active PDF. |
| Answer Feedback | Show the correct option and explanation after an answer. |
| Score Tracking | Count correct quiz answers and show the final score. |
| Separate Upload | Upload a PDF first, then send questions separately. |
| Clear Data | Remove chat history, saved documents, uploaded PDFs, and vectors. |

## Main Functions

| Function | One-line explanation |
|---|---|
| `upload_pdf` | Validates a PDF, extracts its text, and indexes it. |
| `chunk_text` | Splits extracted text into overlapping chunks. |
| `index_pdf` | Embeds chunks and stores or updates them in ChromaDB. |
| `retrieve_context` | Finds the best-matching chunks from the active PDF. |
| `retrieve_document_context` | Gathers bounded PDF text for quiz and flashcard generation. |
| `get_ai_reply` | Sends the question and relevant context to the AI provider. |
| `generate_quiz` | Requests and validates structured multiple-choice questions. |
| `generate_flashcards` | Requests and validates structured front/back cards. |
| `clear_chat` | Clears messages, document records, vector data, and uploaded files. |

## Simple Flow

**Upload** → **Extract** → **Chunk** → **Embed** → **Retrieve** → **Answer / Practice**

- **Upload:** `POST /upload`
- **Chat:** `POST /chat`
- **Quiz:** `POST /quiz`
- **Flashcards:** `POST /flashcards`
- **Clear:** `POST /clear`

## Technology Words

- **Backend:** FastAPI
- **Language:** Python
- **PDF Reader:** pypdf
- **Embeddings:** FastEmbed, BGE small English model
- **Vector Store:** ChromaDB
- **AI Providers:** Groq primary, Gemini fallback
- **History:** SQLite
- **Frontend:** HTML, CSS, JavaScript

## Presentation Q&A

- **Why embeddings?** They match meaning, not just exact keywords.
- **Why chunks?** Smaller passages give the model focused source material.
- **Why PDF scope?** It prevents results from unrelated uploaded documents mixing together.
- **Why two providers?** A fallback can keep AI features available when the primary provider fails.
- **How are quizzes grounded?** Quiz and flashcard prompts use text retrieved from the active PDF.
