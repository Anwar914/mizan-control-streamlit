# Mizan — Arabic control engineering / Streamlit

Native Streamlit learning app: nine Arabic lessons from the user-supplied archive, five quizzes with an error-review mode, 24 Arabic/German flashcards, session notes, focus timer and a thermal P/PI/PID simulator with comparison, step-response metrics (overshoot, 2 % settling time, final error) and CSV export. The Anatomy thermal rig is live: the display bar follows the temperature, the eight LEDs and the heater glow follow the controller output u at the chosen time; on the dashboard it reflects lesson progress.

Run: `python -m streamlit run streamlit_app.py`

Community Cloud: main branch, entrypoint `streamlit_app.py`, Python 3.13. Dependencies are in requirements.txt. No secrets are required. Keep the repository and app private unless the owner chooses otherwise.

Progress and notes use per-user session state; they are not durable across reconnects. Notes can be downloaded as JSON. No shared progress files or server-side user tracking.

Source material: control_arabic.zip supplied by project owner; static text extracted without executing the archive. Quiz form branch feedback excluded. No Studyflix videos, images, or source code were copied. Thermal SVG adapted using Anatomy under MIT; see THIRD_PARTY_NOTICES.md. The previous standalone website remains a separate deployment; Streamlit is a native implementation and does not claim pixel-for-pixel or feature-for-feature parity.

Design: colors follow the control loop. Ink `#13262D` marks the reference (setpoint, primary actions), teal `#0C7C84` the measurement (temperature, progress), heat `#D4521C` only the actuation (u, heater). The paper is `#F3F5F4` with grid `#D9E1DF`. Headings use Reem Kufi and reading text Noto Naskh Arabic (Google Fonts, set in `.streamlit/config.toml`). The dashboard hero is a step-response curve that draws itself once and marks the learner's progress; it respects `prefers-reduced-motion`.
