import re
import unicodedata
from datetime import datetime, date, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestionnaire FDS & Stocks QHSE",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS personnalisé léger pour moderniser les cartes, le bandeau et l'espacement ---
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .hero-banner {
        background: linear-gradient(135deg, #145A32 0%, #1E8449 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.4rem;
        box-shadow: 0 4px 14px rgba(20, 90, 50, 0.18);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .hero-banner p {
        margin: 0.35rem 0 0 0;
        font-size: 0.98rem;
        color: #E8F5E9;
    }
    div[data-testid="stMetric"] {
        background-color: #27AE60;
        border: 1px solid #1E8449;
        border-left: 5px solid #145A32;
        padding: 0.9rem 1.1rem;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        color: #E8F8F5 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

TODAY = date.today()

TRANSLATIONS = {
    "fr": {
        "lang_label": "🌐 Langue / Language",
        "banner_title": "🧪 Gestionnaire FDS & Stocks Chimiques",
        "banner_sub": "Suivi des réactifs, alertes de péremption, fournisseurs et fiches de données de sécurité (QHSE)",
        "init_log": "Initialisation du stock démo.",
        "import_header": "📥 Import de données",
        "upload_label": "Choisir un fichier Excel ou CSV",
        "import_log": "Import de '{name}' ({n} lignes).",
        "import_ok": "Importé : {name}",
        "import_err": "Erreur lors de l'import : {err}",
        "reset_btn": "🔄 Réinitialiser la démo",
        "reset_log": "Réinitialisation du tableau sur les données démo.",
        "hist_header": "🕒 Historique des mises à jour",
        "note_label": "Ajouter une note de suivi",
        "note_placeholder": "Ex: Vérification lot HCl...",
        "note_btn": "✍️ Enregistrer la note",
        "note_prefix": "Note",
        "clear_hist_btn": "🗑️ Effacer l'historique",
        "no_hist": "Aucune modification enregistrée.",
        "kpi_products": "📦 Produits en stock",
        "kpi_expiry": "⚠️ Alertes péremption",
        "kpi_low": "📉 Stock bas",
        "kpi_suppliers": "🏭 Fournisseurs",
        "tab_stock": "📋 Inventaire & Ajout",
        "tab_analyse": "📊 Analyses & Graphiques",
        "add_expander": "➕ Ajouter un nouveau produit manuellement",
        "f_product": "Produit *",
        "f_cas": "Réf. CAS",
        "f_cat": "Catégorie",
        "f_supplier": "Fournisseur",
        "f_qty": "Quantité (L/kg)",
        "f_min": "Seuil min.",
        "f_exp": "Date péremption",
        "f_danger": "Pictogramme / Danger",
        "f_fds": "Lien FDS",
        "add_btn": "Ajouter au stock",
        "warn_no_name": "Merci d'indiquer au moins le nom du produit.",
        "add_log": "Ajout de '{prod}' ({qty} L/kg, {supp}).",
        "add_ok": "« {prod} » ajouté avec succès !",
        "search_label": "🔎 Rechercher (produit, CAS, fournisseur)",
        "filter_supp": "🏭 Filtrer par fournisseur",
        "filter_status": "📌 Filtrer par statut",
        "all_option": "Tous",
        "open_fds": "📄 Ouvrir FDS",
        "chart_cat": "**Quantité totale par catégorie**",
        "chart_status": "**Nombre de produits par statut**",
        "chart_status_col": "Nombre de produits",
        "chart_supp": "**Quantité totale par fournisseur**",
        "no_data_chart": "Aucune donnée à analyser avec les filtres actuels.",
        "status_expired": "🔴 Périmé",
        "status_soon": "🟠 Expire < 30j",
        "status_low": "🟡 Stock bas",
        "status_ok": "🟢 Conforme",
        "def_product_1": "Éthanol 96%",
        "def_cat_1": "Solvant",
        "def_product_2": "Acide chlorhydrique 37%",
        "def_cat_2": "Acide",
        "def_danger_1": "🔥 Inflammable",
        "def_danger_2": "🧪 Corrosif",
        "def_supplier_na": "Non spécifié",
        "def_cat_other": "Autre",
        "def_product_na": "Produit sans nom",
        "def_danger_check": "⚠️ À vérifier",
    },
    "en": {
        "lang_label": "🌐 Language / Langue",
        "banner_title": "🧪 SDS & Chemical Stock Manager",
        "banner_sub": "Chemical inventory tracking, expiration alerts, suppliers, and Safety Data Sheets (QHSE)",
        "init_log": "Demo stock initialized.",
        "import_header": "📥 Data Import",
        "upload_label": "Choose an Excel or CSV file",
        "import_log": "Imported '{name}' ({n} rows).",
        "import_ok": "Imported: {name}",
        "import_err": "Import error: {err}",
        "reset_btn": "🔄 Reset demo data",
        "reset_log": "Reset table to demo data.",
        "hist_header": "🕒 Update History",
        "note_label": "Add a follow-up note",
        "note_placeholder": "e.g., Checked HCl batch...",
        "note_btn": "✍️ Save note",
        "note_prefix": "Note",
        "clear_hist_btn": "🗑️ Clear history",
        "no_hist": "No updates recorded yet.",
        "kpi_products": "📦 Items in stock",
        "kpi_expiry": "⚠️ Expiration alerts",
        "kpi_low": "📉 Low stock",
        "kpi_suppliers": "🏭 Suppliers",
        "tab_stock": "📋 Inventory & Add",
        "tab_analyse": "📊 Analytics & Charts",
        "add_expander": "➕ Add a new product manually",
        "f_product": "Product *",
        "f_cas": "CAS Ref.",
        "f_cat": "Category",
        "f_supplier": "Supplier",
        "f_qty": "Quantity (L/kg)",
        "f_min": "Min. threshold",
        "f_exp": "Expiration date",
        "f_danger": "Hazard / Pictogram",
        "f_fds": "SDS Link",
        "add_btn": "Add to stock",
        "warn_no_name": "Please enter at least the product name.",
        "add_log": "Added '{prod}' ({qty} L/kg, {supp}).",
        "add_ok": "'{prod}' added successfully!",
        "search_label": "🔎 Search (product, CAS, supplier)",
        "filter_supp": "🏭 Filter by supplier",
        "filter_status": "📌 Filter by status",
        "all_option": "All",
        "open_fds": "📄 Open SDS",
        "chart_cat": "**Total quantity by category**",
        "chart_status": "**Product count by status**",
        "chart_status_col": "Product count",
        "chart_supp": "**Total quantity by supplier**",
        "no_data_chart": "No data to analyze with current filters.",
        "status_expired": "🔴 Expired",
        "status_soon": "🟠 Expiring < 30d",
        "status_low": "🟡 Low stock",
        "status_ok": "🟢 Compliant",
        "def_product_1": "Ethanol 96%",
        "def_cat_1": "Solvent",
        "def_product_2": "Hydrochloric acid 37%",
        "def_cat_2": "Acid",
        "def_danger_1": "🔥 Flammable",
        "def_danger_2": "🧪 Corrosive",
        "def_supplier_na": "Unspecified",
        "def_cat_other": "Other",
        "def_product_na": "Unnamed product",
        "def_danger_check": "⚠️ To verify",
    },
}

if "lang" not in st.session_state:
    st.session_state.lang = "fr"


def tr(key: str, **kwargs) -> str:
    text = TRANSLATIONS[st.session_state.lang][key]
    return text.format(**kwargs) if kwargs else text


def normalize_col_name(text: str) -> str:
    s = str(text).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def match_column(columns, aliases, keywords=None):
    norm_map = {col: normalize_col_name(col) for col in columns}
    norm_aliases = [normalize_col_name(a) for a in aliases]

    for alias in norm_aliases:
        for col, ncol in norm_map.items():
            if ncol == alias:
                return col

    for alias in norm_aliases:
        for col, ncol in norm_map.items():
            if alias and alias in ncol:
                return col

    if keywords:
        nkeys = [normalize_col_name(k) for k in keywords]
        for col, ncol in norm_map.items():
            if any(k in ncol for k in nkeys):
                return col

    return None


def compute_status(row):
    exp_date = row["Date péremption"]
    qty = float(row["Quantité (L/kg)"])
    seuil = float(row["Seuil min."])

    if pd.notna(exp_date) and exp_date < TODAY:
        return tr("status_expired")
    if pd.notna(exp_date) and (exp_date - TODAY).days <= 30:
        return tr("status_soon")
    if qty <= seuil:
        return tr("status_low")
    return tr("status_ok")


def log_history(message: str):
    stamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.history.insert(0, f"[{stamp}] {message}")


def standardize_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    col_produit = match_column(
        df.columns,
        ["produit", "nom produit", "designation", "article", "reactif", "substance", "nom", "product", "item"],
        keywords=["produit", "design", "article", "reactif", "product", "item"],
    )
    col_cas = match_column(
        df.columns,
        ["ref cas", "cas", "n cas", "no cas", "numero cas", "reference", "cas ref"],
        keywords=["cas"],
    )
    col_cat = match_column(
        df.columns,
        ["categorie", "famille", "type", "classe", "category", "family"],
        keywords=["categ", "famill", "type"],
    )
    col_fournisseur = match_column(
        df.columns,
        ["fournisseur", "fournisseurs", "fabricant", "supplier", "distributeur", "vendeur", "vendor"],
        keywords=["fourniss", "fabric", "suppl", "distrib", "vendor"],
    )
    col_qty = match_column(
        df.columns,
        ["quantite", "quantite l kg", "qte", "stock", "volume", "masse", "quantity"],
        keywords=["quant", "qte", "stock", "vol"],
    )
    col_seuil = match_column(
        df.columns,
        ["seuil min", "seuil", "stock min", "minimum", "alerte stock", "min threshold", "min stock"],
        keywords=["seuil", "min", "thresh"],
    )
    col_date = match_column(
        df.columns,
        [
            "date peremption",
            "date de peremption",
            "date d exp",
            "date exp",
            "exp",
            "expiration",
            "expiration date",
            "date expiration",
            "peremption",
            "dlc",
            "ddm",
            "validite",
        ],
        keywords=["peremp", "exp", "dlc", "ddm", "valid"],
    )
    col_danger = match_column(
        df.columns,
        ["pictogramme danger", "pictogramme", "danger", "risque", "sgh", "clp", "hazard"],
        keywords=["picto", "danger", "risqu", "sgh", "clp", "hazard"],
    )
    col_fds = match_column(
        df.columns,
        ["lien fds", "fds", "fiche fds", "fiche securite", "lien", "url", "sds", "sds link"],
        keywords=["fds", "sds", "securit", "lien", "url"],
    )

    out = pd.DataFrame()
    out["Produit"] = (
        df[col_produit].fillna(tr("def_product_na")).astype(str).str.strip()
        if col_produit
        else tr("def_product_na")
    )
    out["Réf. CAS"] = df[col_cas].fillna("N/A").astype(str).str.strip() if col_cas else "N/A"
    out["Catégorie"] = (
        df[col_cat].fillna(tr("def_cat_other")).astype(str).str.strip()
        if col_cat
        else tr("def_cat_other")
    )
    out["Fournisseur"] = (
        df[col_fournisseur].fillna(tr("def_supplier_na")).astype(str).str.strip()
        if col_fournisseur
        else tr("def_supplier_na")
    )

    if col_qty:
        out["Quantité (L/kg)"] = (
            pd.to_numeric(df[col_qty].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            .fillna(0.0)
        )
    else:
        out["Quantité (L/kg)"] = 0.0

    if col_seuil:
        out["Seuil min."] = (
            pd.to_numeric(df[col_seuil].astype(str).str.replace(",", ".", regex=False), errors="coerce")
            .fillna(0.0)
        )
    else:
        out["Seuil min."] = 0.0

    if col_date:
        parsed_dates = pd.to_datetime(df[col_date], errors="coerce", dayfirst=True).dt.date
        out["Date péremption"] = parsed_dates.fillna(TODAY + timedelta(days=90))
    else:
        out["Date péremption"] = TODAY + timedelta(days=90)

    out["Pictogramme / Danger"] = (
        df[col_danger].fillna(tr("def_danger_check")).astype(str).str.strip()
        if col_danger
        else tr("def_danger_check")
    )
    out["Lien FDS"] = (
        df[col_fds].fillna("https://www.inrs.fr/").astype(str).str.strip()
        if col_fds
        else "https://www.inrs.fr/"
    )

    out = out[out["Produit"].str.strip() != ""].reset_index(drop=True)
    out["Statut"] = out.apply(compute_status, axis=1)
    return out


def default_stock() -> pd.DataFrame:
    data = [
        {
            "Produit": tr("def_product_1"),
            "Réf. CAS": "64-17-5",
            "Catégorie": tr("def_cat_1"),
            "Fournisseur": "Sigma-Aldrich",
            "Quantité (L/kg)": 25.0,
            "Seuil min.": 10.0,
            "Date péremption": TODAY + timedelta(days=120),
            "Pictogramme / Danger": tr("def_danger_1"),
            "Lien FDS": "https://www.inrs.fr/",
        },
        {
            "Produit": tr("def_product_2"),
            "Réf. CAS": "7647-01-0",
            "Catégorie": tr("def_cat_2"),
            "Fournisseur": "Carlo Erba",
            "Quantité (L/kg)": 4.0,
            "Seuil min.": 5.0,
            "Date péremption": TODAY + timedelta(days=18),
            "Pictogramme / Danger": tr("def_danger_2"),
            "Lien FDS": "https://www.inrs.fr/",
        },
    ]
    df = pd.DataFrame(data)
    df["Statut"] = df.apply(compute_status, axis=1)
    return df


if "df_stock" not in st.session_state:
    st.session_state.df_stock = default_stock()

if "last_uploaded_key" not in st.session_state:
    st.session_state.last_uploaded_key = None

if "history" not in st.session_state:
    st.session_state.history = [f"[{datetime.now().strftime('%H:%M:%S')}] {tr('init_log')}"]

# --- Barre latérale gauche : Langue + Import + Historique ---
with st.sidebar:
    lang_choice = st.selectbox(
        tr("lang_label"),
        options=["fr", "en"],
        format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇬🇧 English",
        index=0 if st.session_state.lang == "fr" else 1,
    )
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

    st.divider()
    st.header(tr("import_header"))
    uploaded_file = st.file_uploader(tr("upload_label"), type=["xlsx", "xls", "csv"])

    if uploaded_file is not None:
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        if file_key != st.session_state.last_uploaded_key:
            try:
                if uploaded_file.name.lower().endswith(".csv"):
                    df_raw = pd.read_csv(uploaded_file)
                else:
                    df_raw = pd.read_excel(uploaded_file)

                df_clean = standardize_dataframe(df_raw)
                st.session_state.df_stock = df_clean
                st.session_state.last_uploaded_key = file_key
                log_history(tr("import_log", name=uploaded_file.name, n=len(df_clean)))
                st.success(tr("import_ok", name=uploaded_file.name))
                st.rerun()
            except Exception as e:
                st.error(tr("import_err", err=e))

    if st.button(tr("reset_btn"), use_container_width=True):
        st.session_state.df_stock = default_stock()
        st.session_state.last_uploaded_key = None
        log_history(tr("reset_log"))
        st.rerun()

    st.divider()
    st.header(tr("hist_header"))

    note_manuelle = st.text_input(tr("note_label"), placeholder=tr("note_placeholder"))
    if st.button(tr("note_btn"), use_container_width=True):
        if note_manuelle.strip():
            log_history(f"{tr('note_prefix')} : {note_manuelle.strip()}")
            st.rerun()

    if st.session_state.history:
        for item in st.session_state.history[:25]:
            st.caption(item)
        if st.button(tr("clear_hist_btn"), use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption(tr("no_hist"))

# --- En-tête stylisé ---
st.markdown(
    f"""
    <div class="hero-banner">
        <h1>{tr("banner_title")}</h1>
        <p>{tr("banner_sub")}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Préparation des données ---
df_display = st.session_state.df_stock.copy()
df_display["Statut"] = df_display.apply(compute_status, axis=1)

# --- Cartes KPI en haut ---
m1, m2, m3, m4 = st.columns(4)
m1.metric(tr("kpi_products"), len(df_display))
m2.metric(
    tr("kpi_expiry"),
    int(df_display["Statut"].isin([tr("status_expired"), tr("status_soon")]).sum()),
)
m3.metric(tr("kpi_low"), int((df_display["Statut"] == tr("status_low")).sum()))
m4.metric(tr("kpi_suppliers"), df_display["Fournisseur"].nunique())

st.write("")

# --- Onglets ---
tab_stock, tab_analyse = st.tabs([tr("tab_stock"), tr("tab_analyse")])

with tab_stock:
    with st.expander(tr("add_expander"), expanded=False):
        with st.form("add_product_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                produit = st.text_input(tr("f_product"))
                cas = st.text_input(tr("f_cas"), value="N/A")
            with c2:
                categorie = st.text_input(tr("f_cat"), value=tr("def_cat_1"))
                fournisseur = st.text_input(tr("f_supplier"), value=tr("def_supplier_na"))
            with c3:
                quantite = st.number_input(tr("f_qty"), min_value=0.0, step=0.5, value=1.0)
                seuil = st.number_input(tr("f_min"), min_value=0.0, step=0.5, value=1.0)
            with c4:
                date_per = st.date_input(tr("f_exp"), value=TODAY + timedelta(days=90))
                danger = st.text_input(tr("f_danger"), value=tr("def_danger_check"))
                lien_fds = st.text_input(tr("f_fds"), value="https://www.inrs.fr/")

            submitted = st.form_submit_button(tr("add_btn"), type="primary")
            if submitted:
                if not produit.strip():
                    st.warning(tr("warn_no_name"))
                else:
                    new_row = {
                        "Produit": produit.strip(),
                        "Réf. CAS": cas.strip() or "N/A",
                        "Catégorie": categorie.strip() or tr("def_cat_other"),
                        "Fournisseur": fournisseur.strip() or tr("def_supplier_na"),
                        "Quantité (L/kg)": float(quantite),
                        "Seuil min.": float(seuil),
                        "Date péremption": date_per,
                        "Pictogramme / Danger": danger.strip() or tr("def_danger_check"),
                        "Lien FDS": lien_fds.strip() or "https://www.inrs.fr/",
                    }
                    new_row["Statut"] = compute_status(new_row)
                    st.session_state.df_stock = pd.concat(
                        [st.session_state.df_stock, pd.DataFrame([new_row])],
                        ignore_index=True,
                    )
                    log_history(
                        tr(
                            "add_log",
                            prod=new_row["Produit"],
                            qty=new_row["Quantité (L/kg)"],
                            supp=new_row["Fournisseur"],
                        )
                    )
                    st.success(tr("add_ok", prod=new_row["Produit"]))
                    st.rerun()

    # --- Filtres rapides ---
    f1, f2, f3 = st.columns(3)
    all_lbl = tr("all_option")
    with f1:
        search = st.text_input(tr("search_label"))
    with f2:
        fournisseurs_dispo = [all_lbl] + sorted(df_display["Fournisseur"].dropna().unique().tolist())
        fournisseur_sel = st.selectbox(tr("filter_supp"), fournisseurs_dispo)
    with f3:
        statuts_dispo = [all_lbl] + sorted(df_display["Statut"].dropna().unique().tolist())
        statut_sel = st.selectbox(tr("filter_status"), statuts_dispo)

    df_filtered = df_display.copy()
    if search.strip():
        q = search.strip().lower()
        mask = (
            df_filtered["Produit"].astype(str).str.lower().str.contains(q, na=False)
            | df_filtered["Réf. CAS"].astype(str).str.lower().str.contains(q, na=False)
            | df_filtered["Fournisseur"].astype(str).str.lower().str.contains(q, na=False)
        )
        df_filtered = df_filtered[mask]

    if fournisseur_sel != all_lbl:
        df_filtered = df_filtered[df_filtered["Fournisseur"] == fournisseur_sel]

    if statut_sel != all_lbl:
        df_filtered = df_filtered[df_filtered["Statut"] == statut_sel]

    max_qty = float(df_filtered["Quantité (L/kg)"].max()) if not df_filtered.empty else 100.0
    max_qty = max(max_qty, 1.0)

    st.dataframe(
        df_filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Quantité (L/kg)": st.column_config.ProgressColumn(
                tr("f_qty"),
                format="%.1f",
                min_value=0.0,
                max_value=max_qty,
            ),
            "Date péremption": st.column_config.DateColumn(
                tr("f_exp"),
                format="DD/MM/YYYY",
            ),
            "Lien FDS": st.column_config.LinkColumn(
                tr("f_fds"),
                display_text=tr("open_fds"),
            ),
        },
    )

with tab_analyse:
    if not df_filtered.empty:
        g1, g2, g3 = st.columns(3)

        with g1:
            st.markdown(tr("chart_cat"))
            qty_par_cat = (
                df_filtered.groupby("Catégorie", as_index=True)["Quantité (L/kg)"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(qty_par_cat, color="#1B7A43")

        with g2:
            st.markdown(tr("chart_status"))
            nb_par_statut = (
                df_filtered["Statut"]
                .value_counts()
                .to_frame(name=tr("chart_status_col"))
            )
            st.bar_chart(nb_par_statut, color="#2E86C1")

        with g3:
            st.markdown(tr("chart_supp"))
            qty_par_fourn = (
                df_filtered.groupby("Fournisseur", as_index=True)["Quantité (L/kg)"]
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(qty_par_fourn, color="#D68910")
    else:
        st.info(tr("no_data_chart"))
