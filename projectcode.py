# Note: Sections of code that fall between the comments "BEGIN: Code by Giovanni Fernandez" and "END: Code by Giovanni Fernandez" are what I was directly responsible for.

# BEGIN: Code by Giovanni Fernandez
import streamlit as st
from openai import OpenAI
import fitz
import pytesseract
from PIL import Image
# END: Code by Giovanni Fernandez

API_KEY = 'YOUR-API-KEY-HERE'
client = OpenAI(api_key=API_KEY)

def main():
    st.set_page_config(page_title="Energy Bill Analyzer", layout='centered')

    # Custom CSS to inject for styling
    #custom_css = """
    #<style>
       # /* General background and text color */
       # .stApp {
        #    background-color: #837B7B;
       #     color: #FAFAFA;
      #  }
      #  /* Primary color for buttons and other elements */
      #  .st-bb, .st-at, .st-cb {
      #      background-color: #F63366;
      #  }
      #  /* Secondary background for containers */
       # .st-bv {
       #     background-color: #1A1A1A;
       # }
       # /* Customize fonts across the app */
       # body, .st-bx, .st-cx {
        #    font-family: system-ui;
       # }
   # </style>
   # """ 
   # st.markdown(custom_css, unsafe_allow_html=True)
    
    st.title("Energy Bill Analyzer")
    
    # Session state for the extracted text and responses
    if 'extracted_text' not in st.session_state:
        st.session_state.extracted_text = ""
    if 'responses' not in st.session_state:
        st.session_state.responses = []

# BEGIN: Code by Giovanni Fernandez
    st.markdown("""
    **About:**
    This tool analyzes your PG&E bill to provide personalized advice on reducing your energy costs.
    It uses OCR technology to extract text from your uploaded bill and an AI model to analyze the content.
                
    **Instructions:**
    - Upload a PDF version of your PG&E bill
    - Ensure the bill is clear to facilitate accurate text extraction
    """)
    
    uploaded_file = st.file_uploader("Upload your PDF bill here", type=['pdf'], label_visibility="collapsed")
# END: Code by Giovanni Fernandez
    
    if uploaded_file is not None:
        st.write("Click ''Submit'' to begin analysis.")
        st.session_state.extracted_text = process_pdf(uploaded_file)
        display_results(st.session_state.extracted_text)
        
    if 'audio_ready' in st.session_state and st.session_state.audio_ready:
        handle_questions(client, st.session_state.extracted_text)

# BEGIN: Code by Giovanni Fernandez
def process_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype='pdf')
    if len(doc) == 0:
        st.error("The document is empty or could not be loaded.")
        return ""
    text = ""
    for page in doc:
        text += extract_text_from_page(page)
    return text

def extract_text_from_page(page):
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return pytesseract.image_to_string(img)

def display_results(extracted_text):
    prompt = "You are a virtual assistant specialized in energy savings. After analyzing the details of the provided utility bill, summarize the key points and offer specific, actionable advice that could help reduce energy costs. Emphasize clear organization of information and ensure the complete omission of private data for security and privacy. Focus on areas where changes can have the most impact according to usage patterns and data from the bill. Handle all data with the utmost security, comply with privacy regulations, and redact all sensitive information, including account numbers and personal identifiers, to ensure confidentiality is maintained."
    with st.form("search_file_query_form"):
        submit_button = st.form_submit_button("Submit")
        if submit_button:
            advice, error = get_energy_advice(prompt, extracted_text)
            if advice:
                st.success("Analysis completed successfully.")
                st.session_state.advice = advice
            else:
                st.error(f"Failed to get advice: {error}")
# END: Code by Giovanni Fernandez

    if 'advice' in st.session_state and st.session_state.advice:
        st.write("", st.session_state.advice)
        if 'audio_ready' not in st.session_state or not st.session_state.audio_ready:
            play_audio(st.session_state.advice)

# BEGIN: Code by Giovanni Fernandez
def get_energy_advice(prompt, text):
    client = OpenAI(api_key=API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": text}]
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"An error occurred: {str(e)}"
  
def play_audio(text):
    if 'audio_content' not in st.session_state or st.session_state.last_advice_text != text:
        client = OpenAI(api_key=API_KEY)
        try:
            response = client.audio.speech.create(model="tts-1", voice="nova", input=text)
            st.session_state.audio_content = response.content
            st.session_state.audio_ready = True
            st.session_state.last_advice_text = text
        except Exception as e:
            st.session_state.audio_ready = False
            return "Failed to generate audio: " + str(e)
   
def display_audio_player():
    if 'audio_content' in st.session_state:
        st.audio(st.session_state.audio_content, format='audio/mp3')

def text_to_speech(text):
    client = OpenAI(api_key=API_KEY)
    try:
        response = client.audio.speech.create(model="tts-1", voice="nova", input=text)
        return response.content
    except Exception as e:
        return None
# END: Code by Giovanni Fernandez

def generate_response_to_question(client, question, extracted_text):
    try:
        system_message = "The following information has been extracted from your energy bill: " + extracted_text
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": question}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"An error occurred while generating a response: {str(e)}"

def handle_questions(client, extracted_text):
    display_audio_player()

    st.write("**Follow-Up Questions:**")
    question = st.text_input("Type your question(s) below.", key="question")
    submit = st.button('Submit', key='submit_question')
    
    if submit and question:
        response = generate_response_to_question(client, question, extracted_text)
        st.session_state.responses.append(response)
        for response in st.session_state.responses:
            st.write(response)
    elif submit and not question:
        st.write("Please enter a question.")

if __name__ == "__main__":
    main()
