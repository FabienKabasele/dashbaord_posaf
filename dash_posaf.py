import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Dashboard POSAF 2026", layout="wide")
st.title("📊 Tableau de Bord - Suivi des Activités POSAF 2026")

# --- Chargement des données ---
@st.cache_data
def load_data():
    df = pd.read_excel('POSAF_SCRUM (1).xlsx', sheet_name='2026')
    df.columns = df.columns.str.strip()
    date_cols = ['Date de début', 'Date de fin']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

df = load_data()

# --- Fonction pour convertir l'état en pourcentage numérique ---
def etat_to_pourcentage(etat):
    if pd.isna(etat):
        return 0
    etat_str = str(etat)
    if 'Pas commencé' in etat_str:
        return 0
    elif '50 à 69%' in etat_str:
        return 60
    elif '70 à 79' in etat_str:
        return 75
    elif '80-99%' in etat_str:
        return 90
    elif '1.0' in etat_str or '100%' in etat_str:
        return 100
    else:
        return 0

df['avancement_pct'] = df['État'].apply(etat_to_pourcentage)

# --- Barre latérale pour les filtres ---
st.sidebar.header("🔍 Filtres")

# Filtre par Service
services = ['Tous'] + sorted(df['Services'].dropna().unique().tolist())
selected_service = st.sidebar.selectbox("Service", services)

# Filtre par Projet
projets = ['Tous'] + sorted(df['Projet'].dropna().unique().tolist())
selected_projet = st.sidebar.selectbox("Projet", projets)

# Filtre par Classification
classification_values = [str(x) for x in df['Classification'].dropna().unique().tolist()]
classification_values.sort()
classifications = ['Tous'] + classification_values
selected_classification = st.sidebar.selectbox("Classification", classifications)

# Filtre par État
etat_values = [str(x) for x in df['État'].dropna().unique().tolist()]
etat_values.sort()
etats = ['Tous'] + etat_values
selected_etat = st.sidebar.selectbox("État d'avancement", etats)

# --- FILTRE PAR PÉRIODE (IMPORTANT) ---
st.sidebar.subheader("📅 Période")
if 'Date de début' in df.columns and 'Date de fin' in df.columns:
    # Récupérer les dates min et max valides
    dates_debut = df['Date de début'].dropna()
    dates_fin = df['Date de fin'].dropna()
    
    if not dates_debut.empty and not dates_fin.empty:
        min_date = dates_debut.min()
        max_date = dates_fin.max()
        
        # Convertir en date si c'est un Timestamp
        if hasattr(min_date, 'date'):
            min_date = min_date.date()
        if hasattr(max_date, 'date'):
            max_date = max_date.date()
        
        date_debut = st.sidebar.date_input(
            "Date de début",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
        date_fin = st.sidebar.date_input(
            "Date de fin",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    else:
        st.sidebar.warning("Aucune date valide dans les données")
        date_debut = None
        date_fin = None
else:
    st.sidebar.warning("Colonnes de dates non disponibles")
    date_debut = None
    date_fin = None

# Application des filtres
filtered_df = df.copy()
if selected_service != 'Tous':
    filtered_df = filtered_df[filtered_df['Services'] == selected_service]
if selected_projet != 'Tous':
    filtered_df = filtered_df[filtered_df['Projet'] == selected_projet]
if selected_classification != 'Tous':
    filtered_df = filtered_df[filtered_df['Classification'].astype(str) == selected_classification]
if selected_etat != 'Tous':
    filtered_df = filtered_df[filtered_df['État'].astype(str) == selected_etat]

# Application du filtre de période
if date_debut and date_fin:
    date_debut = pd.to_datetime(date_debut)
    date_fin = pd.to_datetime(date_fin)
    
    # Filtrer sur les activités dont la date de début ou de fin est dans la période
    mask = (
        (filtered_df['Date de début'].notna() & (filtered_df['Date de début'] >= date_debut) & (filtered_df['Date de début'] <= date_fin)) |
        (filtered_df['Date de fin'].notna() & (filtered_df['Date de fin'] >= date_debut) & (filtered_df['Date de fin'] <= date_fin))
    )
    filtered_df = filtered_df[mask]

# --- Calcul des KPI ---
total_activites = len(filtered_df)
avg_avancement = filtered_df['avancement_pct'].mean() if total_activites > 0 else 0
activites_urgentes = filtered_df[filtered_df['Classification'].astype(str).str.contains('urgent', na=False, case=False)].shape[0]
activites_terminees = filtered_df[filtered_df['avancement_pct'] >= 90].shape[0]
semaines_uniques = filtered_df['Semaine'].nunique()
taux_urgence = (activites_urgentes / total_activites * 100) if total_activites > 0 else 0
taux_achevement = (activites_terminees / total_activites * 100) if total_activites > 0 else 0

# --- SECTION INDICATEURS CLÉS (sans jauges) ---
st.header("📈 Indicateurs Clés")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📊 Total Activités", total_activites)

with col2:
    st.metric("📈 Avancement moyen", f"{avg_avancement:.1f}%")

with col3:
    st.metric("⚠️ Activités urgentes", activites_urgentes)

with col4:
    st.metric("✅ Activités terminées", activites_terminees)

with col5:
    st.metric("📅 Semaines couvertes", semaines_uniques)

st.markdown("---")

# --- GRAPHIQUES ---
st.header("📊 Visualisations")

tab1, tab2, tab3, tab4 = st.tabs([
    "Par Projet",
    "Par Service (Planification vs Réalisation)",
    "Calendrier",
    "Données détaillées"
])

with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        projet_counts = filtered_df['Projet'].value_counts().reset_index()
        projet_counts.columns = ['Projet', 'Nombre']
        fig = px.pie(projet_counts, values='Nombre', names='Projet',
                     title="Répartition des activités par Projet",
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        avancement_projet = filtered_df.groupby('Projet')['avancement_pct'].mean().reset_index()
        avancement_projet.columns = ['Projet', 'Avancement moyen (%)']
        fig = px.bar(avancement_projet, x='Projet', y='Avancement moyen (%)',
                     title="Avancement moyen par Projet", color='Projet', text_auto='.1f')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📋 PLANIFICATION : Ce qui est prévu")
    
    # --- Graphiques de planification ---
    col_left, col_right = st.columns(2)

    with col_left:
        service_counts = filtered_df['Services'].value_counts().reset_index()
        service_counts.columns = ['Services', 'Nombre']
        fig = px.bar(service_counts, x='Services', y='Nombre',
                     title="📋 Planification : Nombre d'activités prévues par Service",
                     color='Services', text_auto=True)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        pivot = pd.crosstab(filtered_df['Services'], filtered_df['Projet'])
        fig = px.imshow(pivot, text_auto=True,
                        title="📋 Planification : Matrice Services vs Projets (activités prévues)",
                        color_continuous_scale='Blues', aspect="auto")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("✅ RÉALISATION : Où en est-on ?")
    
    # --- Graphiques de réalisation (basés sur les mêmes données filtrées) ---
    col_left, col_right = st.columns(2)

    with col_left:
        # Avancement par service (les mêmes services que dans la planification)
        avancement_service = filtered_df.groupby('Services')['avancement_pct'].mean().reset_index()
        avancement_service.columns = ['Services', 'Avancement réel (%)']
        avancement_service = avancement_service.sort_values('Avancement réel (%)', ascending=True)

        fig = px.bar(avancement_service,
                     x='Avancement réel (%)', y='Services',
                     title="✅ Réalisation : Avancement réel par Service\n(par rapport aux activités prévues)",
                     color='Avancement réel (%)',
                     color_continuous_scale=['#FF6B6B', '#FFE66D', '#6BCB77'],
                     text_auto='.1f', orientation='h')
        fig.update_layout(xaxis_title="Avancement réel (%)", yaxis_title="Service", showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # Répartition par état d'avancement
        etat_counts = filtered_df['État'].value_counts().reset_index()
        etat_counts.columns = ['État', 'Nombre']

        ordre_etats = ['Pas commencé', '50 à 69%', '70 à 79', '80-99%', '1.0', '100%']
        # Garder seulement les états qui existent
        ordre_etats_existants = [e for e in ordre_etats if e in etat_counts['État'].values]
        
        if ordre_etats_existants:
            etat_counts['État_ordre'] = pd.Categorical(etat_counts['État'], categories=ordre_etats_existants, ordered=True)
            etat_counts = etat_counts.sort_values('État_ordre')

        couleurs = {
            'Pas commencé': '#FF6B6B', '50 à 69%': '#FFB347', '70 à 79': '#FFE66D',
            '80-99%': '#6BCB77', '1.0': '#4CAF50', '100%': '#2E7D32'
        }

        fig = px.bar(etat_counts, x='État', y='Nombre',
                     title="✅ Réalisation : État d'avancement des activités prévues",
                     color='État', color_discrete_map=couleurs, text_auto=True)
        fig.update_layout(showlegend=False, xaxis_title="État d'avancement", yaxis_title="Nombre d'activités")
        st.plotly_chart(fig, use_container_width=True)

    # --- Graphique comparatif supplémentaire ---
    if not filtered_df.empty:
        st.markdown("---")
        st.subheader("📊 Comparaison Planification vs Réalisation")

        # Calcul du nombre d'activités par service et de leur avancement
        comp_df = filtered_df.groupby('Services').agg({
            'Activités': 'count',
            'avancement_pct': 'mean'
        }).reset_index()
        comp_df.columns = ['Services', 'Nb activités prévues', 'Avancement réel (%)']
        comp_df = comp_df.sort_values('Nb activités prévues', ascending=False)

        if not comp_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=comp_df['Services'],
                y=comp_df['Nb activités prévues'],
                name='Activités prévues',
                marker_color='#4C72B0'
            ))
            fig.add_trace(go.Scatter(
                x=comp_df['Services'],
                y=comp_df['Avancement réel (%)'],
                name='Avancement réel (%)',
                yaxis='y2',
                mode='lines+markers',
                marker=dict(color='#DD8452', size=10),
                line=dict(color='#DD8452', width=3)
            ))
            fig.update_layout(
                title="📊 Comparaison : Volume d'activités prévues vs Taux d'avancement par Service",
                xaxis_title="Service",
                yaxis_title="Nombre d'activités prévues",
                yaxis2=dict(title="Avancement réel (%)", overlaying='y', side='right', range=[0, 110]),
                legend=dict(x=0.02, y=0.98),
                hovermode='x'
            )
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    if 'Date de début' in filtered_df.columns and 'Date de fin' in filtered_df.columns:
        gantt_df = filtered_df.dropna(subset=['Date de début', 'Date de fin']).copy()
        if not gantt_df.empty:
            gantt_df['Activité courte'] = gantt_df['Activités'].str[:30] + '...'
            fig = px.timeline(gantt_df, x_start='Date de début', x_end='Date de fin',
                              y='Activité courte', color='Projet',
                              title="📅 Calendrier des activités",
                              hover_data=['Responsable', 'État'])
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée de date disponible pour le calendrier")
    else:
        st.info("Colonnes de dates non disponibles")

with tab4:
    st.subheader("📋 Données détaillées")
    default_cols = ['Semaine', 'Services', 'Projet', 'Activités', 'Responsable',
                    'Classification', 'État', 'Date de début', 'Date de fin']
    available_cols = [col for col in default_cols if col in filtered_df.columns]
    display_cols = st.multiselect("Choisir les colonnes à afficher",
                                   options=filtered_df.columns.tolist(),
                                   default=available_cols)
    if display_cols:
        st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True,
                     column_config={'Activités': st.column_config.TextColumn(width='large'),
                                    'Date de début': st.column_config.DateColumn(format="DD/MM/YYYY"),
                                    'Date de fin': st.column_config.DateColumn(format="DD/MM/YYYY")})

    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Télécharger les données filtrées (CSV)",
                       data=csv,
                       file_name=f"posaf_2026_filtre_{datetime.now().strftime('%Y%m%d')}.csv",
                       mime="text/csv")

# --- Pied de page ---
st.markdown("---")
st.caption(f"Dernière mise à jour des données : {datetime.now().strftime('%d/%m/%Y %H:%M')}")