import streamlit as st 
import google.generativeai as genai 
st.title("Reparatur")
enai.configure(api_key=st.secrets["GOOGLE_API_KEY"]) 
t.write("Ich suche Modelle...") 
for m in genai.list_models():    
    st.write(m.name)
