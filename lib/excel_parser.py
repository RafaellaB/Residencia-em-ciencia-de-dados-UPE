from typing import Dict, List, Any
import pandas as pd
import random

COORDINATION_NAMES = [
    'Coordenação Administrativa',
    'Coordenação Técnica',
    'Coordenação Financeira',
    'Coordenação de Projetos',
]

COORDINATION_COLORS = [
    'hsl(221, 83%, 53%)',
    'hsl(160, 84%, 39%)',
    'hsl(38, 92%, 50%)',
    'hsl(340, 82%, 52%)',
]


def generate_sample_data() -> Dict[str, Any]:
    coordinations = [
        { 'name': COORDINATION_NAMES[i], 'projects': p, 'completed': c, 'inProgress': ip, 'budget': b, 'spent': s, 'team': t, 'satisfaction': sat }
        for i, (p, c, ip, b, s, t, sat) in enumerate([
            (24, 18, 6, 850000, 620000, 32, 87),
            (31, 22, 9, 1200000, 980000, 45, 92),
            (18, 15, 3, 600000, 520000, 20, 78),
            (27, 19, 8, 950000, 710000, 38, 85),
        ])
    ]

    months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    monthly = []
    for month in months:
        monthly.append({
            'month': month,
            'coord1': random.randint(60, 100),
            'coord2': random.randint(60, 100),
            'coord3': random.randint(60, 100),
            'coord4': random.randint(60, 100),
        })

    return { 'coordinations': coordinations, 'monthly': monthly }


def _get_value_from_row(row: pd.Series, candidates: List[str]) -> Any:
    for c in candidates:
        if c in row and pd.notna(row[c]):
            return row[c]
    return None


def parse_excel(file) -> Dict[str, Any]:
    """Parse an uploaded Excel file (file-like or bytes) into the dashboard data structure.

    Returns dict with keys: 'coordinations' and 'monthly'. Falls back to sample data on failure.
    """
    try:
        # read all sheets
        x = pd.read_excel(file, sheet_name=None)
    except Exception:
        return generate_sample_data()

    sheet_names = list(x.keys())
    coordinations: List[Dict] = []

    # take up to first 4 sheets as coordination sheets
    for idx, sheet_name in enumerate(sheet_names[:4]):
        df = x[sheet_name]
        if df.empty:
            continue
        row = df.iloc[0]
        coordinations.append({
            'name': COORDINATION_NAMES[idx] if idx < len(COORDINATION_NAMES) else sheet_name,
            'projects': int(_get_value_from_row(row, ['projetos','projects','Projetos']) or 0),
            'completed': int(_get_value_from_row(row, ['concluidos','completed','Concluídos']) or 0),
            'inProgress': int(_get_value_from_row(row, ['em_andamento','in_progress','Em Andamento']) or 0),
            'budget': int(_get_value_from_row(row, ['orcamento','budget','Orçamento']) or 0),
            'spent': int(_get_value_from_row(row, ['gasto','spent','Gasto']) or 0),
            'team': int(_get_value_from_row(row, ['equipe','team','Equipe']) or 0),
            'satisfaction': int(_get_value_from_row(row, ['satisfacao','satisfaction','Satisfação']) or 0),
        })

    # try to find monthly sheet
    monthly_candidates = ['mensal', 'Mensal', 'monthly', 'Monthly']
    monthly_df = None
    for name in monthly_candidates:
        if name in x:
            monthly_df = x[name]
            break

    monthly: List[Dict] = []
    if monthly_df is not None and not monthly_df.empty:
        for _, row in monthly_df.iterrows():
            monthly.append({
                'month': str(_get_value_from_row(row, ['mes','month','Mês']) or ''),
                'coord1': int(_get_value_from_row(row, ['coord1','Coord1']) or 0),
                'coord2': int(_get_value_from_row(row, ['coord2','Coord2']) or 0),
                'coord3': int(_get_value_from_row(row, ['coord3','Coord3']) or 0),
                'coord4': int(_get_value_from_row(row, ['coord4','Coord4']) or 0),
            })

    if len(coordinations) == 0:
        return generate_sample_data()

    if len(monthly) == 0:
        monthly = generate_sample_data()['monthly']

    return { 'coordinations': coordinations, 'monthly': monthly }
