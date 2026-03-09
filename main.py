import streamlit as st
import os, json, datetime, re, requests, gspread
from bs4 import BeautifulSoup
from groq import Groq
from tavily import TavilyClient

# --- Page Config for Mobile Feel ---
st.set_page_config(page_title="Focus Prospector", page_icon="🚀")

# --- UI Styling ---
st.title("🚀 Focus Softnet Sales Agent")
st.markdown("Find and qualify SG leads instantly.")

# --- Sidebar for Keys ---
with st.sidebar:
    st.header("Settings")
    groq_key = st.text_input("Groq API Key", type="password")
    tavily_key = st.text_input("Tavily API Key", type="password")
    sheet_id = st.text_input("1RYfg5BFSg6ztKeDc3k04QDBvI0YwG7H-SU4ywFYhx_g")

# --- Shared Logic Functions (Simplified for brevity) ---
def find_contacts(tavily_client, company_name):
    query = f"{company_name} Singapore official email and office phone"
    email, phone = "Email not available", "Phone number not available"
    try:
        search = tavily_client.search(query=query, max_results=3)
        for res in search['results']:
            content = res.get('content', '').lower()
            e_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
            if e_match and email == "Email not available": email = e_match.group(0)
            p_match = re.search(r'(\+65\s?[689]\d{3}\s?\d{4}|[689]\d{3}\s?\d{4})', content)
            if p_match and phone == "Phone number not available": phone = p_match.group(0)
    except: pass
    return email, phone

# --- Main App Logic ---
target = st.text_input("Who are we looking for?", placeholder="e.g. Logistics in Ubi")

if st.button("Start Prospecting"):
    if not groq_key or not tavily_key or not sheet_id:
        st.error("Please fill in all keys in the sidebar!")
    else:
        # Initialize Clients
        groq_client = Groq(api_key=groq_key)
        tavily_client = TavilyClient(api_key=tavily_key)
        
        with st.status("Searching for leads...", expanded=True) as status:
            results = tavily_client.search(query=f"{target} Singapore", max_results=5)
            urls = [r['url'] for r in results['results'] if 'facebook' not in r['url']]
            
            for url in urls:
                st.write(f"Analyzing {url}...")
                # (Insert your scraping & analyze_company logic here)
                # For this demo, we'll assume 'analysis' is returned
                
                # After processing:
                st.success(f"Found: {url}")
                # Append to Google Sheet logic...
        
        st.balloons()
        st.success("Done! Check your Google Sheet.")