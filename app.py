import streamlit as st
import requests
import google.generativeai as genai
import os

# --- 1. Page Config & CSS ---
st.set_page_config(page_title="ניתוח שיחת מכירה - גשר הבהירות", layout="wide", page_icon="🧠")

# CSS מתקדם לסידור הטבלאות והפונטים בעברית
st.markdown("""
<style>
    /* כיוון כללי לימין */
    .stApp { direction: rtl; text-align: right; }
    
    /* סידור טבלאות בעברית */
    .stMarkdown table {
        direction: rtl !important;
        text-align: right !important;
        width: 100% !important;
        border-collapse: collapse;
    }
    .stMarkdown th {
        background-color: #f0f2f6;
        text-align: right !important;
        padding: 10px;
    }
    .stMarkdown td {
        text-align: right !important;
        padding: 10px;
        border-bottom: 1px solid #ddd;
    }
    
    /* כותרות וטקסטים */
    h1, h2, h3, h4, p, div, span, label { text-align: right !important; }
    .stAlert { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- 2. Header ---
st.title("מנתח השיחות האוטומטי 🧠")
st.caption("מבוסס מודל 'גשר הבהירות' (The Clarity Bridge)")
st.divider()

# --- 3. API Keys Handling ---
try:
    DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ חסרים מפתחות API. יש להגדיר אותם ב-Streamlit Secrets בענן.")
    st.stop()

# --- 4. Functions ---

def transcribe_audio(file_buffer):
    """Deepgram Transcription"""
    # שימוש במודל Whisper שהוא יציב יותר בעברית בתוך Deepgram
    url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=he&diarize=true&smart_format=true"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/*"
    }
    response = requests.post(url, headers=headers, data=file_buffer)
    
    if response.status_code != 200:
        return None
    return response.json()

def format_transcript(data):
    """Formatting Transcript"""
    try:
        transcript = ""
        words = data['results']['channels'][0]['alternatives'][0]['words']
        current_speaker = None
        current_sentence = ""
        
        for word in words:
            speaker = word.get('speaker', 0)
            if current_speaker is None:
                current_speaker = speaker
            
            if speaker != current_speaker:
                # המרת מספרי דוברים לתוויות ברורות יותר (אם אפשר, אחרת משאיר מספר)
                speaker_label = "דובר א'" if current_speaker == 0 else "דובר ב'"
                transcript += f"\n{speaker_label}: {current_sentence.strip()}\n"
                current_sentence = ""
                current_speaker = speaker
                
            current_sentence += f"{word['word']} "
        
        # Last sentence
        speaker_label = "דובר א'" if current_speaker == 0 else "דובר ב'"
        transcript += f"\n{speaker_label}: {current_sentence.strip()}\n"
        return transcript
    except:
        return "שגיאה בפרמוט התמלול."

def analyze_with_gemini(transcript_text, audience_desc):
    """Gemini Analysis - STRICT & OPTIMIZED"""
    genai.configure(api_key=GEMINI_API_KEY)
    
    # שימוש בטמפרטורה נמוכה לדיוק מקסימלי
    generation_config = genai.types.GenerationConfig(
        temperature=0.2
    )
    
    # שימוש במודל החזק והעדכני ביותר
    model = genai.GenerativeModel('gemini-2.0-flash-exp', generation_config=generation_config)
    
    prompt = f"""
    תפקיד: אתה יועץ עסקי בכיר המומחה במודל המכירות "גשר הבהירות".
    מטרה: בצע ניתוח כירורגי לשיחת המכירה המצורפת.
    
    הקשר: הלקוח בשיחה מוגדר כך: "{audience_desc}"
    
    --- חוקים קריטיים (אל תפר אותם!) ---
    1. **אל תחזור על התמלול!** הפלט שלך צריך להכיל רק את הניתוח.
    2. **אל תמציא**: בסס הכל על ציטוטים מהטקסט.
    3. **עיצוב**: השתמש בטבלאות Markdown מסודרות.
    ------------------------------------

    מבנה הדו"ח הנדרש:

    ## 1. 🗣️ תרגום הסימפטום (The Translation Gap)
    האם המוכר הצליח לקחת תלונה ("יקר לי") ולתרגם אותה לבעיית שורש?
    | הסימפטום שהלקוח הציג | האם תורגם לבעיית שורש? | ציטוט מהשיחה |
    |---|---|---|
    | ... | ... | ... |

    ## 2. 🔺 משולש האמון (The Trust Triad)
    מה סטטוס האמון ב-3 הגזרות?
    | סוג האמון | סטטוס (✅ קיים / ⚠️ רופף / ❌ חסר) | הסבר וציטוט |
    |---|---|---|
    | **במוצר/בשיטה** | ... | ... |
    | **במוכר/בסמכות** | ... | ... |
    | **בעצמו (מסוגלות הלקוח)** | ... | ... |

    ## 3. 😱 תרחיש האימים
    * **הפחד העמוק שזוהה:** (במשפט אחד)
    * **האם טופל בשיחה?** (כן/לא + הסבר)

    ## 4. 🏁 סיכום מנהלים: החסם הקריטי
    מהי הסיבה האחת והיחידה שבגללה העסקה הזו תיתקע או תיפול?

    ---
    השיחה לניתוח:
    {transcript_text}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"שגיאה בניתוח: {str(e)}"

# --- 5. Main UI Logic ---

col1, col2 = st.columns([2, 1])
with col1:
    target_audience = st.text_input("מי הלקוח בשיחה? (חובה)", placeholder="לדוגמה: זוג צעיר שחושש מבירוקרטיה...")
with col2:
    uploaded_file = st.file_uploader("העלה הקלטה", type=['mp3', 'wav', 'm4a'])

if st.button("התחל ניתוח 🚀", type="primary", disabled=not (uploaded_file and target_audience)):
    
    # Progress Bar
    progress_bar = st.progress(0, text="מתחיל בתהליך...")
    
    try:
        # שלב 1: תמלול
        progress_bar.progress(25, text="🎧 מתמלל את השיחה ומפריד דוברים (Deepgram)...")
        raw_data = transcribe_audio(uploaded_file.getvalue())
        
        if raw_data:
            transcript = format_transcript(raw_data)
            
            # שלב 2: ניתוח
            progress_bar.progress(75, text="🧠 המנתח האוטומטי סורק את השיחה (Gemini 2.0)...")
            analysis = analyze_with_gemini(transcript, target_audience)
            
            progress_bar.progress(100, text="סיימנו!")
            
            # הצגת תוצאות
            st.success("הניתוח מוכן!")
            
            # לשוניות לניווט נוח
            tab1, tab2 = st.tabs(["📊 הניתוח המלא", "📝 התמלול הגולמי"])
            
            with tab1:
                st.markdown(analysis)
                # כפתור הורדת הניתוח
                st.download_button("📥 הורד את הניתוח כקובץ", analysis, file_name="analysis_report.txt")
                
            with tab2:
                st.text_area("תמלול השיחה", transcript, height=400)
                
        else:
            st.error("שגיאה בתהליך התמלול.")
            
    except Exception as e:
        st.error(f"התרחשה שגיאה בלתי צפויה: {e}")
