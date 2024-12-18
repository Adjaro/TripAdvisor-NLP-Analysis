import streamlit as st
import requests
import json

API_URL = "http://server:8000"

st.title("Item Manager")

# Create Item
with st.form("create_item"):
    name = st.text_input("Name")
    description = st.text_input("Description")
    if st.form_submit_button("Create Item"):
        response = requests.post(
            f"{API_URL}/items/",
            json={"name": name, "description": description}
        )
        if response.status_code == 200:
            st.success("Item created!")

# List Items
if st.button("Refresh Items"):
    response = requests.get(f"{API_URL}/items/")
    if response.status_code == 200:
        items = response.json()
        for item in items:
            st.write(f"Name: {item['name']}, Description: {item['description']}")