from __future__ import annotations
import os
from typing import Iterable


def llm_available() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def _rule_based_opt(resume_text: str, job_desc: str, missing_keywords: Iterable[str]) -> str:
    missing_sorted = sorted({k for k in missing_keywords if k and len(k) < 40})
    summary = (
        "Professional Summary\n"
        "Results-driven professional with experience relevant to the target role.\n"
        "Tailored to the job description with emphasis on measurable impact, tools, and domain expertise.\n"
    )
    skills = "Key Skills\n" + (", ".join(missing_sorted) if missing_sorted else "Aligned with JD; core skills already present.") + "\n"

    optimized = (
        summary
        + "\n"
        + skills
        + "\n"
        + "Experience\n"
        + resume_text.strip()
    )
    return optimized


def _llm_opt(resume_text: str, job_desc: str, missing_keywords: Iterable[str]) -> str:
    try:
        from groq import Groq
    except Exception:
        return _rule_based_opt(resume_text, job_desc, missing_keywords)

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return _rule_based_opt(resume_text, job_desc, missing_keywords)

    client = Groq(api_key=api_key)
    missing = ", ".join(sorted(set(missing_keywords)))
    prompt = f"""
    You are an expert resume writer. Improve the following resume to better match the job description. Keep the structure concise and quantifiable. Use action verbs and measurable outcomes. Ensure inclusion of these missing keywords when relevant: {missing}.

    Job Description:\n{job_desc}\n\nResume:\n{resume_text}

    Output a refined resume with sections: Professional Summary, Key Skills, Experience, Education (if present), Projects (if present).
    """
    model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You improve resumes for ATS and readability."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = (resp.choices[0].message.content or "").strip()
        return content or _rule_based_opt(resume_text, job_desc, missing_keywords)
    except Exception:
        return _rule_based_opt(resume_text, job_desc, missing_keywords)


def optimize_text(resume_text: str, job_desc: str, missing_keywords: Iterable[str], use_llm: bool = False) -> str:
    if use_llm and llm_available():
        return _llm_opt(resume_text, job_desc, missing_keywords)
    return _rule_based_opt(resume_text, job_desc, missing_keywords)
