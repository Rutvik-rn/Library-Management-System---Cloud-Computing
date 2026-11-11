import streamlit as st
import requests
import pandas as pd

API_BASE_URL = "http://api:8000"

st.set_page_config(page_title='Library Management System', layout='wide')
st.title("Library Management System Kiel")
st.caption("Streamlit Dashboard to Access Books in Library Management System (FastAPI + MySQL + Streamlit)")

# fetch function 
def show_books(data):
    if not data:
        st.info("no books found")
        return
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width = True)

# To View all books with a clickable button
st.subheader("View All Books in the LMS ")

load_all = st.button("Load")

if load_all:
    response = requests.get(f"{API_BASE_URL}/books", timeout=5)
    if response.status_code == 200:
        show_books(response.json())
    
st.divider()

# Add a new Book to our Library Management System
st.subheader("Add a New Book")

with st.form("Add book Details Here:"):
    title = st.text_input("title")
    author = st.text_input("author")
    category = st.text_input("category")
    status = st.selectbox("status - pick one", ["available","issued"])
    submit = st.form_submit_button("Add book / Click Here to Add")

if submit:
    if not title or not author or not category or not status:
        st.warning("Please Enter/Fill All Fields")
    else:
        payload = {"title": title, "author": author, "category": category, "status": status}
        response = requests.post(f"{API_BASE_URL}/books", json=payload, timeout=5)
        if response.status_code == 200:
            st.success("Book Added - Go Back to View ALL Books to Verify book has been created")
            st.json(response.json())

st.divider()

# Update Existing Book Details 

st.subheader("Update Existing Book")

with st.form("Update book Details Here:"):
    new_id = st.number_input("Book ID to Update", min_value = 1, step=1)
    new_title = st.text_input("title")
    new_author = st.text_input("author")
    new_category = st.text_input("category")
    new_status = st.selectbox("status - pick one", ["available","issued"])
    submitt = st.form_submit_button("Update book / Click Here to Update Book")

if submitt:
    if not new_title or not new_author or not new_category or not new_status:
        st.warning("Please Enter/Fill All Fields")
    else:
        payload = {"title": new_title, "author": new_author, "category": new_category, "status": new_status}
        response = requests.put(f"{API_BASE_URL}/books/{int(new_id)}", json=payload, timeout=5)
        if response.status_code == 200:
            st.success("Book Updated - Go Back to View ALL Books to Verify book has been Updated")
            st.json(response.json())

st.divider()

# Delete a Old Book

st.subheader("Delete Existing Book")

with st.form("Delete a book Here:"):
    del_id = st.number_input("Book ID to Update", min_value = 1, step=1)
    confirm = st.checkbox("Confirm Deletion?", value=False)
    
    delete = st.form_submit_button("Delete book / Click Here to Delete Book")

if delete:
    if not confirm:
        st.warning("Please click to confirm first")
    else:
        response = requests.delete(f"{API_BASE_URL}/books/{int(del_id)}", timeout=5)
        if response.status_code == 200:
            st.success("Book has been Deleted - Go Back to View ALL Books to Verify book has been Deleted")
            st.json(response.json())

st.divider()
