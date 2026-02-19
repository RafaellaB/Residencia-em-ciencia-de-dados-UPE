"""Busca dados em planilhas Google (varias localizacoes online).

Requisitos:
- criar uma Service Account no Google Cloud e baixar o JSON de credenciais
- compartilhar as planilhas com o e-mail da service account
- definir a variavel de ambiente `GOOGLE_SERVICE_ACCOUNT_FILE` apontando para o JSON

Uso:
from busca_dados import sheet_to_df, fetch_multiple, fetch_coord_data
df = sheet_to_df('https://docs.google.com/spreadsheets/d/...')
docs = ['sheet_url_or_id_1', 'sheet_url_or_id_2']
all_dfs = fetch_multiple(docs)
"""
from typing import Optional, Union, List, Dict
import os
import unicodedata

from google.oauth2.service_account import Credentials
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_service_account_file(creds_path: Optional[str]) -> str:
    if creds_path:
        return creds_path
    env = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if env:
        return env
    raise RuntimeError(
        "Caminho para JSON da service account nao informado. Defina `GOOGLE_SERVICE_ACCOUNT_FILE` ou passe `creds_path`"
    )


def get_gspread_client(creds_path: Optional[str] = None) -> gspread.Client:
    """Cria e retorna um cliente gspread autenticado por service account."""
    sa_file = _get_service_account_file(creds_path)
    creds = Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    return gspread.authorize(creds)


def _open_sheet(client: gspread.Client, identifier: str) -> gspread.Spreadsheet:
    if identifier.startswith("http://") or identifier.startswith("https://"):
        return client.open_by_url(identifier)
    return client.open_by_key(identifier)


def sheet_to_df(
    sheet_id_or_url: str,
    worksheet: Union[int, str] = 0,
    creds_path: Optional[str] = None,
) -> pd.DataFrame:
    """Retorna a worksheet especificada como um `pandas.DataFrame`.

    - `sheet_id_or_url`: URL completa da planilha ou seu `spreadsheetId`.
    - `worksheet`: indice (int) ou nome (str) da aba. Default 0 (primeira aba).
    - `creds_path`: caminho para JSON da service account (opcional).
    """
    client = get_gspread_client(creds_path)
    sh = _open_sheet(client, sheet_id_or_url)

    if isinstance(worksheet, int):
        ws = sh.get_worksheet(worksheet)
    else:
        ws = sh.worksheet(worksheet)

    df = get_as_dataframe(ws, evaluate_formulas=True, header=0)
    if df is None:
        return pd.DataFrame()
    return df


def fetch_multiple(
    sources: List[str], worksheet: Union[int, str] = 0, creds_path: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """Busca varias fontes e retorna um dicionario {source: DataFrame}."""
    client = get_gspread_client(creds_path)
    result: Dict[str, pd.DataFrame] = {}
    for src in sources:
        try:
            sh = _open_sheet(client, src)
            if isinstance(worksheet, int):
                ws = sh.get_worksheet(worksheet)
            else:
                ws = sh.worksheet(worksheet)
            df = get_as_dataframe(ws, evaluate_formulas=True, header=0) or pd.DataFrame()
            result[src] = df
        except Exception as e:
            result[src] = pd.DataFrame()
            result[src].attrs["error"] = str(e)
    return result


def _normalize_title(t: str) -> str:
    t = (t or '').strip().lower()
    t = unicodedata.normalize('NFKD', t)
    t = ''.join([c for c in t if not unicodedata.combining(c)])
    return t


def _find_sheet_by_title(sh: gspread.Spreadsheet, title: str) -> Optional[gspread.Worksheet]:
    norm = _normalize_title(title)
    for ws in sh.worksheets():
        if _normalize_title(ws.title) == norm:
            return ws
    return None


def fetch_coord_data(
    spreadsheet: str,
    pos_sheet_name: str = 'pós lato sensu',
    inov_sheet_name: str = 'inov',
    creds_path: Optional[str] = None,
) -> pd.DataFrame:
    """Busca as duas abas (Pos e Inov) e concatena em um unico DataFrame.

    - `spreadsheet`: URL ou spreadsheetId
    - nomes das abas podem ser ajustados por `pos_sheet_name` e `inov_sheet_name`
    - retorna DataFrame concatenado (linhas de ambas as abas)
    """
    client = get_gspread_client(creds_path)
    sh = _open_sheet(client, spreadsheet)

    ws_pos = _find_sheet_by_title(sh, pos_sheet_name)
    ws_inov = _find_sheet_by_title(sh, inov_sheet_name)

    dfs = []
    if ws_pos is not None:
        df_pos = get_as_dataframe(ws_pos, evaluate_formulas=True, header=0)
        if df_pos is None:
            df_pos = pd.DataFrame()
        dfs.append(df_pos)
    if ws_inov is not None:
        df_inov = get_as_dataframe(ws_inov, evaluate_formulas=True, header=0)
        if df_inov is None:
            df_inov = pd.DataFrame()
        dfs.append(df_inov)

    if not dfs:
        raise RuntimeError(f"Nenhuma aba encontrada com os nomes: {pos_sheet_name}, {inov_sheet_name}")

    combined = pd.concat(dfs, ignore_index=True, sort=False)
    return combined


if __name__ == "__main__":
    print("Nenhuma planilha de exemplo configurada. Edite o script com URLs/IDs.")