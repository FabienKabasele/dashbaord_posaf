import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, date
import calendar

# Configuration de la page
st.set_page_config(
    page_title="Stop TB - Tableau de Bord FCSDS",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
    <style>
    .main-header {
        background-color: #1f77b4;
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .national-badge {
        background-color: #1f77b4;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .provincial-badge {
        background-color: #ff7f0e;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .facility-badge {
        background-color: #2ca02c;
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown('<div class="main-header"><h1>🩺 Stop TB - Tableau de Bord FCSDS</h1><p>Suivi des activités de lutte contre la tuberculose</p></div>', unsafe_allow_html=True)

# ============================================================================
# DONNÉES DE RÉFÉRENCE POUR LA COMPLÉTUDE
# ============================================================================

ZS_CDT_REFERENCE = pd.DataFrame({
    'Province': [
        'Haut Katanga', 'Haut Lomami', 'Kasai Oriental', 'Kasai Central',
        'Lualaba', 'Lomami', 'Sud Kivu', 'Sankuru', 'Tanganyika'
    ],
    'ZS_attendues': [27, 16, 19, 25, 14, 16, 31, 16, 11],
    'CDT_attendus': [105, 74, 132, 101, 62, 101, 104, 85, 69]
})

DATE_LIMITE_JOUR = 7

# ============================================================================
# FONCTIONS DE TRAITEMENT DES DONNÉES
# ============================================================================

def clean_province_name(name):
    """Nettoie et uniformise les noms de provinces"""
    if pd.isna(name):
        return None
    
    name = str(name).strip()
    
    # Mapping des noms de provinces
    mapping = {
        'haut katanga': 'Haut Katanga',
        'hautkatanga': 'Haut Katanga',
        'katanga': 'Haut Katanga',
        'haut lomami': 'Haut Lomami',
        'hautlomami': 'Haut Lomami',
        'lomami': 'Lomami',
        'kasai oriental': 'Kasai Oriental',
        'kasaioriental': 'Kasai Oriental',
        'kasai central': 'Kasai Central',
        'kasaicentral': 'Kasai Central',
        'lualaba': 'Lualaba',
        'sud kivu': 'Sud Kivu',
        'sudkivu': 'Sud Kivu',
        'sankuru': 'Sankuru',
        'tanganyika': 'Tanganyika'
    }
    
    name_clean = name.lower().strip()
    
    if name_clean in mapping:
        return mapping[name_clean]
    
    if ' ' in name:
        parts = name.split(' ', 1)
        if len(parts) == 2:
            code, nom = parts
            nom_clean = nom.lower().strip()
            if nom_clean in mapping:
                return mapping[nom_clean]
    
    if name in mapping.values():
        return name
    
    return name

@st.cache_data
def load_and_process_data():
    """Charge le fichier CSV et recrée tous les calculs"""
    df = pd.read_csv('drc_stop_tb_data.csv')
    
    # Extraction des informations géographiques
    if 'q010b' in df.columns:
        df['province_name_raw'] = df['q010b']
        df['province_name'] = df['q010b'].apply(clean_province_name)
    
    if 'q011b' in df.columns:
        df['healthzone_name'] = df['q011b']
    
    if 'q012b' in df.columns:
        df['facility_name'] = df['q012b']
    
    if 'q012a' in df.columns:
        df['facility_id'] = df['q012a']
    
    # Conversion de la date de saisie
    if 'q001a' in df.columns:
        df['date_saisie'] = pd.to_datetime(df['q001a'], format='%d/%m/%Y', errors='coerce')
        df['jour_soumission'] = df['date_saisie'].dt.day
        df['mois_soumission'] = df['date_saisie'].dt.month
        df['annee_soumission'] = df['date_saisie'].dt.year
        df['est_prompt'] = df['jour_soumission'] <= DATE_LIMITE_JOUR
        df['statut_promptitude'] = df['est_prompt'].map({True: 'À temps', False: 'En retard'})
    
    # Ajout du trimestre
    if 'qmois' in df.columns:
        mois_num = df['qmois'].str.extract(r'(\d+)')[0].astype(float)
        mois_num = mois_num.fillna(0)
        trimestre_calc = np.ceil(mois_num / 3)
        trimestre_calc = trimestre_calc.replace(0, np.nan)
        df['trimestre'] = trimestre_calc.astype('Int64')
        df['trimestre'] = df['trimestre'].map({1: 'T1', 2: 'T2', 3: 'T3', 4: 'T4'})
    
    # ==================== SECTION 1.0 à 10.2 ====================
    colonnes_q = ['q1_0_h', 'q1_0_f', 'q1_0_age15m', 'q1_0_age15p', 'q1_0_niv_sante', 'q1_0_niv_com',
                  'q1_1_h', 'q1_1_f', 'q1_1_age15m', 'q1_1_age15p', 'q1_1_niv_sante', 'q1_1_niv_com',
                  'q1_2_h', 'q1_2_f', 'q1_2_age15m', 'q1_2_age15p', 'q1_2_niv_sante', 'q1_2_niv_com',
                  'q1_3_h', 'q1_3_f', 'q1_3_age15m', 'q1_3_age15p', 'q1_3_niv_sante', 'q1_3_niv_com',
                  'q1_4_h', 'q1_4_f', 'q1_4_age15m', 'q1_4_age15p',
                  'q1_5_h', 'q1_5_f', 'q1_5_age15m', 'q1_5_age15p',
                  'q2_0_h', 'q2_0_f', 'q2_0_age15m', 'q2_0_age15p',
                  'q2_1_h', 'q2_1_f', 'q2_1_age15m', 'q2_1_age15p',
                  'q2_2_h', 'q2_2_f', 'q2_2_age15m', 'q2_2_age15p',
                  'q3_0_h', 'q3_0_f', 'q3_0_age15m', 'q3_0_age15p',
                  'q3_4_g04', 'q3_4_g514', 'q3_4_h1524', 'q3_4_h2534', 'q3_4_h3544', 'q3_4_h4554', 'q3_4_h5564', 'q3_4_h65p',
                  'q3_4_f04', 'q3_4_f514', 'q3_4_f1524', 'q3_4_f2534', 'q3_4_f3544', 'q3_4_f4554', 'q3_4_f5564', 'q3_4_f65p',
                  'q4_0_h', 'q4_0_f', 'q4_0_age15m', 'q4_0_age15p',
                  'q4_1_h', 'q4_1_f', 'q4_1_age15m', 'q4_1_age15p',
                  'q5_0_h', 'q5_0_f', 'q5_0_age15m', 'q5_0_age15p',
                  'q6_0_h', 'q6_0_f', 'q6_0_age15m', 'q6_0_age15p',
                  'q7_0_h', 'q7_0_f', 'q7_0_age15m', 'q7_0_age15p',
                  'q8_0_h', 'q8_0_f', 'q8_0_age5m', 'q8_0_age5p',
                  'q8_1_h', 'q8_1_f', 'q8_1_age5m', 'q8_1_age5p',
                  'q8_2_h', 'q8_2_f', 'q8_2_age5m', 'q8_2_age5p',
                  'q8_3_h', 'q8_3_f', 'q8_3_age5m', 'q8_3_age5p',
                  'q8_4_h', 'q8_4_f', 'q8_4_age5m', 'q8_4_age5p',
                  'q8_5_h', 'q8_5_f', 'q8_5_age15m', 'q8_5_age15p',
                  'q8_6_h', 'q8_6_f', 'q8_6_age5m', 'q8_6_age5p',
                  'q9_1_h', 'q9_1_f', 'q9_1_age5m', 'q9_1_age5p',
                  'q9_2_h', 'q9_2_f', 'q9_2_age15m', 'q9_2_age15p',
                  'q9_3_h', 'q9_3_f', 'q9_3_age5m', 'q9_3_age5p',
                  'q10_0_h', 'q10_0_f', 'q10_0_age5m', 'q10_0_age5p',
                  'q10_1_h', 'q10_1_f', 'q10_1_age5m', 'q10_1_age5p',
                  'q10_2_h', 'q10_2_f', 'q10_2_age5m', 'q10_2_age5p']
    
    for col in colonnes_q:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # Calculs des totaux
    df['q1_0_hf_total'] = df['q1_0_h'] + df['q1_0_f']
    df['q1_0_age_total'] = df['q1_0_age15m'] + df['q1_0_age15p']
    df['q1_0_niv_total'] = df['q1_0_niv_sante'] + df['q1_0_niv_com']
    
    df['q1_1_hf_total'] = df['q1_1_h'] + df['q1_1_f']
    df['q1_1_age_total'] = df['q1_1_age15m'] + df['q1_1_age15p']
    df['q1_1_niv_total'] = df['q1_1_niv_sante'] + df['q1_1_niv_com']
    
    df['q1_2_hf_total'] = df['q1_2_h'] + df['q1_2_f']
    df['q1_2_age_total'] = df['q1_2_age15m'] + df['q1_2_age15p']
    df['q1_2_niv_total'] = df['q1_2_niv_sante'] + df['q1_2_niv_com']
    
    df['q1_3_hf_total'] = df['q1_3_h'] + df['q1_3_f']
    df['q1_3_age_total'] = df['q1_3_age15m'] + df['q1_3_age15p']
    df['q1_3_niv_total'] = df['q1_3_niv_sante'] + df['q1_3_niv_com']
    
    df['q1_4_hf_total'] = df['q1_4_h'] + df['q1_4_f']
    df['q1_4_age_total'] = df['q1_4_age15m'] + df['q1_4_age15p']
    
    df['q1_5_hf_total'] = df['q1_5_h'] + df['q1_5_f']
    df['q1_5_age_total'] = df['q1_5_age15m'] + df['q1_5_age15p']
    
    df['q2_0_hf_total'] = df['q2_0_h'] + df['q2_0_f']
    df['q2_0_age_total'] = df['q2_0_age15m'] + df['q2_0_age15p']
    
    df['q2_1_hf_total'] = df['q2_1_h'] + df['q2_1_f']
    df['q2_1_age_total'] = df['q2_1_age15m'] + df['q2_1_age15p']
    
    df['q2_2_hf_total'] = df['q2_2_h'] + df['q2_2_f']
    df['q2_2_age_total'] = df['q2_2_age15m'] + df['q2_2_age15p']
    
    df['q3_0_hf_total'] = df['q3_0_h'] + df['q3_0_f']
    df['q3_0_age_total'] = df['q3_0_age15m'] + df['q3_0_age15p']
    
    df['q3_4_h_total'] = (df['q3_4_g04'] + df['q3_4_g514'] + df['q3_4_h1524'] + 
                          df['q3_4_h2534'] + df['q3_4_h3544'] + df['q3_4_h4554'] + 
                          df['q3_4_h5564'] + df['q3_4_h65p'])
    df['q3_4_f_total'] = (df['q3_4_f04'] + df['q3_4_f514'] + df['q3_4_f1524'] + 
                          df['q3_4_f2534'] + df['q3_4_f3544'] + df['q3_4_f4554'] + 
                          df['q3_4_f5564'] + df['q3_4_f65p'])
    df['q3_4_hf_total'] = df['q3_4_h_total'] + df['q3_4_f_total']
    
    df['q4_0_hf_total'] = df['q4_0_h'] + df['q4_0_f']
    df['q4_0_age_total'] = df['q4_0_age15m'] + df['q4_0_age15p']
    
    df['q4_1_hf_total'] = df['q4_1_h'] + df['q4_1_f']
    df['q4_1_age_total'] = df['q4_1_age15m'] + df['q4_1_age15p']
    
    df['q5_0_hf_total'] = df['q5_0_h'] + df['q5_0_f']
    df['q5_0_age_total'] = df['q5_0_age15m'] + df['q5_0_age15p']
    
    df['q6_0_hf_total'] = df['q6_0_h'] + df['q6_0_f']
    df['q6_0_age_total'] = df['q6_0_age15m'] + df['q6_0_age15p']
    
    df['q7_0_hf_total'] = df['q7_0_h'] + df['q7_0_f']
    df['q7_0_age_total'] = df['q7_0_age15m'] + df['q7_0_age15p']
    
    df['q8_0_hf_total'] = df['q8_0_h'] + df['q8_0_f']
    df['q8_0_age_total'] = df['q8_0_age5m'] + df['q8_0_age5p']
    
    df['q8_1_hf_total'] = df['q8_1_h'] + df['q8_1_f']
    df['q8_1_age_total'] = df['q8_1_age5m'] + df['q8_1_age5p']
    
    df['q8_2_hf_total'] = df['q8_2_h'] + df['q8_2_f']
    df['q8_2_age_total'] = df['q8_2_age5m'] + df['q8_2_age5p']
    
    df['q8_3_hf_total'] = df['q8_3_h'] + df['q8_3_f']
    df['q8_3_age_total'] = df['q8_3_age5m'] + df['q8_3_age5p']
    
    df['q8_4_hf_total'] = df['q8_4_h'] + df['q8_4_f']
    df['q8_4_age_total'] = df['q8_4_age5m'] + df['q8_4_age5p']
    
    df['q8_5_hf_total'] = df['q8_5_h'] + df['q8_5_f']
    df['q8_5_age_total'] = df['q8_5_age15m'] + df['q8_5_age15p']
    
    df['q8_6_hf_total'] = df['q8_6_h'] + df['q8_6_f']
    df['q8_6_age_total'] = df['q8_6_age5m'] + df['q8_6_age5p']
    
    df['q9_1_hf_total'] = df['q9_1_h'] + df['q9_1_f']
    df['q9_1_age_total'] = df['q9_1_age5m'] + df['q9_1_age5p']
    
    df['q9_2_hf_total'] = df['q9_2_h'] + df['q9_2_f']
    df['q9_2_age_total'] = df['q9_2_age15m'] + df['q9_2_age15p']
    
    df['q9_3_hf_total'] = df['q9_3_h'] + df['q9_3_f']
    df['q9_3_age_total'] = df['q9_3_age5m'] + df['q9_3_age5p']
    
    df['q10_0_hf_total'] = df['q10_0_h'] + df['q10_0_f']
    df['q10_0_age_total'] = df['q10_0_age5m'] + df['q10_0_age5p']
    
    df['q10_1_hf_total'] = df['q10_1_h'] + df['q10_1_f']
    df['q10_1_age_total'] = df['q10_1_age5m'] + df['q10_1_age5p']
    
    df['q10_2_hf_total'] = df['q10_2_h'] + df['q10_2_f']
    df['q10_2_age_total'] = df['q10_2_age5m'] + df['q10_2_age5p']
    
    # INDICATEURS TPT
    df['tpt_eligible_total'] = df['q8_4_hf_total'] + df['q8_5_hf_total'] + df['q8_6_hf_total']
    df['tpt_started_total'] = df['q9_1_hf_total'] + df['q9_2_hf_total'] + df['q9_3_hf_total']
    df['tpt_completed_total'] = df['q10_0_hf_total'] + df['q10_1_hf_total'] + df['q10_2_hf_total']
    
    df['enfants_moins_5_depistes'] = df['q8_0_age5m']
    df['enfants_moins_5_eligibles'] = df['q8_4_age5m']
    df['enfants_moins_5_commences'] = df['q9_1_age5m']
    df['enfants_moins_5_termines'] = df['q10_0_age5m']
    
    # Taux
    df['xpert_test_rate'] = np.where(df['q1_4_hf_total'] > 0, 
                                      df['q1_5_hf_total'] / df['q1_4_hf_total'] * 100, 0)
    df['rrmdr_detection_rate'] = np.where(df['q4_0_hf_total'] > 0,
                                           df['q4_1_hf_total'] / df['q4_0_hf_total'] * 100, 0)
    df['ds_treatment_success_rate'] = np.where(df['q3_0_hf_total'] > 0,
                                                df['q6_0_hf_total'] / df['q3_0_hf_total'] * 100, 0)
    df['rrmdr_treatment_success_rate'] = np.where(df['q5_0_hf_total'] > 0,
                                                   df['q7_0_hf_total'] / df['q5_0_hf_total'] * 100, 0)
    df['tpt_coverage'] = np.where(df['tpt_eligible_total'] > 0,
                                  df['tpt_started_total'] / df['tpt_eligible_total'] * 100, 0)
    df['tpt_completion_rate'] = np.where(df['tpt_started_total'] > 0,
                                         df['tpt_completed_total'] / df['tpt_started_total'] * 100, 0)
    
    # Mapping des mois
    mois_map = {
        'mois_1': 'Janvier', 'mois_2': 'Février', 'mois_3': 'Mars',
        'mois_4': 'Avril', 'mois_5': 'Mai', 'mois_6': 'Juin',
        'mois_7': 'Juillet', 'mois_8': 'Août', 'mois_9': 'Septembre',
        'mois_10': 'Octobre', 'mois_11': 'Novembre', 'mois_12': 'Décembre'
    }
    if 'qmois' in df.columns:
        df['mois_nom'] = df['qmois'].map(mois_map)
    
    # Supprimer les lignes avec province_name NULL
    df = df[df['province_name'].notna()]
    
    return df

def filter_by_hierarchy(df, niveau, province=None, facility=None):
    """Filtre les données selon le niveau hiérarchique"""
    if niveau == 'National':
        return df
    elif niveau == 'Provincial' and province and province != 'Toutes':
        return df[df['province_name'] == province]
    elif niveau == 'Provincial' and province == 'Toutes':
        return df
    elif niveau == 'Etablissement' and facility and facility != 'Tous':
        return df[df['facility_name'] == facility]
    elif niveau == 'Etablissement' and facility == 'Tous':
        return df
    return df

# ============================================================================
# FONCTIONS DE VISUALISATION
# ============================================================================

def show_kpi_cards(df_filtered, niveau):
    """Affiche les cartes KPI avec badge de niveau"""
    
    if niveau == 'National':
        st.markdown('<div class="national-badge">🌍 NIVEAU NATIONAL</div>', unsafe_allow_html=True)
    elif niveau == 'Provincial':
        st.markdown('<div class="provincial-badge">📍 NIVEAU PROVINCIAL</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="facility-badge">🏥 NIVEAU ÉTABLISSEMENT</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("👥 Personnes dépistées", f"{df_filtered['q1_0_hf_total'].sum():,.0f}")
    with col2:
        st.metric("🔬 Cas présumés", f"{df_filtered['q1_2_hf_total'].sum():,.0f}")
    with col3:
        st.metric("🧪 Testés Xpert", f"{df_filtered['q1_5_hf_total'].sum():,.0f}")
    with col4:
        st.metric("🦠 TB détectée", f"{df_filtered['q2_0_hf_total'].sum():,.0f}")
    with col5:
        taux_succes = df_filtered['ds_treatment_success_rate'].mean()
        st.metric("💊 Succès DS-TB", f"{taux_succes:.1f}%")
    with col6:
        tpt_cov = df_filtered['tpt_coverage'].mean()
        st.metric("🛡️ Couverture TPT", f"{tpt_cov:.1f}%")

def show_depistage_tab(df_filtered):
    """Onglet Dépistage et Diagnostic"""
    st.subheader("📈 Cascade de dépistage et diagnostic")
    
    cascade_data = pd.DataFrame({
        'Étape': ['Personnes dépistées', 'Cas présumés TB', 'Testés (Xpert)', 'TB détectée', 'TB confirmée bactério'],
        'Nombre': [
            df_filtered['q1_0_hf_total'].sum(),
            df_filtered['q1_2_hf_total'].sum(),
            df_filtered['q1_5_hf_total'].sum(),
            df_filtered['q2_0_hf_total'].sum(),
            df_filtered['q2_2_hf_total'].sum()
        ]
    })
    
    fig_cascade = px.funnel(cascade_data, x='Nombre', y='Étape', 
                             title="Cascade des patients TB",
                             color_discrete_sequence=['#1f77b4'])
    fig_cascade.update_traces(textposition="inside", textinfo="value+percent previous")
    st.plotly_chart(fig_cascade, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Répartition par sexe - Dépistage")
        sexe_data = pd.DataFrame({
            'Sexe': ['Hommes', 'Femmes'],
            'Dépistés': [df_filtered['q1_0_h'].sum(), df_filtered['q1_0_f'].sum()],
            'Présumés': [df_filtered['q1_2_h'].sum(), df_filtered['q1_2_f'].sum()],
            'Détectés': [df_filtered['q2_0_h'].sum(), df_filtered['q2_0_f'].sum()]
        })
        sexe_melted = sexe_data.melt(id_vars=['Sexe'], var_name='Catégorie', value_name='Nombre')
        fig_sexe = px.bar(sexe_melted, x='Catégorie', y='Nombre', color='Sexe', 
                          barmode='group', title="Distribution par sexe")
        st.plotly_chart(fig_sexe, use_container_width=True)
    
    with col2:
        st.subheader("Répartition par âge")
        age_data = pd.DataFrame({
            'Âge': ['≤ 15 ans', '> 15 ans'],
            'Dépistés': [df_filtered['q1_0_age15m'].sum(), df_filtered['q1_0_age15p'].sum()],
            'Présumés': [df_filtered['q1_2_age15m'].sum(), df_filtered['q1_2_age15p'].sum()],
            'Détectés': [df_filtered['q2_0_age15m'].sum(), df_filtered['q2_0_age15p'].sum()]
        })
        age_melted = age_data.melt(id_vars=['Âge'], var_name='Catégorie', value_name='Nombre')
        fig_age = px.bar(age_melted, x='Catégorie', y='Nombre', color='Âge', 
                         barmode='group', title="Distribution par âge")
        st.plotly_chart(fig_age, use_container_width=True)
    
    st.subheader("🧬 Détection de la tuberculose résistante (RR/MDR)")
    col3, col4 = st.columns(2)
    
    with col3:
        rr_data = pd.DataFrame({
            'Indicateur': ['Testés pour résistance', 'Diagnostiqués RR/MDR'],
            'Nombre': [df_filtered['q4_0_hf_total'].sum(), df_filtered['q4_1_hf_total'].sum()]
        })
        fig_rr = px.bar(rr_data, x='Indicateur', y='Nombre', 
                        color='Indicateur', title="Test de résistance à la Rifampicine")
        st.plotly_chart(fig_rr, use_container_width=True)
    
    with col4:
        taux_rr = df_filtered['rrmdr_detection_rate'].mean()
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_rr,
            title={'text': "Taux de détection RR/MDR (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#1f77b4"},
                   'steps': [
                       {'range': [0, 50], 'color': "lightgray"},
                       {'range': [50, 80], 'color': "gray"},
                       {'range': [80, 100], 'color': "darkgray"}],
                   'threshold': {'line': {'color': "red", 'width': 4},
                                 'thickness': 0.75, 'value': 90}}))
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

def show_traitement_tab(df_filtered):
    """Onglet Traitement"""
    st.subheader("💊 Résultats du traitement")
    
    st.markdown("### Tuberculose sensible (DS-TB)")
    col1, col2 = st.columns(2)
    
    with col1:
        ds_data = pd.DataFrame({
            'Statut': ['Traitement débuté', 'Traitement réussi'],
            'Hommes': [df_filtered['q3_0_h'].sum(), df_filtered['q6_0_h'].sum()],
            'Femmes': [df_filtered['q3_0_f'].sum(), df_filtered['q6_0_f'].sum()]
        })
        ds_melted = ds_data.melt(id_vars=['Statut'], var_name='Sexe', value_name='Nombre')
        fig_ds = px.bar(ds_melted, x='Statut', y='Nombre', color='Sexe', 
                        barmode='group', title="Traitement DS-TB par sexe")
        st.plotly_chart(fig_ds, use_container_width=True)
    
    with col2:
        taux_ds = df_filtered['ds_treatment_success_rate'].mean()
        fig_ds_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_ds,
            title={'text': "Taux de succès DS-TB (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#2ca02c"},
                   'steps': [
                       {'range': [0, 60], 'color': "lightgray"},
                       {'range': [60, 85], 'color': "gray"},
                       {'range': [85, 100], 'color': "darkgray"}]}))
        fig_ds_gauge.update_layout(height=300)
        st.plotly_chart(fig_ds_gauge, use_container_width=True)
    
    st.markdown("### Tuberculose résistante (RR/MDR)")
    col3, col4 = st.columns(2)
    
    with col3:
        rr_data_tx = pd.DataFrame({
            'Statut': ['Traitement débuté', 'Traitement réussi'],
            'Hommes': [df_filtered['q5_0_h'].sum(), df_filtered['q7_0_h'].sum()],
            'Femmes': [df_filtered['q5_0_f'].sum(), df_filtered['q7_0_f'].sum()]
        })
        rr_melted = rr_data_tx.melt(id_vars=['Statut'], var_name='Sexe', value_name='Nombre')
        fig_rr_tx = px.bar(rr_melted, x='Statut', y='Nombre', color='Sexe', 
                           barmode='group', title="Traitement RR/MDR par sexe")
        st.plotly_chart(fig_rr_tx, use_container_width=True)
    
    with col4:
        taux_rr_tx = df_filtered['rrmdr_treatment_success_rate'].mean()
        fig_rr_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=taux_rr_tx,
            title={'text': "Taux de succès RR/MDR (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#d62728"}}))
        fig_rr_gauge.update_layout(height=300)
        st.plotly_chart(fig_rr_gauge, use_container_width=True)
    
    st.subheader("📊 Nouveaux cas et rechutes par âge et sexe")
    
    age_categories = ['0-4', '5-14', '15-24', '25-34', '35-44', '45-54', '55-64', '≥65']
    
    hommes_data = [
        df_filtered['q3_4_g04'].sum(),
        df_filtered['q3_4_g514'].sum(),
        df_filtered['q3_4_h1524'].sum(),
        df_filtered['q3_4_h2534'].sum(),
        df_filtered['q3_4_h3544'].sum(),
        df_filtered['q3_4_h4554'].sum(),
        df_filtered['q3_4_h5564'].sum(),
        df_filtered['q3_4_h65p'].sum()
    ]
    
    femmes_data = [
        df_filtered['q3_4_f04'].sum(),
        df_filtered['q3_4_f514'].sum(),
        df_filtered['q3_4_f1524'].sum(),
        df_filtered['q3_4_f2534'].sum(),
        df_filtered['q3_4_f3544'].sum(),
        df_filtered['q3_4_f4554'].sum(),
        df_filtered['q3_4_f5564'].sum(),
        df_filtered['q3_4_f65p'].sum()
    ]
    
    age_df = pd.DataFrame({
        'Tranche d\'âge': age_categories,
        'Hommes': hommes_data,
        'Femmes': femmes_data
    })
    
    fig_age_detailed = px.bar(age_df, x='Tranche d\'âge', y=['Hommes', 'Femmes'],
                               barmode='group', title="Distribution détaillée par âge et sexe",
                               color_discrete_sequence=['#1f77b4', '#ff7f0e'])
    st.plotly_chart(fig_age_detailed, use_container_width=True)

def show_prevention_tab(df_filtered):
    """Onglet Prévention TPT avec focus enfants <5 ans"""
    st.subheader("🛡️ Traitement Préventif à la Tuberculose (TPT)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Dépistés TPT", f"{df_filtered['q8_0_hf_total'].sum():,.0f}")
    with col2:
        st.metric("Éligibles TPT", f"{df_filtered['tpt_eligible_total'].sum():,.0f}")
    with col3:
        st.metric("Ont commencé", f"{df_filtered['tpt_started_total'].sum():,.0f}")
    with col4:
        st.metric("Ont terminé", f"{df_filtered['tpt_completed_total'].sum():,.0f}")
    with col5:
        tpt_cov = df_filtered['tpt_coverage'].mean()
        st.metric("Couverture", f"{tpt_cov:.1f}%")
    
    st.markdown("### 👶 Focus : Enfants de moins de 5 ans")
    
    enfants_data = {
        'Dépistés': df_filtered['enfants_moins_5_depistes'].sum(),
        'Éligibles': df_filtered['enfants_moins_5_eligibles'].sum(),
        'TPT commencé': df_filtered['enfants_moins_5_commences'].sum(),
        'TPT terminé': df_filtered['enfants_moins_5_termines'].sum()
    }
    
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    with col_e1:
        st.metric("👶 Enfants <5 ans dépistés", f"{enfants_data['Dépistés']:,.0f}")
    with col_e2:
        st.metric("✅ Enfants <5 ans éligibles", f"{enfants_data['Éligibles']:,.0f}")
    with col_e3:
        st.metric("💊 Enfants <5 ans ont commencé", f"{enfants_data['TPT commencé']:,.0f}")
    with col_e4:
        st.metric("🏁 Enfants <5 ans ont terminé", f"{enfants_data['TPT terminé']:,.0f}")
    
    enfants_df = pd.DataFrame({
        'Étape': ['Dépistés', 'Éligibles', 'TPT commencé', 'TPT terminé'],
        'Nombre': list(enfants_data.values())
    })
    fig_enfants = px.bar(enfants_df, x='Étape', y='Nombre', 
                         title="Cascade TPT pour les enfants de moins de 5 ans",
                         color='Étape', text='Nombre')
    fig_enfants.update_traces(textposition='outside')
    st.plotly_chart(fig_enfants, use_container_width=True)
    
    st.subheader("📊 TPT par groupe cible")
    
    tpt_flow = pd.DataFrame({
        'Groupe cible': ['Contacts (dont <5 ans)', 'PVVIH', 'Autres groupes'],
        'Dépistés': [
            df_filtered['q8_0_hf_total'].sum(),
            df_filtered['q8_2_hf_total'].sum(),
            df_filtered['q8_3_hf_total'].sum()
        ],
        'Éligibles': [
            df_filtered['q8_4_hf_total'].sum(),
            df_filtered['q8_5_hf_total'].sum(),
            df_filtered['q8_6_hf_total'].sum()
        ],
        'Ont commencé': [
            df_filtered['q9_1_hf_total'].sum(),
            df_filtered['q9_2_hf_total'].sum(),
            df_filtered['q9_3_hf_total'].sum()
        ],
        'Ont terminé': [
            df_filtered['q10_0_hf_total'].sum(),
            df_filtered['q10_1_hf_total'].sum(),
            df_filtered['q10_2_hf_total'].sum()
        ]
    })
    
    tpt_flow_melted = tpt_flow.melt(id_vars=['Groupe cible'], var_name='Étape', value_name='Nombre')
    fig_tpt_flow = px.bar(tpt_flow_melted, x='Groupe cible', y='Nombre', color='Étape',
                          barmode='group', title="Cascade TPT par groupe cible")
    st.plotly_chart(fig_tpt_flow, use_container_width=True)
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        fig_tpt_cov = go.Figure(go.Indicator(
            mode="gauge+number",
            value=df_filtered['tpt_coverage'].mean(),
            title={'text': "Couverture TPT (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#17becf"}}))
        fig_tpt_cov.update_layout(height=300)
        st.plotly_chart(fig_tpt_cov, use_container_width=True)
    
    with col_c2:
        fig_tpt_comp = go.Figure(go.Indicator(
            mode="gauge+number",
            value=df_filtered['tpt_completion_rate'].mean(),
            title={'text': "Taux d'achèvement TPT (%)"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "#2ca02c"}}))
        fig_tpt_comp.update_layout(height=300)
        st.plotly_chart(fig_tpt_comp, use_container_width=True)

def show_logistique_tab(df_filtered):
    """Onglet Logistique"""
    st.subheader("📦 Gestion des stocks et intrants")
    
    produits = {
        'Cartouches Xpert MTB/RIF': {
            'initial': 'xpert_stock_initial',
            'physique': 'xpert_stock_physique',
            'rupture': 'xpert_jours_rupture',
            'expiration': 'xpert_quantite_expiration'
        },
        'Ethambutol (E) 100 mg': {
            'initial': 'e100_stock_initial',
            'physique': 'e100_stock_physique',
            'rupture': 'e100_jours_rupture',
            'expiration': 'e100_quantite_expiration'
        },
        'RHZE 150/75/400/275 mg': {
            'initial': 'rhze_stock_initial',
            'physique': 'rhze_stock_physique',
            'rupture': 'rhze_jours_rupture',
            'expiration': 'rhze_quantite_expiration'
        },
        'RH 150/75 mg': {
            'initial': 'rh150_stock_initial',
            'physique': 'rh150_stock_physique',
            'rupture': 'rh150_jours_rupture',
            'expiration': 'rh150_quantite_expiration'
        },
        'RH 75/50 mg': {
            'initial': 'rh75_stock_initial',
            'physique': 'rh75_stock_physique',
            'rupture': 'rh75_jours_rupture',
            'expiration': 'rh75_quantite_expiration'
        }
    }
    
    for produit, colonnes in produits.items():
        with st.expander(f"📊 {produit}"):
            if all(col in df_filtered.columns for col in colonnes.values()):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Stock initial", f"{df_filtered[colonnes['initial']].sum():,.0f}")
                with col2:
                    st.metric("Stock physique", f"{df_filtered[colonnes['physique']].sum():,.0f}")
                with col3:
                    jours_rupture = df_filtered[colonnes['rupture']].sum()
                    st.metric("Jours de rupture", f"{jours_rupture:.0f}")
                with col4:
                    qte_expiration = df_filtered[colonnes['expiration']].sum()
                    st.metric("Expiration <6 mois", f"{qte_expiration:.0f}")
                
                if jours_rupture > 0:
                    st.warning(f"⚠️ Rupture de stock : {jours_rupture:.0f} jours")
                if qte_expiration > 0:
                    st.error(f"🔴 Expiration imminente : {qte_expiration:.0f} unités")
            else:
                st.info(f"Données non disponibles pour {produit}")

def show_completude_promptitude_tab(df):
    """Onglet Complétude et Promptitude avec tableau récapitulatif par province"""
    st.subheader("📊 Complétude et Promptitude des rapports")
    st.markdown(f"**Date limite de soumission :** Le {DATE_LIMITE_JOUR} de chaque mois")
    
    if 'date_saisie' in df.columns:
        total_soumissions = len(df)
        soumissions_a_temps = df['est_prompt'].sum() if 'est_prompt' in df.columns else 0
        taux_promptitude_global = (soumissions_a_temps / total_soumissions * 100) if total_soumissions > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total soumissions", f"{total_soumissions}")
        with col2:
            st.metric("Soumissions à temps", f"{soumissions_a_temps}")
        with col3:
            st.metric("Taux promptitude global", f"{taux_promptitude_global:.1f}%")
    
    st.markdown("---")
    st.subheader("📋 Tableau récapitulatif de la complétude par province")
    
    if 'province_name' in df.columns:
        # Calcul des indicateurs par province
        completeness = df.groupby('province_name').agg({
            'healthzone_name': 'nunique',
            'facility_name': 'nunique',
            'q1_0_hf_total': 'sum',
            'q1_2_hf_total': 'sum',
            'q2_0_hf_total': 'sum',
            'q3_0_hf_total': 'sum',
            'q4_0_hf_total': 'sum',
            'q5_0_hf_total': 'sum',
            'q8_0_hf_total': 'sum',
            'tpt_started_total': 'sum'
        }).reset_index()
        
        completeness.columns = ['Province', 'ZS_soumises', 'CDT_soumis', 
                                'Dépistages', 'Cas_présumés', 'TB_détectée',
                                'Traitement_DS', 'Test_RR', 'Traitement_RR',
                                'Dépistés_TPT', 'TPT_commencé']
        
        # Fusion avec les références
        completeness = completeness.merge(ZS_CDT_REFERENCE, on='Province', how='outer')
        
        # Remplacer les NaN par 0
        completeness = completeness.fillna(0)
        
        # Calcul des taux
        completeness['Taux_ZS'] = (completeness['ZS_soumises'] / completeness['ZS_attendues'] * 100).round(1)
        completeness['Taux_CDT'] = (completeness['CDT_soumis'] / completeness['CDT_attendus'] * 100).round(1)
        
        # Indicateur de performance
        completeness['Performance'] = completeness.apply(
            lambda row: '✅ Bonne' if row['Taux_ZS'] >= 100 and row['Taux_CDT'] >= 100
            else '⚠️ Moyenne' if row['Taux_ZS'] >= 80 and row['Taux_CDT'] >= 80
            else '🔴 Faible', axis=1
        )
        
        # Réorganiser les colonnes pour l'affichage
        cols_affichage = ['Province', 'ZS_attendues', 'ZS_soumises', 'Taux_ZS',
                         'CDT_attendus', 'CDT_soumis', 'Taux_CDT',
                         'Dépistages', 'Cas_présumés', 'TB_détectée',
                         'Traitement_DS', 'Test_RR', 'Traitement_RR',
                         'Dépistés_TPT', 'TPT_commencé', 'Performance']
        
        cols_affichage = [col for col in cols_affichage if col in completeness.columns]
        df_affichage = completeness[cols_affichage].copy()
        
        for col in df_affichage.columns:
            if col not in ['Province', 'Performance']:
                df_affichage[col] = df_affichage[col].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "0")
        
        st.dataframe(df_affichage, use_container_width=True, height=400)
        
        st.download_button(
            label="📥 Télécharger le tableau de complétude (CSV)",
            data=completeness.to_csv(index=False).encode('utf-8'),
            file_name="completude_provinces.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            fig_zs = go.Figure()
            fig_zs.add_trace(go.Bar(
                x=completeness['Province'],
                y=completeness['Taux_ZS'],
                text=completeness['Taux_ZS'].apply(lambda x: f"{x:.1f}%"),
                textposition='outside',
                marker_color=completeness['Taux_ZS'].apply(
                    lambda x: '#28a745' if x >= 100 else '#ffc107' if x >= 80 else '#dc3545'
                )
            ))
            fig_zs.update_layout(
                title="Taux de complétude des Zones de Santé",
                xaxis_title="Province",
                yaxis_title="Taux (%)",
                height=400,
                yaxis_range=[0, 120],
                showlegend=False
            )
            fig_zs.add_hline(y=100, line_dash="dash", line_color="green", 
                            annotation_text="Cible 100%")
            fig_zs.add_hline(y=80, line_dash="dash", line_color="orange", 
                            annotation_text="Seuil minimal 80%")
            st.plotly_chart(fig_zs, use_container_width=True)
        
        with col_g2:
            fig_cdt = go.Figure()
            fig_cdt.add_trace(go.Bar(
                x=completeness['Province'],
                y=completeness['Taux_CDT'],
                text=completeness['Taux_CDT'].apply(lambda x: f"{x:.1f}%"),
                textposition='outside',
                marker_color=completeness['Taux_CDT'].apply(
                    lambda x: '#28a745' if x >= 100 else '#ffc107' if x >= 80 else '#dc3545'
                )
            ))
            fig_cdt.update_layout(
                title="Taux de complétude des CDT",
                xaxis_title="Province",
                yaxis_title="Taux (%)",
                height=400,
                yaxis_range=[0, 120],
                showlegend=False
            )
            fig_cdt.add_hline(y=100, line_dash="dash", line_color="green", 
                             annotation_text="Cible 100%")
            fig_cdt.add_hline(y=80, line_dash="dash", line_color="orange", 
                             annotation_text="Seuil minimal 80%")
            st.plotly_chart(fig_cdt, use_container_width=True)
        
        st.markdown("### 📊 Synthèse des performances")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        
        with col_m1:
            moy_zs = completeness['Taux_ZS'].mean()
            st.metric("📈 Taux ZS moyen", f"{moy_zs:.1f}%")
        with col_m2:
            moy_cdt = completeness['Taux_CDT'].mean()
            st.metric("📈 Taux CDT moyen", f"{moy_cdt:.1f}%")
        with col_m3:
            nb_bonnes = len(completeness[completeness['Performance'] == '✅ Bonne'])
            st.metric("✅ Provinces en bonne performance", f"{nb_bonnes}/{len(completeness)}")
        with col_m4:
            nb_faibles = len(completeness[completeness['Performance'] == '🔴 Faible'])
            st.metric("🔴 Provinces en performance faible", f"{nb_faibles}/{len(completeness)}")

def show_donnees_brutes_tab(df_filtered):
    """Onglet Données brutes"""
    st.subheader("📋 Aperçu des données collectées")
    
    colonnes_a_afficher = ['province_name', 'healthzone_name', 'facility_name', 'mois_nom', 'qannee', 'trimestre']
    colonnes_disponibles = [col for col in colonnes_a_afficher if col in df_filtered.columns]
    colonnes_disponibles.extend([col for col in df_filtered.columns if col.startswith('q') and '_hf_total' in col][:10])
    
    st.dataframe(df_filtered[colonnes_disponibles], use_container_width=True)
    
    st.download_button(
        label="📥 Télécharger les données (CSV)",
        data=df_filtered.to_csv(index=False).encode('utf-8'),
        file_name="stop_tb_export.csv",
        mime="text/csv"
    )

# ============================================================================
# ONGLET STOCKS PAR PROVINCE
# ============================================================================

def safe_int_convert(value):
    """Convertit une valeur en entier de manière sécurisée"""
    try:
        if pd.isna(value) or np.isinf(value) or np.isnan(value):
            return 0
        return int(value)
    except (ValueError, TypeError):
        return 0

def show_stocks_province_tab(df):
    """Onglet 7 : Gestion des stocks par province"""
    st.subheader("📊 Gestion des stocks par province")
    st.markdown("**Analyse des stocks :** Consommation Moyenne Mensuelle (CMM) vs Stock Disponible")
    
    colonnes_necessaires = ['province_name', 'q_cmm', 'q_stock_disp', 'stock_pro', 'stock_cdr']
    colonnes_manquantes = [col for col in colonnes_necessaires if col not in df.columns]
    
    if colonnes_manquantes:
        st.warning(f"⚠️ Colonnes manquantes dans les données : {', '.join(colonnes_manquantes)}")
        with st.expander("🔍 Voir les colonnes disponibles"):
            st.write(list(df.columns))
        return
    
    for col in ['q_cmm', 'q_stock_disp', 'stock_pro', 'stock_cdr']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df[col] = df[col].replace([np.inf, -np.inf], 0)
    
    stocks_province = df.groupby('province_name').agg({
        'q_cmm': 'sum',
        'q_stock_disp': 'sum',
        'stock_pro': 'sum',
        'stock_cdr': 'sum'
    }).reset_index()
    
    for col in ['q_cmm', 'q_stock_disp', 'stock_pro', 'stock_cdr']:
        stocks_province[col] = stocks_province[col].fillna(0)
    
    stocks_province['alerte_rouge'] = stocks_province['q_cmm'] < stocks_province['q_stock_disp']
    stocks_province['ratio_stock_cmm'] = stocks_province.apply(
        lambda row: row['q_stock_disp'] / row['q_cmm'] if row['q_cmm'] > 0 else 0, 
        axis=1
    )
    
    ordre_provinces = [
        'Haut Katanga', 'Haut Lomami', 'Kasai Oriental', 'Kasai Central',
        'Lualaba', 'Lomami', 'Sud Kivu', 'Sankuru', 'Tanganyika'
    ]
    stocks_province['province_name'] = pd.Categorical(stocks_province['province_name'], 
                                                       categories=ordre_provinces, 
                                                       ordered=True)
    stocks_province = stocks_province.sort_values('province_name')
    
    total_cmm = safe_int_convert(stocks_province['q_cmm'].sum())
    total_stock = safe_int_convert(stocks_province['q_stock_disp'].sum())
    total_stock_pro = safe_int_convert(stocks_province['stock_pro'].sum())
    total_stock_cdr = safe_int_convert(stocks_province['stock_cdr'].sum())
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Total CMM", f"{total_cmm:,.0f}")
    with col2:
        st.metric("🏭 Total Stock Disponible", f"{total_stock:,.0f}")
    with col3:
        st.metric("📋 Total Stock Programmé", f"{total_stock_pro:,.0f}")
    with col4:
        st.metric("🏢 Total Stock CDR", f"{total_stock_cdr:,.0f}")
    
    df_affichage = stocks_province.copy()
    df_affichage['ratio_stock_cmm'] = df_affichage['ratio_stock_cmm'].apply(
        lambda x: f"{x:.1f}x" if x > 0 else "N/A"
    )
    df_affichage['alerte'] = df_affichage['alerte_rouge'].apply(
        lambda x: "🔴 ALERTE : Stock > CMM" if x else "✅ OK"
    )
    
    colonnes_affichage = {
        'province_name': 'Province',
        'q_cmm': 'CMM',
        'q_stock_disp': 'Stock Disponible',
        'stock_pro': 'Stock Programmée',
        'stock_cdr': 'Stock CDR',
        'ratio_stock_cmm': 'Ratio Stock/CMM',
        'alerte': 'Statut'
    }
    
    df_style = df_affichage[list(colonnes_affichage.keys())].rename(columns=colonnes_affichage)
    st.dataframe(df_style, use_container_width=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=stocks_province['province_name'],
        y=stocks_province['q_cmm'],
        name='CMM',
        marker_color='#1f77b4'
    ))
    fig.add_trace(go.Bar(
        x=stocks_province['province_name'],
        y=stocks_province['q_stock_disp'],
        name='Stock Disponible',
        marker_color=stocks_province['alerte_rouge'].apply(
            lambda x: '#d62728' if x else '#2ca02c'
        )
    ))
    fig.update_layout(
        title="Comparaison CMM et Stock Disponible par province",
        xaxis_title="Province",
        yaxis_title="Quantité",
        barmode='group',
        height=500,
        xaxis={'tickangle': 45}
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main():
    try:
        df = load_and_process_data()
        
        # ==================== SIDEBAR FILTRES ====================
        st.sidebar.header("🔍 Filtres")
        
        # 1. NIVEAU HIÉRARCHIQUE
        st.sidebar.subheader("📍 Niveau géographique")
        niveau = st.sidebar.radio(
            "Sélectionnez le niveau",
            options=['National', 'Provincial', 'Etablissement'],
            horizontal=True
        )
        
        province_selectionne = "Toutes"
        facility_selectionne = "Tous"
        
        # Liste des provinces disponibles
        provinces_disponibles = df['province_name'].dropna().unique().tolist() if 'province_name' in df.columns else []
        provinces_disponibles = sorted([p for p in provinces_disponibles if p and str(p) != 'nan'])
        
        # Ajouter l'option "Toutes"
        provinces_options = ['Toutes'] + provinces_disponibles
        
        if niveau == 'Provincial':
            province_selectionne = st.sidebar.selectbox(
                "Sélectionnez la Province", 
                options=provinces_options,
                index=0
            )
            
        elif niveau == 'Etablissement':
            province_selectionne = st.sidebar.selectbox(
                "Sélectionnez la Province", 
                options=provinces_options,
                index=0
            )
            
            if province_selectionne and province_selectionne != 'Toutes':
                facilities_disponibles = df[df['province_name'] == province_selectionne]['facility_name'].dropna().unique().tolist()
                facilities_disponibles = sorted([f for f in facilities_disponibles if f and str(f) != 'nan'])
                
                # Ajouter l'option "Tous"
                facilities_options = ['Tous'] + facilities_disponibles
                
                facility_selectionne = st.sidebar.selectbox(
                    "Sélectionnez l'Établissement", 
                    options=facilities_options,
                    index=0
                )
            else:
                st.sidebar.info("Sélectionnez d'abord une province pour voir les établissements")
        
        # 2. PÉRIODE
        st.sidebar.subheader("📅 Période")
        type_periode = st.sidebar.radio(
            "Type de période",
            options=['Mois', 'Trimestre'],
            horizontal=True
        )
        
        df_filtered = df.copy()
        
        if type_periode == 'Mois':
            if 'mois_nom' in df.columns and 'qannee' in df.columns:
                mois_options = sorted(df['mois_nom'].dropna().unique())
                if mois_options:
                    mois_selectionne = st.sidebar.selectbox("Mois", options=mois_options)
                    annee_options = sorted(df['qannee'].dropna().unique())
                    annee_selectionne = st.sidebar.selectbox("Année", options=annee_options)
                    df_filtered = df_filtered[(df_filtered['mois_nom'] == mois_selectionne) & 
                                               (df_filtered['qannee'] == annee_selectionne)]
        else:
            if 'trimestre' in df.columns and 'qannee' in df.columns:
                trimestre_options = ['T1', 'T2', 'T3', 'T4']
                trimestre_selectionne = st.sidebar.selectbox("Trimestre", options=trimestre_options)
                annee_options = sorted(df['qannee'].dropna().unique())
                if annee_options:
                    annee_selectionne = st.sidebar.selectbox("Année", options=annee_options)
                    df_filtered = df_filtered[(df_filtered['trimestre'] == trimestre_selectionne) & 
                                               (df_filtered['qannee'] == annee_selectionne)]
        
        # Application du filtre hiérarchique
        df_filtered = filter_by_hierarchy(df_filtered, niveau, province_selectionne, facility_selectionne)
        
        # Affichage du contexte
        st.sidebar.info(f"📊 **{len(df_filtered)}** établissements affichés")
        if niveau == 'Provincial' and province_selectionne and province_selectionne != 'Toutes':
            st.sidebar.success(f"📍 Province : {province_selectionne}")
        elif niveau == 'Etablissement' and facility_selectionne and facility_selectionne != 'Tous':
            st.sidebar.success(f"🏥 Établissement : {facility_selectionne}")
        elif niveau == 'Etablissement' and province_selectionne and province_selectionne != 'Toutes':
            st.sidebar.success(f"📍 Province : {province_selectionne} (tous les établissements)")
        elif niveau == 'National' or (niveau == 'Provincial' and province_selectionne == 'Toutes'):
            st.sidebar.success("🌍 Vue Nationale")
        
        # KPI principaux
        show_kpi_cards(df_filtered, niveau)
        
        # Onglets
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📈 Dépistage & Diagnostic",
            "💊 Traitement",
            "🛡️ Prévention (TPT)",
            "📦 Logistique",
            "📊 Complétude & Promptitude",
            "📋 Données brutes",
            "🏭 Stocks par Province"
        ])
        
        with tab1:
            show_depistage_tab(df_filtered)
        with tab2:
            show_traitement_tab(df_filtered)
        with tab3:
            show_prevention_tab(df_filtered)
        with tab4:
            show_logistique_tab(df_filtered)
        with tab5:
            show_completude_promptitude_tab(df_filtered)
        with tab6:
            show_donnees_brutes_tab(df_filtered)
        with tab7:
            show_stocks_province_tab(df)
        
        st.markdown("---")
        st.markdown(f"*Dernière mise à jour : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
    except FileNotFoundError:
        st.error("""
        ❌ **Fichier introuvable !**
        
        Le fichier `drc_stop_tb_data.csv` n'a pas été trouvé.
        Vérifiez qu'il se trouve dans le même répertoire que ce script.
        """)
    except Exception as e:
        st.error(f"❌ Erreur : {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()