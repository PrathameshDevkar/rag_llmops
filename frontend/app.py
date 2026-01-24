import streamlit as st
import requests
import os

backend_url=os.getenv("API_BASE","http://localhost:8000")

st.title("rag chatbot (langgraph)")

if "token" not in st.session_state:
    st.session_state["token"]=None

if "documents" not in st.session_state:
    st.session_state["documents"]=None

if "document_id" not in st.session_state:
    st.session_state["document_id"]=None

if "conversations" not in st.session_state:
    st.session_state["conversations"]=None

if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"]=None
    
if "chat_history" not in st.session_state:
    st.session_state["chat_history"]=[]

if "selected_document" not in st.session_state:
    st.session_state["selected_document"]=None

if not st.session_state["token"]:
    st.subheader("login")
    username= st.text_input("Username")
    password = st.text_input("Password",type="password")
    
    if st.button("login"):
        res = requests.post(
            f"{backend_url}/auth/login",
            json={
                "username":username,
                "password":password
            }
        )
        print("res is",res)
        if res.status_code==200:
            st.session_state["token"]=res.json()["access_token"]
            st.success("logged in")
        else:
            st.error("login failed")
            
        docs=requests.get(
            f"{backend_url}/documents",
            headers={"Authorization":f"Bearer {st.session_state['token']}"}
        )
        print("*"*30)
        print("docs are",docs.json())
        if docs.status_code==200:
            st.session_state["documents"]=docs.json()
            st.rerun()

        else:
            st.session_state["documents"]=[]
    st.stop()
    

st.subheader("upload pdf")

uploaded_file=st.file_uploader("choose a file",type=["pdf"])

if uploaded_file:
    files={"file":(uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
    headers={"Authorization":f"Bearer {st.session_state['token']}"}
    res= requests.post(
        f"{backend_url}/documents/upload",
        files=files,
        headers=headers
    )
    
    if res.status_code==200:
        st.session_state["document_id"]=res.json()["document_id"]
        st.success("document uploaded")
    else:
        st.error("upload failed")
        
        
st.subheader("your documents")
if st.session_state["documents"]:
    selected_doc=st.selectbox(
        "select a document",
        st.session_state["documents"],
        format_func=lambda d: d["document_name"]
    )
    print("*"*30)
    with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
        f_1.write(f"selected doc is{selected_doc['document_id']}")
        f_1.write("\n\n")
    print("selected doc is",selected_doc["document_id"])
    print("*"*30)
    st.session_state["selected_document"]=selected_doc
    document_id=selected_doc["document_id"]
    st.session_state["document_id"]=document_id
    
    if document_id:
        res = requests.get(
            f"{backend_url}/conversations",
            params={"document_id":document_id},
            headers={"Authorization":f"Bearer {st.session_state['token']}"}
        )
        if res.status_code==200:
            st.session_state["conversations"]=res.json()
        else:
            st.session_state["conversations"]=[]
    else:
        st.info("No documents_id found.")

else:
    st.info("No documents found. upload new pdf.")

    
st.subheader("conversations")

options= [{"conversation_id":None,"label": "new conversation"}]

if st.session_state["conversations"]:
    for c in st.session_state["conversations"]:
        options.append({
            "conversation_id":c["conversation_id"],
            "label":f"conversation created at {c['created_at']}"
        })
    
    selected_conv=st.selectbox(
        "select conversation",
        options,
        format_func= lambda c: c["label"]
    )
    print("*"*50)
    with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
        f_1.write(f"selected_conv conversation is {selected_conv}")
        f_1.write("\n\n")
    print("selected_conv conversation is",selected_conv)
    print("*"*50)
    st.session_state["conversation_id"]=selected_conv["conversation_id"]
# else:
#     st.session_state["conversations"]=[]
    
st.subheader("chat")
question=st.text_input("ask question")
if st.button("send") and question:
    headers={
        "Authorization":f"Bearer {st.session_state['token']}",
        "Content-Type":"application/json"
    }
    
    print("*"*50)
    with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
        f_1.write(f"in chat endpoint conversation_id is {st.session_state['conversation_id']}")
        f_1.write("\n\n")
    print("in chat endpoint conversation_id is",st.session_state["conversation_id"])
    print("*"*50)
    print("*"*50)
    with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
        f_1.write(f"in chat endpoint document_id is {st.session_state['document_id']}")
        f_1.write("\n\n")
    print("in chat endpoint document_id is",st.session_state["document_id"])
    print("*"*50)    
    payload={
        "question":question,
        "conversation_id":st.session_state["conversation_id"],
        "document_id":st.session_state["document_id"]
    }
    
    response=requests.post(
        f"{backend_url}/chat",
        headers=headers,
        json=payload,
        stream=True
    )

    answer=""
    
    placeholder=st.empty()
    
    for chunk in response.iter_content(chunk_size=None):
        token=chunk.decode("utf-8")
        answer+=token
        placeholder.markdown(answer)
        
    if st.session_state["conversation_id"] is None:
        st.session_state['conversation_id']=response.headers.get("x-conversation-id")
        print("*"*50)
        with open(r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\backend\error.txt","a") as f_1:
            f_1.write(f"at the end conversation_id is {st.session_state['conversation_id']}")
            f_1.write("\n\n")
        print("at the end conversation_id is",st.session_state["conversation_id"])
        print("*"*50)
        
    st.session_state["chat_history"].append(("user",question))
    st.session_state["chat_history"].append(("assistant",answer))