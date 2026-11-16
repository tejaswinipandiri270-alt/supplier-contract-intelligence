import os, requests, streamlit as st

st.set_page_config(
    page_title="Supplier Contract Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Supplier Contract Intelligence Assistant")
st.caption("Ask questions about supplier contracts, renewal dates, notice periods and SLAs.")
api_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
question = st.text_area("Enter your contract question", value="What is the notice period to terminate the CleanCo facilities contract?")
if st.button("Ask assistant", type="primary"):
    with st.spinner("Searching contracts..."):
        try:
            response = requests.post(f"{api_url}/query", json={"question": question}, timeout=180)
            response.raise_for_status()
            data = response.json()
            st.subheader("Answer")
            st.write(data["answer"])
            st.subheader("Retrieval details")
            st.json({"filters_applied": data["filters_applied"], "scores": data["scores"], "retrieved_chunks": data["retrieved_chunks"]})
            st.subheader("Citations")
            for c in data["citations"]:
                with st.expander(f"{c['supplier']} | {c['source']} | {c['clause']}"):
                    st.write(c.get("excerpt", ""))
                    st.caption(f"Chunk: {c['chunk_id']} | Score: {c.get('score')}")
        except Exception as e:
            st.error(f"API request failed: {e}. Check that FastAPI is running.")
st.info("For API documentation and direct testing, open http://localhost:8000/docs")
