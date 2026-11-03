# StudyMate Progress

## Completed

- Added Gemini/Groq provider failover. Groq is tried first with a 15-second timeout; Gemini is the fallback.
- Changed the default Groq model to `openai/gpt-oss-20b`, which was confirmed available to the configured Groq account.
- Scoped RAG retrieval to the latest uploaded PDF so chunks from other stored PDFs are excluded.
- Made PDF re-indexing replace existing chunks and remove stale chunks; empty extracted text is handled.
- Added upload validation for file type, empty files, unreadable PDFs, and PDFs without extractable text.
- Updated chat failure handling to return a useful JSON error and show upload/chat/clear errors in the chat UI.
- Updated the clear operation to remove messages, document records, vector data, and uploaded files.
- Replaced the unfinished `get_answer()` stub with the working answer function.
- Implemented an AI Quiz Generator grounded in the latest uploaded PDF, with configurable question count, multiple-choice answers, feedback, and score tracking.
- Fixed occasional blank chat replies by rejecting whitespace-only provider output in both backend and UI, trimming valid replies, and continuing to the fallback provider.
- Reused provider clients for HTTP connection pooling, handled empty completion choices through fallback, and removed per-query stdout logging from retrieval.
- Corrected README provider and file-layout descriptions and removed an unused backend import.
- Separated PDF upload from asking a question; a queued PDF can be uploaded without automatically sending the question.
- Implemented PDF-grounded flashcards with configurable deck size, answer reveal, next-card navigation, completion, and restart.
- Hardened quiz generation against empty provider completions so the configured fallback is tried instead of returning a 503.

## Verification

- Python modules compile with `compileall`.
- `templates/chat.js` passes `node --check`.
- Focused FastAPI tests cover provider failure, successful chat, invalid uploads, clear behavior, and passing the active PDF ID.
- Focused Chroma tests confirm upsert and document metadata filtering behavior.
- Quiz API tests cover active-document selection, question-count limits, missing PDFs, and malformed provider response fallback.
- Empty-choice quiz completion test confirms fallback reaches the second provider; live 5- and 10-question quizzes generated successfully.
- Browser interaction test covers quiz creation, answer feedback, question navigation, and final score.
- Active PDF quiz context is bounded to 14,000 characters and sampled across its chunks.
- Focused chat test confirms whitespace-only output triggers provider fallback and valid output is trimmed.
- Focused provider test confirms clients are cached and empty-choice responses fall back safely.
- Browser test confirms a whitespace-only API reply displays an explicit error instead of a blank message.
- A live reply with active-PDF context completed successfully with non-empty text.
- A short live Groq response succeeded in about 2.14 seconds.
- Confirmed the upload/send separation works in the chat workflow.
- Flashcard API validation confirms active-document selection, card-count bounds, and missing-PDF errors.
- Browser test covers flashcard reveal, next card, deck completion, and restart.
- Live generation produced three valid flashcards from the active PDF in about 2.23 seconds.
- The local app at `http://127.0.0.1:8001` returned HTTP 200 on the last check.

## Future Work

- [x] Implement an AI Quiz Generator grounded in the active PDF, with structured questions, answer choices, feedback, and score tracking.
- [x] Allow uploading a PDF separately from sending a chat question.
- [x] Implement active-PDF flashcards with reveal and deck navigation.
- [ ] Add persistent automated regression tests and configure a test runner; `pytest` is not currently installed in the workspace environment.
- [ ] Verify the full browser workflow with multiple real PDFs, including upload, document-scoped questions, and clearing data.
- [ ] Review the missing `requirements.txt`; it was already deleted in the workspace and has not been restored.
