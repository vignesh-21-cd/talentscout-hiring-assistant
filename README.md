# TalentScout Hiring Assistant

AI-powered Hiring Assistant chatbot built using **Streamlit** and **Groq LLM** for intelligent technical candidate screening.

---

## Overview

TalentScout Hiring Assistant:

- Collects candidate information (name, email, phone, experience, position, location, tech stack)
- Validates inputs (email format, 10-digit phone, experience range)
- Generates technical interview questions based on declared tech stack
- Evaluates answers strictly using an LLM
- Produces a structured recruiter evaluation summary
- Saves interview results as JSON for recruiter review

---

## Tech Stack

- Python
- Streamlit
- Groq API (LLaMA 3.3 70B)
- JSON (local storage)

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/vignesh-21-cd/talentscout-hiring-assistant
cd talentscout-hiring-assistant
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file:

```
GROQ_API_KEY=your_api_key_here
```

### 5. Run Application

```bash
streamlit run app.py
```

---

## Interview Flow

greeting → information collection → tech stack validation → question generation → answer evaluation → recruiter summary → JSON export

---

## Output Storage

Completed interviews are saved in:

```
interview_results/
```

Each file contains:
- Candidate information
- Technical questions
- Candidate answers
- Evaluation summary

---

## Prompt Design

- Strict system prompts for evaluation
- Penalization of shallow or copied answers
- Detection of low-confidence responses
- Forced rejection when majority answers indicate lack of knowledge

## Live Demo

🔗 https://your-app-name.streamlit.app

---

## Live Demo

🔗 https://your-app-name.streamlit.app

## Author

Vignesh Kumar  
AI/ML Intern Assignment
