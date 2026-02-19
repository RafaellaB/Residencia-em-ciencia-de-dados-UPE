import io
import os
import unicodedata
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from busca_dados import fetch_coord_data


DEFAULT_SPREADSHEET = (
    "https://docs.google.com/spreadsheets/d/1pUa66-abnwnE0qQ_34YX4qFmLUtTnNIwk4Jm59OK_us/edit?gid=585129450#gid=585129450"
)


def parse_int_series(s):
    """Converte série de strings para int, tratando valores inválidos."""
    if s is None or len(s) == 0:
        return pd.Series([0] * len(s))
    return pd.to_numeric(
        s.fillna('0').astype(str).str.replace(r'[^0-9]', '', regex=True).replace('', '0'),
        errors='coerce'
    ).fillna(0).astype(int)


def parse_money_series(s):
    """Converte série de strings monetárias para float."""
    if s is None or len(s) == 0:
        return pd.Series([0.0] * len(s))
    return (
        s.fillna('').astype(str)
        .str.replace(r'[^0-9,.-]', '', regex=True)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .replace('', '0')
        .astype(float)
    )


def _normalize_col(name: str) -> str:
    text = (name or '').strip().lower()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])
    out = []
    prev_underscore = False
    for ch in text:
        if ch.isalnum():
            out.append(ch)
            prev_underscore = False
        else:
            if not prev_underscore:
                out.append('_')
                prev_underscore = True
    return ''.join(out).strip('_')


def _has_tokens(col_norm: str, *tokens: str) -> bool:
    return all(token in col_norm for token in tokens)


def main() -> None:
    st.set_page_config(page_title="Dashboard Coordenações UPE", layout="wide")

    st.markdown(
        """
        <style>
            .metric-card {
                background-color: #f0f2f6;
                border-radius: 10px;
                padding: 20px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .chart-card {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            h1 {
                color: #1f1f1f;
                text-align: center;
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            h2 {
                color: #333333;
                margin-top: 30px;
                margin-bottom: 20px;
                font-size: 1.8em;
                border-bottom: 3px solid #0068C9;
                padding-bottom: 10px;
            }
            h3 {
                color: #555555;
                margin-top: 20px;
                margin-bottom: 15px;
                font-size: 1.3em;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Dashboard PROPEGI")

    df = None
    spreadsheet = os.getenv('SPREADSHEET_URL') or os.getenv('SPREADSHEET_ID') or DEFAULT_SPREADSHEET
    creds_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')

    # Cache curto para acelerar carregamento sem atrasar atualizacoes
    @st.cache_data(ttl=30)
    def load_sheet_cached(spreadsheet_url: str, creds: Optional[str]):
        return fetch_coord_data(spreadsheet_url, creds_path=creds)

    if spreadsheet:
        if creds_path:
            try:
                df = load_sheet_cached(spreadsheet, creds_path)
                df.columns = [c.strip() for c in df.columns]
            except Exception:
                pass
        else:
            # Sem credenciais, tenta leitura publica por nome de aba
            def _extract_id(s: str) -> str:
                if s.startswith('http'):
                    try:
                        parts = s.split('/d/')
                        id_part = parts[1].split('/')[0]
                        return id_part
                    except Exception:
                        return s
                return s

            def public_sheet_df(spreadsheet_url_or_id: str, sheet_name: str):
                sid = _extract_id(spreadsheet_url_or_id)
                sheet_q = quote_plus(sheet_name)
                url = f'https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&sheet={sheet_q}'
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
                return pd.read_csv(io.StringIO(resp.text), dtype=str)

            try:
                sheets_to_try = ['pós lato sensu', 'inov']
                dfs_public = []
                for name in sheets_to_try:
                    try:
                        pdf = public_sheet_df(spreadsheet, name)
                        if not pdf.empty:
                            dfs_public.append(pdf)
                    except Exception:
                        pass

                if dfs_public:
                    df = pd.concat(dfs_public, ignore_index=True, sort=False)
                    df.columns = [c.strip() for c in df.columns]
            except Exception:
                pass

    if df is None:
        dados_csv = Path(__file__).parent / 'dados_coordenacoes.csv'
        if dados_csv.exists():
            try:
                df = pd.read_csv(dados_csv, sep=';', dtype=str, encoding='utf-8')
                df.columns = [c.strip() for c in df.columns]
            except Exception:
                pass

    if df is None:
        st.error('Nao foi possivel carregar dados da planilha online nem do CSV local.')
        st.info(
            'Verifique se o arquivo no Drive e uma planilha Google (nao XLSX) e se a '
            'service account tem acesso a ela.'
        )
        st.stop()

    if df is not None:
        tab_pos, tab_inov = st.tabs(["Pós Lato-Sensu", "Inovação"])

        with tab_pos:
            st.markdown("## Coordenação de Pós Lato-Sensu")

            col_unidade_pos = None
            col_denom_pos = None
            col_status_pos = None
            col_alunos_pos = None
            col_remuneracao_pos = None

            for col in df.columns:
                col_lower = _normalize_col(col)
                if 'unidade_pos' in col_lower or _has_tokens(col_lower, 'unidade', 'pos'):
                    col_unidade_pos = col
                if 'denominacao_pos' in col_lower or _has_tokens(col_lower, 'denominacao', 'pos'):
                    col_denom_pos = col
                if _has_tokens(col_lower, 'status', 'curso', 'pos') or _has_tokens(col_lower, 'status', 'pos'):
                    col_status_pos = col
                if _has_tokens(col_lower, 'alunos', 'matriculados', 'pos') or _has_tokens(col_lower, 'alunos', 'pos'):
                    col_alunos_pos = col
                if _has_tokens(col_lower, 'remuneracao', 'pos') or _has_tokens(col_lower, 'total', 'remuner', 'pos'):
                    col_remuneracao_pos = col

            with st.sidebar:
                st.markdown("### Filtro - Pós Lato-Sensu")
                unidade_pos_sel = None
                if col_unidade_pos:
                    unidades = df[col_unidade_pos].dropna().unique().tolist()
                    unidades = [u for u in unidades if str(u).strip() != '']
                    unidades = ['Todos'] + sorted(unidades)
                    unidade_pos_sel = st.selectbox('UNIDADE (Pós)', unidades, key='unidade_pos')

            df_pos = df.copy()
            if unidade_pos_sel and unidade_pos_sel != 'Todos' and col_unidade_pos:
                df_pos = df_pos[df_pos[col_unidade_pos].astype(str) == unidade_pos_sel]

            if col_status_pos:
                df_andamento = df_pos[
                    df_pos[col_status_pos].astype(str).str.contains('andamento', case=False, na=False)
                ]
                count_andamento = len(df_andamento)
                st.metric('Cursos em Andamento', count_andamento)

            if col_denom_pos and col_alunos_pos:
                df_top = df_pos[[col_denom_pos, col_alunos_pos]].copy()
                df_top.columns = ['Denominacao', 'Alunos']
                df_top = df_top[df_top['Denominacao'].notna()]
                df_top = df_top[df_top['Alunos'].notna()]
                df_top['Alunos'] = parse_int_series(df_top['Alunos'])
                df_top = df_top[df_top['Alunos'] > 0]
                df_top = df_top.sort_values('Alunos', ascending=False).head(10)

                if not df_top.empty:
                    st.markdown("### Top 10 Denominações com Mais Alunos Matriculados")
                    fig2 = px.bar(
                        df_top,
                        x='Alunos',
                        y='Denominacao',
                        orientation='h',
                        title='',
                        labels={'Alunos': 'Quantidade de Alunos', 'Denominacao': ''},
                        color='Alunos',
                        color_continuous_scale=['#08306b', '#08519c', '#2171b5', '#4292c6'],
                    )
                    fig2.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        showlegend=False,
                        height=400,
                        margin=dict(l=0, r=0, t=0, b=0),
                    )
                    fig2.update_traces(marker=dict(line=dict(color='#0b3d91', width=1)))
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Sem dados de alunos para exibir.")

        with tab_inov:
            st.markdown("## Coordenação de Inovação")

            col_ano_inov = None
            col_unidade_inov = None
            col_via_inov = None
            col_cidade_inov = None
            col_natureza_inov = None
            col_projeto_inov = None

            for col in df.columns:
                col_lower = _normalize_col(col)
                if col_lower == 'ano_inov' or _has_tokens(col_lower, 'ano', 'inov'):
                    col_ano_inov = col
                if col_lower == 'unidade' or _has_tokens(col_lower, 'unidade', 'inov'):
                    col_unidade_inov = col
                if col_lower == 'via_inov' or _has_tokens(col_lower, 'via', 'inov'):
                    col_via_inov = col
                if col_lower == 'cidade' or _has_tokens(col_lower, 'cidade', 'inov'):
                    col_cidade_inov = col
                if col_lower == 'natureza_inov' or _has_tokens(col_lower, 'natureza', 'inov'):
                    col_natureza_inov = col
                if col_lower == 'projeto' or _has_tokens(col_lower, 'projeto', 'inov'):
                    col_projeto_inov = col

            with st.sidebar:
                st.markdown("### Filtro - Inovação")
                ano_inov_sel = None
                if col_ano_inov:
                    anos = df[col_ano_inov].dropna().unique().tolist()
                    anos = [a for a in anos if str(a).strip() != '' and str(a).strip() != 'nan']
                    try:
                        anos = sorted([int(a) for a in anos])
                        anos = [str(a) for a in anos]
                    except Exception:
                        anos = sorted(anos)
                    anos = ['Todos'] + anos
                    ano_inov_sel = st.selectbox('Ano de Criação (Inovação)', anos, key='ano_inov')

            df_inov = df.copy()
            df_inov = df_inov[df_inov[col_projeto_inov].notna()] if col_projeto_inov else df_inov

            if ano_inov_sel and ano_inov_sel != 'Todos' and col_ano_inov:
                df_inov = df_inov[df_inov[col_ano_inov].astype(str) == str(ano_inov_sel)]

            kpi_via_col1, kpi_via_col2 = st.columns([1, 1.5])

            if col_unidade_inov:
                df_per_unit = df_inov[df_inov[col_unidade_inov].notna()].copy()
                df_per_unit = df_per_unit[df_per_unit[col_unidade_inov].astype(str).str.strip() != '']
                count_per_unit = df_per_unit.groupby(col_unidade_inov).size().reset_index(name='Quantidade')
                total_projetos = count_per_unit['Quantidade'].sum()

                with kpi_via_col1:
                    st.metric('Total de Projetos', total_projetos)

            if col_via_inov:
                df_per_via = df_inov[df_inov[col_via_inov].notna()].copy()
                df_per_via = df_per_via[df_per_via[col_via_inov].astype(str).str.strip() != '']
                count_per_via = df_per_via.groupby(col_via_inov).size().reset_index(name='Quantidade')
                count_per_via = count_per_via.sort_values('Quantidade', ascending=False)

                with kpi_via_col2:
                    if not count_per_via.empty:
                        st.markdown("### Projetos por Via")
                        fig4 = px.bar(
                            count_per_via,
                            x=col_via_inov,
                            y='Quantidade',
                            title='',
                            labels={'Quantidade': 'Quantidade de Projetos', col_via_inov: 'Via'},
                            color='Quantidade',
                            color_continuous_scale=['#08306b', '#08519c', '#2171b5', '#4292c6'],
                        )
                        fig4.update_layout(
                            showlegend=False,
                            height=300,
                            margin=dict(l=0, r=0, t=0, b=0),
                        )
                        fig4.update_traces(marker=dict(line=dict(color='#0b3d91', width=1)))
                        st.plotly_chart(fig4, use_container_width=True)

            st.markdown("### Distribuição de Projetos por Unidade")
            if col_unidade_inov:
                df_per_unit = df_inov[df_inov[col_unidade_inov].notna()].copy()
                df_per_unit = df_per_unit[df_per_unit[col_unidade_inov].astype(str).str.strip() != '']
                count_per_unit = df_per_unit.groupby(col_unidade_inov).size().reset_index(name='Quantidade')
                count_per_unit = count_per_unit.sort_values('Quantidade', ascending=True)

                if not count_per_unit.empty:
                    fig3 = px.bar(
                        count_per_unit,
                        x='Quantidade',
                        y=col_unidade_inov,
                        orientation='h',
                        title='',
                        labels={'Quantidade': 'Quantidade de Projetos', col_unidade_inov: 'Unidade'},
                        color='Quantidade',
                        color_continuous_scale=['#08306b', '#08519c', '#2171b5', '#4292c6'],
                    )
                    fig3.update_layout(
                        showlegend=False,
                        height=350,
                        margin=dict(l=0, r=0, t=0, b=0),
                    )
                    fig3.update_traces(marker=dict(line=dict(color='#0b3d91', width=1)))
                    st.plotly_chart(fig3, use_container_width=True)

            cidade_nat_col1, cidade_nat_col2 = st.columns(2)

            if col_cidade_inov:
                df_per_city = df_inov[df_inov[col_cidade_inov].notna()].copy()
                df_per_city = df_per_city[df_per_city[col_cidade_inov].astype(str).str.strip() != '']
                count_per_city = df_per_city.groupby(col_cidade_inov).size().reset_index(name='Quantidade')
                count_per_city = count_per_city.sort_values('Quantidade', ascending=False).head(15)

                with cidade_nat_col1:
                    if not count_per_city.empty:
                        st.markdown("### Top 15 Cidades com Mais Projetos")
                        fig5 = px.bar(
                            count_per_city,
                            x='Quantidade',
                            y=col_cidade_inov,
                            orientation='h',
                            title='',
                            labels={'Quantidade': 'Quantidade de Projetos', col_cidade_inov: 'Cidade'},
                            color='Quantidade',
                            color_continuous_scale=['#08306b', '#08519c', '#2171b5', '#4292c6'],
                        )
                        fig5.update_layout(
                            yaxis={'categoryorder': 'total ascending'},
                            showlegend=False,
                            height=400,
                            margin=dict(l=0, r=0, t=0, b=0),
                        )
                        fig5.update_traces(marker=dict(line=dict(color='#0b3d91', width=1)))
                        st.plotly_chart(fig5, use_container_width=True)

            if col_natureza_inov:
                df_per_nat = df_inov[df_inov[col_natureza_inov].notna()].copy()
                df_per_nat = df_per_nat[df_per_nat[col_natureza_inov].astype(str).str.strip() != '']
                count_per_nat = df_per_nat.groupby(col_natureza_inov).size().reset_index(name='Quantidade')
                count_per_nat = count_per_nat.sort_values('Quantidade', ascending=False)

                with cidade_nat_col2:
                    if not count_per_nat.empty:
                        st.markdown("### Projetos por Natureza")
                        fig6 = px.bar(
                            count_per_nat,
                            x=col_natureza_inov,
                            y='Quantidade',
                            title='',
                            labels={'Quantidade': 'Quantidade de Projetos', col_natureza_inov: 'Natureza'},
                            color='Quantidade',
                            color_continuous_scale=['#08306b', '#08519c', '#2171b5', '#4292c6'],
                        )
                        fig6.update_layout(
                            showlegend=False,
                            height=400,
                            margin=dict(l=0, r=0, t=0, b=0),
                        )
                        fig6.update_traces(marker=dict(line=dict(color='#0b3d91', width=1)))
                        st.plotly_chart(fig6, use_container_width=True)


if __name__ == "__main__":
    main()