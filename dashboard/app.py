#!/usr/bin/env python3
"""
Italia Dipendenze · Dashboard Streamlit
Italy Resource & Dependency Map — quanto dipende l'Italia dall'estero.
"""

import streamlit as st
from lab_connectors.branding import apply_branding

st.set_page_config(
    page_title="Italia Dipendenze · Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_branding(
    repo_name="italia-dipendenze",
    repo_url="https://github.com/dataciviclab/italia-dipendenze",
)

pages = {
    "": [
        st.Page("pages/01_Panoramica.py", title="Panoramica", icon="📊", default=True),
    ],
    "Analisi": [
        st.Page("pages/02_Dipendenze.py", title="Dipendenze", icon="🌐"),
        st.Page("pages/03_Commercio.py", title="Commercio", icon="🚢"),
        st.Page("pages/04_Energia.py", title="Energia", icon="⚡"),
    ],
    "Strumenti": [
        st.Page("pages/05_SQL.py", title="Query SQL", icon="🧪"),
    ],
}

pg = st.navigation(pages, position="sidebar")

st.sidebar.markdown("---")
st.sidebar.caption("Fonti: Eurostat NRG_BAL_C · UN Comtrade · FAO — 2020–2024")
st.sidebar.caption(
    "Caveat: valori commerciali in USD · dipendenza fisica solo su prodotti energetici"
)

pg.run()
