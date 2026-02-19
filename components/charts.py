from typing import Dict, List
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd


def render_performance_monthly(monthly: List[Dict], coordination_names: List[str], colors: List[str]) -> None:
    if not monthly:
        st.info("Sem dados mensais")
        return

    df = pd.DataFrame(monthly)
    fig = go.Figure()
    for i, name in enumerate(coordination_names):
        key = f"coord{i+1}"
        if key in df:
            fig.add_trace(go.Scatter(x=df["month"], y=df[key], mode="lines", name=name,
                                     line=dict(color=colors[i % len(colors)]), fill='tozeroy'))

    fig.update_layout(margin=dict(t=30, b=20, l=0, r=0), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)


def render_budget_pie(coordinations: List[Dict], colors: List[str]) -> None:
    # Use bar chart instead of pie to show budget distribution
    if not coordinations:
        st.info("Sem dados de coordenações")
        return
    labels = [c["name"].replace("Coordenação ", "") for c in coordinations]
    values = [c.get("budget", 0) for c in coordinations]
    df = pd.DataFrame({"coord": labels, "budget": values})
    fig = px.bar(df, x="coord", y="budget", color="coord", color_discrete_sequence=colors, title="Distribuição de Orçamento (barra)")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_projects_by_coordination(coordinations: List[Dict], colors: List[str]) -> None:
    names = [c["name"].replace("Coordenação ", "Coord. ") for c in coordinations]
    concluido = [c.get("completed", 0) for c in coordinations]
    andamento = [c.get("inProgress", 0) for c in coordinations]
    df = pd.DataFrame({"name": names, "Concluídos": concluido, "Em Andamento": andamento})
    fig = go.Figure(data=[
        go.Bar(name='Concluídos', x=df['name'], y=df['Concluídos'], marker_color='rgb(22,163,74)'),
        go.Bar(name='Em Andamento', x=df['name'], y=df['Em Andamento'], marker_color='rgb(245,158,11)')
    ])
    fig.update_layout(barmode='group', margin=dict(t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)


def render_team_size(coordinations: List[Dict], colors: List[str]) -> None:
    names = [c["name"].replace("Coordenação ", "Coord. ") for c in coordinations]
    team = [c.get("team", 0) for c in coordinations]
    fig = go.Figure(go.Bar(x=team, y=names, orientation='h', marker_color=colors))
    fig.update_layout(margin=dict(t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)


def render_all(data: Dict, coordination_names: List[str] | None = None, colors: List[str] | None = None) -> None:
    coords = data.get('coordinations', [])
    if coordination_names is None:
        coordination_names = [c['name'].replace('Coordenação ', 'Coord. ') for c in coords]
    if colors is None:
        # fallback palette
        colors = px.colors.qualitative.Plotly

    col1, col2 = st.columns(2)
    with col1:
        st.subheader('Performance Mensal')
        render_performance_monthly(data.get('monthly', []), coordination_names, colors)

    with col2:
        st.subheader('Distribuição de Orçamento')
        render_budget_pie(coords, colors)

    st.subheader('Projetos por Coordenação')
    render_projects_by_coordination(coords, colors)

    st.subheader('Tamanho da Equipe')
    render_team_size(coords, colors)
