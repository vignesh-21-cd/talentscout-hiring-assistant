import os
import re
import json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from prompts import (
    DEFAULT_TECH_STACK,
    QUESTION_GENERATION_SYSTEM,
    build_question_prompt,
    EVAL_SYSTEM_FULL,
    build_eval_prompt_full,
    EVAL_SYSTEM,
    build_eval_prompt,
    MSG_GREETING,
    MSG_GOODBYE,
    MSG_FINISHED,
    MSG_ASK_EMAIL,
    MSG_INVALID_EMAIL,
    MSG_ASK_PHONE,
    MSG_INVALID_PHONE,
    MSG_ASK_EXPERIENCE,
    MSG_INVALID_EXPERIENCE,
    MSG_ASK_POSITION,
    MSG_ASK_LOCATION,
    MSG_ASK_TECH_STACK,
    MSG_INVALID_TECH_STACK,
    MSG_NO_QUESTIONS_GENERATED,
    MSG_CAN_TYPE_DONE,
    MSG_ANSWER_AT_LEAST_5,
    MSG_MORE_DETAILED_ANSWER,
    MSG_COULD_NOT_GENERATE_QUESTIONS,
    msg_default_tech_stack,
    msg_answer_remaining,
    msg_questions_with_intro,
    msg_eval_summary_full,
    msg_eval_summary_done,
    msg_need_more_answers,
)
from ui import apply_global_styles, render_app_header, render_mode_badge, render_section, render_card

INTERVIEW_RESULTS_DIR = "interview_results"
RECRUITER_PASSWORD = "admin123"

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="🤖", layout="wide")
apply_global_styles()
render_app_header()

mode = st.sidebar.radio("Mode", ["Candidate Mode", "Recruiter Mode"], index=0)
render_mode_badge(mode)

if mode == "Recruiter Mode":
    pwd = st.sidebar.text_input("Password", type="password", key="recruiter_pwd")
    if not pwd:
        st.info("Enter recruiter password in the sidebar.")
        st.stop()
    if pwd != RECRUITER_PASSWORD:
        st.error("Access restricted to recruiters only.")
        st.stop()
    # Password correct: show recruiter dashboard
    render_section("Recruiter Dashboard")
    if os.path.isdir(INTERVIEW_RESULTS_DIR):
        files = sorted(
            [f for f in os.listdir(INTERVIEW_RESULTS_DIR) if f.endswith(".json")],
            reverse=True,
        )
        if not files:
            st.info("No interview results yet.")
        else:
            selected = st.selectbox("Select interview result", files, key="recruiter_select")
            if selected:
                path = os.path.join(INTERVIEW_RESULTS_DIR, selected)
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                interview_id = data.get("interview_id", "N/A")
                st.markdown(f"**📌 Interview ID:** `{interview_id}`")
                st.divider()
                render_card(
                    "Candidate Information",
                    json.dumps(data.get("candidate_information", {}), indent=2, ensure_ascii=False),
                )
                q = data.get("technical_questions") or ""
                render_card(
                    "Technical Questions",
                    q if isinstance(q, str) else json.dumps(q, indent=2),
                )
                ta = data.get("technical_answers", [])
                render_card(
                    "Technical Answers",
                    json.dumps(ta, indent=2, ensure_ascii=False),
                )
                summary = data.get("evaluation_summary") or ""
                render_card(
                    "Evaluation Summary",
                    summary if isinstance(summary, str) else json.dumps(summary, indent=2),
                )
    else:
        st.info("No interview results folder yet.")
    st.stop()

# Candidate Mode: run interview flow below
if "messages" not in st.session_state:
    st.session_state.messages = []

if "stage" not in st.session_state:
    st.session_state.stage = "greeting"

if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = {
        "name": None,
        "email": None,
        "phone": None,
        "experience": None,
        "position": None,
        "location": None,
        "tech_stack": None,
    }

if "technical_answers" not in st.session_state:
    st.session_state.technical_answers = []

if "answer_count" not in st.session_state:
    st.session_state.answer_count = 0

if "min_answers_required" not in st.session_state:
    st.session_state.min_answers_required = 3

if "tech_stack_attempts" not in st.session_state:
    st.session_state.tech_stack_attempts = 0

if "questions_generated" not in st.session_state:
    st.session_state.questions_generated = False

if "questions_text" not in st.session_state:
    st.session_state.questions_text = None

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", (email or "").strip()))


def is_valid_phone(phone: str) -> bool:
    s = (phone or "").strip()
    if not s.isdigit():
        return False
    if len(s) != 10:
        return False
    if len(set(s)) == 1:
        return False
    return True


def is_valid_experience(exp: str) -> bool:
    s = (exp or "").strip()
    if not s.isdigit():
        return False
    n = int(s)
    return 0 <= n <= 50


def is_valid_tech_stack(stack: str) -> bool:
    """Require at least one alphabetic word; reject gibberish (e.g. no vowel)."""
    s = (stack or "").strip()
    if not s:
        return False
    words = [w for w in s.replace(",", " ").split() if w]
    if not words:
        return False
    vowels = set("aeiouAEIOU")
    return any(
        w and any(c.isalpha() for c in w) and any(c in vowels for c in w)
        for w in words
    )


def is_valid_position(position: str) -> bool:
    """Reject numeric-only, < 3 chars, special-char-only. Accept meaningful job titles."""
    s = (position or "").strip()
    if len(s) < 3:
        return False
    if s.isdigit():
        return False
    if not any(c.isalpha() for c in s):
        return False
    return True


def is_valid_location(location: str) -> bool:
    """Reject numeric-only, < 2 chars, special-char-only. Accept city names or meaningful location."""
    s = (location or "").strip()
    if len(s) < 2:
        return False
    if s.isdigit():
        return False
    if not any(c.isalpha() for c in s):
        return False
    return True


# Phrases that count as valid "lack of knowledge" answers (no minimum word count)
LACK_OF_KNOWLEDGE_PHRASES = (
    "i don't know",
    "i dont know",
    "not sure",
    "no idea",
    "i only know this much",
    "i am not aware",
    "not aware",
    "don't know",
    "dont know",
    "i dont know any",
)

# Early termination messages (validation / answer handling)
MSG_INVALID_POSITION = "Please enter a valid job title (e.g., SDE, Backend Developer)."
MSG_INVALID_LOCATION = "Please enter a valid location (e.g., Bangalore, Mumbai)."
MSG_EARLY_TERMINATION_UNPREPARED = (
    "It appears you are not prepared for the technical round. The screening will now conclude."
)
MSG_EARLY_TERMINATION_CONSECUTIVE = (
    "Multiple answers indicated lack of knowledge. The screening will now conclude."
)

# Global "I don't know any (of the answers)" → end interview immediately, Reject
FULL_LACK_PHRASES = (
    "i don't know any of the answers",
    "i dont know any of the answers",
    "i don't know any of these",
    "i dont know any of these",
    "don't know any of the answers",
    "dont know any of the answers",
    "i don't know any",
    "i dont know any",
    "no idea about any",
    "not sure about any",
    "i don't know any of them",
    "i dont know any of them",
)


def is_lack_of_knowledge_answer(text: str) -> bool:
    """Simple keyword detection: treat as valid answer that admits lack of knowledge."""
    t = (text or "").strip().lower()
    return any(phrase in t for phrase in LACK_OF_KNOWLEDGE_PHRASES)


def is_full_lack_of_knowledge(text: str) -> bool:
    """Candidate says they don't know any answers → end interview, Reject."""
    t = (text or "").strip().lower()
    return any(phrase in t for phrase in FULL_LACK_PHRASES)


if st.session_state.stage == "greeting" and len(st.session_state.messages) == 0:
    st.session_state.messages.append({"role": "assistant", "content": MSG_GREETING})
    st.session_state.stage = "collect_name"


if st.session_state.stage != "finished":
    user_input = st.chat_input("Type your message here...")
else:
    st.info("Interview completed. Refresh the page to start a new session.")
    user_input = None

if user_input:
    text = (user_input or "").strip()
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Exit/quit/bye → stop immediately
    if text.lower() in ("exit", "quit", "bye"):
        st.session_state.messages.append({"role": "assistant", "content": MSG_GOODBYE})
        st.session_state.stage = "finished"

    elif st.session_state.stage == "finished":
        st.session_state.messages.append({"role": "assistant", "content": MSG_FINISHED})

    elif st.session_state.stage == "collect_name":
        st.session_state.candidate_data["name"] = text
        st.session_state.messages.append({"role": "assistant", "content": MSG_ASK_EMAIL})
        st.session_state.stage = "collect_email"

    elif st.session_state.stage == "collect_email":
        if not is_valid_email(text):
            st.session_state.messages.append({"role": "assistant", "content": MSG_INVALID_EMAIL})
        else:
            st.session_state.candidate_data["email"] = text
            st.session_state.messages.append({"role": "assistant", "content": MSG_ASK_PHONE})
            st.session_state.stage = "collect_phone"

    elif st.session_state.stage == "collect_phone":
        if not is_valid_phone(text):
            st.session_state.messages.append({"role": "assistant", "content": MSG_INVALID_PHONE})
        else:
            st.session_state.candidate_data["phone"] = text
            st.session_state.messages.append({"role": "assistant", "content": MSG_ASK_EXPERIENCE})
            st.session_state.stage = "collect_experience"

    elif st.session_state.stage == "collect_experience":
        if not is_valid_experience(text):
            st.session_state.messages.append({"role": "assistant", "content": MSG_INVALID_EXPERIENCE})
        else:
            st.session_state.candidate_data["experience"] = text
            st.session_state.messages.append({"role": "assistant", "content": MSG_ASK_POSITION})
            st.session_state.stage = "collect_position"

    elif st.session_state.stage == "collect_position":
        if not is_valid_position(text):
            st.session_state.messages.append({"role": "assistant", "content": MSG_INVALID_POSITION})
        else:
            st.session_state.candidate_data["position"] = text
            st.session_state.messages.append({"role": "assistant", "content": MSG_ASK_LOCATION})
            st.session_state.stage = "collect_location"

    elif st.session_state.stage == "collect_location":
        if not is_valid_location(text):
            st.session_state.messages.append({"role": "assistant", "content": MSG_INVALID_LOCATION})
        else:
            st.session_state.candidate_data["location"] = text
            st.session_state.messages.append({"role": "assistant", "content": MSG_ASK_TECH_STACK})
            st.session_state.stage = "collect_tech_stack"

    elif st.session_state.stage == "collect_tech_stack":
        if not is_valid_tech_stack(text):
            st.session_state.tech_stack_attempts += 1
            if st.session_state.tech_stack_attempts == 1:
                st.session_state.messages.append({"role": "assistant", "content": MSG_INVALID_TECH_STACK})
            else:
                st.session_state.candidate_data["tech_stack"] = DEFAULT_TECH_STACK
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg_default_tech_stack(DEFAULT_TECH_STACK),
                })
                st.session_state.stage = "generate_questions"
        else:
            st.session_state.candidate_data["tech_stack"] = text
            st.session_state.tech_stack_attempts = 0
            st.session_state.stage = "generate_questions"

    elif st.session_state.stage == "generate_questions":
        # No user action advances this stage; LLM runs in the block above on next run
        pass

    elif st.session_state.stage == "answering_questions":
        if not st.session_state.questions_generated or not st.session_state.questions_text:
            st.session_state.messages.append({
                "role": "assistant",
                "content": MSG_NO_QUESTIONS_GENERATED,
            })
            st.session_state.questions_generated = False
            st.session_state.questions_text = None
            st.session_state.stage = "collect_tech_stack"
        elif is_full_lack_of_knowledge(text):
            # Candidate says they don't know any answers → end interview, generate eval, Reject
            st.session_state.technical_answers.append({"response": text, "confidence": "low"})
            st.session_state.answer_count += 1
            answers_for_eval = []
            for a in st.session_state.technical_answers:
                if isinstance(a, dict):
                    answers_for_eval.append(a)
                else:
                    answers_for_eval.append({"response": a, "confidence": "normal"})
            eval_prompt_full = build_eval_prompt_full(
                st.session_state.candidate_data,
                st.session_state.questions_text,
                answers_for_eval,
            )
            with st.spinner("Evaluating your responses..."):
                summary_response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": EVAL_SYSTEM_FULL},
                        {"role": "user", "content": eval_prompt_full},
                    ],
                    temperature=0.2,
                )
                summary = (summary_response.choices[0].message.content or "").strip()
            interview_id = f"TS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            id_msg = f"📌 Interview ID: {interview_id}\nPlease use this ID for any follow-up communication.\n\n"
            st.session_state.messages.append({
                "role": "assistant",
                "content": id_msg + msg_eval_summary_full(summary),
            })
            st.session_state.stage = "finished"
            os.makedirs(INTERVIEW_RESULTS_DIR, exist_ok=True)
            safe_name = re.sub(r"[^\w\-]", "_", (st.session_state.candidate_data.get("name") or "Unknown").strip())[:50]
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(INTERVIEW_RESULTS_DIR, f"{safe_name}_{ts}.json")
            payload = {
                "timestamp": datetime.now().isoformat(),
                "interview_id": interview_id,
                "candidate_information": dict(st.session_state.candidate_data),
                "tech_stack": st.session_state.candidate_data.get("tech_stack"),
                "technical_questions": st.session_state.questions_text,
                "technical_answers": answers_for_eval,
                "evaluation_summary": summary,
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        elif text.lower() == "done":
            if st.session_state.answer_count < st.session_state.min_answers_required:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg_need_more_answers(
                        st.session_state.answer_count,
                        st.session_state.min_answers_required,
                    ),
                })
            else:
                # Normalize answers: may be dicts (response/confidence) or legacy strings
                answers_for_eval = []
                for a in st.session_state.technical_answers:
                    if isinstance(a, dict):
                        answers_for_eval.append(a)
                    else:
                        answers_for_eval.append({"response": a, "confidence": "normal"})

                # Strict evaluation: penalize low-confidence heavily; majority low → Reject
                low_count = sum(1 for a in answers_for_eval if isinstance(a, dict) and a.get("confidence") == "low")
                majority_low = low_count > len(answers_for_eval) / 2
                eval_prompt = build_eval_prompt(
                    st.session_state.candidate_data,
                    st.session_state.questions_text,
                    answers_for_eval,
                    low_count,
                    majority_low,
                )
                with st.spinner("Evaluating your responses..."):
                    summary_response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": EVAL_SYSTEM},
                            {"role": "user", "content": eval_prompt},
                        ],
                        temperature=0.2,
                    )
                    summary = (summary_response.choices[0].message.content or "").strip()
                interview_id = f"TS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                id_msg = f"📌 Interview ID: {interview_id}\nPlease use this ID for any follow-up communication.\n\n"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": id_msg + msg_eval_summary_done(summary),
                })
                st.session_state.stage = "finished"

                # Save interview results for recruiter review
                os.makedirs(INTERVIEW_RESULTS_DIR, exist_ok=True)
                safe_name = re.sub(r"[^\w\-]", "_", (st.session_state.candidate_data.get("name") or "Unknown").strip())[:50]
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(INTERVIEW_RESULTS_DIR, f"{safe_name}_{ts}.json")
                payload = {
                    "timestamp": datetime.now().isoformat(),
                    "interview_id": interview_id,
                    "candidate_information": dict(st.session_state.candidate_data),
                    "tech_stack": st.session_state.candidate_data.get("tech_stack"),
                    "technical_questions": st.session_state.questions_text,
                    "technical_answers": answers_for_eval,
                    "evaluation_summary": summary,
                }
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2, ensure_ascii=False)
        else:
            if is_lack_of_knowledge_answer(text):
                st.session_state.technical_answers.append({
                    "response": text,
                    "confidence": "low",
                })
                st.session_state.answer_count += 1
                first_answer_low = st.session_state.answer_count == 1
                two_consecutive_low = (
                    len(st.session_state.technical_answers) >= 2
                    and isinstance(st.session_state.technical_answers[-2], dict)
                    and st.session_state.technical_answers[-2].get("confidence") == "low"
                )
                if first_answer_low or two_consecutive_low:
                    answers_for_eval = []
                    for a in st.session_state.technical_answers:
                        if isinstance(a, dict):
                            answers_for_eval.append(a)
                        else:
                            answers_for_eval.append({"response": a, "confidence": "normal"})
                    eval_prompt_full = build_eval_prompt_full(
                        st.session_state.candidate_data,
                        st.session_state.questions_text,
                        answers_for_eval,
                    )
                    with st.spinner("Evaluating your responses..."):
                        summary_response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": EVAL_SYSTEM_FULL},
                                {"role": "user", "content": eval_prompt_full},
                            ],
                            temperature=0.2,
                        )
                        summary = (summary_response.choices[0].message.content or "").strip()
                    interview_id = f"TS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    id_msg = f"📌 Interview ID: {interview_id}\nPlease use this ID for any follow-up communication.\n\n"
                    early_msg = (
                        MSG_EARLY_TERMINATION_UNPREPARED
                        if first_answer_low
                        else MSG_EARLY_TERMINATION_CONSECUTIVE
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": id_msg + early_msg + "\n\n📊 Recruiter Evaluation Summary:\n\n" + summary,
                    })
                    st.session_state.stage = "finished"
                    os.makedirs(INTERVIEW_RESULTS_DIR, exist_ok=True)
                    safe_name = re.sub(r"[^\w\-]", "_", (st.session_state.candidate_data.get("name") or "Unknown").strip())[:50]
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(INTERVIEW_RESULTS_DIR, f"{safe_name}_{ts}.json")
                    payload = {
                        "timestamp": datetime.now().isoformat(),
                        "interview_id": interview_id,
                        "candidate_information": dict(st.session_state.candidate_data),
                        "tech_stack": st.session_state.candidate_data.get("tech_stack"),
                        "technical_questions": st.session_state.questions_text,
                        "technical_answers": answers_for_eval,
                        "evaluation_summary": summary,
                    }
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(payload, f, indent=2, ensure_ascii=False)
                else:
                    remaining = st.session_state.min_answers_required - st.session_state.answer_count
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": msg_answer_remaining(remaining) if remaining > 0 else MSG_CAN_TYPE_DONE,
                    })
            else:
                word_count = len(text.split())
                if st.session_state.answer_count == 0 and word_count < 5:
                    st.session_state.messages.append({"role": "assistant", "content": MSG_ANSWER_AT_LEAST_5})
                elif word_count < 5:
                    st.session_state.messages.append({"role": "assistant", "content": MSG_MORE_DETAILED_ANSWER})
                else:
                    st.session_state.technical_answers.append({"response": text, "confidence": "normal"})
                    st.session_state.answer_count += 1
                    remaining = st.session_state.min_answers_required - st.session_state.answer_count
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": msg_answer_remaining(remaining) if remaining > 0 else MSG_CAN_TYPE_DONE,
                    })



if st.session_state.stage == "generate_questions" and not st.session_state.questions_generated:
    tech_stack = st.session_state.candidate_data.get("tech_stack") or DEFAULT_TECH_STACK
    prompt = build_question_prompt(tech_stack)
    with st.spinner("Generating technical questions..."):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": QUESTION_GENERATION_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        questions = (response.choices[0].message.content or "").strip()
    invalid_markers = ("no recognizable", "cannot identify", "could not identify", "unable to", "no valid", "no technologies", "no technology")
    questions_valid = len(questions) > 50 and not any(m in questions.lower() for m in invalid_markers)
    if questions_valid:
        st.session_state.questions_text = questions
        st.session_state.questions_generated = True
        st.session_state.messages.append({
            "role": "assistant",
            "content": msg_questions_with_intro(questions),
        })
        st.session_state.stage = "answering_questions"
    else:
        st.session_state.messages.append({"role": "assistant", "content": MSG_COULD_NOT_GENERATE_QUESTIONS})
        st.session_state.stage = "collect_tech_stack"
        


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
