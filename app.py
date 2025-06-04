import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp
from calculs import OptimisationRemunerationSARL

def main():
    st.set_page_config(
        page_title="Optimisation Fiscale SARL + Holding",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🎯 Optimisation Fiscale SARL + Holding")
    st.markdown("---")
    
    # Sidebar pour la configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Paramètres de base
        st.subheader("📊 Paramètres de base")
        resultat_initial = st.number_input(
            "Résultat avant rémunération (€)",
            min_value=0,
            value=300000,
            step=10000,
            help="Résultat de votre SARL avant déduction de la rémunération de gérance"
        )
        
        charges_existantes = st.number_input(
            "Charges existantes (€)",
            min_value=0,
            value=50000,
            step=5000,
            help="Autres charges déjà déduites du résultat"
        )
        
        parts_fiscales = st.number_input(
            "Nombre de parts fiscales",
            min_value=1.0,
            value=1.0,
            step=0.5,
            help="Votre nombre de parts fiscales pour le calcul de l'IR"
        )
        
        # Optimisations fiscales
        st.subheader("🎯 Optimisations Fiscales")
        
        st.markdown("**Cochez les optimisations que vous souhaitez activer :**")
        
        # PER
        use_per = st.checkbox(
            "📈 Plan d'Épargne Retraite (PER)",
            help="Déduction fiscale sur le revenu imposable (max 32,419€ en 2024)"
        )
        per_max = 0
        if use_per:
            per_max = st.slider(
                "Montant PER maximum (€)",
                min_value=0,
                max_value=50000,
                value=32419,
                step=1000,
                help="Plafond légal : 8 x PASS = 32,419€ en 2024"
            )
        
        # Madelin
        use_madelin = st.checkbox(
            "🏥 Contrat Madelin TNS",
            help="Déduction fiscale complémentaire pour les TNS (max 84,000€ en 2024)"
        )
        madelin_max = 0
        if use_madelin:
            madelin_max = st.slider(
                "Montant Madelin maximum (€)",
                min_value=0,
                max_value=100000,
                value=84000,
                step=5000,
                help="Plafond légal pour les contrats Madelin TNS"
            )
        
        # Girardin
        use_girardin = st.checkbox(
            "🏭 Girardin Industriel",
            help="⚠️ ATTENTION : Il s'agit d'une DÉPENSE qui génère une réduction d'impôt"
        )
        girardin_max = 0
        if use_girardin:
            st.warning("⚠️ Le Girardin Industriel nécessite un INVESTISSEMENT réel. C'est une dépense qui génère une réduction d'impôt.")
            girardin_max = st.slider(
                "Montant d'investissement Girardin (€)",
                min_value=0,
                max_value=100000,
                value=50000,
                step=5000,
                help="Montant de l'investissement (dépense) qui génère la réduction d'impôt"
            )
        
        # Paramètres de calcul
        st.subheader("⚙️ Paramètres de calcul")
        pas_calcul = st.selectbox(
            "Précision du calcul",
            options=[1000, 2500, 5000, 10000],
            index=1,
            help="Plus le pas est petit, plus le calcul est précis mais plus long"
        )
        
        # Bouton de calcul
        if st.button("🚀 Calculer l'optimisation", type="primary"):
            st.session_state.run_calculation = True
    
    # Zone principale
    if 'run_calculation' not in st.session_state:
        st.session_state.run_calculation = False
    
    if st.session_state.run_calculation:
        # Initialisation de l'optimiseur
        with st.spinner("🔄 Calcul en cours..."):
            optimiseur = OptimisationRemunerationSARL(
                resultat_avant_remuneration=resultat_initial,
                charges_existantes=charges_existantes,
                parts_fiscales=parts_fiscales
            )
            
            # Optimisation avec niches fiscales
            meilleur_global, tous_scenarios_niches = optimiseur.optimiser_avec_niches(
                pas=pas_calcul,
                per_max=per_max if use_per else 0,
                madelin_max=madelin_max if use_madelin else 0,
                girardin_max=girardin_max if use_girardin else 0
            )
            
            # Forcer l'utilisation des optimisations cochées par l'utilisateur
            meilleur_avec_niches = None
            for strategie in tous_scenarios_niches:
                opt = strategie['optimisations']
                # Vérifier si cette stratégie correspond aux choix de l'utilisateur
                per_match = (opt['per'] > 0) == use_per
                madelin_match = (opt['madelin'] > 0) == use_madelin  
                girardin_match = (opt['girardin'] > 0) == use_girardin
                
                if per_match and madelin_match and girardin_match:
                    if meilleur_avec_niches is None or strategie['meilleur']['total_net'] > meilleur_avec_niches['total_net']:
                        meilleur_avec_niches = strategie['meilleur']
            
            # Si aucune stratégie ne correspond, utiliser la meilleure globale
            if meilleur_avec_niches is None:
                meilleur_avec_niches = meilleur_global
            
            # Optimisation classique pour comparaison
            meilleur_classique, scenarios_classiques = optimiseur.optimiser(pas=pas_calcul)
        
        # Affichage des résultats
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🏆 Résultat Optimal")
            
            # Métriques principales
            st.metric(
                "💰 Total Net Optimal",
                f"{meilleur_avec_niches['total_net']:,.0f}€",
                delta=f"+{meilleur_avec_niches['total_net'] - meilleur_classique['total_net']:,.0f}€"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(
                    "💼 Rémunération Optimale",
                    f"{meilleur_avec_niches['remuneration_brute']:,.0f}€"
                )
            with col_b:
                st.metric(
                    "📉 Taux Prélèvement",
                    f"{meilleur_avec_niches['taux_prelevement_global']:.1f}%"
                )
            
            # Détail des optimisations
            if any(meilleur_avec_niches['optimisations'][k] > 0 for k in ['per', 'madelin', 'girardin']):
                st.subheader("🎯 Optimisations Utilisées")
                
                if meilleur_avec_niches['optimisations']['per'] > 0:
                    st.info(f"📈 PER : {meilleur_avec_niches['optimisations']['per']:,.0f}€")
                
                if meilleur_avec_niches['optimisations']['madelin'] > 0:
                    st.info(f"🏥 Madelin : {meilleur_avec_niches['optimisations']['madelin']:,.0f}€")
                
                if meilleur_avec_niches['optimisations']['girardin'] > 0:
                    st.error(f"🏭 Girardin (DÉPENSE) : {meilleur_avec_niches['optimisations']['girardin']:,.0f}€")
                
                st.success(f"💰 Économies d'impôt totales : {meilleur_avec_niches['optimisations']['economies_ir']:,.0f}€")
        
        with col2:
            st.subheader("📊 Répartition du Revenu")
            
            # Graphique en camembert
            labels = ['Salaire Net', 'Dividendes Nets', 'Cotisations TNS', 'IR', 'IS Total', 'Flat Tax']
            values = [
                meilleur_avec_niches['remuneration_nette_apres_ir'],
                meilleur_avec_niches['dividendes_nets'],
                meilleur_avec_niches['cotisations_tns'],
                meilleur_avec_niches['ir_remuneration'],
                meilleur_avec_niches['is_sarl'] + meilleur_avec_niches['is_holding'],
                meilleur_avec_niches['flat_tax']
            ]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie.update_layout(
                title="Répartition du résultat initial",
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Résumé détaillé complet
        st.subheader("📋 Résumé Détaillé de l'Optimisation")
        
        # Colonnes pour l'affichage du résumé
        col_resume1, col_resume2, col_resume3 = st.columns(3)
        
        with col_resume1:
            st.markdown("**🏢 NIVEAU SARL**")
            st.info(f"""
            **Résultat initial :** {resultat_initial:,.0f}€  
            **Charges existantes :** {charges_existantes:,.0f}€  
            **Résultat avant rémun. :** {resultat_initial - charges_existantes:,.0f}€  
            
            **Rémunération brute :** {meilleur_avec_niches['remuneration_brute']:,.0f}€  
            **Cotisations TNS :** {meilleur_avec_niches['cotisations_tns']:,.0f}€  
            **Résultat après rémun. :** {meilleur_avec_niches['resultat_apres_remuneration']:,.0f}€  
            
            **IS SARL :** {meilleur_avec_niches['is_sarl']:,.0f}€  
            **Dividendes SARL :** {meilleur_avec_niches['dividendes_sarl']:,.0f}€
            """)
        
        with col_resume2:
            st.markdown("**💼 NIVEAU PERSONNEL**")
            st.success(f"""
            **Rémunération nette avant IR :** {meilleur_avec_niches['remuneration_nette_avant_ir']:,.0f}€  
            **Abattement frais pro (10%) :** {meilleur_avec_niches['abattement_frais_pro']:,.0f}€  
            **Revenu imposable initial :** {meilleur_avec_niches['revenu_imposable']:,.0f}€  
            
            **Déductions fiscales :**  
            • PER : {meilleur_avec_niches.get('per_deduction', 0):,.0f}€  
            • Madelin : {meilleur_avec_niches.get('madelin_deduction', 0):,.0f}€  
            **Revenu imposable final :** {meilleur_avec_niches.get('revenu_imposable_final', meilleur_avec_niches['revenu_imposable']):,.0f}€  
            
            **IR avant Girardin :** {meilleur_avec_niches.get('ir_avant_girardin', meilleur_avec_niches['ir_remuneration']):,.0f}€  
            **Réduction Girardin :** {meilleur_avec_niches.get('reduction_girardin', 0):,.0f}€  
            **IR final :** {meilleur_avec_niches['ir_remuneration']:,.0f}€  
            
            **💰 Salaire net après IR :** {meilleur_avec_niches['remuneration_nette_apres_ir']:,.0f}€
            
            **🏭 INVESTISSEMENT GIRARDIN :** -{meilleur_avec_niches['optimisations']['girardin']:,.0f}€
            """)
        
        with col_resume3:
            st.markdown("**🏠 NIVEAU HOLDING + FINAL**")
            st.warning(f"""
            **Dividendes reçus :** {meilleur_avec_niches['dividendes_sarl']:,.0f}€  
            **Quote-part imposable (5%) :** {meilleur_avec_niches['quote_part_imposable']:,.0f}€  
            **IS Holding :** {meilleur_avec_niches['is_holding']:,.0f}€  
            **Dividendes dans holding :** {meilleur_avec_niches['dividendes_holding']:,.0f}€  
            
            **Flat tax (30%) :** {meilleur_avec_niches['flat_tax']:,.0f}€  
            **💎 Dividendes nets :** {meilleur_avec_niches['dividendes_nets']:,.0f}€  
            
            **🎯 TOTAL NET PERÇU :** {meilleur_avec_niches['total_net']:,.0f}€  
            **Taux prélèvement global :** {meilleur_avec_niches['taux_prelevement_global']:.1f}%
            """)
        
        # Tableau récapitulatif des économies d'impôts si optimisations
        if any(meilleur_avec_niches['optimisations'][k] > 0 for k in ['per', 'madelin', 'girardin']):
            st.subheader("💰 Détail des Économies d'Impôts")
            
            col_eco1, col_eco2, col_eco3, col_eco4 = st.columns(4)
            
            with col_eco1:
                if meilleur_avec_niches['optimisations']['per'] > 0:
                    economie_per = meilleur_avec_niches.get('per_deduction', 0) * 0.30  # Estimation 30% d'économie
                    st.metric("📈 PER", f"{meilleur_avec_niches['optimisations']['per']:,.0f}€", f"Économie: {economie_per:,.0f}€")
                else:
                    st.metric("📈 PER", "Non utilisé", "0€")
            
            with col_eco2:
                if meilleur_avec_niches['optimisations']['madelin'] > 0:
                    economie_madelin = meilleur_avec_niches.get('madelin_deduction', 0) * 0.30  # Estimation 30% d'économie
                    st.metric("🏥 Madelin", f"{meilleur_avec_niches['optimisations']['madelin']:,.0f}€", f"Économie: {economie_madelin:,.0f}€")
                else:
                    st.metric("🏥 Madelin", "Non utilisé", "0€")
            
            with col_eco3:
                if meilleur_avec_niches['optimisations']['girardin'] > 0:
                    st.metric("🏭 Girardin (DÉPENSE)", f"{meilleur_avec_niches['optimisations']['girardin']:,.0f}€", f"Réduction: {meilleur_avec_niches.get('reduction_girardin', 0):,.0f}€")
                else:
                    st.metric("🏭 Girardin", "Non utilisé", "0€")
            
            with col_eco4:
                st.metric("💰 TOTAL ÉCONOMIES", f"{meilleur_avec_niches['optimisations']['economies_ir']:,.0f}€", f"vs sans optim: +{meilleur_avec_niches['total_net'] - meilleur_classique['total_net']:,.0f}€")
        
        # Comparaison avec/sans optimisations
        st.subheader("⚖️ Comparaison Avec/Sans Optimisations")
        col_comp1, col_comp2, col_comp3 = st.columns(3)
        
        with col_comp1:
            st.metric("💰 Sans optimisations", f"{meilleur_classique['total_net']:,.0f}€", "Référence")
        
        with col_comp2:
            st.metric("🎯 Avec optimisations", f"{meilleur_avec_niches['total_net']:,.0f}€", f"+{meilleur_avec_niches['total_net'] - meilleur_classique['total_net']:,.0f}€")
        
        with col_comp3:
            amelioration = ((meilleur_avec_niches['total_net'] / meilleur_classique['total_net']) - 1) * 100
            st.metric("📈 Amélioration", f"+{amelioration:.1f}%", f"Gain: {meilleur_avec_niches['total_net'] - meilleur_classique['total_net']:,.0f}€")
        
        # Graphiques de comparaison
        st.subheader("📈 Analyses Détaillées")
        
        tabs = st.tabs(["🎯 Comparaison Stratégies", "📊 Optimisation Détaillée"])
        
        with tabs[0]:
            # Graphique de comparaison des stratégies
            fig_comp = create_comparison_chart(tous_scenarios_niches)
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # Tableau de synthèse
            st.subheader("📋 Synthèse des Stratégies")
            create_strategy_table(tous_scenarios_niches)
        
        with tabs[1]:
            # Graphique d'optimisation classique
            fig_opt = create_optimization_chart(scenarios_classiques)
            st.plotly_chart(fig_opt, use_container_width=True)

def create_comparison_chart(tous_scenarios):
    """Crée le graphique de comparaison des stratégies"""
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=('Comparaison des stratégies par rémunération', 
                      'Gain net par stratégie',
                      'Économies d\'impôt par stratégie', 
                      'Taux de prélèvement par stratégie'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    couleurs = ['blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray']
    
    # Données pour comparaison
    meilleurs_par_strategie = []
    noms_strategies = []
    
    for i, strategie in enumerate(tous_scenarios):
        scenarios = strategie['scenarios']
        optimisations = strategie['optimisations']
        
        # Utiliser tous les scénarios (dividendes négatifs désormais gérés correctement)
        scenarios_valides = scenarios
        
        # Nom de la stratégie
        nom = f"PER:{optimisations['per']:,} | Mad:{optimisations['madelin']:,} | Gir:{optimisations['girardin']:,}"
        noms_strategies.append(nom)
        meilleurs_par_strategie.append(strategie['meilleur'])
        
        remunerations = [s['remuneration_brute'] for s in scenarios_valides]
        totaux_nets = [s['total_net'] for s in scenarios_valides]
        taux_prelevements = [s['taux_prelevement_global'] for s in scenarios_valides]
        economies = [s['optimisations']['economies_ir'] for s in scenarios_valides]
        
        couleur = couleurs[i % len(couleurs)]
        
        # Graphique 1 : Courbes par rémunération
        fig.add_trace(
            go.Scatter(
                x=remunerations, 
                y=totaux_nets,
                mode='lines',
                name=nom,
                line=dict(color=couleur, width=2),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Rémunération: %{x:,.0f}€<br>' +
                             'Total net: %{y:,.0f}€<extra></extra>',
                showlegend=(i < 4)  # Limiter la légende
            ),
            row=1, col=1
        )
        
        # Graphique 3 : Économies d'impôt
        fig.add_trace(
            go.Scatter(
                x=remunerations, 
                y=economies,
                mode='lines',
                name=f'Économies {nom}',
                line=dict(color=couleur, width=2, dash='dash'),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Rémunération: %{x:,.0f}€<br>' +
                             'Économies: %{y:,.0f}€<extra></extra>',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Graphique 4 : Taux de prélèvement
        fig.add_trace(
            go.Scatter(
                x=remunerations, 
                y=taux_prelevements,
                mode='lines',
                name=f'Taux {nom}',
                line=dict(color=couleur, width=2, dash='dot'),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Rémunération: %{x:,.0f}€<br>' +
                             'Taux: %{y:.1f}%<extra></extra>',
                showlegend=False
            ),
            row=2, col=2
        )
    
    # Graphique 2 : Barres comparatives des meilleurs gains
    gains_nets = [s['total_net'] for s in meilleurs_par_strategie]
    remunerations_opt = [s['remuneration_brute'] for s in meilleurs_par_strategie]
    economies_totales = [s['optimisations']['economies_ir'] for s in meilleurs_par_strategie]
    
    fig.add_trace(
        go.Bar(
            x=noms_strategies,
            y=gains_nets,
            name='Gain net optimal',
            marker_color=couleurs[:len(noms_strategies)],
            hovertemplate='<b>%{x}</b><br>' +
                         'Gain net optimal: %{y:,.0f}€<br>' +
                         'Rémunération optimale: %{customdata:,.0f}€<extra></extra>',
            customdata=remunerations_opt,
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Mise en forme
    fig.update_layout(
        height=800,
        title_text="🎯 Comparaison des Stratégies d'Optimisation Fiscale",
        title_x=0.5,
        title_font_size=18,
        showlegend=True,
        hovermode='closest'
    )
    
    # Formatage des axes
    fig.update_xaxes(title_text="Rémunération de gérance (€)", tickformat=",", row=1, col=1)
    fig.update_xaxes(title_text="Stratégies", tickangle=45, row=1, col=2)
    fig.update_xaxes(title_text="Rémunération de gérance (€)", tickformat=",", row=2, col=1)
    fig.update_xaxes(title_text="Rémunération de gérance (€)", tickformat=",", row=2, col=2)
    
    fig.update_yaxes(title_text="Total net perçu (€)", tickformat=",", row=1, col=1)
    fig.update_yaxes(title_text="Gain net optimal (€)", tickformat=",", row=1, col=2)
    fig.update_yaxes(title_text="Économies d'impôt (€)", tickformat=",", row=2, col=1)
    fig.update_yaxes(title_text="Taux de prélèvement (%)", row=2, col=2)
    
    return fig

def create_optimization_chart(scenarios):
    """Crée le graphique d'optimisation détaillée"""
    # Utiliser tous les scénarios (dividendes négatifs désormais gérés correctement)
    scenarios_valides = scenarios
    
    remunerations = [s['remuneration_brute'] for s in scenarios_valides]
    totaux_nets = [s['total_net'] for s in scenarios_valides]
    taux_prelevements = [s['taux_prelevement_global'] for s in scenarios_valides]
    remunerations_nettes = [s['remuneration_nette_apres_ir'] for s in scenarios_valides]
    dividendes_nets = [s['dividendes_nets'] for s in scenarios_valides]
    cotisations = [s['cotisations_tns'] for s in scenarios_valides]
    ir = [s['ir_remuneration'] for s in scenarios_valides]
    is_sarl = [s['is_sarl'] for s in scenarios_valides]
    flat_tax = [s['flat_tax'] for s in scenarios_valides]
    
    # Créer des sous-graphiques (2x2 - 1)
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=('Optimisation du revenu net total', 
                      'Taux de prélèvement global',
                      'Composition des prélèvements',
                      ''),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Graphique 1 : Total net avec optimum marqué
    if totaux_nets:  # Vérifier qu'il y a des données
        max_idx = totaux_nets.index(max(totaux_nets))
    else:
        max_idx = 0
    
    fig.add_trace(
        go.Scatter(
            x=remunerations, 
            y=totaux_nets,
            mode='lines',
            name='Total net perçu',
            line=dict(color='blue', width=3),
            hovertemplate='<b>Rémunération:</b> %{x:,.0f}€<br>' +
                         '<b>Total net:</b> %{y:,.0f}€<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Marquer l'optimum
    if totaux_nets:  # Seulement si on a des données
        fig.add_trace(
            go.Scatter(
                x=[remunerations[max_idx]], 
                y=[totaux_nets[max_idx]],
                mode='markers',
                marker=dict(color='red', size=15, symbol='star'),
                name='Optimum',
                hovertemplate='<b>🎯 OPTIMUM</b><br>' +
                             '<b>Rémunération:</b> %{x:,.0f}€<br>' +
                             '<b>Total net:</b> %{y:,.0f}€<extra></extra>'
            ),
            row=1, col=1
        )
    
    # Graphique 2 : Taux de prélèvement
    fig.add_trace(
        go.Scatter(
            x=remunerations, 
            y=taux_prelevements,
            mode='lines',
            name='Taux prélèvement',
            line=dict(color='red', width=3),
            hovertemplate='<b>Rémunération:</b> %{x:,.0f}€<br>' +
                         '<b>Taux prélèvement:</b> %{y:.1f}%<extra></extra>'
        ),
        row=1, col=2
    )
    
    # Graphique 3 : Composition des prélèvements (déplacé en position 2,1)
    fig.add_trace(
        go.Scatter(
            x=remunerations, 
            y=cotisations,
            mode='lines',
            name='Cotisations TNS',
            fill='tonexty',
            line=dict(color='orange'),
            hovertemplate='<b>Rémunération:</b> %{x:,.0f}€<br>' +
                         '<b>Cotisations TNS:</b> %{y:,.0f}€<extra></extra>'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=remunerations, 
            y=[c + i for c, i in zip(cotisations, ir)],
            mode='lines',
            name='+ IR',
            fill='tonexty',
            line=dict(color='red'),
            hovertemplate='<b>Rémunération:</b> %{x:,.0f}€<br>' +
                         '<b>IR:</b> %{customdata:,.0f}€<extra></extra>',
            customdata=ir
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=remunerations, 
            y=[c + i + is_val for c, i, is_val in zip(cotisations, ir, is_sarl)],
            mode='lines',
            name='+ IS',
            fill='tonexty',
            line=dict(color='darkred'),
            hovertemplate='<b>Rémunération:</b> %{x:,.0f}€<br>' +
                         '<b>IS SARL:</b> %{customdata:,.0f}€<extra></extra>',
            customdata=is_sarl
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=remunerations, 
            y=[c + i + is_val + ft for c, i, is_val, ft in zip(cotisations, ir, is_sarl, flat_tax)],
            mode='lines',
            name='+ Flat tax',
            fill='tonexty',
            line=dict(color='darkblue'),
            hovertemplate='<b>Rémunération:</b> %{x:,.0f}€<br>' +
                         '<b>Flat tax:</b> %{customdata:,.0f}€<extra></extra>',
            customdata=flat_tax
        ),
        row=2, col=1
    )
    
    # Mise en forme
    fig.update_layout(
        height=800,  # Hauteur normale pour 3 graphiques
        title_text="Optimisation Fiscale SARL + Holding - Analyse Interactive",
        title_x=0.5,
        title_font_size=16,
        showlegend=True,
        hovermode='closest'
    )
    
    # Formatage des axes pour tous les graphiques
    for i in range(1, 3):  # 2 rangées
        for j in range(1, 3):  # 2 colonnes
            fig.update_xaxes(title_text="Rémunération de gérance (€)", row=i, col=j)
            fig.update_xaxes(tickformat=",", row=i, col=j)
    
    # Titre des axes Y
    fig.update_yaxes(title_text="Total net perçu (€)", tickformat=",", row=1, col=1)
    fig.update_yaxes(title_text="Taux (%)", row=1, col=2)
    fig.update_yaxes(title_text="Prélèvements cumulés (€)", tickformat=",", row=2, col=1)
    
    return fig

def create_strategy_table(tous_scenarios):
    """Crée un tableau de synthèse des stratégies"""
    data = []
    for i, strategie in enumerate(tous_scenarios):
        opt = strategie['optimisations']
        meilleur = strategie['meilleur']
        
        data.append({
            'Stratégie': f"PER: {opt['per']:,}€ | Madelin: {opt['madelin']:,}€ | Girardin: {opt['girardin']:,}€",
            'Gain Net (€)': f"{meilleur['total_net']:,.0f}",
            'Rémunération Optimale (€)': f"{meilleur['remuneration_brute']:,.0f}",
            'Économies IR (€)': f"{meilleur['optimisations']['economies_ir']:,.0f}",
            'Taux Prélèvement (%)': f"{meilleur['taux_prelevement_global']:.1f}"
        })
    
    import pandas as pd
    df = pd.DataFrame(data)
    
    # Identifier la meilleure stratégie
    gains = [float(d['Gain Net (€)'].replace(',', '')) for d in data]
    meilleur_idx = gains.index(max(gains))
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    st.success(f"🏆 **Meilleure stratégie :** {data[meilleur_idx]['Stratégie']}")
    st.info(f"💰 **Gain supplémentaire vs sans optimisation :** +{max(gains) - min(gains):,.0f}€")

if __name__ == "__main__":
    main()