from h2ogpte import H2OGPTE
import streamlit as st
import os
from dotenv import load_dotenv
import uuid


def set_page_config():
    """
    Page configurations
    """
    st.set_page_config(
        page_title="Chat App",
        page_icon="📖",
        layout="centered",
        initial_sidebar_state="expanded",
    )


def initialize_session_state(client: H2OGPTE):
    """
    Session state initializations
    """
    if "collection_id" not in st.session_state:
        st.session_state.collection_id = client.create_collection(
            name="Collection_" + str(uuid.uuid4()), description=""
        )

    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = client.create_chat_session(
            st.session_state.collection_id
        )

    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    if "uploaded_docs" not in st.session_state:
        st.session_state.uploaded_docs = []


def display_page_details():
    """
    Display page details: title
    """
    st.title(body="Chat with your documents :book:", anchor=False)


def display_sidebar(client: H2OGPTE):
    """
    Sidebar configurations
    """
    with st.sidebar:
        st.subheader("Choose file(s) to upload")
        uploaded_files_st = st.file_uploader(
            "Upload your documents here",
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        upload_files_h2o_button = st.button("Upload :arrow_up:")

        if uploaded_files_st is not None and upload_files_h2o_button:
            st.divider()
            st.subheader("Upload status", anchor=False)

            with st.spinner("Uploading documents..."):
                upload_h2o_ids = []
                for file_st in uploaded_files_st:

                    # Only upload new documents
                    if file_st.name not in st.session_state.uploaded_docs:

                        # Upload files to h2ogpte backend
                        upload_h2o_id = client.upload(
                            file_name=file_st.name, file=file_st
                        )
                        upload_h2o_ids.append(upload_h2o_id)

                        # Append uploaded h2o docs to session state list
                        st.session_state.uploaded_docs.append(file_st.name)

            with st.spinner("Ingesting documents..."):
                # Upload backend files to collection
                client.ingest_uploads(
                    collection_id=st.session_state.collection_id,
                    upload_ids=upload_h2o_ids,
                )

            st.success("Successfully processed your documents", icon="✅")

        if len(st.session_state.uploaded_docs) is not 0:
            st.divider()
            st.subheader("Uploaded documents")
            for doc in st.session_state.uploaded_docs:
                st.markdown("- " + doc)

        # Display clear chat button if conversation history is NOT empty
        if len(st.session_state.conversation) is not 0:
            clear_chat_button = st.button("🗑️ Clear chat history")
            if clear_chat_button:
                st.session_state.conversation.clear()


def display_convo_history():
    """
    Display conversation history in session state
    """
    for conversation in st.session_state.conversation:
        if conversation["role"] == "user":
            with st.chat_message("user"):
                st.markdown(conversation["message"])
        else:
            with st.chat_message("ai"):
                st.markdown(conversation["message"])


def display_chat(client: H2OGPTE):
    user_query = st.chat_input("Ask a question...")
    if user_query:
        # Display user query
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.conversation.append({"role": "user", "message": user_query})

        # Check number of documents in the collection
        num_docs_in_collection = client.count_documents_in_collection(
            st.session_state.collection_id
        )

        # Assign rag approach
        if num_docs_in_collection > 0:
            rag_approach = "rag"
        else:
            rag_approach = "llm_only"

        with client.connect(st.session_state.chat_session_id) as chat_session:
            response = chat_session.query(
                message=user_query,
                llm="gpt-4-1106-preview",
                llm_args={
                    "temperature": 0,
                },
                rag_config={
                    "rag_type": rag_approach,
                },
                timeout=None,
            )
            # Display LLM response
            with st.chat_message("ai"):
                st.markdown(response.content)
            st.session_state.conversation.append(
                {
                    "role": "ai",
                    "message": response.content,
                }
            )


def main():
    load_dotenv()
    try:
        client = H2OGPTE(
            address=os.getenv("H2OGPTE_ADDRESS"),
            api_key=os.getenv("H2OGPTE_GLOBAL_API_KEY"),
        )
    except Exception as e:
        print(f"ERROR DETAILS ({e})")

    # Page configurations
    set_page_config()

    # Session state initializations
    initialize_session_state(client)

    # Page details
    display_page_details()

    # Sidebar configurations
    display_sidebar(client)

    # Display conversation history in session state
    display_convo_history()

    # Chat feature
    display_chat(client)

    # st.session_state  # display session state for degugging

    # Delete the collection in h2ogpte
    # client.delete_collections([st.session_state.collection_id])


if __name__ == "__main__":
    main()
