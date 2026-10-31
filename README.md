# Mizan — Arabic control engineering / Streamlit

Native Streamlit learning app: nine Arabic lessons from the user-supplied archive, five quizzes with an error-review mode, twelve Arabic/German flashcards, session notes, focus timer and a thermal P/PI/PID simulator with comparison and CSV export.

Run: `python -m streamlit run streamlit_app.py`

Community Cloud: main branch, entrypoint `streamlit_app.py`, Python 3.13. Dependencies are in requirements.txt. No secrets are required. Keep the repository and app private unless the owner chooses otherwise.

Progress and notes use per-user session state; they are not durable across reconnects. Notes can be downloaded as JSON. No shared progress files or server-side user tracking.

Source material: control_arabic.zip supplied by project owner; static text extracted without executing the archive. Quiz form branch feedback excluded. No Studyflix videos, images, or source code were copied. Thermal SVG adapted using Anatomy under MIT; see THIRD_PARTY_NOTICES.md. The previous standalone website remains a separate deployment; Streamlit is a native implementation and does not claim pixel-for-pixel or feature-for-feature parity.
