from h2ogpte import H2OGPTE
import streamlit as st
import os
from dotenv import load_dotenv
import uuid

def main():
    load_dotenv()
    try:
        client = H2OGPTE(
            address=os.getenv("H2OGPTE_ADDRESS"),
            api_key=os.getenv("H2OGPTE_GLOBAL_API_KEY")
        )
    except Exception as e:
        print(e)
    
    # Page configurations
    st.set_page_config(page_title="Chat App", page_icon="📖", layout="centered", initial_sidebar_state="expanded")
    
    st.title(body="Chat with your documents :book:", anchor=False)
    
    # Sidebar configurations
    with st.sidebar:
        st.subheader("Choose file(s) to upload")
        uploaded_files_st = st.file_uploader("Upload your documents here", accept_multiple_files=True, key="sidebar_page", label_visibility="collapsed")
        upload_files_h2o_button = st.button("Upload :arrow_up:", key="button_upload_docs")            
    
        if uploaded_files_st is not None and upload_files_h2o_button:
            st.divider()
            st.subheader("Upload Status", anchor=False)
            with st.spinner("Starting processing documents..."):
                # Create a collection in h2ogpte
                collection_id = client.create_collection(name="Collection_" + str(uuid.uuid4()), description="")
                
            with st.spinner("Uploading documents..."):
                # Upload files to h2ogpte backend
                upload_h2o_ids = []
                for file_st in uploaded_files_st: 
                    upload_h2o_ids.append(client.upload(file_name=file_st.name, file=file_st))

            with st.spinner("Ingesting documents..."):
                # Upload backend files to collection
                client.ingest_uploads(collection_id=collection_id,upload_ids=upload_h2o_ids)
                
            st.success("Successfully processed your documents", icon="✅")
        
        
        
    
    # Delete the collection in h2ogpte
    # client.delete_collections(collection_ids=[collection_id], timeout=30)

if __name__ == "__main__":
    main()