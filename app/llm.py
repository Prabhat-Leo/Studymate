import os
import logging
import json
from functools import lru_cache
from dotenv import load_dotenv
from openai import APIError, OpenAI
from app.rag import retrieve_context, retrieve_document_context

load_dotenv()

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_providers() -> list[tuple[str, OpenAI, str]]:
    providers = []
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key:
        providers.append((
            "Groq",
            OpenAI(
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=15.0,
                max_retries=0
            ),
            os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        ))
    if gemini_key:
        providers.append((
            "Gemini",
            OpenAI(
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=15.0,
                max_retries=0
            ),
            os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        ))

    if not providers:
        raise RuntimeError(
            "No AI provider is configured. Add GEMINI_API_KEY or GROQ_API_KEY to .env."
        )
    return providers

def get_ai_reply(user_message: str, doc_id: str | None = None) -> str:
    context = retrieve_context(user_message, doc_id=doc_id)

    system_prompt = (
        "You are StudyMate, a study tutor who explains concepts FAST and SIMPLE.\n"
        "STRICT RULES:\n"
        "- Maximum 4-5 sentences OR 3-4 short bullet points. Never more.\n"
        "- No headers, no markdown titles, no multi-section breakdowns unless the user explicitly asks for 'detailed' or 'full explanation'.\n"
        "- Explain like you're texting a friend before an exam — quick and clear, not a textbook chapter.\n"
        "- Use your own words. Never copy sentences from the notes.\n"
        "- If no relevant notes are found, say \"Not in your notes, but here's a quick explanation:\" then answer briefly.\n"
        "- Never refuse to answer."
    )

    user_prompt = (
        f"NOTES CONTEXT:\n{context}\n\nQUESTION: {user_message}"
        if context else
        f"QUESTION: {user_message}"
    )

    last_error = None
    for provider_name, client, model in _get_providers():
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=220,
                temperature=0.4
            )
            if not response.choices:
                last_error = RuntimeError(f"{provider_name} returned no completion choices.")
                continue
            reply = response.choices[0].message.content
            if isinstance(reply, str) and reply.strip():
                return reply.strip()
            last_error = RuntimeError(f"{provider_name} returned an empty response.")
        except APIError as error:
            last_error = error

        logger.warning(
            "%s request failed (%s); trying the next configured provider.",
            provider_name,
            type(last_error).__name__
        )

    raise RuntimeError(
        "All configured AI providers failed. Check provider keys, model names, and availability."
    ) from last_error

def get_answer(question: str, doc_id: str | None = None) -> str:
    return get_ai_reply(question, doc_id=doc_id)


def generate_quiz(doc_id: str, question_count: int = 10) -> dict:
    context = retrieve_document_context(doc_id)
    if not context:
        raise ValueError("The active PDF has no indexed text to build a quiz from.")

    system_prompt = (
        "Create accurate study quizzes using only the supplied PDF excerpts. "
        "Return one JSON object with a title and questions array. Each question "
        "must have question, options (exactly four strings), answer_index "
        "(integer from 0 to 3), and explanation. Do not include markdown."
    )
    user_prompt = (
        f"Create exactly {question_count} varied multiple-choice questions from "
        "the following PDF excerpts. Do not test information that is absent from "
        "the excerpts.\n\nPDF EXCERPTS:\n" + context
    )
    last_error = None
    for provider_name, client, model in _get_providers():
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=min(4000, 400 + question_count * 180),
                temperature=0.3
            )
            if not response.choices:
                raise ValueError("The provider returned no quiz choices.")
            content = response.choices[0].message.content
            if not isinstance(content, str) or not content.strip():
                raise ValueError("The provider returned an empty quiz response.")
            quiz = json.loads(content)
            if not isinstance(quiz, dict):
                raise ValueError("The provider returned an invalid quiz object.")
            questions = quiz.get("questions")
            if not isinstance(questions, list) or len(questions) != question_count:
                raise ValueError("The provider returned the wrong number of questions.")

            validated_questions = []
            for question in questions:
                if not isinstance(question, dict):
                    raise ValueError("The provider returned an invalid question object.")
                options = question.get("options")
                answer_index = question.get("answer_index")
                if (
                    not isinstance(question.get("question"), str)
                    or not isinstance(options, list)
                    or len(options) != 4
                    or any(not isinstance(option, str) or not option.strip() for option in options)
                    or not isinstance(answer_index, int)
                    or isinstance(answer_index, bool)
                    or not 0 <= answer_index < 4
                    or not isinstance(question.get("explanation"), str)
                ):
                    raise ValueError("The provider returned an invalid question format.")
                validated_questions.append({
                    "question": question["question"].strip(),
                    "options": [option.strip() for option in options],
                    "answer_index": answer_index,
                    "explanation": question["explanation"].strip()
                })

            return {
                "title": quiz.get("title") if isinstance(quiz.get("title"), str) else "PDF Practice Quiz",
                "questions": validated_questions
            }
        except (APIError, ValueError, TypeError, KeyError) as error:
            last_error = error
            logger.warning(
                "%s quiz generation failed (%s); trying the next configured provider.",
                provider_name,
                type(error).__name__
            )

    raise RuntimeError(
        "All configured AI providers failed to generate a valid quiz."
    ) from last_error


def generate_flashcards(doc_id: str, card_count: int = 12) -> dict:
    context = retrieve_document_context(doc_id)
    if not context:
        raise ValueError("The active PDF has no indexed text to build flashcards from.")

    system_prompt = (
        "Create accurate study flashcards using only the supplied PDF excerpts. "
        "Return one JSON object with a title and cards array. Each card must "
        "have front and back string fields. Do not include markdown."
    )
    user_prompt = (
        f"Create exactly {card_count} useful, non-duplicate flashcards from the "
        "following PDF excerpts. Put a concise question or term on the front and "
        "a concise explanation on the back. Do not add information absent from "
        f"the excerpts.\n\nPDF EXCERPTS:\n{context}"
    )
    last_error = None
    for provider_name, client, model in _get_providers():
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=min(4000, 300 + card_count * 140),
                temperature=0.3
            )
            if not response.choices:
                raise ValueError("The provider returned no flashcards.")
            payload = json.loads(response.choices[0].message.content or "")
            if not isinstance(payload, dict):
                raise ValueError("The provider returned an invalid flashcard set.")
            cards = payload.get("cards")
            if not isinstance(cards, list) or len(cards) != card_count:
                raise ValueError("The provider returned the wrong number of flashcards.")

            validated_cards = []
            for card in cards:
                if not isinstance(card, dict):
                    raise ValueError("The provider returned an invalid flashcard.")
                front, back = card.get("front"), card.get("back")
                if (
                    not isinstance(front, str) or not front.strip()
                    or not isinstance(back, str) or not back.strip()
                ):
                    raise ValueError("The provider returned an incomplete flashcard.")
                validated_cards.append({"front": front.strip(), "back": back.strip()})

            title = payload.get("title")
            return {
                "title": title.strip() if isinstance(title, str) and title.strip() else "PDF Flashcards",
                "cards": validated_cards
            }
        except (APIError, ValueError, TypeError, KeyError) as error:
            last_error = error
            logger.warning(
                "%s flashcard generation failed (%s); trying the next configured provider.",
                provider_name,
                type(error).__name__
            )

    raise RuntimeError(
        "All configured AI providers failed to generate valid flashcards."
    ) from last_error