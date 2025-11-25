import streamlit as st 
import google.generativeai as genai 
st.title("Reparatur")
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"]) 
st.write("Ich suche Modelle...") 
for m in genai.list_models():    
    st.write(m.name)
