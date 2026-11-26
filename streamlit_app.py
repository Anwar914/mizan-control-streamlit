"""Mizan: native Arabic Streamlit learning environment. No uploaded code executed."""
from pathlib import Path
import json
import math
import re
import textwrap
import time
import base64
from html import escape

import bleach
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="ميزان | هندسة التحكم", page_icon="⚙️", layout="wide", initial_sidebar_state="auto")
st.html("""<style>
:root{--paper:#f3f5f4;--panel:#ffffff;--ink:#13262d;--muted:#5b6b70;--grid:#d9e1df;--measure:#0c7c84;--heat:#d4521c;
--display:"Reem Kufi",var(--body);--body:"Noto Naskh Arabic","Noto Sans Arabic",serif}
[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stSidebar"]{direction:rtl;text-align:right}
[data-testid="stMarkdownContainer"]{text-align:right}
[data-testid="stMainBlockContainer"]{max-width:1240px;padding-top:2.25rem}
h1,h2,h3,h4{font-family:var(--display)!important;letter-spacing:0!important;font-weight:600!important}
[data-testid="stMetric"]{border-top:2px solid var(--ink);padding:10px 0 0}
[data-testid="stMetricValue"]{direction:ltr;unicode-bidi:isolate;text-align:right;font-variant-numeric:tabular-nums}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--panel);border-radius:8px}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{color:#e9efee}
[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarContent"]{visibility:hidden}
[data-testid="stSidebarNavLink"]{border-radius:6px;padding:8px 12px;border-right:3px solid transparent}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:#ffffff14;border-right-color:#7fd1d6}
:focus-visible{outline:2px solid var(--measure)!important;outline-offset:2px}
.katex,[data-testid="stVegaLiteChart"],[data-testid="stSlider"]{direction:ltr}
.st-key-reading [data-testid="stMarkdownContainer"],.st-key-reading [data-testid="stHtml"]{max-width:70ch;line-height:2}
/* dashboard */
.greet{display:flex;justify-content:space-between;align-items:baseline;gap:16px;margin-bottom:8px}
.greet p{margin:0;color:var(--muted);font-size:15px}.points{color:var(--ink);font-size:14px;white-space:nowrap}.points bdi{font-variant-numeric:tabular-nums;font-weight:600}
.hero{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.15fr);gap:40px;align-items:center;padding:28px 0 8px}
.hero h1{font-family:var(--display);font-size:clamp(36px,4.6vw,64px);line-height:1.35;margin:0 0 18px;color:var(--ink)}
.hero p{font-size:17px;line-height:2;color:var(--muted);max-width:46ch;margin:0}
.curve{position:relative}.curve img{display:block;width:100%;height:auto}
.curve .lbl{position:absolute;font-size:13px;color:var(--muted);white-space:nowrap}
.curve .goal{top:calc(19.3% - 30px);right:0}.curve .you{color:var(--measure);font-weight:600}
.readouts{display:grid;grid-template-columns:repeat(var(--n,4),minmax(0,1fr));gap:24px;margin:8px 0 4px}
.readout{border-top:2px solid var(--role,var(--ink));padding-top:10px}
.readout span{display:block;color:var(--muted);font-size:14px}
.readout b{display:block;font-family:var(--body);font-size:30px;font-weight:600;color:var(--ink);direction:ltr;unicode-bidi:isolate;text-align:right;font-variant-numeric:tabular-nums;line-height:1.5}
.readout small{display:block;color:var(--muted);font-size:12.5px;line-height:1.7}
.stage{display:grid;grid-template-columns:40px 1fr;gap:14px;align-items:start;padding-top:6px}
.stage i{font-style:normal;width:34px;height:34px;border-radius:50%;display:grid;place-items:center;border:2px solid var(--ink);font-family:var(--display);font-size:17px;color:var(--ink);background:var(--paper)}
.stage[data-done] i{background:var(--measure);border-color:var(--measure);color:#fff}
.stage h3{font-size:19px;margin:0}.stage p{margin:2px 0 0;color:var(--muted);font-size:14px}
.brand{display:flex;gap:12px;align-items:center;margin:4px 0 26px}.brand b{font-family:var(--display);font-size:30px;color:#fff;font-weight:600}
.brand small{display:block;font-size:12px;color:#a9bbbd}.brand-mark{background:var(--paper);color:var(--ink);width:44px;height:44px;border-radius:8px;display:grid;place-items:center;font-family:var(--body);font-weight:600;font-size:30px;line-height:1;padding-bottom:4px}
/* Anatomy plate (MIT) around the live rig */
.iso-figure{margin:0}.iso-plate{position:relative;padding:40px 18px 34px;border-radius:8px;box-shadow:0 0 0 1px var(--grid);background:#fbfbfa}
.iso-plate img{display:block;width:100%;height:auto}
.iso-plate figcaption,.iso-plate .t{position:absolute;top:14px;right:18px;font-size:14px;color:var(--ink)}.iso-plate .t{right:auto;left:18px;color:var(--muted);direction:ltr;font-variant-numeric:tabular-nums}
.iso-legend{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:10px;color:var(--muted);font-size:13.5px;line-height:1.6}
.iso-key{display:inline-flex;align-items:center;gap:7px}.iso-chip{width:16px;height:3px;border-radius:2px;flex:none}
@media(max-width:760px){.hero{grid-template-columns:1fr;gap:18px;padding-top:8px}.readouts{grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.readout b{font-size:24px}
[data-testid="stMainBlockContainer"]{padding:1rem 16px}.greet{flex-direction:column;gap:2px}}
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
    svg = svg.replace('aria-label="', f'aria-label="{escape(label)}، ', 1)
    svg = svg.replace('viewBox="0 0 720 440"', 'viewBox="105 25 510 375"', 1)  # crop to the drawing
    data = base64.b64encode(svg.encode("utf-8")).decode()
    return f'<img class="rig" src="data:image/svg+xml;base64,{data}" alt="{escape(label)}" />', heat

ss = st.session_state
for key, value in {"done": [], "notes": {}, "answers": {}, "wrong": [], "known": [], "card": 0, "flip": False, "focus_end": None}.items():
    ss.setdefault(key, value)

def unindent(text):
    """Source blocks often start flush and continue indented; Markdown would turn the rest into code."""
    first, _, rest = text.strip("\n").partition("\n")
    return (first.strip()+"\n"+textwrap.dedent(rest)).strip()

def title(text):
    return re.sub(r"^[^\w\u0600-\u06ff]+", "", text).strip()

def clean(text):
    return bleach.clean(text, tags={"p","div","span","strong","b","em","i","code","pre","ul","ol","li","table","thead","tbody","tr","th","td","h1","h2","h3","h4","br","hr","sup","sub","blockquote"}, attributes={}, strip=True)

def step_curve(progress):
    """Hero figure: an underdamped step response; the marker sits where the learner is."""
    w, h, x0, x1, y0, ys = 600, 300, 20, 580, 268, 58
    def y(t):
        z, wn = .6, 1.
        wd = wn*math.sqrt(1-z*z)
        r = 1-math.exp(-z*wn*t)*(math.cos(wd*t)+z/math.sqrt(1-z*z)*math.sin(wd*t))
        return y0-(y0-ys)*r
    pts = [(x0+(x1-x0)*k/240, y(12*k/240)) for k in range(241)]
    d = "M"+" L".join(f"{a:.1f} {b:.1f}" for a, b in pts)
    mx, my = pts[round(240*min(1., max(0., progress)))]
    grid = "".join(f'<path d="M{x} 20V284" />' for x in range(20, 600, 40))+"".join(f'<path d="M20 {yy}H580" />' for yy in range(28, 290, 40))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><style>
.g path{{stroke:#d9e1df;stroke-width:1}}.c{{fill:none;stroke:#0c7c84;stroke-width:3;stroke-linecap:round;stroke-dasharray:1;stroke-dashoffset:1;animation:d 1.8s cubic-bezier(.3,.7,.2,1) .2s forwards}}
.m{{opacity:0;animation:f .4s ease-out 1.9s forwards}}@keyframes d{{to{{stroke-dashoffset:0}}}}@keyframes f{{to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{.c{{animation:none;stroke-dashoffset:0}}.m{{animation:none;opacity:1}}}}</style>
<g class="g">{grid}</g><path d="M20 {ys}H580" stroke="#13262d" stroke-width="1.5" stroke-dasharray="6 6"/>
<path d="M20 284H580" stroke="#13262d" stroke-width="1.5"/><path class="c" pathLength="1" d="{d}"/>
<g class="m"><path d="M{mx:.1f} {my:.1f}V284" stroke="#0c7c84" stroke-dasharray="2 4"/><circle cx="{mx:.1f}" cy="{my:.1f}" r="8" fill="#f3f5f4" stroke="#0c7c84" stroke-width="3"/></g></svg>'''
    return "data:image/svg+xml;base64,"+base64.b64encode(svg.encode()).decode(), (mx/w*100, my/h*100)

def readouts(items):
    """items: (label, value, note, role) with role in ink/measure/heat."""
    cells = "".join(f'<div class="readout" style="--role:var(--{role})"><span>{escape(label)}</span><b>{escape(value)}</b>{f"<small>{escape(note)}</small>" if note else ""}</div>' for label, value, note, role in items)
    st.html(f'<div class="readouts" style="--n:{len(items)}">{cells}</div>')

def home():
    done = len(ss.done)
    xp = 20*done+10*sum(ss.answers.values())+5*len(ss.known)
    next_lesson = next((l for l in course["lessons"] if l["number"] not in ss.done), None)
    st.html(f'<div class="greet"><p>مساحتك في هندسة التحكم</p><span class="points">رصيدك <bdi>{xp}</bdi> نقطة</span></div>')
    src, (mx, my) = step_curve(done/9)
    you = "نقطة البداية" if done == 0 else ("وصلت إلى الهدف" if done == 9 else f"أنت هنا: {done} من 9 دروس")
    st.html(f'''<section class="hero"><div><h1>كل نظام يبحث عن ميزانه.</h1>
<p>تسعة دروس بالعربية ومختبر حراري تجرّب فيه P وPI وPID بنفسك. المنحنى يتبع تقدّمك: كل درس تنهيه يقرّبه من الهدف.</p></div>
<div class="curve"><img src="{src}" alt="منحنى استجابة لقفزة يقترب من الهدف؛ {you}"><span class="lbl goal">الهدف</span>
<span class="lbl you" style="top:calc({my:.1f}% + 14px);left:min(calc({mx:.1f}% + 14px),70%)">{you}</span></div></section>''')
    with st.container(horizontal=True):
        if next_lesson and st.button(f"{'تابع' if done else 'ابدأ'} الدرس {next_lesson['number']}", type="primary"):
            ss["lesson-choice"] = next_lesson["number"]
            st.switch_page(PAGES["lessons"])
        if st.button("افتح المختبر الحراري", icon=":material/science:"):
            st.switch_page(PAGES["lab"])
    readouts([("دروس أنهيتها", f"{done} / 9", "", "measure"),
              ("أسئلة أجبت عنها صحيحًا", f"{sum(ss.answers.values())} / 5", "", "measure"),
              ("بطاقات لم تراجعها", str(len(TERMS)-len(ss.known)), "", "ink"),
              ("نقاطك", str(xp), "20 لكل درس، 10 لكل سؤال، 5 لكل بطاقة", "ink")])
    path, practice = st.columns([1.35, 1], gap="large")
    with path:
        st.subheader("مسارك في أربع مراحل")
        for i, (name, nums) in enumerate([("البداية وفكرة التحكم", [1, 2]), ("لغة النمذجة الرياضية", [3, 4, 5]), ("من P إلى PID", [6, 7]), ("من النموذج إلى التطبيق", [8, 9])]):
            count = sum(n in ss.done for n in nums)
            first = next((n for n in nums if n not in ss.done), nums[0])
            st.html(f'<div class="stage"{" data-done" if count == len(nums) else ""}><i>{"١٢٣٤"[i]}</i><div><h3>{name}</h3><p>الدروس {nums[0]}–{nums[-1]}، أنهيت {count} من {len(nums)}</p></div></div>')
            if st.button(f"افتح الدرس {first}", key=f"path-{i}"):
                ss["lesson-choice"] = first
                st.switch_page(PAGES["lessons"])
    with practice:
        st.subheader("تدرّب اليوم")
        if st.button("اختبر فهمك في خمسة أسئلة", icon=":material/quiz:", width="stretch"):
            st.switch_page(PAGES["quiz"])
        if st.button("راجع المصطلحات بالعربية والألمانية", icon=":material/style:", width="stretch"):
            st.switch_page(PAGES["cards"])
        if st.button("جلسة تركيز لمدة 25 دقيقة", icon=":material/timer:", width="stretch"):
            st.switch_page(PAGES["focus"])
        st.caption("يُحفظ تقدّمك وملاحظاتك في هذه الجلسة فقط. نزّل ملاحظاتك من صفحة «ملاحظاتي» قبل أن تغلق المتصفح.")
        st.link_button("الكتاب المرجعي والمختبرات السابقة ↗", "https://mizan-control-ar.nuttycream6.chatgpt.site/book.html", width="stretch")

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
    with st.container(border=True, key="reading"):
        for block in lesson["blocks"]:
            text = unindent(block["text"])
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
    st.title("المختبر الحراري: P وPI وPID")
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
        st.html(f'''<figure class="iso-figure"><div class="iso-plate"><figcaption>الشكل ١: متحكّم {mode}</figcaption><span class="t">t = {at:.1f} s</span>{svg}</div>
<div class="iso-legend"><span class="iso-key"><span class="iso-chip" style="background:{heat}"></span>توهج السخان ومؤشرات LED: خرج المتحكّم u</span>
<span class="iso-key"><span class="iso-chip" style="background:{heat_color(level)}"></span>العمود في الشاشة: درجة الحرارة من 20 إلى 100 °C</span></div></figure>''')
    with readings:
        st.html('<div style="height:6px"></div>')
        readouts([("درجة الحرارة T", f"{row['T (°C)']:.1f} °C", "", "measure")])
        readouts([("الخطأ e = الهدف − T", f"{target-row['T (°C)']:.1f} °C", "", "ink")])
        readouts([("خرج المتحكّم u", f"{row['u']:.2f} / 8", "", "heat")])
    perf = step_metrics(data, target)
    readouts([("التجاوز الأقصى", f"{perf['overshoot']:.1f} %", "أعلى قيمة فوق الهدف، نسبةً إلى قفزة المرجع", "measure"),
              ("زمن الاستقرار ±2 %", "لم يستقر" if perf["settling"] is None else f"{perf['settling']:.1f} s", "منذ متى تبقى T داخل نطاق ±2 % حول الهدف", "measure"),
              ("الخطأ عند t = 240 s", f"{perf['final_error']:.2f} °C", "P وحده يترك خطأً دائمًا؛ التكامل في PI وPID يزيله", "ink")])
    st.line_chart(data.set_index("t (s)")[["T (°C)","الهدف (°C)"]], color=["#0c7c84","#13262d"], x_label="t (s)", y_label="°C")
    compare = st.toggle("قارن P وPI وPID على المنحنى نفسه")
    if compare:
        frame = pd.DataFrame({m: simulate(m,target,kp,ki,kd,a,b,aw)["T (°C)"].to_numpy() for m in ["P","PI","PID"]}, index=data["t (s)"])
        st.line_chart(frame, color=["#9aa9ae","#0c7c84","#13262d"], x_label="t (s)", y_label="°C")
    st.download_button("تنزيل بيانات التجربة CSV", data.to_csv(index=False).encode("utf-8-sig"), "mizan-thermal.csv", "text/csv")
    with st.expander("النموذج والافتراضات"):
        st.latex(r"\frac{dT}{dt}=a u-b(T-20),\quad 0\leq u\leq8,\quad T(0)=20")
        st.markdown("حساب كل 0.05 ثانية بحل أسي للنبات مع دخل ثابت خلال العينة. المشتقة على القياس ومرشحها 0.25 ثانية. لا ضوضاء ولا تأخير ولا تبريد نشط. القيم في نموذج تعليمي وليست إعدادات جهاز حقيقي.")
        st.image(str(ROOT/"thermal-rig.svg"), caption="تصوّر تعليمي للحجرة الحرارية، رُسم بأدوات Anatomy (رخصة MIT)")

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
    st.title("مصطلحات بالعربية والألمانية")
    i = ss.card % len(TERMS)
    ar, de, meaning = TERMS[i]
    st.caption(f"البطاقة {i+1} من {len(TERMS)}، تذكّرت {len(ss.known)}")
    st.progress(len(ss.known)/len(TERMS))
    with st.container(border=True):
        st.header(ar)
        if ss.flip:
            st.subheader(de)
            st.write(meaning)
        if st.button("اكشف الترجمة والمعنى"):
            ss.flip = True
            st.rerun()
    with st.container(horizontal=True):
        if st.button("تذكّرتها ✓", disabled=not ss.flip):
            ss.known = sorted(set(ss.known + [i]))
            ss.card += 1
            ss.flip = False
            st.rerun()
        if st.button("البطاقة التالية"):
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
    "lab": st.Page(lab, title="مختبر P وPI وPID", icon=":material/science:")
}
pg = st.navigation({"مساحة التعلّم": [PAGES[n] for n in ["home","lessons","cards","quiz","notes","focus"]], "من النظرية إلى الواقع": [PAGES["lab"]]})
with st.sidebar:
    st.html('<div class="brand"><span class="brand-mark">م</span><div><b>ميزان</b><small>هندسة التحكم بالعربية</small></div></div>')
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
st.caption("ميزان. المحتوى من control_arabic.zip المرفق، والتطوير مستقل. Studyflix مرجع لتنظيم الموضوعات فقط؛ لم تُنسخ الفيديوهات أو الصور.")
