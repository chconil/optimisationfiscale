#!/usr/bin/env python3
"""
Analyse comparative des coûts réels : Rémunération vs Dividendes
Affiche un tableau détaillé pour comprendre pourquoi l'optimisation donne des résultats "tout ou rien"
"""

from calculs import OptimisationRemunerationSARL
import pandas as pd

def analyser_couts_reels(resultat_avant_remuneration=250000, max_montant=200000, pas=5000, ca_variable=False):
    """
    Analyse les coûts réels de la rémunération vs dividendes
    
    Args:
        resultat_avant_remuneration: Résultat de la société avant rémunération
        max_montant: Montant maximum à analyser
        pas: Pas d'analyse en euros
    """
    
    optimiseur = OptimisationRemunerationSARL(
        resultat_avant_remuneration=resultat_avant_remuneration,
        charges_existantes=0,
        parts_fiscales=1
    )
    
    print(f"📊 ANALYSE DES COÛTS RÉELS - Résultat avant rémunération: {resultat_avant_remuneration:,}€")
    print("=" * 120)
    
    # Collecte des données
    donnees = []
    
    for montant_net_cible in range(pas, max_montant + 1, pas):
        
        # === ADAPTATION DU CA SI DEMANDÉ ===
        if ca_variable:
            resultat_adapte = montant_net_cible * 1.4
            optimiseur = OptimisationRemunerationSARL(
                resultat_avant_remuneration=resultat_adapte,
                charges_existantes=0,
                parts_fiscales=1
            )
        else:
            resultat_adapte = resultat_avant_remuneration
        
        # === CALCUL RÉMUNÉRATION ===
        # Pour obtenir montant_net_cible en rémunération, il faut calculer le brut nécessaire
        remuneration_brute_estimee = montant_net_cible * 1.8  # Estimation initiale
        
        # Ajustement itératif pour trouver le bon brut
        for tentative in range(10):
            scenario_rem = optimiseur.calculer_scenario(remuneration_brute_estimee)
            ecart = scenario_rem['remuneration_nette_apres_ir'] - montant_net_cible
            
            if abs(ecart) < 50:  # Précision de 50€
                break
                
            # Ajustement proportionnel
            if ecart > 0:
                remuneration_brute_estimee *= 0.98
            else:
                remuneration_brute_estimee *= 1.02
        
        # Coût réel de la rémunération pour l'entreprise
        if ca_variable:
            # En CA variable, le coût = le CA nécessaire pour avoir le net ciblé
            cout_remuneration = resultat_adapte  # = montant_net_cible * 1.4
            is_sur_reste = 0  # Pas d'IS, tout va en rémunération
        else:
            # En CA fixe, coût = charges salariales + IS sur résultat résiduel
            resultat_apres_remuneration = resultat_adapte - scenario_rem['remuneration_brute'] - scenario_rem['cotisations_tns']
            if resultat_apres_remuneration > 0:
                is_sur_reste, _ = optimiseur.calculer_is(resultat_apres_remuneration)
            else:
                is_sur_reste = 0
            cout_remuneration = scenario_rem['remuneration_brute'] + scenario_rem['cotisations_tns'] + is_sur_reste
        
        # === CALCUL DIVIDENDES ===
        # Pour obtenir montant_net_cible en dividendes nets
        # Il faut remonter la chaîne : nets → holding → sarl → avant IS
        
        # 1. Dividendes holding nécessaires (avant flat tax 30%)
        dividendes_holding_necessaires = montant_net_cible / 0.70
        
        # 2. Dividendes SARL nécessaires (avant IS holding 1.25%)
        taux_is_holding_effectif = 0.05 * 0.25  # 1.25%
        dividendes_sarl_necessaires = dividendes_holding_necessaires / (1 - taux_is_holding_effectif)
        
        # 3. Résultat avant IS SARL nécessaire
        # Calcul IS selon tranches
        if dividendes_sarl_necessaires <= 42500:
            is_sarl_necessaire = dividendes_sarl_necessaires * 0.15
        else:
            is_sarl_necessaire = 42500 * 0.15 + (dividendes_sarl_necessaires - 42500) * 0.25
        
        resultat_avant_is_necessaire = dividendes_sarl_necessaires + is_sarl_necessaire
        
        # Coût réel des dividendes = résultat avant IS nécessaire
        cout_dividendes = resultat_avant_is_necessaire
        
        # === CALCULS DE VÉRIFICATION ===
        # Vérification avec un scénario réel (0€ de rémunération, tout en dividendes)
        if resultat_avant_is_necessaire <= resultat_adapte:
            scenario_div = optimiseur.calculer_scenario(0)
            
            # Calculer quel pourcentage du résultat on utilise
            pourcentage_utilise = resultat_avant_is_necessaire / resultat_adapte
            
            dividendes_nets_reels = scenario_div['dividendes_nets'] * pourcentage_utilise
            is_reel = scenario_div['is_sarl'] * pourcentage_utilise
            flat_tax_reelle = scenario_div['flat_tax'] * pourcentage_utilise
        else:
            dividendes_nets_reels = 0
            is_reel = 0
            flat_tax_reelle = 0
        
        # === CALCUL DES EFFICACITÉS ===
        efficacite_remuneration = montant_net_cible / cout_remuneration if cout_remuneration > 0 else 0
        efficacite_dividendes = montant_net_cible / cout_dividendes if cout_dividendes > 0 else 0
        
        # Différence de coût
        diff_cout = cout_dividendes - cout_remuneration
        meilleur = "REMUNERATION" if cout_remuneration < cout_dividendes else "DIVIDENDES"
        
        # IR réel payé pour ce niveau de net
        ir_reel = scenario_rem['ir_remuneration']
        
        donnees.append({
            'montant_net': montant_net_cible,
            'ir_reel': ir_reel,
            'cout_remuneration': cout_remuneration,
            'cout_dividendes': cout_dividendes,
            'diff_cout': diff_cout,
            'efficacite_rem': efficacite_remuneration,
            'efficacite_div': efficacite_dividendes,
            'meilleur': meilleur,
            'rem_brute': scenario_rem['remuneration_brute'],
            'cotisations': scenario_rem['cotisations_tns'],
            'ir': scenario_rem['ir_remuneration'],
            'is_sur_reste': is_sur_reste,
            'is_necessaire': is_sarl_necessaire,
            'flat_tax': flat_tax_reelle,
            'ca_adapte': resultat_adapte
        })
    
    # === AFFICHAGE DU TABLEAU ===
    df = pd.DataFrame(donnees)
    
    if ca_variable:
        print(f"{'Net Ciblé':>9} {'IR réel':>8} {'CA adapt':>9} {'Coût Rém':>9} {'Coût Div':>9} {'Diff':>7} {'Eff R/D':>10} {'Meilleur':>9}")
        print(f"{'(€)':>9} {'(€)':>8} {'(€)':>9} {'(€)':>9} {'(€)':>9} {'(€)':>7} {'':>10} {'':>9}")
        print("-" * 81)
    else:
        print(f"{'Net Ciblé':>9} {'IR réel':>8} {'Coût Rémun':>11} {'Coût Divid':>11} {'Différence':>9} {'Efficacité':>15} {'Meilleur':>10}")
        print(f"{'(€)':>9} {'(€)':>8} {'(€)':>11} {'(€)':>11} {'(€)':>9} {'Rém/Div':>15} {'':>10}")
        print("-" * 89)
    
    for _, row in df.iterrows():
        if ca_variable:
            print(f"{row['montant_net']:>9,} "
                  f"{row['ir_reel']:>8,.0f} "
                  f"{row['ca_adapte']:>9,.0f} "
                  f"{row['cout_remuneration']:>9,.0f} "
                  f"{row['cout_dividendes']:>9,.0f} "
                  f"{row['diff_cout']:>7,.0f} "
                  f"{row['efficacite_rem']:.2f}/{row['efficacite_div']:.2f} "
                  f"{row['meilleur']:>9}")
        else:
            print(f"{row['montant_net']:>9,} "
                  f"{row['ir_reel']:>8,.0f} "
                  f"{row['cout_remuneration']:>11,.0f} "
                  f"{row['cout_dividendes']:>11,.0f} "
                  f"{row['diff_cout']:>9,.0f} "
                  f"{row['efficacite_rem']:.2f}/{row['efficacite_div']:.2f} "
                  f"{row['meilleur']:>10}")
    
    if ca_variable:
        print("-" * 81)
    else:
        print("-" * 89)
    
    # === ANALYSE DÉTAILLÉE ===
    print("\n📈 ANALYSE DÉTAILLÉE DES COÛTS")
    print("=" * 60)
    
    # Point d'équilibre
    equilibres = df[abs(df['diff_cout']) < 500]  # Différence < 500€
    if not equilibres.empty:
        print(f"🎯 Points d'équilibre (différence < 500€):")
        for _, row in equilibres.iterrows():
            print(f"   - {row['montant_net']:,}€ net → Différence: {row['diff_cout']:,.0f}€")
    
    # Zones de domination
    zones_rem = df[df['meilleur'] == 'REMUNERATION']
    zones_div = df[df['meilleur'] == 'DIVIDENDES']
    
    if not zones_rem.empty:
        print(f"\n💼 Rémunération plus efficace pour:")
        print(f"   - {zones_rem['montant_net'].min():,}€ à {zones_rem['montant_net'].max():,}€ net")
        print(f"   - Économie moyenne: {zones_rem['diff_cout'].mean():,.0f}€")
    
    if not zones_div.empty:
        print(f"\n💰 Dividendes plus efficaces pour:")
        print(f"   - {zones_div['montant_net'].min():,}€ à {zones_div['montant_net'].max():,}€ net")
        print(f"   - Économie moyenne: {-zones_div['diff_cout'].mean():,.0f}€")
    
    # === EXPLICATION DES COÛTS ===
    print(f"\n🔍 DÉTAIL DES COÛTS MARGINAUX")
    print("=" * 60)
    
    # Prendre quelques exemples
    exemples = [25000, 50000, 100000, 150000]
    
    for montant in exemples:
        if montant <= max_montant:
            row = df[df['montant_net'] == montant].iloc[0]
            
            print(f"\n💡 Pour {montant:,}€ nets :")
            print(f"   RÉMUNÉRATION → Coût total: {row['cout_remuneration']:,.0f}€")
            print(f"   ├─ Brut nécessaire: {row['rem_brute']:,.0f}€")
            print(f"   ├─ Cotisations TNS: {row['cotisations']:,.0f}€")
            print(f"   ├─ IS sur reste: {row['is_sur_reste']:,.0f}€")
            print(f"   └─ IR (payé par salarié): {row['ir']:,.0f}€")
            print(f"   ")
            print(f"   DIVIDENDES → Coût total: {row['cout_dividendes']:,.0f}€")
            print(f"   ├─ IS SARL: {row['is_necessaire']:,.0f}€")
            print(f"   ├─ IS Holding: {row['is_necessaire'] * 0.0125:.0f}€")
            print(f"   └─ Flat tax (payée par actionnaire): {row['cout_dividendes'] * 0.3 * 0.9875:.0f}€")
            print(f"   ")
            print(f"   ⚖️  {row['meilleur']} plus efficace (écart: {abs(row['diff_cout']):,.0f}€)")
    
    return df

def analyser_taux_marginaux():
    """Analyse les taux marginaux pour comprendre les seuils"""
    print(f"\n📊 ANALYSE DES TAUX MARGINAUX")
    print("=" * 60)
    
    # Taux marginaux rémunération
    print("💼 RÉMUNÉRATION :")
    print("   ├─ Cotisations TNS: ~41% (variable selon plafonds)")
    print("   ├─ IR marginal: 0% → 11% → 30% → 41% → 45%")
    print("   └─ Taux marginal total: 41% à 86%")
    
    print("\n💰 DIVIDENDES :")
    print("   ├─ IS SARL: 15% (≤42.5k€) puis 25%")
    print("   ├─ IS Holding: 1.25% (5% × 25%)")
    print("   ├─ Flat tax: 30%")
    print("   └─ Taux marginal total: ~41% à 47%")
    
    print("\n🎯 EXPLICATION du 'tout ou rien' :")
    print("   → Taux marginaux proches créent des équilibres instables")
    print("   → Petites variations font basculer l'optimum")
    print("   → D'où les allocations extrêmes dans l'optimisation")

if __name__ == "__main__":
    print("🚀 LANCEMENT DE L'ANALYSE DES COÛTS RÉELS")
    print("=" * 80)
    
    # Configuration
    resultat = 250000  # €
    max_analyse = 150000  # €
    pas_analyse = 5000  # €
    
    print("\n📊 ANALYSE 1: CA FIXE à 250k€")
    print("=" * 50)
    df_resultats_fixe = analyser_couts_reels(resultat, max_analyse, pas_analyse, ca_variable=False)
    
    print("\n📊 ANALYSE 2: CA VARIABLE (Net ciblé × 1.4)")
    print("=" * 50)
    df_resultats_variable = analyser_couts_reels(resultat, max_analyse, pas_analyse, ca_variable=True)
    
    # Analyse des taux marginaux
    analyser_taux_marginaux()
    
    print(f"\n✅ Analyses terminées.")
    print(f"📈 Données CA fixe: df_resultats_fixe")
    print(f"📈 Données CA variable: df_resultats_variable")