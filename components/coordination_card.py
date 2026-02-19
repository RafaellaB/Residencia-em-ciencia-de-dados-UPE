import streamlit as st


def render_coordination_card(data: dict, index: int = 0, color: str | None = None) -> None:
    name = data.get("name", "Coordenação")
    completed = data.get("completed", 0)
    in_progress = data.get("inProgress", 0)
    team = data.get("team", 0)
    projects = data.get("projects", completed + in_progress)
    satisfaction = data.get("satisfaction", 0)
    spent = data.get("spent", 0)
    budget = data.get("budget", 0)

    budget_usage = int((spent / budget) * 100) if budget else 0

    card = st.container()
    with card:
        html = (
            f"<div style='border-radius:12px;border:1px solid #e6e6e6;padding:14px;background:#fff;'>"
            f"<div style='height:6px;background:{color or '#ddd'};border-radius:6px;margin:-14px -14px 8px -14px;'></div>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
            f"<strong>{name}</strong>"
            f"<span style='background:{color or '#ddd'};color:#fff;padding:4px 8px;border-radius:999px;font-size:12px;'>{satisfaction}% satisfação</span>"
            "</div>"
            "</div>"
        )
        st.markdown(html, unsafe_allow_html=True)

        cols = st.columns(4)
        cols[0].markdown(f"**{completed}**\n\nConcluídos")
        cols[1].markdown(f"**{in_progress}**\n\nEm andamento")
        cols[2].markdown(f"**{team}**\n\nEquipe")
        cols[3].markdown(f"**{projects}**\n\nTotal projetos")

        # st.progress expects 0..1
        prog_val = (budget_usage / 100) if budget else 0
        st.progress(prog_val)
        st.caption(f"R$ {spent:,} gasto • R$ {budget:,} total")
