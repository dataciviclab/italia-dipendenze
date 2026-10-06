"""Query SQL — Interroga clean layer del repo."""

from lab_connectors.duckdb.sql_page import render_sql_query
from sources import PREFIX, TOOLKIT_YEAR, load_registry_obj

registry = load_registry_obj()

render_sql_query(
    registry=registry,
    prefix=PREFIX,
    default_slug="comtrade_bilateral",
    years=[TOOLKIT_YEAR],
    title="🧪 Query SQL",
    description=(
        "Interroga i dati clean di Italia Dipendenze. Usa ``clean_input`` come tabella virtuale. "
    ),
)
