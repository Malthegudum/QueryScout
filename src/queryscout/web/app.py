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
    st.markdown(f"**Source:** {result.source}")
    st.markdown(f"**Rows:** {result.row_count:,}")
    st.markdown(f"**Columns:** {', '.join(result.columns)}")
    st.dataframe(result.preview(20), use_container_width=True)


for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.markdown(message["content"])
        else:
            render_result(message["content"])
