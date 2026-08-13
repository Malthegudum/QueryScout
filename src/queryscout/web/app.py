"""Local Streamlit chat interface for QueryScout."""

import streamlit as st

from queryscout.models import QueryScoutResult
from queryscout.session import QueryScoutSession

st.set_page_config(page_title="QueryScout")
st.title("QueryScout")
st.caption("Find statistical data by describing what you need.")

if "queryscout_session" not in st.session_state:
    st.session_state.queryscout_session = QueryScoutSession()
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


def render_result(result: QueryScoutResult) -> None:
    """Render a retrieved dataset inside the chat."""
    st.markdown(f"**Source:** {result.source}")
    st.markdown(f"**Rows:** {result.row_count:,}")
    st.markdown(f"**Columns:** {', '.join(result.columns)}")
    st.dataframe(result.preview(20), use_container_width=True)

    st.download_button(
        "Download CSV",
        data=result.data.to_csv(index=False).encode("utf-8"),
        file_name="data.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("**Reproduce this dataset with Python:**")
    st.code(result.code, language="python")


for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.markdown(message["content"])
        else:
            render_result(message["content"])

prompt = st.chat_input("What data do you want?")

if prompt:
    st.session_state.chat_messages.append(
        {"role": "user", "kind": "text", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Finding and checking data..."):
                response = st.session_state.queryscout_session.send(prompt)

            if isinstance(response, str):
                st.markdown(response)
                assistant_message = {
                    "role": "assistant",
                    "kind": "text",
                    "content": response,
                }
            else:
                render_result(response)
                assistant_message = {
                    "role": "assistant",
                    "kind": "result",
                    "content": response,
                }

            st.session_state.chat_messages.append(assistant_message)
        except Exception as exc:
            message = f"QueryScout could not complete the request: {exc}"
            st.error(message)
            st.session_state.chat_messages.append(
                {"role": "assistant", "kind": "text", "content": message}
            )

with st.sidebar:
    st.header("Session")
    if st.button("New conversation", use_container_width=True):
        st.session_state.queryscout_session.reset()
        st.session_state.chat_messages = []
        st.rerun()
