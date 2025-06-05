import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from formes_juridiques import creer_optimiseur, FORMES_JURIDIQUES
from parametres_fiscaux import TAUX_COTISATIONS_TNS, MICRO_BIC, MICRO_BNC, MICRO_BIC_VENTE, MICRO_BIC_SERVICES, TAUX_COTISATIONS_SALARIE, TAUX_COTISATIONS_PATRONALES

def main():
    st.set_page_config(
        page_title="Optimisation Fiscale Multi-Formes",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🎯 Optimisation Fiscale Multi-Formes Juridiques")
    st.markdown("---")
    
    # Sidebar pour la configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Sélection de la forme juridique
        st.subheader("🏢 Forme Juridique")
        forme_juridique = st.selectbox(
            "Choisissez votre forme juridique",
            FORMES_JURIDIQUES,
            index=3,  # SARL + Holding par défaut pour compatibilité
            help="Sélectionnez la forme juridique à optimiser"
        )
        
        # Paramètres de base
        st.subheader("📊 Paramètres de base")
        # Interface adaptée selon la forme juridique mais avec conservation des valeurs
        if 'resultat_initial' not in st.session_state:
            if forme_juridique == "Micro-entreprise":
                st.session_state.resultat_initial = 100000
            else:
                st.session_state.resultat_initial = 300000
        
        if forme_juridique == "Micro-entreprise":
            resultat_initial = st.number_input(
                "Chiffre d'affaires (€)",
                min_value=0,
                value=st.session_state.resultat_initial,
                step=5000,
                help="Chiffre d'affaires de votre micro-entreprise (peut dépasser les seuils pendant 2 ans)",
                key="resultat_micro"
            )
            type_activite = st.selectbox(
                "Type d'activité",
                ["BIC - Prestations de services", "BIC - Vente de marchandises", "BNC - Professions libérales"],
                help="Choisissez votre type d'activité pour appliquer les bons taux et abattements"
            )
        else:
            resultat_initial = st.number_input(
                "Résultat avant rémunération (€)",
                min_value=0,
                value=st.session_state.resultat_initial,
                step=10000,
                help=f"Résultat de votre {forme_juridique} avant déduction de la rémunération",
                key="resultat_societe"
            )
        
        # Mise à jour du session state
        st.session_state.resultat_initial = resultat_initial
        
        # Charges existantes pour toutes les formes juridiques
        if 'charges_existantes' not in st.session_state:
            st.session_state.charges_existantes = 50000
        if 'parts_fiscales' not in st.session_state:
            st.session_state.parts_fiscales = 2.0
            
        if forme_juridique == "Micro-entreprise":
            charges_existantes = st.number_input(
                "Charges réelles estimées (€)",
                min_value=0,
                value=st.session_state.charges_existantes,
                step=5000,
                help="Charges réelles à déduire du revenu net final (frais, matériel, etc.)"
            )
        else:
            charges_existantes = st.number_input(
                "Charges existantes (€)",
                min_value=0,
                value=st.session_state.charges_existantes,
                step=5000,
                help="Autres charges déjà déduites du résultat"
            )
        st.session_state.charges_existantes = charges_existantes
        
        parts_fiscales = st.number_input(
            "Nombre de parts fiscales",
            min_value=1.0,
            value=st.session_state.parts_fiscales,
            step=0.25,
            help="Votre nombre de parts fiscales pour le calcul de l'IR"
        )
        st.session_state.parts_fiscales = parts_fiscales
        
        # Créer l'optimiseur pour connaître les optimisations disponibles
        optimiseur_temp = creer_optimiseur(forme_juridique, resultat_avant_remuneration=resultat_initial, 
                                          charges_existantes=charges_existantes, parts_fiscales=parts_fiscales)
        optimisations_disponibles = optimiseur_temp.get_optimisations_disponibles()
        
        # Optimisations fiscales - Niveau Entreprise
        optimisations_entreprise = [opt for opt in optimisations_disponibles if opt in ['madelin', 'acre']]
        if optimisations_entreprise:
            st.subheader("🏢 Optimisations Niveau Entreprise")
            st.markdown("*Déductions et réductions au niveau de l'entreprise*")
            
            # Madelin (seulement pour TNS)
            use_madelin = False
            madelin_max = 0
            if 'madelin' in optimisations_disponibles:
                use_madelin = st.checkbox(
                    "🏥 Contrat Madelin TNS",
                    help="Charge déductible pour les TNS (max 84,000€ en 2024)"
                )
                if use_madelin:
                    madelin_max = st.slider(
                        "Montant Madelin (€)",
                        min_value=0,
                        max_value=35000,
                        value=5000,
                        step=500,
                        help="Plafond légal pour les charges Madelin TNS déductibles"
                    )
            
            # ACRE (pour micro-entreprise)
            use_acre = False
            if 'acre' in optimisations_disponibles:
                use_acre = st.checkbox(
                    "🎆 ACRE (Aide à la Création d'Entreprise)",
                    help="Réduction de 50% des cotisations sociales la première année (sous conditions)"
                )
        else:
            use_madelin = False
            madelin_max = 0
            use_acre = False
        
        # Optimisations fiscales - Niveau IR Personnel
        optimisations_ir = [opt for opt in optimisations_disponibles if opt in ['per', 'girardin']]
        if optimisations_ir:
            st.subheader("👤 Optimisations Niveau IR Personnel")
            st.markdown("*Déductions et réductions d'impôt sur le revenu*")
            
            # PER (disponible pour tous sauf certains cas)
            use_per = False
            per_max = 0
            if 'per' in optimisations_disponibles:
                use_per = st.checkbox(
                    "📈 Plan d'Épargne Retraite (PER)",
                    help="Déduction fiscale sur le revenu imposable (max 32,419€ en 2024)"
                )
                if use_per:
                    per_max = st.slider(
                        "Montant PER (€)",
                        min_value=0,
                        max_value=30000,
                        value=15000,
                        step=1000,
                        help="Plafond légal : 8 x PASS = 32,419€ en 2024"
                    )
            
            # Girardin (pour les IR)
            use_girardin = False
            girardin_max = 0
            if 'girardin' in optimisations_disponibles:
                use_girardin = st.checkbox(
                    "🏭 Girardin Industriel",
                    help="⚠️ ATTENTION : Il s'agit d'une DÉPENSE qui génère une réduction d'impôt"
                )
                if use_girardin:
                    girardin_max = st.slider(
                        "Montant d'investissement Girardin (€)",
                        min_value=0,
                        max_value=40000,
                        value=20000,
                        step=1000,
                        help="Montant de l'investissement (dépense) qui génère la réduction d'impôt"
                    )
        else:
            use_per = False
            per_max = 0
            use_girardin = False
            girardin_max = 0
        
        # Paramètres de calcul
        st.subheader("⚙️ Paramètres de calcul")
        pas_calcul = st.selectbox(
            "Précision du calcul",
            options=[1000, 2500, 5000, 10000],
            index=0,
            help="Plus le pas est petit, plus le calcul est précis mais plus long"
        )
        
        # Bouton de calcul
        if st.button("🚀 Calculer l'optimisation", type="primary"):
            st.session_state.run_calculation = True
    
    # Zone principale
    if 'run_calculation' not in st.session_state:
        st.session_state.run_calculation = False
    
    if st.session_state.run_calculation:
        # Initialisation de l'optimiseur selon la forme juridique
        with st.spinner("🔄 Calcul en cours..."):
            optimiseur = creer_optimiseur(
                forme_juridique,
                resultat_avant_remuneration=resultat_initial,
                charges_existantes=charges_existantes,
                parts_fiscales=parts_fiscales
            )
            
            # Optimisation selon la forme juridique
            if forme_juridique == "Micro-entreprise":
                meilleur_global, tous_scenarios = optimiseur.optimiser(
                    type_activite=type_activite,
                    pas=pas_calcul,
                    per_max=per_max if use_per else 0,
                    madelin_max=madelin_max if use_madelin else 0,
                    acre=use_acre
                )
                # Adapter format pour compatibilité
                tous_scenarios_niches = [{'scenarios': tous_scenarios, 'meilleur': meilleur_global}]
            elif forme_juridique == "SARL + Holding":
                # Utiliser la méthode optimiser
                meilleur_global, tous_scenarios = optimiseur.optimiser(
                    pas=pas_calcul,
                    per_max=per_max if use_per else 0,
                    madelin_max=madelin_max if use_madelin else 0,
                    girardin_max=girardin_max if use_girardin else 0
                )
                # Adapter format pour compatibilité
                tous_scenarios_niches = [{'scenarios': tous_scenarios, 'meilleur': meilleur_global}]
            else:
                # Autres formes juridiques
                meilleur_global, tous_scenarios = optimiseur.optimiser(
                    pas=pas_calcul,
                    per_max=per_max if use_per else 0,
                    madelin_max=madelin_max if use_madelin else 0,
                    girardin_max=girardin_max if use_girardin else 0
                )
                # Adapter format pour compatibilité
                tous_scenarios_niches = [{'scenarios': tous_scenarios, 'meilleur': meilleur_global}]
            
            # Utiliser directement le meilleur global pour toutes les formes
            meilleur_avec_niches = meilleur_global
            
            # Récupérer les scénarios pour les graphiques
            scenarios_avec_niches = None
            if tous_scenarios_niches and len(tous_scenarios_niches) > 0:
                if forme_juridique == "SARL + Holding":
                    # Pour SARL + Holding, chercher la stratégie du meilleur global
                    for strategie in tous_scenarios_niches:
                        if strategie['meilleur'] == meilleur_global:
                            scenarios_avec_niches = strategie['scenarios']
                            break
                else:
                    # Pour les autres formes, utiliser les scénarios du premier élément
                    scenarios_avec_niches = tous_scenarios_niches[0]['scenarios']
            
            # Scénario de référence sans optimisations pour comparaison
            if forme_juridique == "Micro-entreprise":
                scenario_ref = optimiseur.calculer_scenario(meilleur_avec_niches['chiffre_affaires'], type_activite=type_activite, acre=False)
            elif forme_juridique == "SAS":
                scenario_ref = optimiseur.calculer_scenario(meilleur_avec_niches['salaire_brut'])
            else:
                scenario_ref = optimiseur.calculer_scenario(meilleur_avec_niches.get('remuneration_brute', meilleur_avec_niches.get('salaire_brut', 0)))
            meilleur_classique = scenario_ref
        
        # Affichage des résultats
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader(f"🏆 Résultat Optimal - {forme_juridique}")
            
            # Métriques principales adaptées selon la forme
            net_key = 'net_final' if forme_juridique == "Micro-entreprise" else 'total_net'
            net_optimal = meilleur_avec_niches.get(net_key, 0)
            net_classique = meilleur_classique.get(net_key, 0)
            
            st.metric(
                "💰 Total Net Optimal",
                f"{net_optimal:,.0f}€",
                delta=f"+{net_optimal - net_classique:,.0f}€"
            )
            
            col_a, col_b, col_c = st.columns(3)
            
            # Adapter les métriques selon la forme juridique
            if forme_juridique == "Micro-entreprise":
                with col_a:
                    st.metric(
                        "💼 CA optimal",
                        f"{meilleur_avec_niches['chiffre_affaires']:,.0f}€"
                    )
                with col_b:
                    st.metric(
                        "🏥 Cotisations sociales",
                        f"{meilleur_avec_niches['cotisations_sociales']:,.0f}€"
                    )
                with col_c:
                    st.metric(
                        "📉 Taux Prélèvement Global",
                        f"{meilleur_avec_niches['taux_prelevement_global']:.1f}%"
                    )
            elif forme_juridique == "SAS":
                with col_a:
                    st.metric(
                        "💼 Salaire brut",
                        f"{meilleur_avec_niches['salaire_brut']:,.0f}€"
                    )
                with col_b:
                    st.metric(
                        "💎 Dividendes nets",
                        f"{meilleur_avec_niches['dividendes_nets']:,.0f}€"
                    )
                with col_c:
                    st.metric(
                        "📉 Taux Prélèvement Global",
                        f"{meilleur_avec_niches['taux_prelevement_global']:.1f}%"
                    )
            else:  # SARL et SARL + Holding
                with col_a:
                    st.metric(
                        "💼 Rémunération brute",
                        f"{meilleur_avec_niches.get('remuneration_brute', 0):,.0f}€"
                    )
                with col_b:
                    if 'dividendes_sarl' in meilleur_avec_niches:
                        st.metric(
                            "💎 Dividendes bruts",
                            f"{meilleur_avec_niches['dividendes_sarl']:,.0f}€"
                        )
                    else:
                        st.metric(
                            "💎 Dividendes nets",
                            f"{meilleur_avec_niches.get('dividendes_nets', 0):,.0f}€"
                        )
                with col_c:
                    st.metric(
                        "📉 Taux Prélèvement Global",
                        f"{meilleur_avec_niches['taux_prelevement_global']:.1f}%"
                    )
            
            # Détail des optimisations
            optimisations = meilleur_avec_niches.get('optimisations', {})
            if any(optimisations.get(k, 0) > 0 or optimisations.get(k, False) for k in ['per', 'madelin', 'girardin', 'acre']):
                st.subheader("🎯 Optimisations Utilisées")
                
                # Optimisations niveau entreprise
                optimisations_entreprise_utilisees = []
                if optimisations.get('madelin', 0) > 0:
                    optimisations_entreprise_utilisees.append(f"🏥 Madelin (charge déductible) : {optimisations['madelin']:,.0f}€")
                
                if optimisations.get('acre', False):
                    acre_economie = meilleur_avec_niches.get('acre_reduction', 0)
                    optimisations_entreprise_utilisees.append(f"🎆 ACRE : -50% cotisations (économie {acre_economie:,.0f}€)")
                
                if optimisations_entreprise_utilisees:
                    st.markdown("**🏢 Niveau Entreprise :**")
                    for opt in optimisations_entreprise_utilisees:
                        st.info(opt)
                
                # Optimisations niveau IR personnel
                optimisations_ir_utilisees = []
                if optimisations.get('per', 0) > 0:
                    optimisations_ir_utilisees.append(f"📈 PER (déduction IR) : {optimisations['per']:,.0f}€")
                
                if optimisations.get('girardin', 0) > 0:
                    reduction_girardin = meilleur_avec_niches.get('reduction_girardin', 0)
                    optimisations_ir_utilisees.append(f"🏭 Girardin (réduction IR) : {optimisations['girardin']:,.0f}€ → -{reduction_girardin:,.0f}€ d'IR")
                
                if optimisations_ir_utilisees:
                    st.markdown("**👤 Niveau IR Personnel :**")
                    for opt in optimisations_ir_utilisees:
                        if "Girardin" in opt:
                            st.error(opt)  # En rouge car c'est une dépense
                        else:
                            st.info(opt)
                
                st.success(f"💰 Économies totales : {optimisations.get('economies_totales', 0):,.0f}€")
        
        with col2:
            st.subheader("📊 Répartition du Revenu")
            
            # Graphique en camembert adapté selon la forme juridique
            if forme_juridique == "Micro-entreprise":
                labels = ['Net Final', 'Cotisations Sociales', 'IR', 'PER']
                values = [
                    meilleur_avec_niches.get('net_final', 0),
                    meilleur_avec_niches.get('cotisations_sociales', 0),
                    meilleur_avec_niches.get('ir', 0),
                    meilleur_avec_niches.get('optimisations', {}).get('per', 0)
                ]
            else:
                labels = ['Salaire Net', 'Dividendes Nets', 'Cotisations TNS', 'IR', 'IS Total', 'Flat Tax']
                values = [
                    meilleur_avec_niches.get('remuneration_nette_apres_ir', 0),
                    meilleur_avec_niches.get('dividendes_nets', 0),
                    meilleur_avec_niches.get('cotisations_tns', 0),
                    meilleur_avec_niches.get('ir_remuneration', 0),
                    meilleur_avec_niches.get('is_sarl', 0) + meilleur_avec_niches.get('is_holding', 0),
                    meilleur_avec_niches.get('flat_tax', 0)
                ]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie.update_layout(
                title=f"Répartition - {forme_juridique}",
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Résumé détaillé complet
        st.subheader("📋 Résumé Détaillé de l'Optimisation")
        
        # Colonnes pour l'affichage du résumé
        col_resume1, col_resume2, col_resume3 = st.columns(3)
        
        # Préparer les détails des cotisations (adapté selon la forme)
        cotisations_detail_str = ""
        if forme_juridique == "Micro-entreprise":
            # Pour la micro : détail des cotisations sociales
            type_activite_resultat = meilleur_avec_niches.get('type_activite', 'BIC - Prestations de services')
            if type_activite_resultat == 'BIC - Vente de marchandises':
                config = MICRO_BIC_VENTE
            elif type_activite_resultat in ['BIC - Prestations de services', 'BIC']:
                config = MICRO_BIC_SERVICES
            else:
                config = MICRO_BNC
            taux_effectif = meilleur_avec_niches.get('taux_cotisations_effectif', config['cotisations'])
            cotisations_detail_str = f"  • Cotisations sociales ({taux_effectif*100:.1f}%) : {meilleur_avec_niches.get('cotisations_sociales', 0):,.0f}€  \n"
            if meilleur_avec_niches.get('acre_reduction', 0) > 0:
                cotisations_detail_str += f"  • Réduction ACRE (-50%) : -{meilleur_avec_niches.get('acre_reduction', 0):,.0f}€  \n"
        elif forme_juridique == "SAS":
            # Pour la SAS : détail des cotisations salariales et patronales
            cotisations_salariales = meilleur_avec_niches.get('cotisations_salariales', 0)
            cotisations_patronales = meilleur_avec_niches.get('cotisations_patronales', 0)
            taux_salariales = TAUX_COTISATIONS_SALARIE * 100
            taux_patronales = TAUX_COTISATIONS_PATRONALES * 100
            cotisations_detail_str = f"  • Cotisations salariales ({taux_salariales:.1f}%) : {cotisations_salariales:,.0f}€  \n"
            cotisations_detail_str += f"  • Cotisations patronales ({taux_patronales:.1f}%) : {cotisations_patronales:,.0f}€  \n"
            cotisations_detail_str += f"  • **Total cotisations :** {cotisations_salariales + cotisations_patronales:,.0f}€  \n"
        else:
            # Pour les autres formes : détail TNS
            for nom, montant in meilleur_avec_niches.get('cotisations_detail', {}).items():
                nom_affiche = {
                    'maladie': 'Maladie',
                    'allocations_familiales': 'Allocations familiales', 
                    'retraite_base': 'Retraite base',
                    'retraite_complementaire': 'Retraite complémentaire',
                    'invalidite_deces': 'Invalidité décès',
                    'csg_crds': 'CSG/CRDS',
                    'formation': 'Formation'
                }.get(nom, nom)
                taux = TAUX_COTISATIONS_TNS.get(nom, 0) * 100
                cotisations_detail_str += f"  • {nom_affiche} ({taux:.2f}%) : {montant:,.0f}€  \n"
        
        # Préparer les détails IS
        is_detail_str = ""
        for detail in meilleur_avec_niches['is_detail']:
            is_detail_str += f"  • {detail['base']:,.0f}€ à {detail['taux']*100:.0f}% = {detail['impot']:,.0f}€  \n"
        
        # Préparer les détails IR
        ir_detail_str = ""
        for detail in meilleur_avec_niches['ir_detail']:
            if detail['impot'] > 0:  # Ne montrer que les tranches avec de l'impôt
                ir_detail_str += f"  • De {detail['de']:,.0f}€ à {detail['a']:,.0f}€ : {detail['taux']*100:.0f}% = {detail['impot']:,.0f}€  \n"
        
        with col_resume1:
            if forme_juridique == "Micro-entreprise":
                st.markdown("#### 💼 NIVEAU MICRO-ENTREPRISE")
                st.markdown(f"""
                **Chiffre d'affaires :** {meilleur_avec_niches['chiffre_affaires']:,.0f}€  
                **Type d'activité :** {meilleur_avec_niches.get('type_activite', 'BIC')}  
                
                **Abattement fiscal :** {meilleur_avec_niches.get('abattement_micro', 0):,.0f}€  
                **Base imposable :** {meilleur_avec_niches.get('base_imposable', 0):,.0f}€  
                
                """)
                
                with st.expander(f"**Cotisations sociales :** {meilleur_avec_niches.get('cotisations_sociales', 0):,.0f}€  "):
                    st.markdown(cotisations_detail_str)
                
                st.markdown(f"""
                **Net avant charges :** {meilleur_avec_niches.get('net_avant_charges', 0):,.0f}€  
                **Charges réelles :** {meilleur_avec_niches.get('charges_reelles', 0):,.0f}€  
                **Net final :** {meilleur_avec_niches.get('net_final', 0):,.0f}€  
                
                """)
            elif forme_juridique == "SAS":
                st.markdown("#### 🏢 NIVEAU SAS")
                st.markdown(f"""
                **Résultat initial :** {resultat_initial:,.0f}€  
                **Charges existantes :** {charges_existantes:,.0f}€  
                **Résultat avant rémun. :** {resultat_initial - charges_existantes:,.0f}€  
                
                **Salaire brut :** {meilleur_avec_niches['salaire_brut']:,.0f}€  
                
                """)
                
                with st.expander(f"**Cotisations sociales :** {meilleur_avec_niches.get('cotisations_salariales', 0) + meilleur_avec_niches.get('cotisations_patronales', 0):,.0f}€  "):
                    st.markdown(cotisations_detail_str)
                
                st.markdown(f"""
                **Coût total employeur :** {meilleur_avec_niches.get('cout_total_salaire', 0):,.0f}€  
                **Résultat après salaire :** {meilleur_avec_niches.get('resultat_apres_salaire', meilleur_avec_niches['resultat_apres_remuneration']):,.0f}€  
                
                """)
                
                with st.expander(f"**IS SAS :** {meilleur_avec_niches['is_sarl']:,.0f}€  "):
                    st.markdown(is_detail_str)
                
                st.markdown(f"**Dividendes bruts :** {meilleur_avec_niches['dividendes_sarl']:,.0f}€")
            else:
                st.markdown("#### 🏢 NIVEAU SARL")
                st.markdown(f"""
                **Résultat initial :** {resultat_initial:,.0f}€  
                **Charges existantes :** {charges_existantes:,.0f}€  
                **Résultat avant rémun. :** {resultat_initial - charges_existantes:,.0f}€  
                
                **Rémunération brute :** {meilleur_avec_niches['remuneration_brute']:,.0f}€  
                
                """)
                
                with st.expander(f"**Cotisations TNS :** {meilleur_avec_niches['cotisations_tns']:,.0f}€  "):
                    st.markdown(cotisations_detail_str)
                
                st.markdown(f"""
                **Charge Madelin :** {meilleur_avec_niches.get('madelin_charge', 0):,.0f}€  
                **Résultat après rémun. :** {meilleur_avec_niches['resultat_apres_remuneration']:,.0f}€  
                
                """)
                
                with st.expander(f"**IS SARL :** {meilleur_avec_niches['is_sarl']:,.0f}€  "):
                    st.markdown(is_detail_str)
                
                st.markdown(f"**Dividendes SARL :** {meilleur_avec_niches['dividendes_sarl']:,.0f}€")
        
        with col_resume2:
            st.markdown("#### 💼 NIVEAU PERSONNEL")
            if forme_juridique == "SAS":
                st.markdown(f"""
                **Salaire net avant IR :** {meilleur_avec_niches.get('salaire_net_avant_ir', meilleur_avec_niches['remuneration_nette_avant_ir']):,.0f}€  
                **Abattement frais pro (10%) :** {meilleur_avec_niches['abattement_frais_pro']:,.0f}€  
                **Revenu imposable initial :** {meilleur_avec_niches['revenu_imposable']:,.0f}€  
                
                **Déductions fiscales :**  
                • PER : {meilleur_avec_niches.get('per_deduction', 0):,.0f}€  
                **Revenu imposable final :** {meilleur_avec_niches.get('revenu_imposable_final', meilleur_avec_niches['revenu_imposable']):,.0f}€  
                """)
            else:
                st.markdown(f"""
                **Rémunération nette avant IR :** {meilleur_avec_niches['remuneration_nette_avant_ir']:,.0f}€  
                **Abattement frais pro (10%) :** {meilleur_avec_niches['abattement_frais_pro']:,.0f}€  
                **Revenu imposable initial :** {meilleur_avec_niches['revenu_imposable']:,.0f}€  
                
                **Déductions fiscales :**  
                • PER : {meilleur_avec_niches.get('per_deduction', 0):,.0f}€  
                **Revenu imposable final :** {meilleur_avec_niches.get('revenu_imposable_final', meilleur_avec_niches['revenu_imposable']):,.0f}€  
                """)
            
            if ir_detail_str.strip():
                with st.expander(f"**IR :** {meilleur_avec_niches.get('ir_avant_girardin', meilleur_avec_niches['ir_remuneration']):,.0f}€  "):
                    st.markdown(ir_detail_str)
            else:
                st.markdown(f"**IR avant Girardin :** {meilleur_avec_niches.get('ir_avant_girardin', meilleur_avec_niches['ir_remuneration']):,.0f}€  ")
            
            st.markdown(f"""
            **Réduction Girardin :** {meilleur_avec_niches.get('reduction_girardin', 0):,.0f}€  
            **IR final :** {meilleur_avec_niches['ir_remuneration']:,.0f}€  
            """)
            
            if forme_juridique == "SAS":
                st.markdown(f"""
                **💰 Salaire net après IR :** {meilleur_avec_niches.get('salaire_net_final', meilleur_avec_niches['remuneration_nette_apres_ir']):,.0f}€
                
                **💰 Placement PER :** {meilleur_avec_niches.get('per_deduction', 0):,.0f}€  
                
                **📊 Taux prélèvement personnel :** {(1-meilleur_avec_niches.get('salaire_net_final', meilleur_avec_niches['remuneration_nette_apres_ir']) / (meilleur_avec_niches.get('cout_total_salaire', meilleur_avec_niches['remuneration_brute']))) * 100:.1f}%
                
                **🏭 INVESTISSEMENT GIRARDIN :** -{meilleur_avec_niches['optimisations']['girardin']:,.0f}€
                """)
            else:
                st.markdown(f"""
                **💰 Salaire net après IR :** {meilleur_avec_niches['remuneration_nette_apres_ir']-meilleur_avec_niches.get('per_deduction', 0):,.0f}€
                
                **💰 Placement PER :** {meilleur_avec_niches.get('per_deduction', 0):,.0f}€  
                
                **📊 Taux prélèvement personnel :** {(1-meilleur_avec_niches['remuneration_nette_apres_ir'] / (meilleur_avec_niches.get('cotisations_tns', 0) +  meilleur_avec_niches['remuneration_brute'])) * 100:.1f}%
                
                **🏭 INVESTISSEMENT GIRARDIN :** -{meilleur_avec_niches['optimisations']['girardin']:,.0f}€
                """)
        
        with col_resume3:
            if forme_juridique == "SARL + Holding":
                st.markdown("#### 🏠 NIVEAU HOLDING + FINAL")
                st.markdown(f"""
                **Dividendes reçus :** {meilleur_avec_niches['dividendes_sarl']:,.0f}€  
                **Quote-part imposable (5%) :** {meilleur_avec_niches['quote_part_imposable']:,.0f}€  
                **IS Holding :** {meilleur_avec_niches['is_holding']:,.0f}€  
                **Dividendes dans holding :** {meilleur_avec_niches['dividendes_holding']:,.0f}€  
                
                **Flat tax (30%) :** {meilleur_avec_niches['flat_tax']:,.0f}€  
                **💎 Dividendes nets :** {meilleur_avec_niches['dividendes_nets']:,.0f}€  
                **📊 Taux prélèvement dividendes :** {meilleur_avec_niches['taux_prelevement_dividendes']:.1f}%  
                
                **🎯 TOTAL NET PERÇU :** {meilleur_avec_niches['total_net']:,.0f}€  
                **Taux prélèvement global :** {meilleur_avec_niches['taux_prelevement_global']:.1f}%
                """)
            elif forme_juridique == "SAS":
                st.markdown("#### 🎯 RÉSULTAT FINAL SAS")
                st.markdown(f"""
                **Dividendes bruts :** {meilleur_avec_niches['dividendes_sarl']:,.0f}€  
                **Flat tax (30%) :** {meilleur_avec_niches['flat_tax']:,.0f}€  
                **💎 Dividendes nets :** {meilleur_avec_niches['dividendes_nets']:,.0f}€  
                **📊 Taux prélèvement dividendes :** {meilleur_avec_niches['taux_prelevement_dividendes']:.1f}%  
                
                **🎯 TOTAL NET PERÇU :** {meilleur_avec_niches['total_net']:,.0f}€  
                **Taux prélèvement global :** {meilleur_avec_niches['taux_prelevement_global']:.1f}%
                
                **Détail :**  
                • Salaire net : {meilleur_avec_niches.get('salaire_net_final', meilleur_avec_niches.get('remuneration_nette_apres_ir', 0)):,.0f}€  
                • Dividendes nets : {meilleur_avec_niches.get('dividendes_nets', 0):,.0f}€  
                • Économies optimisations : {meilleur_avec_niches['optimisations']['economies_totales']:,.0f}€  
                """)
            else:
                st.markdown("#### 🎯 RÉSULTAT FINAL")
                st.markdown(f"""
                **Dividendes reçus :** {meilleur_avec_niches['dividendes_sarl']:,.0f}€  
                **Flat tax (30%) :** {meilleur_avec_niches['flat_tax']:,.0f}€  
                **💎 Dividendes nets :** {meilleur_avec_niches['dividendes_nets']:,.0f}€  
                **📊 Taux prélèvement dividendes :** {meilleur_avec_niches['taux_prelevement_dividendes']:.1f}%  
                
                **🎯 TOTAL NET PERÇU :** {meilleur_avec_niches['total_net']:,.0f}€  
                **Taux prélèvement global :** {meilleur_avec_niches['taux_prelevement_global']:.1f}%
                """)
                
                st.markdown(f"""
                **💎 Total revenus nets :** {meilleur_avec_niches['total_net']:,.0f}€  
                **📄 Taux prélèvement global :** {meilleur_avec_niches['taux_prelevement_global']:.1f}%  
                
                **Détail :**  
                • Revenus nets : {meilleur_avec_niches.get('remuneration_nette_apres_ir', 0):,.0f}€  
                • Dividendes nets : {meilleur_avec_niches.get('dividendes_nets', 0):,.0f}€  
                • Économies optimisations : {meilleur_avec_niches['optimisations']['economies_totales']:,.0f}€  
                """)
        
        # Tableau récapitulatif des économies d'impôts si optimisations
        optimisations_actives = (
            any(meilleur_avec_niches['optimisations'].get(k, 0) > 0 for k in ['per', 'madelin', 'girardin']) or
            meilleur_avec_niches['optimisations'].get('acre', False)
        )
        if optimisations_actives:
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
                    economie_madelin = meilleur_avec_niches.get('economie_is_madelin', 0)  # Économie d'IS
                    st.metric("🏥 Madelin (charge)", f"{meilleur_avec_niches['optimisations']['madelin']:,.0f}€", f"Économie IS: {economie_madelin:,.0f}€")
                else:
                    st.metric("🏥 Madelin", "Non utilisé", "0€")
            
            with col_eco3:
                if meilleur_avec_niches['optimisations'].get('acre', False):
                    acre_economie = meilleur_avec_niches.get('acre_reduction', 0)
                    st.metric("🎆 ACRE", "Activée", f"Économie: {acre_economie:,.0f}€")
                elif meilleur_avec_niches['optimisations'].get('girardin', 0) > 0:
                    st.metric("🏭 Girardin", f"{meilleur_avec_niches['optimisations']['girardin']:,.0f}€", f"Réduction: {meilleur_avec_niches.get('reduction_girardin', 0):,.0f}€")
                else:
                    st.metric("🎆 ACRE / 🏭 Girardin", "Non utilisé", "0€")
            
            with col_eco4:
                st.metric("💰 TOTAL ÉCONOMIES", f"{meilleur_avec_niches['optimisations']['economies_totales']:,.0f}€", f"vs sans optim: +{meilleur_avec_niches['total_net'] - meilleur_classique['total_net']:,.0f}€")
        
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
        
        # Graphique d'optimisation unique
        st.subheader("📈 Analyse Détaillée")
        fig_opt = create_optimization_chart(scenarios_avec_niches)
        st.plotly_chart(fig_opt, use_container_width=True)
        
        # Tableau détaillé des données
        st.subheader("📋 Tableau Détaillé des Scénarios")
        df_scenarios = create_scenarios_dataframe(scenarios_avec_niches)
        
        # Affichage avec possibilité de filtrer
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            min_remun_filter = st.number_input(
                "Rémunération minimum à afficher (€)",
                min_value=0,
                max_value=int(df_scenarios['Rémunération Brute'].max()) if not df_scenarios.empty else 0,
                value=0,
                step=10000
            )
        with col_filter2:
            max_remun_filter = st.number_input(
                "Rémunération maximum à afficher (€)",
                min_value=0,
                max_value=int(df_scenarios['Rémunération Brute'].max()) if not df_scenarios.empty else 300000,
                value=int(df_scenarios['Rémunération Brute'].max()) if not df_scenarios.empty else 300000,
                step=10000
            )
        
        # Filtrer le DataFrame
        df_filtered = df_scenarios[
            (df_scenarios['Rémunération Brute'] >= min_remun_filter) & 
            (df_scenarios['Rémunération Brute'] <= max_remun_filter)
        ]
        
        # Mettre en évidence l'optimum
        if not df_filtered.empty:
            optimal_idx = df_filtered['Total Net'].idxmax()
            st.info(f"🎯 **Optimum visible:** Rémunération {df_filtered.loc[optimal_idx, 'Rémunération Brute']:,.0f}€ → Total net {df_filtered.loc[optimal_idx, 'Total Net']:,.0f}€")
        
        # Afficher le tableau
        st.dataframe(
            df_filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rémunération Brute": st.column_config.NumberColumn("Rémunération Brute", format="€%.0f"),
                "Total Net": st.column_config.NumberColumn("Total Net", format="€%.0f"),
                "Rémunération Nette": st.column_config.NumberColumn("Rémunération Nette", format="€%.0f"),
                "Dividendes Nets": st.column_config.NumberColumn("Dividendes Nets", format="€%.0f"),
                "Cotisations TNS": st.column_config.NumberColumn("Cotisations TNS", format="€%.0f"),
                "IR": st.column_config.NumberColumn("IR", format="€%.0f"),
                "IS SARL": st.column_config.NumberColumn("IS SARL", format="€%.0f"),
                "IS Holding": st.column_config.NumberColumn("IS Holding", format="€%.0f"),
                "Flat Tax": st.column_config.NumberColumn("Flat Tax", format="€%.0f"),
                "Total Prélèvements": st.column_config.NumberColumn("Total Prélèvements", format="€%.0f"),
                "Net Disponible": st.column_config.NumberColumn("Net Disponible", format="€%.2f"),
                "Taux Prélèvement (%)": st.column_config.NumberColumn("Taux Prélèvement (%)", format="%.2f%%")
            }
        )
        
        # Bouton de téléchargement CSV
        csv = df_scenarios.to_csv(index=False)
        st.download_button(
            label="📥 Télécharger les données (CSV)",
            data=csv,
            file_name=f"optimisation_fiscale_{resultat_initial}€.csv",
            mime="text/csv"
        )


def create_scenarios_dataframe(scenarios):
    """Crée un DataFrame avec tous les scénarios pour affichage en tableau"""
    data = []
    
    for s in scenarios:
        # Calculs similaires à export_donnees.py
        total_cotisations = s['cotisations_tns'] + s['ir_remuneration'] + s['is_sarl'] + s['is_holding'] + s['flat_tax']
        net_disponible = s['remuneration_nette_apres_ir'] + s['dividendes_nets']
        verification_somme = total_cotisations + net_disponible
        
        row = {
            'Rémunération Brute': s['remuneration_brute'],
            'Total Net': s['total_net'],
            'Rémunération Nette': s['remuneration_nette_apres_ir'],
            'Dividendes Nets': s['dividendes_nets'],
            'Cotisations TNS': s['cotisations_tns'],
            'IR': s['ir_remuneration'],
            'IS SARL': s['is_sarl'],
            'IS Holding': s['is_holding'],
            'Flat Tax': s['flat_tax'],
            'Total Prélèvements': total_cotisations,
            'Net Disponible': net_disponible,
            'Taux Prélèvement (%)': s['taux_prelevement_global']
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Trier par rémunération brute
    df = df.sort_values('Rémunération Brute').reset_index(drop=True)
    
    return df


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
    is_holding = [s['is_holding'] for s in scenarios_valides]
    flat_tax = [s['flat_tax'] for s in scenarios_valides]
    
    # Créer des sous-graphiques (2x2 - 1)
    fig = sp.make_subplots(
        rows=2, cols=2,
        subplot_titles=('Optimisation du revenu net total', 
                      'Composition des prélèvements',
                      'Taux de prélèvement global',
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
    
    # Graphique 2 : Composition des prélèvements
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
        row=1, col=2
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
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=remunerations, 
            y=[c + i + is_s + is_h for c, i, is_s, is_h in zip(cotisations, ir, is_sarl, is_holding)],
            mode='lines',
            name='+ IS Total',
            fill='tonexty',
            line=dict(color='darkred'),
            hovertemplate='<b>Rémunération:</b> %{x:,.0f}€<br>' +
                         '<b>IS Total:</b> %{customdata:,.0f}€<extra></extra>',
            customdata=[s + h for s, h in zip(is_sarl, is_holding)]
        ),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=remunerations, 
            y=[c + i + is_s + is_h + ft for c, i, is_s, is_h, ft in zip(cotisations, ir, is_sarl, is_holding, flat_tax)],
            mode='lines',
            name='+ Flat tax',
            fill='tonexty',
            line=dict(color='darkblue'),
            hovertemplate='<b>Rémunération:</b> %{x:,.0f}€<br>' +
                         '<b>Flat tax:</b> %{customdata:,.0f}€<extra></extra>',
            customdata=flat_tax
        ),
        row=1, col=2
    )
    
    # Graphique 3 : Taux de prélèvement
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
    fig.update_yaxes(title_text="Prélèvements cumulés (€)", tickformat=",", row=1, col=2)
    fig.update_yaxes(title_text="Taux (%)", row=2, col=1)
    
    return fig


if __name__ == "__main__":
    main()
