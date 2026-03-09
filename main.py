import streamlit as st
import os
import json
import datetime
import re
import requests
import gspread
from bs4 import BeautifulSoup
from groq import Groq
from tavily import TavilyClient

# --- Page Configuration ---
st.set_page_config(page_title="Focus Sales AI", page_icon="🏢", layout="wide")

# --- Custom CSS for Mobile Look ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #FF4B4B; color: white; }
    .prospect-card { background-color: white; padding: 20px; border-radius: 15px; border-left: 5px solid #FF4B4B; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- App Header ---
st.title("🚀 Focus Softnet Agent")
st.subheader("Singapore SME Prospecting Tool")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("🔑 API Configuration")
    groq_key = st.text_input("Groq API Key", type="password")
    tavily_key = st.text_input("Tavily API Key", type="password")
    sheet_id = st.text_input("Google Sheet ID")
    
    st.info("Note: Ensure your 'credentials.json' is in the project folder to sync with Google Sheets.")

# --- Helper Functions ---
def get_google_sheet(sid):
    try:
        # Determine the absolute path to credentials.json
        # This helps Streamlit find it regardless of how the app is launched
        current_dir = os.path.dirname(os.path.abspath(__file__))
        creds_path = os.path.join(current_dir, 'credentials.json')
        
        if not os.path.exists(creds_path):
            st.error(f"❌ File Not Found: {creds_path}. Is it in the same folder as app.py?")
            return None

        # Authenticate
        gc = gspread.service_account(filename=creds_path)
        
        # Try to open the sheet
        sh = gc.open_by_key(sid)
        return sh.sheet1
        
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Spreadsheet Not Found. Check your Sheet ID and ensure you shared the sheet with the Service Account email.")
    except Exception as e:
        st.error(f"❌ Connection Error: {str(e)}")
    return None

def find_contacts(client, name):
    query = f"{name} Singapore official email and office phone"
    email, phone = "Email not available", "Phone number not available"
    try:
        search = client.search(query=query, max_results=3)
        for res in search['results']:
            content = res.get('content', '').lower()
            e_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
            if e_match and email == "Email not available": email = e_match.group(0)
            p_match = re.search(r'(\+65\s?[689]\d{3}\s?\d{4}|[689]\d{3}\s?\d{4})', content)
            if p_match and phone == "Phone number not available": phone = p_match.group(0)
    except: pass
    return email, phone

def analyze_site(url, g_client):
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, 'html.parser')
        for s in soup(['script', 'style']): s.decompose()
        text = soup.get_text(separator=' ', strip=True)[:8000]
        
        prompt = f"Analyze {url}. Return JSON: {{'company_name': 'str', 'summary': '120-word str', 'solution': 'str', 'email': 'str'}}. Text: {text}"
        
        chat = g_client.chat.completions.create(
            messages=[{"role": "system", "content": "Return JSON only."}, {"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        return json.loads(chat.choices[0].message.content)
    except: return None

# --- Main App Interface ---
query = st.text_input("Search Target", placeholder="e.g. Logistics SMEs in Jurong")

if st.button("Find Prospects"):
    if not groq_key or not tavily_key or not sheet_id:
        st.warning("Please provide all API keys in the sidebar.")
    else:
        g_client = Groq(api_key=groq_key)
        t_client = TavilyClient(api_key=tavily_key)
        worksheet = get_google_sheet(sheet_id)
        
        st.write("🔎 Searching for matching businesses...")
        search = t_client.search(query=f"{query} Singapore", max_results=5)
        
        for item in search['results']:
            url = item['url']
            if any(x in url for x in ['facebook', 'yelp', 'instagram']): continue
            
            with st.spinner(f"Analyzing {url}..."):
                data = analyze_site(url, g_client)
                if data:
                    email, phone = find_contacts(t_client, data['company_name'])
                    
                    # Display as a "Mobile Card"
                    st.markdown(f"""
                        <div class="prospect-card">
                            <h3>🏢 {data['company_name']}</h3>
                            <p><b>Recommended:</b> {data['solution']}</p>
                            <p><b>Contact:</b> {email} | {phone}</p>
                            <p style="font-size: 0.9em; color: #555;">{data['summary']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Sync to Google Sheets
                    if worksheet:
                        row = [data['company_name'], url, email, phone, data['solution'], data['summary'], data['email'], str(datetime.date.today())]
                        worksheet.append_row(row)

        st.success("Analysis complete! All leads synced to Google Sheets.")