import streamlit as st
import requests
import google.generativeai as genai
import os

# --- 1. Page Config & CSS ---
st.set_page_config(page_title="ניתוח שיחת מכירה - גשר הבהירות", layout="wide", page_icon="🧠")

st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    .stMarkdown table { direction: rtl !important; text-align: right !important; width: 100% !important; }
    .stMarkdown th { background-color: #f0f2f6; text-align: right !important; }
    .stMarkdown td { text-align: right !important; border-bottom: 1px solid #ddd; vertical-align: top; }
    h1, h2, h3, h4, p, div, span, label, li { text-align: right !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. Header ---
st.title("מנתח השיחות האוטומטי 🧠")
st.caption("מבוסס מודל 'גשר הבהירות' (The Clarity Bridge)")
st.divider()

# --- 3. API Keys ---
try:
    DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ חסרים מפתחות API. יש להגדיר אותם ב-Streamlit Secrets.")
    st.stop()

# --- 4. Functions ---

def transcribe_audio(file_buffer):
    """Deepgram Transcription"""
    url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=he&diarize=true&smart_format=true&punctuate=true&filler_words=false"
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
                label = "דובר א'" if current_speaker == 0 else "דובר ב'"
                transcript += f"\n{label}: {current_sentence.strip()}\n"
                current_sentence = ""
                current_speaker = speaker
                
            current_sentence += f"{word['word']} "
        
        label = "דובר א'" if current_speaker == 0 else "דובר ב'"
        transcript += f"\n{label}: {current_sentence.strip()}\n"
        return transcript
    except:
        return "שגיאה בפרמוט התמלול."

def analyze_with_gemini(transcript_text, audience_desc):
    """Gemini Analysis - With Safety Settings Disabled"""
    genai.configure(api_key=GEMINI_API_KEY)
    
    # ביטול חסימות בטיחות (Safety Settings)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    generation_config = genai.types.GenerationConfig(
        temperature=0.15 
    )
    
    model = genai.GenerativeModel('gemini-2.5-flash', 
                                  generation_config=generation_config,
                                  safety_settings=safety_settings)
    
    prompt = f"""
    תפקיד: אתה יועץ עסקי בכיר המתמחה בפסיכולוגית מכירות ושיווק, ובנוסף עורך לשוני מומחה בעברית.
    
    הקשר: התקבל תמלול גולמי של שיחת מכירה. עליך להתעלם משגיאות תמלול ("רעשים") ולהבין את ההקשר הלוגי.
    המשימה: נתח את השיחה אך ורק על פי המתודולוגיה של מודל "גשר הבהירות" המפורט להלן.
    
    הלקוח בשיחה מוגדר: "{audience_desc}"

    --- הגדרות המודל לניתוח (חובה לפעול לפיהן) ---
    שלב 1 - היווצרות הפער/הצורך: הלקוח פסיבי, חווה סימפטום אך לא מבין את הבעיה.
    שלב 2 - אבחון וחיפוש משמעות: הלקוח מנסה להבין "למה זה קורה לי?".
    שלב 3 - חיפוש פתרונות: הלקוח מנסה להבין "מה האופציות הקיימות לסגירת הפער?".
    שלב 4 - בחינת החלופות (Evaluation): הלקוח מעריך מה הפתרון המתאים ביותר עבורו.
    שלב 5 - קבלת החלטה.

    --- מבנה הדו"ח הנדרש (השתמש בטבלאות Markdown) ---

    ### 📍 שלב הלקוח במסע
    זהה באיזה שלב (1-5) נמצא הלקוח *במהלך השיחה הזו* ונמק בקצרה מדוע.

    ### חלק א': תרגום הסימפטום (The Translation Gap)
    זהה תלונות שהלקוח העלה. האם המוכר תרגם אותן לבעיית שורש?
    * אם המוכר הצליח: תן פידבק חיובי.
    * אם המוכר נכשל: תן פידבק לשיפור + הצעה פרקטית לפעם הבאה (מה היה עליו לומר/לשאול).

    | הסימפטום שהוזכר | הבעיה השורשית (כפי שהוצגה או משתמעת) | פידבק למוכר והצעה ליישום |
    |---|---|---|
    | ... | ... | ... |

    ### חלק ב': משולש האמון (The Trust Triad)
    | סוג האמון | סטטוס (✅/⚠️/❌) | הסבר מנומק |
    |---|---|---|
    | **במוצר/בשיטה** | ... | ... |
    | **במוכר/בסמכות** | ... | ... |
    | **בעצמו (מסוגלות הלקוח)** | ... | ... |

    ### חלק ג': פחדים וחששות
    * **הפחד/החשש המרכזי של הלקוח:** (במשפט אחד)
    * **האם נוטרל בשיחה?** (כן/לא + הסבר קצר)

    ### חלק ד': החסם הקריטי
    מהי הסיבה האחת (האתגר המרכזי) שבגללה העסקה הזו תיתקע או תיפול?

    ### 📝 סיכום ביצועי המוכר
    * **נקודה לשימור (לטובה):** (ציין דבר אחד שהמוכר עשה מצוין).
    * **נקודה לשיפור:** (ציין דבר אחד שדורש שיפור דחוף).

    ---
    התמלול הגולמי לניתוח:
    {transcript_text}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"שגיאה בניתוח ה-AI (נסה שוב או שהקובץ חסום): {str(e)}"

# --- 5. Main UI Logic ---

col1, col2 = st.columns([2, 1])
with col1:
    target_audience = st.text_input("מי הלקוח? (חובה)", placeholder="לדוגמה: בעל עסק שחושש משיווק...")
with col2:
    uploaded_file = st.file_uploader("העלה הקלטה", type=['mp3', 'wav', 'm4a'])

if st.button("התחל ניתוח 🚀", type="primary", disabled=not (uploaded_file and target_audience)):
    
    progress_bar = st.progress(0, text="מתחיל בתהליך...")
    
    try:
        # שלב 1
        progress_bar.progress(25, text="🎧 מתמלל ומנקה רעשים (Deepgram Whisper)...")
        raw_data = transcribe_audio(uploaded_file.getvalue())
        
        if raw_data:
            transcript = format_transcript(raw_data)
            
            # שלב 2
            progress_bar.progress(75, text="🧠 המנתח בודק את שלבי המודל (Gemini)...")
            analysis = analyze_with_gemini(transcript, target_audience)
            
            progress_bar.progress(100, text="סיימנו!")
            st.success("הניתוח מוכן!")
            
            tab1, tab2 = st.tabs(["📊 הניתוח המלא", "📝 התמלול הגולמי"])
            with tab1:
                st.markdown(analysis)
                st.download_button("📥 הורד ניתוח", analysis, file_name="analysis.txt")
            with tab2:
                st.info("זהו התמלול הגולמי לפני התיקון של ה-AI:")
                st.text_area("", transcript, height=300)
        else:
            st.error("שגיאה בתמלול.")
            
    except Exception as e:
        st.error(f"שגיאה: {e}")
