import streamlit as st


def render_kpi(title: str, value, subtitle: str | None = None, trend: float | None = None, color: str | None = None) -> None:
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(f"**{title}**")
        st.markdown(f"### {value}")
        if subtitle:
            st.caption(subtitle)
    with cols[1]:
        if trend is not None:
            sign = "↑" if trend >= 0 else "↓"
            trend_color = "#16a34a" if trend >= 0 else "#dc2626"
            st.markdown(f"<div style='text-align:right;color:{trend_color};font-weight:600'>{sign} {abs(trend)}%</div>", unsafe_allow_html=True)
        else:
            st.write(" ")
