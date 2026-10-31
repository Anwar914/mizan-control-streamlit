"""Mizan: native Arabic Streamlit learning environment. No uploaded code executed."""
from pathlib import Path
import json
import math
import re
import time

import bleach
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="ميزان | هندسة التحكم", page_icon="⚙️", layout="wide")
st.html("""<style>
[data-testid="stMain"], [data-testid="stSidebar"] {direction:rtl;text-align:right}
[data-testid="stMarkdownContainer"] {text-align:right}
[data-testid="stMetric"] {background:#fff;border:1px solid #e8e8f2;border-radius:16px;padding:18px}
[data-testid="stSidebar"] {border-left:1px solid #e8e8f2}
.katex, [data-testid="stVegaLiteChart"], [data-testid="stSlider"] {direction:ltr}
h1,h2,h3 {letter-spacing:0!important}
.hero {background:linear-gradient(125deg,#171930,#35305b);color:#fff;padding:36px;border-radius:22px;margin-bottom:24px}
.hero h2 {color:#d7fb91}.hero p {color:#d7d8e8}
</style>""")

@st.cache_data
def load_course():
    return json.loads((ROOT / "course.json").read_text(encoding="utf-8-sig"))

course = load_course()
ss = st.session_state
for key, value in {"done": [], "notes": {}, "answers": {}, "wrong": [], "known": [], "card": 0, "flip": False, "focus_end": None}.items():
    ss.setdefault(key, value)

def title(text):
    return re.sub(r"^[^\w\u0600-\u06ff]+", "", text).strip()

def clean(text):
    return bleach.clean(text, tags={"p","div","span","strong","b","em","i","code","pre","ul","ol","li","table","thead","tbody","tr","th","td","h1","h2","h3","h4","br","hr","sup","sub","blockquote"}, attributes={}, strip=True)

def home():
    st.html('<div class="hero"><small>ميزان / مساحة للفهم والتجربة</small><h2>الفكرة تصبح أوضح حين تراها تعمل.</h2><p>هندسة التحكم بالعربية · اقرأ الفكرة، اختبر النموذج، ثم ثبّت معرفتك.</p></div>')
    cols = st.columns(3)
    cols[0].metric("دروس مكتملة", f"{len(ss.done)} / 9")
    cols[1].metric("أسئلة أتقنتها", f"{sum(ss.answers.values())} / 5")
    cols[2].metric("بطاقات تذكّرتها", f"{len(ss.known)} / 12")
    st.subheader("مسارك، خطوة بخطوة")
    for name, nums in [("01 · البداية وفكرة التحكم", [1,2]), ("02 · لغة النمذجة الرياضية", [3,4,5]), ("03 · من P إلى PID", [6,7]), ("04 · من النموذج إلى التطبيق", [8,9])]:
        with st.container(border=True):
            st.markdown(f"### {name}")
            for l in course["lessons"]:
                if l["number"] in nums:
                    st.markdown(f"{'✓' if l['number'] in ss.done else '○'} **{title(l['title'])}**")
    st.info("الملاحظات والتقدم محفوظان في الجلسة الحالية فقط. نزّل نسخة من دفتر الملاحظات قبل إغلاقها؛ لا توجد مزامنة سحابية.")
    st.link_button("الكتاب والمختبرات السابقة ↗", "https://mizan-control-ar.nuttycream6.chatgpt.site/book.html")

def lessons():
    st.title("مكتبتك في هندسة التحكم")
    query = st.text_input("ابحث في عنوان الدرس")
    items = [l for l in course["lessons"] if query in l["title"]]
    if not items:
        st.info("لا توجد نتائج مطابقة.")
        return
    num = st.selectbox("اختر الدرس", [l["number"] for l in items], format_func=lambda n: title(next(l["title"] for l in items if l["number"] == n)))
    lesson = next(l for l in items if l["number"] == num)
    with st.container(border=True):
        for block in lesson["blocks"]:
            text = block["text"]
            if text == "---":
                st.divider()
            elif block["kind"] == "latex":
                st.latex(text)
            elif "الرسم التوضيحي" in text and text.startswith("#"):
                st.markdown(text)
                st.caption("استكشف النموذج في المختبر الحراري أو راجع مخططات الكتاب التفاعلي.")
            elif "أسئلة قصيرة" in text and text.startswith("#"):
                st.markdown(text)
                st.caption("افتح صفحة «اختبر فهمك» من القائمة للتدريب مع تفسير الإجابات.")
            elif re.search(r"<(div|table|p|span|ul|h[1-4])\b", text, re.I):
                st.html(clean(text))
            else:
                st.markdown(text)
    if st.button("أكملت الدرس ✓", type="primary", disabled=num in ss.done):
        ss.done = sorted(set(ss.done + [num]))
        st.rerun()
    key = f"lesson-{num}"
    def save_note():
        ss.notes[key] = ss[f"note-{num}"]
    st.text_area("اكتب ما فهمته من هذا الدرس", value=ss.notes.get(key, ""), key=f"note-{num}", on_change=save_note, height=150)

@st.cache_data(max_entries=48)
def simulate(mode, target, kp, ki, kd, a, b, antiwindup):
    dt, temp, integ, deriv, previous = .05, 20., 0., 0., 20.
    out = []
    for i in range(4801):
        error = target-temp
        deriv += dt/(.25+dt)*((temp-previous)/dt-deriv)
        candidate = integ+error*dt
        raw = kp*error+(ki*candidate if mode != "P" else 0)-(kd*deriv if mode == "PID" else 0)
        u = min(8., max(0., raw))
        if not antiwindup or raw == u or (raw > 8 and error < 0) or (raw < 0 and error > 0):
            integ = candidate
        raw = kp*error+(ki*integ if mode != "P" else 0)-(kd*deriv if mode == "PID" else 0)
        u = min(8., max(0., raw))
        if i % 4 == 0:
            out.append({"t (s)": i*dt, "T (°C)": temp, "الهدف (°C)": target, "u": u})
        previous = temp
        temp = 20+(temp-20)*math.exp(-b*dt)+a*u/b*(1-math.exp(-b*dt))
    return pd.DataFrame(out)

def lab():
    st.title("المختبر الحراري · P / PI / PID")
    st.caption("غيّر معاملًا واحدًا وراقب أثره على الاستجابة. كل منحنى يحسب النموذج نفسه.")
    with st.container(border=True):
        mode = st.segmented_control("نوع المتحكّم", ["P","PI","PID"], default="P", required=True)
        cols = st.columns(3)
        target = cols[0].slider("الهدف T_set (°C)", 30., 100., 60., 1.)
        kp = cols[1].slider("Kp", .1, 3., 1., .1)
        ki = cols[2].slider("Ki (s⁻¹)", 0., .2, .03, .005, disabled=mode=="P")
        cols = st.columns(3)
        kd = cols[0].slider("Kd (s)", 0., 2., .3, .1, disabled=mode!="PID")
        a = cols[1].slider("فعالية التسخين a", .2, 1.6, .8, .1)
        b = cols[2].slider("معامل الفقد b (s⁻¹)", .01, .1, .04, .005)
        aw = st.toggle("منع تراكم التكامل عند التشبّع", value=True)
    data = simulate(mode, target, kp, ki, kd, a, b, aw)
    at = st.slider("استكشف الزمن t (s)", 0., 240., 20., .2)
    row = data.iloc[min(len(data)-1, round(at/.2))]
    cols = st.columns(3)
    cols[0].metric("درجة الحرارة", f"{row['T (°C)']:.1f} °C")
    cols[1].metric("الخطأ الحالي", f"{target-row['T (°C)']:.1f} °C")
    cols[2].metric("خرج المتحكّم", f"{row['u']:.2f} / 8")
    st.line_chart(data.set_index("t (s)")[["T (°C)","الهدف (°C)"]], color=["#087e83","#bd622b"], x_label="t (s)", y_label="°C")
    compare = st.toggle("قارن P وPI وPID على المنحنى نفسه")
    if compare:
        frame = pd.DataFrame({m: simulate(m,target,kp,ki,kd,a,b,aw)["T (°C)"].to_numpy() for m in ["P","PI","PID"]}, index=data["t (s)"])
        st.line_chart(frame, color=["#bd622b","#087e83","#6552e8"], x_label="t (s)", y_label="°C")
    st.download_button("تنزيل بيانات التجربة CSV", data.to_csv(index=False).encode("utf-8-sig"), "mizan-thermal.csv", "text/csv")
    with st.expander("النموذج والافتراضات"):
        st.latex(r"\frac{dT}{dt}=a u-b(T-20),\quad 0\leq u\leq8,\quad T(0)=20")
        st.markdown("حساب كل 0.05 ثانية بحل أسي للنبات مع دخل ثابت خلال العينة. المشتقة على القياس ومرشحها 0.25 ثانية. لا ضوضاء ولا تأخير ولا تبريد نشط. القيم في نموذج تعليمي وليست إعدادات جهاز حقيقي.")
        st.image(str(ROOT/"thermal-rig.svg"), caption="تصوّر تعليمي للحجرة الحرارية · Anatomy · MIT")

def quiz():
    st.title("اختبر فهمك")
    retry = st.toggle("أسئلة دفتر الأخطاء فقط")
    for i, q in enumerate(course["questions"]):
        if retry and i not in ss.wrong:
            continue
        with st.container(border=True):
            st.markdown(f"### {q['q']}")
            with st.form(f"q-{i}"):
                pick = st.radio("اختر إجابة", q["options"], index=None, key=f"pick-{i}")
                submit = st.form_submit_button("تحقّق من الإجابة")
            if submit:
                if pick is None:
                    st.warning("اختر إجابة أولًا.")
                else:
                    right = pick == q["options"][q["correct"]]
                    ss.answers[i] = right
                    if right:
                        ss.wrong = [x for x in ss.wrong if x != i]
                    elif i not in ss.wrong:
                        ss.wrong.append(i)
            if i in ss.answers:
                (st.success if ss.answers[i] else st.error)("إجابة صحيحة." if ss.answers[i] else "راجع الفكرة ثم حاول من جديد.")
                st.info(q["explanation"])
    if retry and not ss.wrong:
        st.success("لا توجد أسئلة تحتاج إعادة حاليًا.")

TERMS = [("المنظومة","System","علاقة بين دخل وخرج وحالة داخلية."),("القيمة المطلوبة","Sollwert","القيمة التي نريد أن يصل إليها الخرج."),("القيمة الفعلية","Istwert","القيمة التي يقيسها الحساس."),("المتحكّم","Regler","يحسب فعل التحكم انطلاقًا من الخطأ."),("منظومة التحكم","Regelstrecke","العملية التي نريد التحكم فيها."),("التغذية الراجعة","Rückkopplung","إعادة القياس لمقارنته بالمرجع."),("الخطأ","Regelabweichung","e(t) = r(t) − y(t)"),("الاضطراب","Störgröße","تأثير خارجي يغيّر سلوك النظام."),("دالة الانتقال","Übertragungsfunktion","نسبة تحويل الخرج إلى تحويل الدخل عند حالة ابتدائية صفرية."),("الاستقرار","Stabilität","للنظام LTI المستمر التقاربي: الأقطاب في النصف الأيسر المفتوح."),("الثابت الزمني","Zeitkonstante","لنظام PT1: يصل الخرج إلى نحو 63.2% من التغير النهائي عند t=τ."),("التجاوز","Überschwingen","ارتفاع الاستجابة فوق القيمة النهائية.")]

def cards():
    st.title("بطاقات عربية · ألمانية")
    i = ss.card % len(TERMS)
    ar, de, meaning = TERMS[i]
    st.caption(f"البطاقة {i+1} / {len(TERMS)}")
    with st.container(border=True):
        st.header(ar)
        if ss.flip:
            st.subheader(de)
            st.write(meaning)
        if st.button("اكشف المعنى"):
            ss.flip = True
            st.rerun()
    with st.container(horizontal=True):
        if st.button("تذكّرتها ✓", disabled=not ss.flip):
            ss.known = sorted(set(ss.known + [i]))
            ss.card += 1
            ss.flip = False
            st.rerun()
        if st.button("التالي ←"):
            ss.card += 1
            ss.flip = False
            st.rerun()

def notes():
    st.title("دفتر ملاحظاتك")
    st.caption("ملاحظات الجلسة الحالية. نزّل نسخة لحفظها بعد إغلاق المتصفح.")
    def save():
        ss.notes["general"] = ss.general_note
    st.text_area("ملاحظات عامة", value=ss.notes.get("general", ""), key="general_note", on_change=save, height=220)
    for key, text in ss.notes.items():
        if key != "general" and text:
            with st.expander(f"الدرس {key.split('-')[-1]}"):
                st.write(text)
    st.download_button("تنزيل دفتر الملاحظات", json.dumps(ss.notes, ensure_ascii=False, indent=2), "mizan-notes.json", "application/json")

def focus():
    st.title("وقت لفكرة واحدة")
    mins = st.selectbox("مدة التركيز بالدقائق", [5,15,25], index=2)
    with st.container(horizontal=True):
        if st.button("ابدأ الجلسة", type="primary"):
            ss.focus_end = time.time()+mins*60
        if st.button("إعادة الضبط"):
            ss.focus_end = None
    @st.fragment(run_every=1)
    def clock():
        left = max(0, math.ceil(ss.focus_end-time.time())) if ss.focus_end else mins*60
        st.metric("الوقت المتبقي", f"{left//60:02}:{left%60:02}")
        if ss.focus_end and left == 0:
            st.success("انتهت الجلسة. خذ استراحة قصيرة.")
    clock()

pg = st.navigation({"مساحة التعلّم": [st.Page(home,title="لوحة التعلّم",icon=":material/home:",default=True), st.Page(lessons,title="مكتبتي ودروسي",icon=":material/menu_book:"),st.Page(cards,title="بطاقات المراجعة",icon=":material/style:"),st.Page(quiz,title="اختبر فهمك",icon=":material/quiz:"),st.Page(notes,title="ملاحظاتي",icon=":material/edit_note:"),st.Page(focus,title="جلسة تركيز",icon=":material/timer:")],"من النظرية إلى الواقع":[st.Page(lab,title="مختبر P · PI · PID",icon=":material/science:")]})
pg.run()
st.divider()
st.caption("ميزان · محتوى من control_arabic.zip المرفق · تطوير مستقل. Studyflix مرجع لتنظيم الموضوعات فقط؛ لم تُنسخ الفيديوهات أو الصور.")
