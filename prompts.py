"""
TalentScout Hiring Assistant — Prompt constants and prompt-building logic.
All LLM prompts and assistant message strings live here.
"""
import json

DEFAULT_TECH_STACK = "Python, Django, PostgreSQL"

# ---------------------------------------------------------------------------
# Assistant messages (chat UI)
# ---------------------------------------------------------------------------
MSG_GREETING = (
    "Welcome to TalentScout!\n\nLet's begin the screening process.\n\n"
    "What is your full name?"
)
MSG_GOODBYE = "Thank you for your time. Goodbye!"
MSG_FINISHED = "The screening process is completed. To start again, please refresh the page."
MSG_ASK_EMAIL = "Please provide your email address."
MSG_INVALID_EMAIL = "Invalid email format. Please enter a valid email address."
MSG_ASK_PHONE = "Please provide your phone number (exactly 10 digits, numbers only)."
MSG_INVALID_PHONE = (
    "Invalid phone. Use exactly 10 digits, numbers only. "
    "Avoid repeated digits (e.g. 1111111111)."
)
MSG_ASK_EXPERIENCE = "How many years of experience do you have?"
MSG_INVALID_EXPERIENCE = "Please enter a number between 0 and 50 for years of experience."
MSG_ASK_POSITION = "What position(s) are you applying for?"
MSG_ASK_LOCATION = "What is your current location?"
MSG_ASK_TECH_STACK = "Please list your tech stack (e.g. Python, Django, PostgreSQL)."
MSG_INVALID_TECH_STACK = (
    "That doesn't look like a valid tech stack. "
    "Please list technologies clearly (e.g., Python, Django, Java)."
)
MSG_NO_QUESTIONS_GENERATED = (
    "No questions were generated. Please provide a valid tech stack (e.g. Python, Java, Django) to continue."
)
MSG_NEED_MORE_ANSWERS = (
    "You have answered {answer_count} question(s). "
    "Please answer at least {min_required} before typing 'done'."
)
MSG_CAN_TYPE_DONE = "You can type 'done' when you have finished answering."
MSG_ANSWER_AT_LEAST_5 = (
    "Please answer the questions above. Each answer should be at least 5 words "
    "(or say e.g. 'I don't know' if unsure)."
)
MSG_MORE_DETAILED_ANSWER = (
    "Please provide a more detailed answer (at least 5 words), "
    "or say 'I don't know' if you're not sure."
)
MSG_COULD_NOT_GENERATE_QUESTIONS = (
    "Could not generate questions for that stack. "
    "Please provide a valid tech stack (e.g. Python, Java, Django) to try again."
)
MSG_QUESTIONS_INSTRUCTION = (
    "Please answer them (each answer at least 5 words, or say e.g. 'I don't know' if unsure). "
    "Type 'done' when you have answered at least 3 questions."
)
MSG_THANK_YOU_FULL = (
    "Thank you for your time.\n\n"
    "Our recruitment team will review your profile.\n\n"
    "📊 Recruiter Evaluation Summary:\n\n"
)
MSG_THANK_YOU_DONE = (
    "Thank you for completing the screening.\n\n"
    "Our recruitment team will review your profile.\n\n"
    "📊 Recruiter Evaluation Summary:\n\n"
)


def msg_default_tech_stack(default_stack: str) -> str:
    return f"Using default tech stack: {default_stack}. Generating questions..."


def msg_answer_remaining(remaining: int) -> str:
    return f"Thanks. Answer {remaining} more question(s), then type 'done' when finished."


def msg_questions_with_intro(questions_text: str) -> str:
    return f"Here are your technical questions:\n\n{questions_text}\n\n{MSG_QUESTIONS_INSTRUCTION}"


def msg_eval_summary_full(summary: str) -> str:
    return MSG_THANK_YOU_FULL + summary


def msg_eval_summary_done(summary: str) -> str:
    return MSG_THANK_YOU_DONE + summary


def msg_need_more_answers(answer_count: int, min_required: int) -> str:
    return MSG_NEED_MORE_ANSWERS.format(answer_count=answer_count, min_required=min_required)

# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------
QUESTION_GENERATION_SYSTEM = (
    "You are a strict technical interviewer. Do not assume unspecified technologies."
)


def build_question_prompt(tech_stack: str) -> str:
    """Build the user prompt for generating technical questions from a tech stack."""
    return f"""Candidate Tech Stack:
{tech_stack}

Generate 3-5 technical interview questions for EACH technology listed.

Format strictly as:

Technology:
- Question
- Question
"""


# ---------------------------------------------------------------------------
# Evaluation: full lack of knowledge (candidate said they don't know any)
# ---------------------------------------------------------------------------
EVAL_SYSTEM_FULL = """You are a strict technical hiring evaluator.
The candidate stated they do not know any of the answers. You MUST give a very low score (1-2/10) and Final Recommendation MUST be Reject.
Red Flags MUST include: "Candidate admitted lack of knowledge."
Output this exact format only:

Overall Score: X/10

Technical Depth:
Clarity:
Practical Knowledge:
Problem Solving:

Red Flags:
- Candidate admitted lack of knowledge.
- (any other relevant flags)

Final Recommendation: Reject"""


def build_eval_prompt_full(
    candidate_data: dict,
    questions_text: str,
    answers_for_eval: list,
) -> str:
    """Build the user prompt for evaluation when candidate stated they don't know any answers."""
    return f"""Candidate Information:
{json.dumps(candidate_data, indent=2)}

Technical Questions (as asked):
{questions_text}

Technical Answers (candidate stated they do not know any):
{json.dumps(answers_for_eval, indent=2)}

Evaluate. Score must be 1-2/10. Final Recommendation must be Reject. Output the format only."""


# ---------------------------------------------------------------------------
# Evaluation: normal (candidate typed "done" after answering)
# ---------------------------------------------------------------------------
EVAL_SYSTEM = """You are a strict technical hiring evaluator. You must NOT be polite or optimistic.
- Detect if any answer simply repeats or copies the question → penalize heavily.
- Detect shallow or generic responses (e.g. "it depends", "I would look it up") → penalize.
- Penalize lack of concrete examples or code/commands.
- Penalize vague theoretical explanations with no practical detail.
- Answers marked confidence "low" mean the candidate admitted lack of knowledge (e.g. "I don't know") → penalize these HEAVILY. You MUST include in Red Flags: "Candidate admitted lack of knowledge." when any answer has confidence "low".
- If the majority of answers are confidence "low", Final Recommendation MUST be Reject.
Judge ONLY on what the candidate actually wrote. No assumptions. No generosity. No artificial positivity.
Output MUST follow this exact format, nothing else:

Overall Score: X/10

Technical Depth:
Clarity:
Practical Knowledge:
Problem Solving:

Red Flags:
- (list any; include "Candidate admitted lack of knowledge." if any low-confidence answers; or "None" if none)

Final Recommendation:
Proceed / Consider / Reject"""


def build_eval_prompt(
    candidate_data: dict,
    questions_text: str,
    answers_for_eval: list,
    low_count: int,
    majority_low: bool,
) -> str:
    """Build the user prompt for normal evaluation (after candidate types 'done')."""
    critical_line = (
        f"CRITICAL: {low_count} of {len(answers_for_eval)} answers are low-confidence (majority). "
        "Final Recommendation MUST be Reject.\n"
        if majority_low
        else ""
    )
    return f"""Candidate Information:
{json.dumps(candidate_data, indent=2)}

Technical Questions (as asked):
{questions_text}

Technical Answers (in order; "confidence": "low" = candidate admitted lack of knowledge):
{json.dumps(answers_for_eval, indent=2)}

Evaluate strictly. Penalize low-confidence answers heavily. If any low-confidence, Red Flags must include "Candidate admitted lack of knowledge."
{critical_line}Output the required format only."""
