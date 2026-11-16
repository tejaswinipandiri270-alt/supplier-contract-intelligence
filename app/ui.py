
import os
import requests
import streamlit as st

st.set_page_config(
    page_title="Supplier Contract Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Supplier Contract Intelligence Assistant")

st.caption(
    "Ask questions about supplier contracts, renewal dates, "
    "notice periods and SLAs."
)

api_url = os.getenv(
    "API_URL",
    "http://localhost:8000"
).rstrip("/")

question = st.text_area(
    "Enter your contract question",
    value="What is the notice period to terminate the CleanCo facilities contract?"
)

if st.button("Ask Assistant", type="primary"):

    if not question.strip():
        st.warning("Please enter a question.")

    else:
        with st.spinner("Searching supplier contracts..."):

            try:
                response = requests.post(
                    f"{api_url}/query",
                    json={"question": question},
                    timeout=180
                )

                response.raise_for_status()
                data = response.json()

                # Display answer
                st.subheader("Answer")
                st.markdown(
                    data.get("answer", "No answer returned.")
                )

                # Display source citations only
                citations = data.get("citations", [])

                if citations:
                    st.subheader("Source Citations")

                    for citation in citations:

                        with st.expander(
                            f"{citation.get('supplier', 'Unknown')} | "
                            f"{citation.get('source', 'Unknown')} | "
                            f"{citation.get('clause', 'Unknown')}"
                        ):
                            st.write(
                                citation.get("excerpt", "")
                            )

                else:
                    st.info("No source citations returned.")

            except requests.exceptions.RequestException as e:
                st.error(f"API connection failed: {e}")

st.caption("Powered by FastAPI, Amazon OpenSearch and Azure AI Foundry.")
