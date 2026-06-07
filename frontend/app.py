# import streamlit as st
# import requests
# import os
# from colorama import Fore

# # =========================
# # CONFIG
# # =========================
# BACKEND_URL = os.getenv("API_BASE", "http://localhost:8006")

# # =========================
# # SESSION STATE INIT
# # =========================
# def init_state():
#     defaults = {
#         "token": None,
#         "documents": [],
#         "selected_document": None,
#         "selected_document_id": None,
#         "conversations": [],
#         "conversation_id": None,
#         "messages": [],
#         "refresh_conversations": False,  # ← add this flag
#     }
#     for k, v in defaults.items():
#         if k not in st.session_state:
#             st.session_state[k] = v

# init_state()

# # =========================
# # HELPERS
# # =========================
# def auth_headers():
#     return {"Authorization": f"Bearer {st.session_state.token}"}

# def fetch_documents():
#     res = requests.get(f"{BACKEND_URL}/documents/document_list", headers=auth_headers())
#     if res.status_code == 200:
#         st.session_state.documents = res.json()
#     else:
#         st.session_state.documents = []

# def fetch_conversations(document_id):
#     res = requests.get(
#         f"{BACKEND_URL}/conversations/conversation_list",
#         params={"document_id": document_id},
#         headers=auth_headers()
#     )
#     st.session_state.conversations = res.json() if res.status_code == 200 else []

# def fetch_messages(conversation_id):
#     res = requests.get(
#         f"{BACKEND_URL}/messages",
#         params={"conversation_id": conversation_id},
#         headers=auth_headers()
#     )
    
#     st.session_state.messages = res.json() if res.status_code == 200 else []

# def reset_chat():
#     st.session_state.conversation_id = None
#     st.session_state.messages = []
    
# def on_doc_change():
#     # 'doc_selector' is the key we will assign to the selectbox
#     new_doc = st.session_state.doc_selector
#     if new_doc and new_doc != st.session_state.selected_document:
#         st.session_state.selected_document = new_doc
#         st.session_state.selected_document_id = new_doc["document_id"]
#         reset_chat()
#         fetch_conversations(new_doc["document_id"])
    
#     else:
#         st.session_state.selected_document = None
#         st.session_state.selected_document_id = None
#         st.session_state.conversations = []
#         reset_chat()

# # =========================
# # LOGIN
# # =========================
# st.title("📚 RAG Chatbot (LangGraph)")

# if not st.session_state.token:
#     st.subheader("🔐 Login")

#     username = st.text_input("Username")
#     password = st.text_input("Password", type="password")

#     if st.button("Login"):
#         res = requests.post(
#             f"{BACKEND_URL}/auth/login",
#             json={"username": username, "password": password}
#         )
#         if res.status_code == 200:
#             st.session_state.token = res.json()["access_token"]
#             fetch_documents()
#             st.success("Logged in successfully")
#             st.rerun()
#         else:
#             st.error("Login failed")

#     st.stop()

# # =========================
# # SIDEBAR – CONVERSATIONS
# # =========================
# # st.sidebar.title("💬 Chats")

# # if st.sidebar.button("➕ New Chat"):
# #     reset_chat()

# # if st.session_state.selected_document_id:
# #         for c in st.session_state.conversations:
# #             label = f"🧵 {c['conversation_id'][:8]}"
# #             if st.sidebar.button(label):
# #                 st.session_state.conversation_id = c["conversation_id"]
# #                 fetch_messages(c["conversation_id"])
                
# st.sidebar.title("💬 Chats")

# if st.sidebar.button("➕ New Chat"):
#     reset_chat()
#     fetch_conversations(st.session_state.selected_document_id)  # refresh here directly
#     st.rerun()

# if st.session_state.selected_document_id:
#     for c in st.session_state.conversations:
#         label = f"🧵 {c['conversation_id'][:8]}"
#         if st.sidebar.button(label, key=c["conversation_id"]):
#             st.session_state.conversation_id = c["conversation_id"]
#             fetch_messages(c["conversation_id"])
#             # ← NO refresh_conversations, NO st.rerun() here

# # =========================
# # TOP BAR – DOCUMENTS
# # =========================
# st.subheader("📄 Documents")

# col1, col2 = st.columns(2)

# with col1:
#     uploaded_file = st.file_uploader("Upload new PDF", type=["pdf"])
#     if uploaded_file and st.button("Confirm Upload"):
#         files = {
#             "file": (
#                 uploaded_file.name,
#                 uploaded_file.getvalue(),
#                 "application/pdf"
#             )
#         }
#         res = requests.post(
#             f"{BACKEND_URL}/documents/upload",
#             files=files,
#             headers=auth_headers()
#         )

#         if res.status_code == 200:
#             fetch_documents()
#             # st.session_state.uploaded_once=True
#             st.success("PDF uploaded")
#         else:
#             st.error("Upload failed")

# with col2:
#     if st.session_state.documents:
#         selected_doc = st.selectbox(
#             "Select existing PDF",
#             st.session_state.documents,
#             format_func=lambda d: d["document_name"],
#             key="doc_selector",
#             on_change=on_doc_change,
#             index=None,
#             placeholder="Choose a document..."
#         )

# # =========================
# # CHAT WINDOW
# # =========================
# st.divider()
# st.subheader("🧠 Chat")

# # Render messages
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # Chat input
# user_input = st.chat_input("Ask a question...")

# if user_input:
#     if not st.session_state.selected_document_id:
#         st.error("Please select or upload a document first.")
#         st.stop()

#     # Show user message immediately
#     st.session_state.messages.append({
#         "role": "user",
#         "content": user_input
#     })
#     with st.chat_message("user"):
#         st.markdown(user_input)
#     print(Fore.BLUE + f"inside the app the conversation id is: {st.session_state.conversation_id}")
#     payload = {
#         "question": user_input,
#         "conversation_id": st.session_state.conversation_id,
#         "document_id": st.session_state.selected_document_id
#     }

#     res = requests.post(
#         f"{BACKEND_URL}/chat",
#         headers={
#             **auth_headers(),
#             "Content-Type": "application/json"
#         },
#         json=payload,
#         stream=True
#     )

#     # Stream assistant response
#     answer = ""
#     with st.chat_message("assistant"):
#         placeholder = st.empty()
#         for chunk in res.iter_content(chunk_size=None):
#             token = chunk.decode("utf-8")
#             answer += token
#             placeholder.markdown(answer)

#     # Capture conversation_id from response header (new chat)
#     if st.session_state.conversation_id is None:

#         st.session_state.conversation_id = res.headers.get("x-conversation-id")
#     fetch_conversations(st.session_state.selected_document_id)

#     st.session_state.messages.append({
#         "role": "assistant",
#         "content": answer
#     })


import streamlit as st
import requests
import os
from colorama import Fore

BACKEND_URL = os.getenv("API_BASE", "http://localhost:8006")

def init_state():
    defaults = {
        "token": None,
        "documents": [],
        "selected_document": None,
        "selected_document_id": None,
        "conversations": [],
        "conversation_id": None,
        "messages": [],
        "conversation_titles":{}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def fetch_documents():
    res = requests.get(f"{BACKEND_URL}/documents/document_list", headers=auth_headers())
    st.session_state.documents = res.json() if res.status_code == 200 else []

def fetch_conversations(document_id):
    if not document_id:
        return
    res = requests.get(
        f"{BACKEND_URL}/conversations/conversation_list",
        params={"document_id": document_id},
        headers=auth_headers()
    )
    st.session_state.conversations = res.json() if res.status_code == 200 else []

def fetch_messages(conversation_id):
    res = requests.get(
        f"{BACKEND_URL}/messages",
        params={"conversation_id": conversation_id},
        headers=auth_headers()
    )
    st.session_state.messages = res.json() if res.status_code == 200 else []

def reset_chat():
    st.session_state.conversation_id = None
    st.session_state.messages = []

def on_doc_change():
    new_doc = st.session_state.doc_selector
    if new_doc:
        # Compare by document_id string, not dict — avoids dict comparison bug
        new_id = new_doc["document_id"]
        if new_id != st.session_state.selected_document_id:  # ← compare IDs not dicts
            st.session_state.selected_document = new_doc
            st.session_state.selected_document_id = new_id
            reset_chat()
            fetch_conversations(new_id)
        # if same document selected again, do nothing — don't wipe anything
    else:
        st.session_state.selected_document = None
        st.session_state.selected_document_id = None
        st.session_state.conversations = []
        reset_chat()

# =========================
# LOGIN
# =========================
st.title("📚 RAG Chatbot (LangGraph)")

if not st.session_state.token:
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"username": username, "password": password}
        )
        if res.status_code == 200:
            st.session_state.token = res.json()["access_token"]
            fetch_documents()
            st.success("Logged in successfully")
            st.rerun()
        else:
            st.error("Login failed")
    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.title("💬 Chats")

if st.sidebar.button("➕ New Chat"):
    reset_chat()
    fetch_conversations(st.session_state.selected_document_id)
    st.rerun()

if st.session_state.selected_document_id:
    for c in st.session_state.conversations:
        conv_id = c["conversation_id"]
        label = st.session_state.conversation_titles.get(conv_id, f"🧵 {conv_id[:8]}")
        if st.sidebar.button(label, key=c["conversation_id"]):
            st.session_state.conversation_id = c["conversation_id"]
            fetch_messages(c["conversation_id"])
            # no st.rerun() — Streamlit reruns naturally on button click

# =========================
# DOCUMENTS
# =========================
st.subheader("📄 Documents")
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload new PDF", type=["pdf"])
    if uploaded_file and st.button("Confirm Upload"):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        res = requests.post(
            f"{BACKEND_URL}/documents/upload",
            files=files,
            headers=auth_headers()
        )
        if res.status_code == 200:
            fetch_documents()
            st.success("PDF uploaded")
        else:
            st.error("Upload failed")

with col2:
    if st.session_state.documents:
        st.selectbox(
            "Select existing PDF",
            st.session_state.documents,
            format_func=lambda d: d["document_name"],
            key="doc_selector",
            on_change=on_doc_change,
            index=None,
            placeholder="Choose a document..."
        )

# =========================
# CHAT WINDOW
# =========================
st.divider()
st.subheader("🧠 Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask a question...")

if user_input:
    if not st.session_state.selected_document_id:
        st.error("Please select or upload a document first.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    payload = {
        "question": user_input,
        "conversation_id": st.session_state.conversation_id,
        "document_id": st.session_state.selected_document_id
    }

    res = requests.post(
        f"{BACKEND_URL}/chat",
        headers={**auth_headers(), "Content-Type": "application/json"},
        json=payload,
        stream=True
    )

    answer = ""
    with st.chat_message("assistant"):
        placeholder = st.empty()
        for chunk in res.iter_content(chunk_size=None):
            token = chunk.decode("utf-8")
            answer += token
            placeholder.markdown(answer)

    if st.session_state.conversation_id is None:
        new_id = res.headers.get("x-conversation-id")
        new_title = res.headers.get("x-conversation-title")
        st.session_state.conversation_id = new_id
        
        if new_id and new_title:
            st.session_state.conversation_titles[new_id] = new_title
        fetch_conversations(st.session_state.selected_document_id)  # only fetch on NEW conversation

    st.session_state.messages.append({"role": "assistant", "content": answer})