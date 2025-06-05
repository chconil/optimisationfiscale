#!/usr/bin/env python3
"""
Test rapide des calculs SAS pour vérifier la cohérence
100k CA, 50k charges existantes, rémunération 49k
"""

from formes_juridiques import SAS

# Créer l'optimiseur SAS
sas = SAS(resultat_avant_remuneration=100000, charges_existantes=50000, parts_fiscales=1)

print("=== TEST SAS ===")
print(f"Résultat initial: {sas.resultat_initial:,.0f}€")
print(f"Charges existantes: {sas.charges:,.0f}€") 
print(f"Résultat avant rémunération: {sas.resultat_avant_remuneration:,.0f}€")
print()

# Test avec salaire de 49k
salaire_test = 49000
scenario = sas.calculer_scenario(salaire_test)

print(f"=== SCÉNARIO SALAIRE {salaire_test:,.0f}€ ===")
print(f"Salaire brut: {scenario['salaire_brut']:,.0f}€")
print(f"Cotisations salariales: {scenario['cotisations_salariales']:,.0f}€")
print(f"Cotisations patronales: {scenario['cotisations_patronales']:,.0f}€")
print(f"Coût total employeur: {scenario['cout_total_salaire']:,.0f}€")
print(f"Salaire net avant IR: {scenario['salaire_net_avant_ir']:,.0f}€")
print()
print(f"Résultat après salaire: {scenario['resultat_apres_remuneration']:,.0f}€")
print(f"IS: {scenario['is_total']:,.0f}€")
print(f"Dividendes bruts: {scenario['dividendes_bruts']:,.0f}€")
print(f"Flat tax: {scenario['flat_tax']:,.0f}€") 
print(f"Dividendes nets: {scenario['dividendes_nets']:,.0f}€")
print()
print(f"Total net: {scenario['total_net']:,.0f}€")
print(f"Taux prélèvement global: {scenario['taux_prelevement_global']:.1f}%")

# Vérification manuelle
cout_total = scenario['cout_total_salaire']
resultat_apres = sas.resultat_avant_remuneration - cout_total
print(f"\n=== VÉRIFICATION MANUELLE ===")
print(f"Budget disponible: {sas.resultat_avant_remuneration:,.0f}€")
print(f"Coût total salaire: {cout_total:,.0f}€")
print(f"Résultat après salaire calculé: {resultat_apres:,.0f}€")
print(f"Résultat après salaire dans scenario: {scenario['resultat_apres_remuneration']:,.0f}€")
print(f"Cohérent: {resultat_apres == scenario['resultat_apres_remuneration']}")

print(f"\n=== TEST OPTIMISATION ===")
meilleur, tous_scenarios = sas.optimiser(pas=2500)

print(f"Nombre de scénarios testés: {len(tous_scenarios)}")
if len(tous_scenarios) > 0:
    print(f"Premier scénario salaire: {tous_scenarios[0]['salaire_brut']:,.0f}€")
    print(f"Dernier scénario salaire: {tous_scenarios[-1]['salaire_brut']:,.0f}€")

print(f"Salaire optimal proposé: {meilleur['salaire_brut']:,.0f}€")
print(f"Coût total optimal: {meilleur['cout_total_salaire']:,.0f}€")
print(f"Salaire brut max théorique: {int(50000 / 1.42):,.0f}€")
print(f"Total net optimal: {meilleur['total_net']:,.0f}€")