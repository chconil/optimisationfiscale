import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.offline import plot

class OptimisationRemunerationSARL:
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1):
        self.resultat_initial = resultat_avant_remuneration
        self.charges = charges_existantes
        self.resultat_avant_remuneration = resultat_avant_remuneration - charges_existantes
        self.parts_fiscales = parts_fiscales
        
        # Paramètres fiscaux 2024
        self.taux_cotisations_tns = {
            'maladie': 0.065,
            'allocations_familiales': 0.031,
            'retraite_base': 0.1775,
            'retraite_complementaire': 0.07,
            'invalidite_deces': 0.013,
            'csg_crds': 0.097,
            'formation': 0.0025
        }
        
        # Tranches IS
        self.tranches_is = [
            {'limite': 42500, 'taux': 0.15},
            {'limite': float('inf'), 'taux': 0.25}
        ]
        
        # Barème IR 2024 (par part)
        self.tranches_ir = [
            {'limite': 11294, 'taux': 0},
            {'limite': 28797, 'taux': 0.11},
            {'limite': 82341, 'taux': 0.30},
            {'limite': 177106, 'taux': 0.41},
            {'limite': float('inf'), 'taux': 0.45}
        ]
        
        # Autres paramètres
        self.taux_flat_tax = 0.30
        self.taux_exoneration_mere_fille = 0.95
        self.abattement_frais_pro = 0.10  # 10% plafonné
        self.plafond_abattement = 13522  # Pour 2024
        
        # Dispositifs d'optimisation fiscale
        self.plafond_per = 32419  # PER 2024 (8 x PASS)
        self.plafond_madelin = 84000  # Madelin TNS 2024
        self.taux_girardin_industriel = 1.10  # 110% de réduction
        #self.taux_girardin_logement = 1.18  # 118% de réduction sur 5 ans
        
    def calculer_cotisations_tns(self, remuneration_brute):
        """Calcule les cotisations TNS sur la rémunération de gérance"""
        # Assiette après abattement de 10% pour frais professionnels
        assiette = remuneration_brute * 0.9
        
        cotisations = {}
        total = 0
        
        # Calcul détaillé par cotisation
        for nom, taux in self.taux_cotisations_tns.items():
            if nom == 'retraite_base':
                # Plafonnée à 1 PASS (46 368€ en 2024)
                base = min(assiette, 46368)
                cotisations[nom] = base * taux
            elif nom == 'allocations_familiales':
                # Taux réduit si < 3.5 PASS
                if remuneration_brute < 162288:
                    cotisations[nom] = assiette * taux
                else:
                    cotisations[nom] = assiette * 0.031
            else:
                cotisations[nom] = assiette * taux
            
            total += cotisations[nom]
        
        return total, cotisations
    
    def calculer_ir(self, revenu_net_imposable):
        """Calcule l'IR selon le barème progressif"""
        # Revenu imposable par part
        revenu_par_part = revenu_net_imposable / self.parts_fiscales
        
        ir_par_part = 0
        revenu_restant = revenu_par_part
        details = []
        tranche_precedente = 0
        
        for tranche in self.tranches_ir:
            if revenu_restant <= 0:
                break
            
            largeur_tranche = tranche['limite'] - tranche_precedente
            montant_dans_tranche = min(revenu_restant, largeur_tranche)
            
            if montant_dans_tranche > 0:
                ir_tranche = montant_dans_tranche * tranche['taux']
                ir_par_part += ir_tranche
                
                details.append({
                    'de': tranche_precedente,
                    'a': tranche_precedente + montant_dans_tranche,
                    'taux': tranche['taux'],
                    'base': montant_dans_tranche,
                    'impot': ir_tranche
                })
            
            revenu_restant -= montant_dans_tranche
            tranche_precedente = tranche['limite']
            
            if tranche['limite'] == float('inf'):
                break
        
        # IR total
        ir_total = ir_par_part * self.parts_fiscales
        
        return ir_total, details
    
    def calculer_is(self, benefice_imposable):
        """Calcule l'IS selon les tranches"""
        is_total = 0
        reste = benefice_imposable
        details = []
        
        for tranche in self.tranches_is:
            if reste <= 0:
                break
            
            montant_tranche = min(reste, tranche['limite'])
            is_tranche = montant_tranche * tranche['taux']
            is_total += is_tranche
            
            details.append({
                'tranche': tranche['limite'],
                'taux': tranche['taux'],
                'base': montant_tranche,
                'impot': is_tranche
            })
            
            reste -= montant_tranche
            
        return is_total, details
    
    def calculer_scenario(self, remuneration_gerance, per_montant=0, madelin_montant=0, girardin_montant=0):
        """Calcule un scénario complet de rémunération"""
        resultats = {}
        
        # 1. Calcul des cotisations TNS
        cotisations_tns, detail_cotisations = self.calculer_cotisations_tns(remuneration_gerance)
        resultats['remuneration_brute'] = remuneration_gerance
        resultats['cotisations_tns'] = cotisations_tns
        resultats['cotisations_detail'] = detail_cotisations
        resultats['remuneration_nette_avant_ir'] = remuneration_gerance
        
        # 2. Calcul du revenu imposable (après abattement 10%)
        abattement = min(resultats['remuneration_nette_avant_ir'] * self.abattement_frais_pro, 
                         self.plafond_abattement)
        revenu_imposable = resultats['remuneration_nette_avant_ir'] - abattement
        resultats['abattement_frais_pro'] = abattement
        resultats['revenu_imposable'] = revenu_imposable
        
        # 3. Optimisations fiscales sur le revenu
        # PER : déduction du revenu imposable
        per_deduction = min(per_montant, min(revenu_imposable * 0.10, self.plafond_per))
        revenu_imposable_final = revenu_imposable - per_deduction
        
        resultats['per_deduction'] = per_deduction
        resultats['madelin_deduction'] = 0  # Madelin n'est plus une déduction personnelle
        resultats['revenu_imposable_final'] = revenu_imposable_final
        
        # 4. Calcul de l'IR sur la rémunération
        ir_remuneration, detail_ir = self.calculer_ir(revenu_imposable_final)
        
        # Girardin : réduction d'impôt (110% de l'investissement)
        reduction_girardin_brute = girardin_montant * self.taux_girardin_industriel
        reduction_girardin = min(reduction_girardin_brute, ir_remuneration)
        ir_final = ir_remuneration - reduction_girardin
        
        resultats['ir_avant_girardin'] = ir_remuneration
        resultats['reduction_girardin'] = reduction_girardin
        resultats['ir_remuneration'] = ir_final
        resultats['ir_detail'] = detail_ir
        resultats['remuneration_nette_apres_ir'] = resultats['remuneration_nette_avant_ir'] - ir_final
        
        # 5. Calcul du résultat après rémunération et charges Madelin
        # Madelin TNS : charge déductible de la SARL (limité au plafond)
        madelin_charge = min(madelin_montant, self.plafond_madelin)
        resultat_apres_remuneration = self.resultat_avant_remuneration - remuneration_gerance - cotisations_tns - madelin_charge
        resultats['resultat_apres_remuneration'] = resultat_apres_remuneration
        resultats['madelin_charge'] = madelin_charge
        
        # Optimisations utilisées
        # Calcul de l'économie d'IS grâce au Madelin (charge déductible)
        economie_is_madelin = madelin_charge * 0.25  # Économie d'IS à 25%
        resultats['optimisations'] = {
            'per': per_montant,
            'madelin': madelin_montant, 
            'girardin': girardin_montant,
            'economies_ir': per_deduction * 0.30 + reduction_girardin,
            'economie_is_madelin': economie_is_madelin,
            'economies_totales': per_deduction * 0.30 + economie_is_madelin + reduction_girardin,
            'gain_net_girardin': reduction_girardin - girardin_montant
        }
        
        # 6. Calcul de l'IS
        is_total, detail_is = self.calculer_is(resultat_apres_remuneration)
        resultats['is_sarl'] = is_total
        resultats['is_detail'] = detail_is
        
        # 7. Dividendes distribuables
        dividendes_sarl = resultat_apres_remuneration - is_total
        resultats['dividendes_sarl'] = dividendes_sarl
        
        # 8. Remontée à la holding (régime mère-fille)
        quote_part_imposable = dividendes_sarl * (1 - self.taux_exoneration_mere_fille)
        is_holding = quote_part_imposable * 0.25
        dividendes_holding = dividendes_sarl - is_holding
        
        resultats['quote_part_imposable'] = quote_part_imposable
        resultats['is_holding'] = is_holding
        resultats['dividendes_holding'] = dividendes_holding
        
        # 9. Distribution finale et flat tax
        flat_tax = dividendes_holding * self.taux_flat_tax
        dividendes_nets = dividendes_holding - flat_tax
        
        resultats['flat_tax'] = flat_tax
        resultats['dividendes_nets'] = dividendes_nets
        
        # Calcul du taux de prélèvement sur les dividendes
        # Prélèvements totaux = IS SARL + IS Holding + Flat tax
        prelevements_dividendes = is_total + is_holding + flat_tax
        # Base = résultat après rémunération (avant tous prélèvements sur dividendes)
        if resultat_apres_remuneration > 0:
            taux_prelevement_dividendes = (prelevements_dividendes / resultat_apres_remuneration) * 100
        else:
            taux_prelevement_dividendes = 0
        
        resultats['prelevements_dividendes'] = prelevements_dividendes
        resultats['taux_prelevement_dividendes'] = taux_prelevement_dividendes
        
        # 10. Total net perçu (en déduisant l'investissement Girardin)
        # Si les dividendes sont négatifs, on ne peut pas les distribuer
        dividendes_distribuables = max(0, dividendes_nets)
        resultats['total_net'] = resultats['remuneration_nette_apres_ir'] + dividendes_distribuables - girardin_montant
        
        # 11. Taux de prélèvement global
        total_prelevements = (self.resultat_avant_remuneration - resultats['total_net'])
        resultats['taux_prelevement_global'] = total_prelevements / self.resultat_avant_remuneration * 100
        
        return resultats
    
    
    def optimiser_avec_niches(self, pas=5000, min_salaire=0, max_salaire=None, per_max=None, madelin_max=None, girardin_max=None):
        """Trouve la rémunération optimale en incluant les optimisations fiscales basée sur l'efficacité économique"""
        if max_salaire is None:
            max_salaire = self.resultat_avant_remuneration
        if per_max is None:
            per_max = self.plafond_per
        if madelin_max is None:
            madelin_max = self.plafond_madelin
        if girardin_max is None:
            girardin_max = 50000  # Limite raisonnable pour Girardin
        
        meilleur_scenario = None
        meilleur_efficacite = 0
        tous_scenarios = []
        
        # Test différentes combinaisons d'optimisations
        optimisations_a_tester = [
            {'per': 0, 'madelin': 0, 'girardin': 0},  # Sans optimisation
            {'per': per_max, 'madelin': 0, 'girardin': 0},  # PER seul
            {'per': 0, 'madelin': madelin_max, 'girardin': 0},  # Madelin seul
            {'per': 0, 'madelin': 0, 'girardin': girardin_max},  # Girardin seul
            {'per': per_max, 'madelin': madelin_max, 'girardin': 0},  # PER + Madelin
            {'per': per_max, 'madelin': 0, 'girardin': girardin_max},  # PER + Girardin
            {'per': 0, 'madelin': madelin_max, 'girardin': girardin_max},  # Madelin + Girardin
            {'per': per_max, 'madelin': madelin_max, 'girardin': girardin_max},  # Tout
        ]
        
        for optimisations in optimisations_a_tester:
            scenarios_optim = []
            
            # Si Girardin est utilisé, ajuster la stratégie d'optimisation
            if optimisations['girardin'] > 0:
                # Stratégie spéciale pour Girardin : chercher à maximiser l'IR pour utiliser la réduction
                scenarios_optim = self._optimiser_avec_girardin(
                    optimisations, min_salaire, max_salaire, pas
                )
            else:
                # Optimisation classique pour les autres cas
                for remuneration in range(min_salaire, max_salaire + 1, pas):
                    scenario = self.calculer_scenario(
                        remuneration, 
                        per_montant=optimisations['per'],
                        madelin_montant=optimisations['madelin'],
                        girardin_montant=optimisations['girardin']
                    )
                    
                    # Ne pas inclure les scénarios non plausibles (dividendes négatifs)
                    if scenario['flat_tax'] < 0:
                        continue
                        
                    scenario['nom_strategie'] = f"PER:{optimisations['per']:,}€ | Madelin:{optimisations['madelin']:,}€ | Girardin:{optimisations['girardin']:,}€"
                    scenarios_optim.append(scenario)
            
            # Mise à jour du meilleur scénario global basé sur le total net
            for scenario in scenarios_optim:
                if scenario['total_net'] > meilleur_efficacite:
                    meilleur_efficacite = scenario['total_net']
                    meilleur_scenario = scenario
            
            tous_scenarios.append({
                'optimisations': optimisations,
                'scenarios': scenarios_optim,
                'meilleur': max(scenarios_optim, key=lambda x: x['total_net'])
            })
        
        return meilleur_scenario, tous_scenarios
    
    def _optimiser_avec_girardin(self, optimisations, min_salaire, max_salaire, pas):
        """Optimisation spéciale pour Girardin : cherche la rémunération qui maximise l'usage de la réduction"""
        scenarios = []
        girardin_montant = optimisations['girardin']
        reduction_theorique = girardin_montant * self.taux_girardin_industriel
        
        # Phase 1: Recherche grossière pour trouver la zone optimale
        scenarios_grossiers = []
        pas_grossier = max(pas * 4, 10000)  # Pas plus large pour recherche initiale
        
        for remuneration in range(min_salaire, max_salaire + 1, pas_grossier):
            scenario = self.calculer_scenario(
                remuneration,
                per_montant=optimisations['per'],
                madelin_montant=optimisations['madelin'],
                girardin_montant=girardin_montant
            )
            
            # Ne pas inclure les scénarios non plausibles (dividendes négatifs)
            if scenario['flat_tax'] < 0:
                continue
                
            scenario['nom_strategie'] = f"PER:{optimisations['per']:,}€ | Madelin:{optimisations['madelin']:,}€ | Girardin:{optimisations['girardin']:,}€"
            scenarios_grossiers.append(scenario)
        
        # Trouver la rémunération qui maximise le total net
        meilleur_grossier = max(scenarios_grossiers, key=lambda x: x['total_net'])
        remuneration_optimale_approx = meilleur_grossier['remuneration_brute']
        
        # Phase 2: Recherche fine autour de la zone optimale
        zone_min = max(min_salaire, remuneration_optimale_approx - pas_grossier)
        zone_max = min(max_salaire, remuneration_optimale_approx + pas_grossier)
        
        for remuneration in range(zone_min, zone_max + 1, pas):
            scenario = self.calculer_scenario(
                remuneration,
                per_montant=optimisations['per'],
                madelin_montant=optimisations['madelin'],
                girardin_montant=girardin_montant
            )
            
            # Ne pas inclure les scénarios non plausibles (dividendes négatifs)
            if scenario['flat_tax'] < 0:
                continue
                
            scenario['nom_strategie'] = f"PER:{optimisations['per']:,}€ | Madelin:{optimisations['madelin']:,}€ | Girardin:{optimisations['girardin']:,}€"
            
            # Ajouter des métriques d'efficacité Girardin
            scenario['efficacite_girardin'] = scenario['reduction_girardin'] / reduction_theorique if reduction_theorique > 0 else 0
            scenario['ir_genere'] = scenario['ir_avant_girardin']
            
            scenarios.append(scenario)
        
        # Si on n'a pas assez de scenarios (zone trop petite), ajouter tous les scenarios grossiers
        if len(scenarios) < 10:
            scenarios.extend(scenarios_grossiers)
            # Supprimer les doublons basés sur la rémunération
            scenarios_uniques = {}
            for s in scenarios:
                scenarios_uniques[s['remuneration_brute']] = s
            scenarios = list(scenarios_uniques.values())
        
        return scenarios
    
    def _calculer_cout_economique_total(self, scenario):
        """Calcule le coût économique réel d'un scénario"""
        # Coût de la rémunération = (net + IR) × 1.4 pour tenir compte du coût économique
        net_remuneration = scenario['remuneration_nette_apres_ir']
        ir_remuneration = scenario['ir_remuneration']
        cout_remuneration = (net_remuneration + ir_remuneration) * 1.4
        
        # Coût des dividendes = résultat avant IS nécessaire pour générer les dividendes nets
        dividendes_nets = max(0, scenario['dividendes_nets'])  # Pas de dividendes négatifs
        if dividendes_nets > 0:
            # Remontée de la chaîne: nets → holding → sarl → avant IS
            dividendes_holding = dividendes_nets / 0.70  # Avant flat tax 30%
            taux_is_holding_effectif = 0.05 * 0.25  # 1.25%
            dividendes_sarl = dividendes_holding / (1 - taux_is_holding_effectif)
            
            # Calcul IS SARL selon tranches
            if dividendes_sarl <= 42500:
                is_sarl = dividendes_sarl * 0.15
            else:
                is_sarl = 42500 * 0.15 + (dividendes_sarl - 42500) * 0.25
            
            cout_dividendes = dividendes_sarl + is_sarl
        else:
            cout_dividendes = 0
        
        cout_total = cout_remuneration + cout_dividendes
        
        return {
            'cout_remuneration': cout_remuneration,
            'cout_dividendes': cout_dividendes,
            'cout_total': cout_total,
            'efficacite_globale': scenario['total_net'] / cout_total if cout_total > 0 else 0
        }
    
    def _trouver_mix_optimal(self, scenarios):
        """Trouve le mix optimal en maximisant le total net"""
        # Simplement maximiser le total net perçu
        meilleur_scenario = max(scenarios, key=lambda x: x['total_net'])
        return meilleur_scenario
    
    def afficher_resultat(self, resultat):
        """Affiche les résultats de manière formatée"""
        print("=" * 60)
        print("OPTIMISATION FISCALE SARL + HOLDING")
        print("=" * 60)
        print(f"\nRésultat initial : {self.resultat_initial:,.0f}€")
        print(f"Charges existantes : {self.charges:,.0f}€")
        print(f"Résultat avant rémunération : {self.resultat_avant_remuneration:,.0f}€")
        print(f"Nombre de parts fiscales : {self.parts_fiscales}")
        
        # Affichage des optimisations fiscales si présentes
        if 'optimisations' in resultat and any(resultat['optimisations'][k] > 0 for k in ['per', 'madelin', 'girardin']):
            print("\n--- 🎯 OPTIMISATIONS FISCALES UTILISÉES ---")
            if resultat['optimisations']['per'] > 0:
                print(f"PER : {resultat['optimisations']['per']:,.0f}€")
            if resultat['optimisations']['madelin'] > 0:
                print(f"Madelin TNS : {resultat['optimisations']['madelin']:,.0f}€")
            if resultat['optimisations']['girardin'] > 0:
                print(f"Girardin : {resultat['optimisations']['girardin']:,.0f}€")
            print(f"💰 ÉCONOMIES TOTALES : {resultat['optimisations']['economies_totales']:,.0f}€")
        
        print("\n--- RÉMUNÉRATION DE GÉRANCE ---")
        print(f"Rémunération brute : {resultat['remuneration_brute']:,.0f}€")
        print(f"Cotisations TNS : {resultat['cotisations_tns']:,.0f}€")
        print(f"Rémunération nette avant IR : {resultat['remuneration_nette_avant_ir']:,.0f}€")
        print(f"Abattement frais pro (10%) : {resultat['abattement_frais_pro']:,.0f}€")
        print(f"Revenu imposable initial : {resultat['revenu_imposable']:,.0f}€")
        
        # Détail des déductions fiscales
        if 'per_deduction' in resultat and resultat['per_deduction'] > 0:
            print(f"  - Déduction PER : {resultat['per_deduction']:,.0f}€")
        if 'madelin_charge' in resultat and resultat['madelin_charge'] > 0:
            print(f"  - Charge Madelin SARL : {resultat['madelin_charge']:,.0f}€")
        if 'revenu_imposable_final' in resultat:
            print(f"Revenu imposable final : {resultat['revenu_imposable_final']:,.0f}€")
        
        if 'ir_avant_girardin' in resultat:
            print(f"IR avant Girardin : {resultat['ir_avant_girardin']:,.0f}€")
            if resultat['reduction_girardin'] > 0:
                print(f"  - Réduction Girardin : {resultat['reduction_girardin']:,.0f}€")
        print(f"IR final : {resultat['ir_remuneration']:,.0f}€")
        print(f"Rémunération nette après IR : {resultat['remuneration_nette_apres_ir']:,.0f}€")
        
        print("\n--- IMPOSITION SARL ---")
        if 'madelin_charge' in resultat and resultat['madelin_charge'] > 0:
            print(f"Charge Madelin TNS : {resultat['madelin_charge']:,.0f}€")
        print(f"Résultat après rémunération : {resultat['resultat_apres_remuneration']:,.0f}€")
        print(f"IS à payer : {resultat['is_sarl']:,.0f}€")
        for detail in resultat['is_detail']:
            print(f"  → {detail['base']:,.0f}€ à {detail['taux']*100}% = {detail['impot']:,.0f}€")
        
        print("\n--- DIVIDENDES ---")
        print(f"Dividendes SARL : {resultat['dividendes_sarl']:,.0f}€")
        print(f"Quote-part imposable (5%) : {resultat['quote_part_imposable']:,.0f}€")
        print(f"IS holding : {resultat['is_holding']:,.0f}€")
        print(f"Dividendes dans holding : {resultat['dividendes_holding']:,.0f}€")
        
        print("\n--- DISTRIBUTION FINALE ---")
        print(f"Flat tax (30%) : {resultat['flat_tax']:,.0f}€")
        print(f"Dividendes nets : {resultat['dividendes_nets']:,.0f}€")
        print(f"Taux prélèvement dividendes : {resultat['taux_prelevement_dividendes']:.1f}%")
        
        print("\n--- TOTAL ---")
        print(f"🎯 TOTAL NET PERÇU : {resultat['total_net']:,.0f}€")
        print(f"Taux de prélèvement global : {resultat['taux_prelevement_global']:.1f}%")
        
    def graphique_optimisation(self, scenarios):
        """Crée des graphiques interactifs avec Plotly"""
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
        
        # Retourner la figure (sans ouvrir automatiquement pour Streamlit)
        # plot(fig, filename='optimisation_fiscale.html', auto_open=True)
        return fig
    
    def graphique_comparaison_optimisations(self, tous_scenarios):
        """Crée un graphique comparant les différentes stratégies d'optimisation"""
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
            economies = [s['optimisations']['economies_totales'] for s in scenarios_valides]
            
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
        economies_totales = [s['optimisations']['economies_totales'] for s in meilleurs_par_strategie]
        
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
            height=900,
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
        
        # Ajout d'annotations sur les gains
        meilleur_gain = max(gains_nets)
        index_meilleur = gains_nets.index(meilleur_gain)
        
        fig.add_annotation(
            x=noms_strategies[index_meilleur],
            y=meilleur_gain,
            text=f"🏆 MEILLEURE<br>{meilleur_gain:,.0f}€",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="red",
            font=dict(color="red", size=12),
            row=1, col=2
        )
        
        # plot(fig, filename='comparaison_optimisations.html', auto_open=True)
        
        # Tableau de synthèse
        print("\n" + "="*80)
        print("🎯 SYNTHÈSE DES OPTIMISATIONS FISCALES")
        print("="*80)
        print(f"{'Stratégie':<45} {'Gain Net':<15} {'Rémun. Opt.':<15} {'Économies IR':<15}")
        print("-"*80)
        
        for i, scenario in enumerate(meilleurs_par_strategie):
            opt = tous_scenarios[i]['optimisations']
            nom_court = f"PER:{opt['per']//1000}k|Mad:{opt['madelin']//1000}k|Gir:{opt['girardin']//1000}k"
            
            marker = "🏆 " if scenario['total_net'] == meilleur_gain else "   "
            print(f"{marker}{nom_court:<42} {scenario['total_net']:>10,.0f}€ {scenario['remuneration_brute']:>12,.0f}€ {scenario['optimisations']['economies_totales']:>12,.0f}€")
        
        print("-"*80)
        difference_max = meilleur_gain - min(gains_nets)
        print(f"💰 GAIN MAXIMUM AVEC OPTIMISATIONS : +{difference_max:,.0f}€")
        
        return fig
    
    def interface_configuration(self):
        """Interface simple pour configurer les paramètres"""
        print("🔧 CONFIGURATION DES PARAMÈTRES")
        print("=" * 50)
        print(f"Résultat avant rémunération actuel : {self.resultat_avant_remuneration:,.0f}€")
        print(f"Parts fiscales actuelles : {self.parts_fiscales}")
        print("\nVoulez-vous modifier ces paramètres ? (o/n)")
        
        try:
            reponse = input().lower()
            if reponse == 'o':
                nouveau_resultat = input(f"Nouveau résultat avant rémunération ({self.resultat_avant_remuneration:,.0f}€) : ")
                if nouveau_resultat.strip():
                    self.resultat_avant_remuneration = float(nouveau_resultat.replace(',', ''))
                
                nouvelles_parts = input(f"Nouvelles parts fiscales ({self.parts_fiscales}) : ")
                if nouvelles_parts.strip():
                    self.parts_fiscales = float(nouvelles_parts)
            
            print("\n🎯 PARAMÉTRAGE DES OPTIMISATIONS FISCALES")
            print("=" * 50)
            
            per_max = input(f"Montant PER maximum (défaut: {self.plafond_per:,}€) : ")
            per_max = float(per_max.replace(',', '')) if per_max.strip() else self.plafond_per
            
            madelin_max = input(f"Montant Madelin maximum (défaut: {self.plafond_madelin:,}€) : ")
            madelin_max = float(madelin_max.replace(',', '')) if madelin_max.strip() else self.plafond_madelin
            
            girardin_max = input("Montant Girardin maximum (défaut: 50,000€) : ")
            girardin_max = float(girardin_max.replace(',', '')) if girardin_max.strip() else 50000
            
            pas_calcul = input("Pas de calcul en euros (défaut: 2,500€) : ")
            pas_calcul = int(pas_calcul.replace(',', '')) if pas_calcul.strip() else 2500
            
            return {
                'per_max': per_max,
                'madelin_max': madelin_max, 
                'girardin_max': girardin_max,
                'pas': pas_calcul
            }
            
        except (ValueError, KeyboardInterrupt):
            print("\n⚙️ Utilisation des paramètres par défaut...")
            return {
                'per_max': self.plafond_per,
                'madelin_max': self.plafond_madelin,
                'girardin_max': 50000,
                'pas': 2500
            }

# Utilisation du programme en CLI (désactivée pour Streamlit)
if __name__ == "__main__":
    print("🎯 OPTIMISATION FISCALE AVANCÉE SARL + HOLDING")
    print("=" * 60)
    print("💡 Pour utiliser l'interface graphique, lancez : streamlit run app.py")
    print("💡 Pour utiliser en CLI, décommentez le code ci-dessous")
    
    # # Configuration par défaut pour test rapide
    # optimiseur = OptimisationRemunerationSARL(
    #     resultat_avant_remuneration=300000,
    #     charges_existantes=50000,
    #     parts_fiscales=1
    # )
    # 
    # # Test rapide avec paramètres par défaut
    # meilleur_avec_niches, tous_scenarios_niches = optimiseur.optimiser_avec_niches(
    #     pas=5000,
    #     per_max=32419,
    #     madelin_max=84000,
    #     girardin_max=50000
    # )
    # 
    # optimiseur.afficher_resultat(meilleur_avec_niches)
