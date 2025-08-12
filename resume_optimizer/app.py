from pathlib import Path
import os
import json
import streamlit as st

from utils.parser import extract_text_and_fields
from utils.scorer import load_keywords, score_text
from utils.optimizer import optimize_text, llm_available
from utils.exporter import to_pdf_bytes, to_docx_bytes


def load_css():
    css_path = Path(__file__).parent / "static" / "style.css"
    if css_path.exists():
        try:
            st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
        except Exception:
            pass


def sidebar_controls():
    with st.sidebar:
        st.header("Settings")
        # Allow entering an API key inline (optional); will be set only for this session
        api_key = st.text_input("Groq API Key (optional)", type="password", help="If provided, enables LLM optimization via Groq for this session.")
        if api_key:
            os.environ["GROQ_API_KEY"] = api_key
        use_llm_default = llm_available()
        use_llm = st.toggle("Use LLM optimization", value=use_llm_default)
        export_fmt = st.selectbox("Export format", ["PDF", "DOCX"], index=0)
        st.caption("Set GROQ_API_KEY or enter it above. If unset, optimization falls back to rule-based.")
    return use_llm, export_fmt


def _reset_state():
    for k in [
        "resume_text",
        "fields",
        "score",
        "details",
        "matched",
        "missing",
        "optimized",
    ]:
        if k in st.session_state:
            del st.session_state[k]


def main():
    st.set_page_config(page_title="AI Resume Optimiser", page_icon="🧠", layout="wide")
    load_css()

    st.title("AI Resume Optimiser and Generator")
    st.caption("Upload a resume and paste a job description to get ATS-style scoring, semantic similarity, optimization suggestions, and export.")

    use_llm, export_fmt = sidebar_controls()

    left, right = st.columns([1, 1])
    with left:
        uploaded = st.file_uploader("Upload resume", type=["txt", "pdf", "docx"])
    with right:
        jd = st.text_area("Job description", height=240, placeholder="Paste the target job description here…")

    # Sample data helpers
    sample_resume = (
        "John Doe\n"
        "Senior Data Scientist\n"
        "john.doe@example.com | +1-555-123-4567 | San Francisco, CA\n\n"
        "Experience\n"
        "- Led ML projects using Python, Pandas, NumPy, Scikit-learn, and TensorFlow.\n"
        "- Built REST APIs with Docker and Kubernetes on AWS.\n"
        "- Collaborated in Agile teams, improving deployment via MLOps.\n"
    )
    sample_jd = (
        "We are seeking a Senior Machine Learning Engineer with strong Python, SQL, "
        "TensorFlow/PyTorch experience. Responsibilities include building microservices, "
        "developing REST APIs, and deploying on AWS or GCP. Agile and communication skills required."
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Load sample resume + JD"):
            st.session_state.resume_text = sample_resume
            st.session_state.fields = {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
            }
            st.session_state.optimized = None
            st.success("Loaded sample data.")
    with c2:
        if st.button("Reset"):
            _reset_state()
            st.experimental_rerun()

    # Session state defaults
    defaults = {
        "resume_text": "",
        "fields": {},
        "score": None,
        "details": None,
        "matched": set(),
        "missing": set(),
        "optimized": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if uploaded is not None:
        try:
            with st.spinner("Parsing resume..."):
                text, fields = extract_text_and_fields(uploaded)
            if not (text or '').strip():
                st.warning("No text could be extracted from the uploaded file.")
            st.session_state.resume_text = text
            st.session_state.fields = fields
            st.success("Resume parsed.")
        except Exception as e:
            st.error(f"Failed to parse file: {e}")

    if st.session_state.resume_text:
        st.subheader("Extracted details")
        cols = st.columns(3)
        cols[0].metric("Name", st.session_state.fields.get("name", "-") or "-")
        cols[1].metric("Email", st.session_state.fields.get("email", "-") or "-")
        cols[2].metric("Phone", st.session_state.fields.get("phone", "-") or "-")

        st.subheader("Resume text (parsed)")
        st.text_area("", st.session_state.resume_text, height=220, key="resume_text_view")

        if st.button("Score vs Job Description", type="primary", disabled=not bool(jd.strip())):
            kw_dir = Path(__file__).parent / "data" / "keywords"
            with st.spinner("Scoring vs JD..."):
                kw_by_cat = load_keywords(kw_dir)
                score, matched, missing, details = score_text(st.session_state.resume_text, jd, kw_by_cat)
            st.session_state.score = score
            st.session_state.details = details
            st.session_state.matched = matched
            st.session_state.missing = missing

        if st.session_state.score is not None and st.session_state.details is not None:
            st.subheader("ATS-style scoring")
            c1, c2, c3 = st.columns(3)
            c1.metric("Overall score", f"{st.session_state.score:.1f} / 100")
            c2.metric("Exact match", f"{st.session_state.details.get('exact_score', 0):.1f}")
            c3.metric("Semantic sim.", f"{st.session_state.details.get('semantic', 0):.1f}")
            st.progress(min(1.0, st.session_state.score / 100.0))

            with st.expander("Matched keywords"):
                st.write(", ".join(sorted(st.session_state.matched)) or "None")
            with st.expander("Missing keywords (from JD)"):
                st.write(", ".join(sorted(st.session_state.missing)) or "None")

            # Category coverage
            cat = st.session_state.details.get("category_breakdown", {})
            if cat:
                st.subheader("Category coverage")
                for category, info in cat.items():
                    coverage = info.get("coverage", 0.0)
                    st.write(f"{category} — {coverage:.0f}%")
                    st.progress(int(coverage) / 100.0)

            # Download score report as JSON (ensure all sets are serializable)
            _details = st.session_state.details or {}
            _cat = _details.get("category_breakdown", {})
            cat_json = {}
            for _k, _v in _cat.items():
                if isinstance(_v, dict):
                    cat_json[_k] = {
                        "coverage": float(_v.get("coverage", 0.0)),
                        "matched": sorted(list(_v.get("matched", []))),
                        "missing": sorted(list(_v.get("missing", []))),
                    }
            details_json = {
                "exact_score": float(_details.get("exact_score", 0.0)),
                "semantic": float(_details.get("semantic", 0.0)),
                "category_breakdown": cat_json,
            }

            report = {
                "overall": float(st.session_state.score),
                "details": details_json,
                "matched": sorted(list(st.session_state.matched)),
                "missing": sorted(list(st.session_state.missing)),
            }
            st.download_button(
                label="Download score report (JSON)",
                data=json.dumps(report, indent=2).encode("utf-8"),
                file_name="score_report.json",
                mime="application/json",
            )

        if use_llm and not llm_available():
            st.info("LLM is not available (no API key set). Optimization will fall back to rule-based.")

        if st.button("Optimise Resume", disabled=not bool(jd.strip())):
            with st.spinner("Generating optimized resume..."):
                st.session_state.optimized = optimize_text(
                    st.session_state.resume_text,
                    jd,
                    st.session_state.get("missing", set()),
                    use_llm=use_llm,
                )

        if st.session_state.optimized:
            st.subheader("Optimized resume")
            st.text_area("Optimized text", st.session_state.optimized, height=320, key="opt_text_view")

            if export_fmt == "PDF":
                data_bytes = to_pdf_bytes(st.session_state.optimized)
                file_name = "optimized_resume.pdf"
                mime = "application/pdf"
            else:
                data_bytes = to_docx_bytes(st.session_state.optimized)
                file_name = "optimized_resume.docx"
                mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

            st.download_button(
                label=f"Download as {export_fmt}",
                data=data_bytes,
                file_name=file_name,
                mime=mime,
            )


if __name__ == "__main__":
    main()
