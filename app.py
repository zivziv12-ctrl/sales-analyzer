import streamlit as st
import requests
import google.generativeai as genai
import os

# --- Page Config ---
st.set_page_config(page_title="ניתוח שיחת מכירה - גשר הבהירות", layout="wide", page_icon="🧠")

# --- Custom CSS for RTL (Right-to-Left) Support ---
st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    h1, h2, h3, h4, h5, h6, p, div, span, label, .stMarkdown { text-align: right !important; }
    .stTextInput > div > div > input { text-align: right; direction: rtl; }
    .stAlert { direction: rtl; text-align: right; }
    /* Fix for lists */
    ul { direction: rtl; text-align: right; }
    li { text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("מנתח השיחות האוטומטי 🧠")
st.markdown("##### מבוסס מודל 'גשר הבהירות' (The Clarity Bridge)")
st.markdown("---")

# --- API Keys Handling ---
try:
    DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ חסרים מפתחות API. יש להגדיר אותם ב-Streamlit Secrets בענן.")
    st.stop()

# --- User Inputs ---
col1, col2 = st.columns([2, 1])
with col1:
    target_audience = st.text_input("הגדר את הלקוח בשיחה (חובה)", placeholder="לדוגמה: זוג צעיר לפני דירה ראשונה שחושש מבירוקרטיה")
with col2:
    st.info("💡 המערכת תנתח את השיחה ותחפש פערים לוגיים, בעיות אמון ותרחישי אימים.")

uploaded_file = st.file_uploader("העלה הקלטת שיחה (MP3, WAV, M4A)", type=['mp3', 'wav', 'm4a'])

# --- Functions ---

def transcribe_audio(file_buffer):
    """Sends audio to Deepgram for transcription with diarization (Speaker separation)"""
    url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=he&diarize=true&smart_format=true"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/*"
    }
    response = requests.post(url, headers=headers, data=file_buffer)
    
    if response.status_code != 200:
        st.error(f"שגיאה בתמלול (Deepgram): {response.text}")
        return None
        
    return response.json()

def format_transcript(data):
    """Formats the JSON response into a readable dialogue"""
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
                transcript += f"Speaker {current_speaker}: {current_sentence.strip()}\n"
                current_sentence = ""
                current_speaker = speaker
                
            current_sentence += f"{word['word']} "
        
        # Add last sentence
        transcript += f"Speaker {current_speaker}: {current_sentence.strip()}\n"
        return transcript
    except Exception as e:
        return "שגיאה בפרמט התמלול. ייתכן שהקובץ ריק או לא תקין."

def analyze_with_gemini(transcript_text, audience_desc):
    """Sends the transcript to Gemini with the Clarity Bridge Prompt"""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    תפקיד: אתה מומחה למודל המכירות והפסיכולוגיה הצרכנית "גשר הבהירות" (The Clarity Bridge).
    משימה: נתח את תמלול השיחה המצורף.

    הקשר לשיחה:
    קהל היעד והלקוח בשיחה מוגדרים כך: "{audience_desc}"
    
    הנחיות קריטיות (Strict Rules):
    1. **אל תמציא**: אם אין מידע בשיחה על סעיף מסוים, כתוב במפורש: "❌ לא זוהה בשיחה זו". אל תנסה להסיק מסקנות עקיפות.
    2. **זהה דוברים**: בתמלול כתוב Speaker 0 ו-Speaker 1. עליך להבין מההקשר מי המוכר ומי הלקוח ולהשתמש במונחים אלו.
    3. **ציטוטים**: כל תובנה חייבת להיות מגובה בציטוט במירכאות מתוך הטקסט.
    
    אנא הפק דו"ח בעברית בפורמט Markdown הכולל את החלקים הבאים:

    ### 1. תרגום הסימפטום (The Translation Gap)
    האם המוכר הצליח לתרגם את תלונות הלקוח ("יקר לי", "כואב לי") לבעיה השורשית?
    * צור טבלה עם העמודות: הסימפטום שהוזכר | האם בוצע תרגום לבעיה שורשית? | ציטוט מהשיחה.

    ### 2. משולש האמון (The Trust Triad)
    נתח את רמת האמון ב-3 הגזרות. אם חסר מידע, ציין זאת.
    * **אמון במוצר/שיטה**: (האם הלקוח מאמין שזה יעבוד?)
    * **אמון במוכר**: (האם המוכר נתפס מקצועי/ישר?)
    * **אמון עצמי (מסוגלות)**: (האם הלקוח מאמין שהוא יצליח ליישם? זהו לרוב החסם הסמוי).
    *(עבור כל אחד: כתוב סטטוס וציטוט תומך)*.

    ### 3. תרחיש האימים (The Nightmare Scenario)
    האם הלקוח ביטא פחד עמוק מכישלון או השלכות שליליות? כיצד המוכר הגיב לזה?

    ### 4. הזדמנויות שהוחמצו (The Missing Links)
    רשום 2-3 שאלות קריטיות שהמוכר *לא שאל* והיו יכולות לחשוף מידע חסר על הלקוח לפי המודל.

    ### סיכום: החסם הקריטי
    מהי הסיבה האחת והיחידה (בסבירות גבוהה) שבגללה העסקה לא נסגרה או נתקעה?

    הנה התמלול:
    {transcript_text}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"שגיאה בניתוח ה-AI: {str(e)}"

# --- Main App Logic ---

if uploaded_file and target_audience:
    if st.button("התחל ניתוח (כ-60 שניות) 🚀", type="primary"):
        
        # 1. Transcribe
        with st.status("מתקשר עם השרתים...", expanded=True) as status:
            st.write("📤 שולח את האודיו לתמלול (Deepgram)...")
            raw_data = transcribe_audio(uploaded_file.getvalue())
            
            if raw_data:
                st.write("📝 מעבד טקסט ומפריד דוברים...")
                transcript = format_transcript(raw_data)
                
                # 2. Analyze
                st.write("🧠 המנתח האוטומטי סורק את השיחה (Gemini AI)...")
                analysis = analyze_with_gemini(transcript, target_audience)
                
                status.update(label="הניתוח הסתיים!", state="complete", expanded=False)
                
                st.divider()
                st.subheader("תוצאות הניתוח:")
                st.markdown(analysis)
                
                with st.expander("👀 צפה בתמלול השיחה המלא"):
                    st.text(transcript)
    else:
        st.write("") 

elif uploaded_file and not target_audience:
    st.warning("⚠️ רגע, שכחת לכתוב את מי אנחנו מנתחים (בתיבה למעלה).")
