import streamlit as st


def show():
    st.title("welcome to the app")
    st.write("This is a simple app to demonstrate how to use Docker and Streamlit together.")
    st.write("This app displays the content of a file stored in the /data folder.")
    st.write("The content of the file is displayed below:")
    with open("data/data.txt", "r") as file:
        data = file.read()
    st.write(data)
    st.write("This is the end of the file content.")