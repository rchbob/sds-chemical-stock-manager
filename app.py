import re
import unicodedata
from datetime import datetime, date, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestionnaire FDS & Stocks",
    page_icon="🧪",
    layout="wide",
)

TODAY = date.today()


def normalize_col_name(text: str) -> str:
    """Nettoie accents, casse, ponctuation et espaces pour comparer des noms de colonnes."""
    s = str(text).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def match_column(columns, aliases, keywords=None):
    """Trouve la colonne d'un DataFrame correspondant à une liste d'alias ou mots-clés."""
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
    """Calcule le statut QHSE d'une ligne de stock."""
    exp_date = row["Date péremption"]
    qty = float(row["Quantité (L/kg)"])
    seuil = float(row["Seuil min."])

    if pd.notna(exp_date) and exp_date < TODAY:
        return "🔴 Périmé"
    if pd.notna(exp_date) and (exp_date - TODAY).days <= 30:
        return "🟠 Expire < 30j"
    if qty <= seuil:
        return "🟡 Stock bas"
    return "🟢 Conforme"


def log_history(message: str):
    """Ajoute une entrée horodatée à l'historique des modifications."""
    stamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.history.insert(0, f"[{stamp}] {message}")


def standardize_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Harmonise n'importe quel tableau importé vers la structure attendue."""
    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    col_produit = match_column(
        df.columns,
        ["produit", "nom produit", "designation", "article", "reactif", "substance", "nom"],
        keywords=["produit", "design", "article", "reactif"],
    )
    col_cas = match_column(
        df.columns,
        ["ref cas", "cas", "n cas", "no cas", "numero cas", "reference"],
        keywords=["cas"],
    )
    col_cat = match_column(
        df.columns,
        ["categorie", "famille", "type", "classe"],
        keywords=["categ", "famill", "type"],
    )
    col_fournisseur = match_column(
        df.columns,
        ["fournisseur", "fournisseurs", "fabricant", "supplier", "distributeur", "vendeur"],
        keywords=["fourniss", "fabric", "suppl", "distrib"],
    )
    col_qty = match_column(
        df.columns,
        ["quantite", "quantite l kg", "qte", "stock", "volume", "masse", "quantite disponible"],
        keywords=["quant", "qte", "stock", "vol"],
    )
    col_seuil = match_column(
        df.columns,
        ["seuil min", "seuil", "stock min", "minimum", "alerte stock", "seuil minimal"],
        keywords=["seuil", "min"],
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
            "date expiration",
            "peremption",
            "dlc",
            "ddm",
            "validite",
            "date validite",
        ],
        keywords=["peremp", "exp", "dlc", "ddm", "valid"],
    )
    col_danger = match_column(
        df.columns,
        ["pictogramme danger", "pictogramme", "danger", "risque", "sgh", "clp", "mention danger"],
        keywords=["picto", "danger", "risqu", "sgh", "clp"],
    )
    col_fds = match_column(
        df.columns,
        ["lien fds", "fds", "fiche fds", "fiche securite", "lien", "url", "sds"],
        keywords=["fds", "sds", "securit", "lien", "url"],
    )

    out = pd.DataFrame()
    out["Produit"] = (
        df[col_produit].fillna("Produit sans nom").astype(str).str.strip()
        if col_produit
        else "Produit sans nom"
    )
    out["Réf. CAS"] = (
        df[col_cas].fillna("N/A").astype(str).str.strip()
        if col_cas
        else "N/A"
    )
    out["Catégorie"] = (
        df[col_cat].fillna("Autre").astype(str).str.strip()
        if col_cat
        else "Autre"
    )
    out["Fournisseur"] = (
        df[col_fournisseur].fillna("Non spécifié").astype(str).str.strip()
        if col_fournisseur
        else "Non spécifié"
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
        df[col_danger].fillna("⚠️ À vérifier").astype(str).str.strip()
        if col_danger
        else "⚠️ À vérifier"
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
            "Produit": "Éthanol 96%",
            "Réf. CAS": "64-17-5",
            "Catégorie": "Solvant",
            "Fournisseur": "Sigma-Aldrich",
            "Quantité (L/kg)": 25.0,
            "Seuil min.": 10.0,
            "Date péremption": TODAY + timedelta(days=120),
            "Pictogramme / Danger": "🔥 Inflammable",
            "Lien FDS": "https://www.inrs.fr/",
        },
        {
            "Produit": "Acide chlorhydrique 37%",
            "Réf. CAS": "7647-01-0",
            "Catégorie": "Acide",
            "Fournisseur": "Carlo Erba",
            "Quantité (L/kg)": 4.0,
            "Seuil min.": 5.0,
            "Date péremption": TODAY + timedelta(days=18),
            "Pictogramme / Danger": "🧪 Corrosif",
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
    st.session_state.history = [f"[{datetime.now().strftime('%H:%M:%S')}] Initialisation du stock démo."]

st.title("🧪 Gestionnaire FDS & Stocks")

# --- Barre latérale gauche : Import + Historique des modifications ---
with st.sidebar:
    st.header("📥 Import de données")
    uploaded_file = st.file_uploader("Choisir un fichier Excel ou CSV", type=["xlsx", "xls", "csv"])

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
                log_history(f"Import de '{uploaded_file.name}' ({len(df_clean)} lignes).")
                st.success(f"Importé : {uploaded_file.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de l'import : {e}")

    if st.button("🔄 Réinitialiser la démo", use_container_width=True):
        st.session_state.df_stock = default_stock()
        st.session_state.last_uploaded_key = None
        log_history("Réinitialisation du tableau sur les données démo.")
        st.rerun()

    st.divider()
    st.header("🕒 Historique des mises à jour")

    note_manuelle = st.text_input("Ajouter une note de suivi", placeholder="Ex: Vérification lot HCl...")
    if st.button("✍️ Enregistrer la note", use_container_width=True):
        if note_manuelle.strip():
            log_history(f"Note : {note_manuelle.strip()}")
            st.rerun()

    if st.session_state.history:
        for item in st.session_state.history[:25]:
            st.caption(item)
        if st.button("🗑️ Effacer l'historique", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Aucune modification enregistrée.")

# --- Formulaire d'ajout manuel ---
with st.expander("➕ Ajouter un nouveau produit manuellement", expanded=True):
    with st.form("add_product_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            produit = st.text_input("Produit *")
            cas = st.text_input("Réf. CAS", value="N/A")
        with c2:
            categorie = st.text_input("Catégorie", value="Réactif")
            fournisseur = st.text_input("Fournisseur", value="Non spécifié")
        with c3:
            quantite = st.number_input("Quantité (L/kg)", min_value=0.0, step=0.5, value=1.0)
            seuil = st.number_input("Seuil min.", min_value=0.0, step=0.5, value=1.0)
        with c4:
            date_per = st.date_input("Date péremption", value=TODAY + timedelta(days=90))
            danger = st.text_input("Pictogramme / Danger", value="⚠️ À vérifier")
            lien_fds = st.text_input("Lien FDS", value="https://www.inrs.fr/")

        submitted = st.form_submit_button("Ajouter au stock")
        if submitted:
            if not produit.strip():
                st.warning("Merci d'indiquer au moins le nom du produit.")
            else:
                new_row = {
                    "Produit": produit.strip(),
                    "Réf. CAS": cas.strip() or "N/A",
                    "Catégorie": categorie.strip() or "Autre",
                    "Fournisseur": fournisseur.strip() or "Non spécifié",
                    "Quantité (L/kg)": float(quantite),
                    "Seuil min.": float(seuil),
                    "Date péremption": date_per,
                    "Pictogramme / Danger": danger.strip() or "⚠️ À vérifier",
                    "Lien FDS": lien_fds.strip() or "https://www.inrs.fr/",
                }
                new_row["Statut"] = compute_status(new_row)
                st.session_state.df_stock = pd.concat(
                    [st.session_state.df_stock, pd.DataFrame([new_row])],
                    ignore_index=True,
                )
                log_history(
                    f"Ajout de '{new_row['Produit']}' ({new_row['Quantité (L/kg)']} L/kg, {new_row['Fournisseur']})."
                )
                st.success(f"« {new_row['Produit']} » ajouté avec succès !")
                st.rerun()

# --- Filtres rapides ---
df_display = st.session_state.df_stock.copy()
df_display["Statut"] = df_display.apply(compute_status, axis=1)

f1, f2, f3 = st.columns(3)
with f1:
    search = st.text_input("🔎 Rechercher (produit, CAS, fournisseur)")
with f2:
    fournisseurs_dispo = ["Tous"] + sorted(df_display["Fournisseur"].dropna().unique().tolist())
    fournisseur_sel = st.selectbox("🏭 Filtrer par fournisseur", fournisseurs_dispo)
with f3:
    statuts_dispo = ["Tous"] + sorted(df_display["Statut"].dropna().unique().tolist())
    statut_sel = st.selectbox("📌 Filtrer par statut", statuts_dispo)

if search.strip():
    q = search.strip().lower()
    mask = (
        df_display["Produit"].astype(str).str.lower().str.contains(q, na=False)
        | df_display["Réf. CAS"].astype(str).str.lower().str.contains(q, na=False)
        | df_display["Fournisseur"].astype(str).str.lower().str.contains(q, na=False)
    )
    df_display = df_display[mask]

if fournisseur_sel != "Tous":
    df_display = df_display[df_display["Fournisseur"] == fournisseur_sel]

if statut_sel != "Tous":
    df_display = df_display[df_display["Statut"] == statut_sel]

# --- Indicateurs & Tableau ---
m1, m2, m3 = st.columns(3)
m1.metric("Produits affichés", len(df_display))
m2.metric("Périmés / < 30j", int(df_display["Statut"].isin(["🔴 Périmé", "🟠 Expire < 30j"]).sum()))
m3.metric("Fournisseurs", df_display["Fournisseur"].nunique())

st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- Section Graphes d'analyse (Pandas) ---
st.divider()
st.subheader("📊 Analyses du stock (Pandas)")

if not df_display.empty:
    g1, g2, g3 = st.columns(3)

    with g1:
        st.markdown("**Quantité totale par catégorie**")
        qty_par_cat = (
            df_display.groupby("Catégorie", as_index=True)["Quantité (L/kg)"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(qty_par_cat)

    with g2:
        st.markdown("**Nombre de produits par statut**")
        nb_par_statut = (
            df_display["Statut"]
            .value_counts()
            .to_frame(name="Nombre de produits")
        )
        st.bar_chart(nb_par_statut)

    with g3:
        st.markdown("**Quantité totale par fournisseur**")
        qty_par_fourn = (
            df_display.groupby("Fournisseur", as_index=True)["Quantité (L/kg)"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(qty_par_fourn)
else:
    st.info("Aucune donnée à analyser avec les filtres actuels.")