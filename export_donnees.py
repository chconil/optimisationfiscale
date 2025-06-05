#!/usr/bin/env python3
"""
Outil CLI pour exporter les données d'optimisation fiscale
"""
import argparse
import csv
import sys
from formes_juridiques import SARLHolding

def afficher_tableau(scenarios, format_output='table'):
    """Affiche les scénarios sous forme de tableau ou CSV"""
    
    # En-têtes
    headers = [
        'Remuneration_Brute',
        'Total_Net',
        'Remuneration_Nette',
        'Dividendes_Nets', 
        'Cotisations_TNS',
        'IR',
        'IS_SARL',
        'IS_Holding',
        'Flat_Tax',
        'Total_Cotisations',
        'Net_Disponible',
        'Verification_Somme',
        'Taux_Prelevement_%'
    ]
    
    if format_output == 'csv':
        # Export CSV
        writer = csv.writer(sys.stdout)
        writer.writerow(headers)
        
        for s in scenarios:
            total_cotisations = s['cotisations_tns'] + s['ir_remuneration'] + s['is_sarl'] + s['is_holding'] + s['flat_tax']
            net_disponible = s['remuneration_nette_apres_ir'] + s['dividendes_nets']
            verification_somme = total_cotisations + net_disponible
            
            row = [
                s['remuneration_brute'],
                s['total_net'],
                s['remuneration_nette_apres_ir'],
                s['dividendes_nets'],
                s['cotisations_tns'],
                s['ir_remuneration'],
                s['is_sarl'],
                s['is_holding'],
                s['flat_tax'],
                total_cotisations,
                net_disponible,
                verification_somme,
                round(s['taux_prelevement_global'], 1)
            ]
            writer.writerow(row)
    
    else:
        # Affichage tableau formaté
        print("\n" + "="*170)
        print("DONNÉES D'OPTIMISATION FISCALE")
        print("="*170)
        
        # En-têtes avec formatage
        print(f"{'Rémun.':<9} {'Total':<9} {'Rémun.':<9} {'Divid.':<9} {'Cotis.':<9} {'IR':<8} {'IS_SARL':<8} {'IS_Hold':<8} {'FlatTax':<8} {'Tot.Cot':<9} {'Net':<9} {'Vérif':<9} {'Taux%':<6}")
        print(f"{'Brute':<9} {'Net':<9} {'Nette':<9} {'Nets':<9} {'TNS':<9} {'':<8} {'':<8} {'':<8} {'':<8} {'':<9} {'Dispo':<9} {'Somme':<9} {'':<6}")
        print("-"*170)
        
        for s in scenarios:
            total_cotisations = s['cotisations_tns'] + s['ir_remuneration'] + s['is_sarl'] + s['is_holding'] + s['flat_tax']
            net_disponible = s['remuneration_nette_apres_ir'] + s['dividendes_nets']
            verification_somme = total_cotisations + net_disponible
            
            print(f"{s['remuneration_brute']:>9,.0f} "
                  f"{s['total_net']:>9,.0f} "
                  f"{s['remuneration_nette_apres_ir']:>9,.0f} "
                  f"{s['dividendes_nets']:>9,.0f} "
                  f"{s['cotisations_tns']:>9,.0f} "
                  f"{s['ir_remuneration']:>8,.0f} "
                  f"{s['is_sarl']:>8,.0f} "
                  f"{s['is_holding']:>8,.0f} "
                  f"{s['flat_tax']:>8,.0f} "
                  f"{total_cotisations:>9,.0f} "
                  f"{net_disponible:>9,.0f} "
                  f"{verification_somme:>9,.0f} "
                  f"{s['taux_prelevement_global']:>6.1f}")
        
        print("-"*170)
        print(f"Total de {len(scenarios)} scénarios")
        
        # Afficher l'optimal
        optimal = max(scenarios, key=lambda x: x['total_net'])
        print(f"\n🎯 OPTIMUM: Rémunération {optimal['remuneration_brute']:,.0f}€ → Total net {optimal['total_net']:,.0f}€")

def main():
    parser = argparse.ArgumentParser(description='Export des données d\'optimisation fiscale')
    parser.add_argument('--resultat', type=int, default=300000, 
                       help='Résultat avant rémunération (défaut: 300000)')
    parser.add_argument('--charges', type=int, default=50000,
                       help='Charges existantes (défaut: 50000)')
    parser.add_argument('--parts', type=float, default=1.0,
                       help='Nombre de parts fiscales (défaut: 1.0)')
    parser.add_argument('--pas', type=int, default=2500,
                       help='Pas de calcul (défaut: 2500)')
    parser.add_argument('--per', type=int, default=0,
                       help='Montant PER (défaut: 0)')
    parser.add_argument('--madelin', type=int, default=0,
                       help='Montant Madelin (défaut: 0)')
    parser.add_argument('--girardin', type=int, default=0,
                       help='Montant Girardin (défaut: 0)')
    parser.add_argument('--format', choices=['table', 'csv'], default='table',
                       help='Format de sortie (défaut: table)')
    parser.add_argument('--min-salaire', type=int, default=0,
                       help='Salaire minimum (défaut: 0)')
    parser.add_argument('--max-salaire', type=int, 
                       help='Salaire maximum (défaut: résultat avant rémunération)')
    
    args = parser.parse_args()
    
    # Initialisation
    optimiseur = SARLHolding(
        resultat_avant_remuneration=args.resultat,
        charges_existantes=args.charges,
        parts_fiscales=args.parts
    )
    
    max_salaire = args.max_salaire or args.resultat - args.charges
    
    if args.format == 'table':
        print(f"Configuration:")
        print(f"  Résultat avant rémunération: {args.resultat:,}€")
        print(f"  Charges existantes: {args.charges:,}€")
        print(f"  Parts fiscales: {args.parts}")
        print(f"  Range salaire: {args.min_salaire:,}€ à {max_salaire:,}€ (pas: {args.pas:,}€)")
        if args.per > 0:
            print(f"  PER: {args.per:,}€")
        if args.madelin > 0:
            print(f"  Madelin: {args.madelin:,}€")
        if args.girardin > 0:
            print(f"  Girardin: {args.girardin:,}€")
    
    # Calcul des scénarios
    meilleur_scenario, tous_scenarios = optimiseur.optimiser(
        pas=args.pas,
        per_max=args.per,
        madelin_max=args.madelin,
        girardin_max=args.girardin
    )
    
    # Filtrer les scénarios selon la plage demandée
    scenarios_a_afficher = [
        s for s in tous_scenarios 
        if args.min_salaire <= s['remuneration_brute'] <= max_salaire
    ]
    
    if not scenarios_a_afficher:
        print("Erreur: Aucun scénario dans la plage spécifiée", file=sys.stderr)
        return 1
    
    # Affichage
    afficher_tableau(scenarios_a_afficher, args.format)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())