"""Mizan: native Arabic Streamlit learning environment. No uploaded code executed."""
from pathlib import Path
import json
import math
import re
import time
import base64
from html import escape

import bleach
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="ميزان | هندسة التحكم", page_icon="⚙️", layout="wide", initial_sidebar_state="auto")
st.html("""<style>
[data-testid="stMain"], [data-testid="stSidebar"] {direction:rtl;text-align:right}
[data-testid="stMarkdownContainer"] {text-align:right}
[data-testid="stMetric"] {background:#fff;border:1px solid #e8e8f2;border-radius:16px;padding:18px}
[data-testid="stMetricValue"] {direction:ltr;unicode-bidi:isolate;text-align:right}
[data-testid="stAppViewContainer"] {direction:rtl}
[data-testid="stMainBlockContainer"] {max-width:1500px;padding-top:2rem}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {color:#eeeefe}
[data-testid="stSidebarNavLink"] {border-radius:10px;padding:8px 12px}
[data-testid="stSidebarNavLink"][aria-current="page"] {background:#6552e8}
[data-testid="stVerticalBlockBorderWrapper"] {background:#fff;border-radius:18px}
[data-testid="stSidebar"] {border-left:1px solid #e8e8f2}
.katex, [data-testid="stVegaLiteChart"], [data-testid="stSlider"] {direction:ltr}
h1,h2,h3 {letter-spacing:0!important}
.hero {background:linear-gradient(125deg,#171930,#302b53);color:#fff;padding:32px;border-radius:22px;display:grid;grid-template-columns:1.1fr 1fr;align-items:center;overflow:hidden;gap:12px}
.hero h2 {color:white;font-size:clamp(26px,3vw,43px);line-height:1.6;margin:16px 0}.hero h2 em {color:#d7fb91;font-style:normal}.hero p {color:#c9cade;font-size:14px;line-height:1.9}.hero img {width:100%;max-height:340px;object-fit:contain}
.topline {display:flex;justify-content:space-between;align-items:center;margin-bottom:25px;gap:16px}.topline h1{font-size:27px;margin:8px 0}.eyebrow{color:#74758a;font-size:12px}.xp{background:white;border-radius:30px;padding:10px 20px;font-size:12px;color:#6552e8}
.brand{display:flex;gap:12px;align-items:center;margin:5px 0 28px}.brand b{font-size:30px;color:white}.brand small{display:block;font-size:11px;color:#adafc8}.brand-mark{background:#d7fb91;color:#173a30;padding:4px 13px;border-radius:16px 16px 16px 4px;font-size:30px;font-weight:bold}
.step-row{display:flex;align-items:center;gap:16px;padding:16px 0;border-bottom:1px solid #eeedf6}.step-num{background:#eeebfc;color:#6552e8;border-radius:12px;padding:10px;font-weight:bold}.step-row h3{font-size:17px;margin:0}.step-row p{font-size:12px;color:#74758a;margin:5px 0}
/* Anatomy plate (MIT) around the live rig */
.iso-figure{margin:0}.iso-plate{position:relative;padding:46px 18px;border-radius:16px;box-shadow:0 0 0 1px #e1e0ec;background:#fbfbfa}
.iso-plate img{display:block;width:100%;height:auto}
.iso-plate-corners{position:absolute;inset:16px 18px;pointer-events:none;direction:ltr}
.iso-plate-corner{position:absolute;color:#8c8c90;font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:10.5px;line-height:1;letter-spacing:.04em;white-space:nowrap}
.iso-plate-corner[data-corner="fig"]{top:0;left:0;color:#57575a}.iso-plate-corner[data-corner="title"]{top:0;right:0;text-transform:uppercase;letter-spacing:.1em}
.iso-plate-corner[data-corner="hint"]{bottom:0;left:0;text-transform:uppercase;letter-spacing:.1em}.iso-plate-corner[data-corner="readout"]{right:0;bottom:0;color:#57575a;font-variant-numeric:tabular-nums}
.iso-legend{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:10px;color:#74758a;font-size:13px;line-height:1.55}
.iso-key{display:inline-flex;align-items:center;gap:7px}.iso-chip{width:16px;height:3px;border-radius:2px;flex:none}
.hero .rig{width:100%;max-height:340px;object-fit:contain}
.tool-icon{color:#087e83;background:#e6f5f2;font-size:28px;padding:7px 15px;border-radius:14px;display:inline-block}.session-note{font-size:11px;color:#9295b5;margin-top:25px}
@media(max-width:700px){.hero{grid-template-columns:1fr;padding:25px}.hero .rig{max-height:220px}.topline h1{font-size:21px}[data-testid="stMainBlockContainer"]{padding:1rem}.xp{white-space:nowrap}.hero p{font-size:13px}}
</style>""")

@st.cache_data
def load_course():
    return json.loads((ROOT / "course.json").read_text(encoding="utf-8-sig"))

course = load_course()

@st.cache_data
def rig_source():
    return (ROOT / "thermal-rig.svg").read_text(encoding="utf-8")

def heat_color(x):
    """Neutral grey -> amber -> red, x in [0, 1]."""
    stops = [(0., (138, 138, 143)), (.5, (245, 165, 36)), (1., (229, 72, 77))]
    x = min(1., max(0., x))
    for (x0, c0), (x1, c1) in zip(stops, stops[1:]):
        if x <= x1:
            f = (x-x0)/(x1-x0)
            return "#%02x%02x%02x" % tuple(round(a+(b-a)*f) for a, b in zip(c0, c1))

def mix(color, base, f):
    c = [int(color[i:i+2], 16) for i in (1, 3, 5)]
    b = [int(base[i:i+2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x+(y-x)*f) for x, y in zip(c, b))

def rig_svg(level, power, label):
    """Drive the Anatomy rig: level (0..1) fills the display bar, power (0..1)
    lights the eight LEDs and makes the heater elements glow."""
    svg = rig_source()
    heat = heat_color(power)
    svg = svg.replace("--anatomy-lit:#2f9e98;--anatomy-lit-top:#bfe9e4;--anatomy-lit-shade:#75b9b3",
                      f"--anatomy-lit:{heat};--anatomy-lit-top:{mix(heat,'#ffffff',.55)};--anatomy-lit-shade:{mix(heat,'#ffffff',.2)};--rig-heat:{heat}", 1)
    h = 18*min(1., max(0., level))
    svg = svg.replace('d="M372.64 279.57L379.10 283.15L379.10 283.15L372.64 279.57Z" fill="var(--anatomy-lit)"',
                      f'd="M372.64 279.57L379.10 283.15L379.10 {283.15-h:.2f}L372.64 {279.57-h:.2f}Z" fill="{heat_color(level)}"', 1)
    lit = round(8*min(1., max(0., power)))
    for n in range(8):
        if n < lit:
            svg = re.sub(rf'(data-led="{n}"[^>]*?)opacity="\.16"', r'\1opacity="1"', svg, count=1)
    svg = svg.replace('aria-label="', f'aria-label="{escape(label)} · ', 1)
    svg = svg.replace('viewBox="0 0 720 440"', 'viewBox="105 25 510 375"', 1)  # crop to the drawing
    data = base64.b64encode(svg.encode("utf-8")).decode()
    return f'<img class="rig" src="data:image/svg+xml;base64,{data}" alt="{escape(label)}" />', heat

ss = st.session_state
for key, value in {"done": [], "notes": {}, "answers": {}, "wrong": [], "known": [], "card": 0, "flip": False, "focus_end": None}.items():
    ss.setdefault(key, value)

def title(text):
    return re.sub(r"^[^\w\u0600-\u06ff]+", "", text).strip()

def clean(text):
    return bleach.clean(text, tags={"p","div","span","strong","b","em","i","code","pre","ul","ol","li","table","thead","tbody","tr","th","td","h1","h2","h3","h4","br","hr","sup","sub","blockquote"}, attributes={}, strip=True)

def home():
    xp = 20*len(ss.done)+10*sum(ss.answers.values())+5*len(ss.known)
    st.html(f'<div class="topline"><div><small class="eyebrow">مسارك في هندسة التحكم</small><h1>مرحبًا بك في مساحة التعلّم.</h1></div><span class="xp">مستكشف · <bdi>{xp} XP</bdi></span></div>')
    progress = len(ss.done)/9
    rig, _ = rig_svg(progress, progress, f"حجرة تسخين ووحدة تحكم · أنهيت {len(ss.done)} من 9 دروس")
    st.html(f'<section class="hero"><div><small>تعلّم بفهم، لا بالحفظ وحده</small><h2>الفكرة تصبح أوضح<br>حين <em>تراها تعمل.</em></h2><p>دروس عربية، مختبرات تفاعلية، ومراجعة لتنظيم معرفتك. كل خطوة تربط المعادلة بعالم حقيقي.</p></div>{rig}</section>')
    with st.container(horizontal=True):
        if st.button("واصل رحلتك ←",type="primary"):
            st.switch_page(PAGES["lessons"])
        if st.button("افتح المختبر الحراري",icon=":material/science:"):
            st.switch_page(PAGES["lab"])
    cols = st.columns(4)
    cols[0].metric("دروس أنهيتها", f"{len(ss.done)} / 9")
    cols[1].metric("بطاقات للمراجعة", len(TERMS)-len(ss.known))
    cols[2].metric("أسئلة أتقنتها", f"{sum(ss.answers.values())} / 5")
    cols[3].metric("نقاط معرفة مكتسبة", xp)
    path, today = st.columns([1.3,1],gap="large")
    with path:
        st.subheader("مسارك، خطوة بخطوة")
        with st.container(border=True):
            for i,(name,nums) in enumerate([("البداية وفكرة التحكم",[1,2]),("لغة النمذجة الرياضية",[3,4,5]),("من P إلى PID",[6,7]),("من النموذج إلى التطبيق",[8,9])],1):
                count = sum(n in ss.done for n in nums)
                st.html(f'<div class="step-row"><span class="step-num">0{i}</span><div><h3>{name}</h3><p>{len(nums)} دروس · أنهيت {count}</p></div></div>')
                if st.button("استكشف ←",key=f"path-{i}"):
                    ss["lesson-choice"] = nums[0]
                    st.switch_page(PAGES["lessons"])
    with today:
        st.subheader("مساحة اليوم")
        with st.container(border=True):
            st.caption("ابدأ بخطوة واحدة")
            next_lesson = next((l for l in course["lessons"] if l["number"] not in ss.done),course["lessons"][0])
            st.markdown(f"### {title(next_lesson['title'])}")
            st.progress(len(ss.done)/9)
            st.caption("اقرأ المفهوم، ثم جرّبه في المختبر.")
            if st.button("ابدأ الدرس",width="stretch"):
                ss["lesson-choice"] = next_lesson["number"]
                st.switch_page(PAGES["lessons"])
            if st.button("مراجعة قصيرة · بطاقات المصطلحات",width="stretch"):
                st.switch_page(PAGES["cards"])
            if st.button("وقت بلا مشتتات · جلسة تركيز",width="stretch"):
                st.switch_page(PAGES["focus"])
        st.caption("مساحة شخصية: التقدم والملاحظات للجلسة الحالية. نزّل ملاحظاتك قبل إغلاقها.")
    st.subheader("مساحات للتجربة")
    for col,icon,heading,desc,dest in zip(st.columns(3),["♨","∿","▤"],["مختبر حراري حيّ","P أم PI أم PID؟","اختبر فهمك"],["درجة حرارة، حساس، وقدرة تسخين.","قارن الاستجابة والخطأ على منحنى واحد.","تفسير لكل إجابة ودفتر لإعادة الأخطاء."],[lab,lab,quiz]):
        with col,st.container(border=True):
            st.html(f'<span class="tool-icon">{icon}</span>')
            st.markdown(f"### {heading}")
            st.caption(desc)
            if st.button("افتح ←",key=f"tool-{icon}"):
                st.switch_page(PAGES[dest.__name__])
    st.link_button("الكتاب المرجعي والمختبرات السابقة ↗", "https://mizan-control-ar.nuttycream6.chatgpt.site/book.html")

def lessons():
    st.title("مكتبتك في هندسة التحكم")
    query = st.text_input("ابحث في عنوان الدرس")
    items = [l for l in course["lessons"] if query in l["title"]]
    if not items:
        st.info("لا توجد نتائج مطابقة.")
        return
    numbers = [l["number"] for l in items]
    if ss.get("lesson-choice") not in numbers:
        ss["lesson-choice"] = numbers[0]
    num = st.selectbox("اختر الدرس", numbers, key="lesson-choice", persist_state="session", format_func=lambda n: title(next(l["title"] for l in items if l["number"] == n)))
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

def step_metrics(data, target):
    temp = data["T (°C)"].to_numpy()
    time_s = data["t (s)"].to_numpy()
    step = max(target-20, 1e-9)
    outside = abs(temp-target) > .02*step
    settling = None
    if not outside[-1]:
        last = outside.nonzero()[0]
        settling = float(time_s[last[-1]+1]) if len(last) else 0.
    return {"overshoot": max(0., (temp.max()-target)/step*100), "settling": settling, "final_error": float(target-temp[-1])}

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
    figure, readings = st.columns([1.35, 1], gap="large")
    with figure:
        level = (row["T (°C)"]-20)/80
        svg, heat = rig_svg(level, row["u"]/8, f"T = {row['T (°C)']:.1f} °C, u = {row['u']:.2f}")
        st.html(f'''<figure class="iso-figure"><div class="iso-plate">
<div class="iso-plate-corners"><span class="iso-plate-corner" data-corner="fig">FIG. 01 · {mode}</span><span class="iso-plate-corner" data-corner="title">thermal rig</span>
<span class="iso-plate-corner" data-corner="hint">t = {at:.1f} s</span><span class="iso-plate-corner" data-corner="readout">T {row['T (°C)']:.1f} °C · u {row['u']:.2f}/8</span></div>{svg}</div>
<figcaption class="iso-legend"><span class="iso-key"><span class="iso-chip" style="background:{heat}"></span>توهج السخان ومؤشرات LED = خرج المتحكّم u</span>
<span class="iso-key"><span class="iso-chip" style="background:{heat_color(level)}"></span>العمود في الشاشة = درجة الحرارة (20–100 °C)</span></figcaption></figure>''')
    with readings:
        st.metric("درجة الحرارة", f"{row['T (°C)']:.1f} °C")
        st.metric("الخطأ الحالي", f"{target-row['T (°C)']:.1f} °C")
        st.metric("خرج المتحكّم", f"{row['u']:.2f} / 8")
    perf = step_metrics(data, target)
    cols = st.columns(3)
    cols[0].metric("التجاوز الأقصى", f"{perf['overshoot']:.1f} %", help="أعلى قيمة فوق الهدف كنسبة من قفزة المرجع (الهدف − 20 °C).")
    cols[1].metric("زمن الاستقرار ±2 %", "لم يستقر" if perf["settling"] is None else f"{perf['settling']:.1f} s", help="أول زمن تبقى بعده درجة الحرارة داخل نطاق ±2 % من قفزة المرجع حول الهدف.")
    cols[2].metric("الخطأ عند t = 240 s", f"{perf['final_error']:.2f} °C", help="بدون تكامل (P) يبقى خطأ دائم؛ PI وPID يزيلانه.")
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

TERMS = json.loads((ROOT / "terms.json").read_text(encoding="utf-8"))

def cards():
    st.title("بطاقات عربية · ألمانية")
    i = ss.card % len(TERMS)
    ar, de, meaning = TERMS[i]
    st.caption(f"البطاقة {i+1} / {len(TERMS)} · تذكّرت {len(ss.known)}")
    st.progress(len(ss.known)/len(TERMS))
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

PAGES = {
    "home": st.Page(home, title="لوحة التعلّم", icon=":material/home:", default=True, url_path=""),
    "lessons": st.Page(lessons, title="مكتبتي ودروسي", icon=":material/menu_book:"),
    "cards": st.Page(cards, title="بطاقات المراجعة", icon=":material/style:"),
    "quiz": st.Page(quiz, title="اختبر فهمك", icon=":material/quiz:"),
    "notes": st.Page(notes, title="ملاحظاتي", icon=":material/edit_note:"),
    "focus": st.Page(focus, title="جلسة تركيز", icon=":material/timer:"),
    "lab": st.Page(lab, title="مختبر P · PI · PID", icon=":material/science:")
}
pg = st.navigation({"مساحة التعلّم": [PAGES[n] for n in ["home","lessons","cards","quiz","notes","focus"]], "من النظرية إلى الواقع": [PAGES["lab"]]})
with st.sidebar:
    st.html('<div class="brand"><span class="brand-mark">م</span><div><b>ميزان</b><small>مساحة للفهم والتجربة</small></div></div>')
    if st.button("العودة إلى الصفحة الرئيسية", icon=":material/home:", width="stretch"):
        st.switch_page(PAGES["home"])

pg.run()
if ss.get("_rendered_page") != pg.url_path:
    # Streamlit/Cloud can restore the previous scroll offset on root navigation.
    # Reset only when entering a page, never while adjusting a lab control.
    st.html('''<script>
    const resetView = () => {
        const main = document.querySelector('[data-testid="stMain"]');
        if (main) main.scrollTo({top:0,left:0,behavior:'instant'});
        window.scrollTo({top:0,left:0,behavior:'instant'});
    };
    requestAnimationFrame(() => requestAnimationFrame(resetView));
    setTimeout(resetView, 200);
    </script>''', unsafe_allow_javascript=True)
    ss["_rendered_page"] = pg.url_path
st.divider()
st.caption("ميزان · محتوى من control_arabic.zip المرفق · تطوير مستقل. Studyflix مرجع لتنظيم الموضوعات فقط؛ لم تُنسخ الفيديوهات أو الصور.")
