"""
Classe de base pour les optimisations fiscales
"""

import numpy as np
from abc import ABC, abstractmethod
from parametres_fiscaux import *


class OptimisationFiscale(ABC):
    """Classe de base pour tous les régimes fiscaux"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1,
                 per_max=None, madelin_max=None, girardin_max=None, plafond_per_disponible=None):
        self.resultat_initial = resultat_avant_remuneration
        self.charges = charges_existantes
        self.resultat_avant_remuneration = resultat_avant_remuneration - charges_existantes
        self.parts_fiscales = parts_fiscales

        # Paramètres d'optimisation
        # Le plafond PER disponible peut être personnalisé (10% revenus N-1 + reports)
        self.plafond_per_disponible = plafond_per_disponible if plafond_per_disponible is not None else PLAFOND_PER
        self.per_max = per_max if per_max is not None else PLAFOND_PER
        self.madelin_max = madelin_max if madelin_max is not None else 0
        self.girardin_max = girardin_max if girardin_max is not None else 50000
    
    def calculer_ir(self, revenu_net_imposable):
        """Calcule l'IR selon le barème progressif - commun à tous"""
        if revenu_net_imposable <= 0:
            return 0, []
            
        revenu_par_part = revenu_net_imposable / self.parts_fiscales
        
        ir_par_part = 0
        revenu_restant = revenu_par_part
        details = []
        tranche_precedente = 0
        
        for tranche in TRANCHES_IR:
            if revenu_restant <= 0:
                break
            
            largeur_tranche = tranche['limite'] - tranche_precedente
            montant_dans_tranche = min(revenu_restant, largeur_tranche)
            
            if montant_dans_tranche > 0:
                ir_tranche = montant_dans_tranche * tranche['taux']
                ir_par_part += ir_tranche
                
                details.append({
                    'de': tranche_precedente * self.parts_fiscales,
                    'a': (tranche_precedente + montant_dans_tranche) * self.parts_fiscales,
                    'taux': tranche['taux'],
                    'base': montant_dans_tranche * self.parts_fiscales,
                    'impot': ir_tranche * self.parts_fiscales
                })
            
            revenu_restant -= montant_dans_tranche
            tranche_precedente = tranche['limite']
            
            if tranche['limite'] == float('inf'):
                break
        
        ir_total = ir_par_part * self.parts_fiscales
        return ir_total, details
    
    def calculer_is(self, benefice_imposable):
        """Calcule l'IS selon les tranches - commun aux sociétés"""
        if benefice_imposable <= 0:
            return 0, []
            
        is_total = 0
        reste = benefice_imposable
        details = []
        
        for tranche in TRANCHES_IS:
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
    
    def calculer_ir_avec_girardin(self, revenu_imposable, girardin_montant=0):
        """Calcule l'IR avec réduction Girardin - commun à toutes les formes"""
        ir_avant_girardin, ir_detail = self.calculer_ir(revenu_imposable)

        # Girardin
        reduction_girardin = min(girardin_montant * TAUX_GIRARDIN_INDUSTRIEL, ir_avant_girardin)
        ir_final = ir_avant_girardin - reduction_girardin

        return {
            'ir_avant_girardin': ir_avant_girardin,
            'reduction_girardin': reduction_girardin,
            'ir_final': ir_final,
            'ir_detail': ir_detail,
            # Alias pour compatibilité
            'ir': ir_final,
            'ir_remuneration': ir_final
        }

    def calculer_pee(self, remuneration_brute, versement_pee=0):
        """Calcule le PEE + PERCO (épargne salariale et retraite) - commun à toutes les formes"""
        import math
        # Limite le versement salarié au montant qui peut être abondé
        # Si abondement max = 7,418€ et abondement = 300% du versement
        # Alors versement max abondable = 7,418€ / 3 = 2,473€ (arrondi supérieur)
        versement_max_abonde = math.ceil(PLAFOND_ABONDEMENT_PEE / TAUX_ABONDEMENT_MAX)

        # Versement salarié limité à :
        # - 25% du salaire brut (limite légale)
        # - ET au montant qui peut être abondé (optimisation fiscale)
        versement_pee = min(versement_pee, remuneration_brute * LIMITE_VERSEMENT_PEE_SALARIE, versement_max_abonde)

        # Abondement = 300% du versement, plafonné à 16% du PASS (7,418€)
        abondement_pee = min(versement_pee * TAUX_ABONDEMENT_MAX, PLAFOND_ABONDEMENT_PEE)
        # Coût abondement pour l'entreprise (abondement + CSG/CRDS 9.7%)
        cout_abondement = abondement_pee * (1 + TAUX_CSG_CRDS_ABONDEMENT)
        # Économie IS sur l'abondement (charge déductible)
        economie_is_abondement = cout_abondement * 0.25  # Approximation avec taux moyen IS

        return {
            'versement_pee': versement_pee,
            'abondement_pee': abondement_pee,
            'cout_abondement_pee': cout_abondement,
            'economie_is_abondement': economie_is_abondement,
            'placements_pee': versement_pee + abondement_pee
        }

    @abstractmethod
    def calculer_scenario_base(self, remuneration, **kwargs):
        """Méthode abstraite - calcul de base sans PER/Girardin"""
        pass
    
    def appliquer_optimisations_personnelles(self, scenario_base, per_montant=0, girardin_montant=0):
        """Applique PER et Girardin sur un scénario de base - commun à toutes les formes"""
        scenario = scenario_base.copy()

        # Sécurisation des types
        per_montant = float(per_montant) if per_montant else 0
        girardin_montant = float(girardin_montant) if girardin_montant else 0

        # Récupère le revenu imposable de base
        revenu_imposable_base = float(scenario.get('revenu_imposable', 0))

        # 1. Application du PER
        # Le PER est plafonné au plafond disponible (10% revenus N-1 + reports)
        # et ne peut pas dépasser le revenu imposable de l'année
        per_deduction = min(per_montant, self.plafond_per_disponible, revenu_imposable_base)
        revenu_apres_per = max(0, revenu_imposable_base - per_deduction)

        scenario['per_deduction'] = per_deduction

        # 1b. Application du PEE/PERCO (versement salarié exonéré d'IR)
        # Récupère le versement PEE depuis le scénario de base
        versement_pee = float(scenario.get('versement_pee', 0))
        abondement_pee = float(scenario.get('abondement_pee', 0))

        # Le versement PEE est exonéré d'IR (déduit du revenu imposable)
        pee_deduction = min(versement_pee, revenu_apres_per)
        revenu_imposable_final = max(0, revenu_apres_per - pee_deduction)

        scenario['pee_deduction'] = pee_deduction
        scenario['revenu_imposable_final'] = revenu_imposable_final

        # 2. Calcul de l'économie PER et PEE réelle
        # Économie = différence d'IR sans PER/PEE vs avec PER/PEE
        ir_sans_per, _ = self.calculer_ir(revenu_imposable_base)
        ir_avec_per_pee, _ = self.calculer_ir(revenu_imposable_final)
        economie_per_pee = ir_sans_per - ir_avec_per_pee

        # Pour distinguer l'économie PER de l'économie PEE, on calcule l'IR intermédiaire
        ir_avec_per_seulement, _ = self.calculer_ir(revenu_apres_per)
        economie_per_reelle = ir_sans_per - ir_avec_per_seulement
        economie_pee_reelle = ir_avec_per_seulement - ir_avec_per_pee

        # 3. Recalcul de l'IR avec Girardin
        ir_resultats = self.calculer_ir_avec_girardin(revenu_imposable_final, girardin_montant)
        scenario.update(ir_resultats)

        # 4. Mise à jour du net final avec les optimisations personnelles
        remuneration_nette_avant_ir = float(scenario.get('remuneration_nette_avant_ir', 0))
        remuneration_nette_apres_ir = remuneration_nette_avant_ir - ir_resultats['ir_final']
        scenario['remuneration_nette_apres_ir'] = remuneration_nette_apres_ir

        # 5. Calcul du net disponible immédiat (cash après versements Girardin, PER et PEE)
        # Le net disponible = rémunération nette (après IR avec PER/PEE et Girardin) + dividendes - versements
        dividendes_nets = float(scenario.get('dividendes_nets', 0))
        net_disponible_immediat = remuneration_nette_apres_ir + dividendes_nets - girardin_montant - per_deduction - pee_deduction
        scenario['net_disponible_immediat'] = net_disponible_immediat

        # 6. Calcul des placements (PER + Madelin Retraite + PEE + Abondement)
        # Le Madelin Retraite est stocké dans madelin_charge (charge déductible de l'entreprise)
        # Le PEE = versement salarié + abondement employeur
        madelin_charge = float(scenario.get('madelin_charge', 0))
        placements_pee = pee_deduction + abondement_pee
        placements_total = per_deduction + madelin_charge + placements_pee
        scenario['placements_total'] = placements_total
        scenario['placements_pee'] = placements_pee

        # 7. Patrimoine total = Net disponible + Placements
        # Le Girardin a déjà été déduit du net disponible (c'est une vraie dépense)
        # Le PER, Madelin Retraite et PEE (+ abondement) sont des placements qui ont de la valeur
        patrimoine_total = net_disponible_immediat + placements_total
        scenario['patrimoine_total'] = patrimoine_total

        # Pour compatibilité : total_net pointe maintenant vers patrimoine_total
        scenario['total_net'] = patrimoine_total

        # 8. Mise à jour des optimisations
        if 'optimisations' not in scenario:
            scenario['optimisations'] = {}

        scenario['optimisations'].update({
            'per': per_montant,
            'girardin': girardin_montant,
            'economies_per': economie_per_reelle,  # Calcul réel au lieu de l'approximation
            'economies_girardin': ir_resultats['reduction_girardin'],
            'economies_pee': economie_pee_reelle,  # Économie IR sur versement PEE
        })

        # Recalcul des économies totales
        # Inclut les économies IS (Madelin, Abondement PEE) + économies IR (PER, PEE, Girardin)
        # Pour le Girardin : économie nette = réduction IR - investissement (car pas de placement)
        economies_girardin_nette = scenario['optimisations']['economies_girardin'] - girardin_montant
        scenario['optimisations']['economies_girardin_nette'] = economies_girardin_nette

        economies_base = float(scenario['optimisations'].get('economies_totales', 0))
        economies_totales = (economies_base +
                           scenario['optimisations']['economies_per'] +
                           economies_girardin_nette +
                           scenario['optimisations']['economies_pee'])
        scenario['optimisations']['economies_totales'] = economies_totales

        return scenario
    
    def calculer_scenario(self, remuneration, per_montant=0, girardin_montant=0, **kwargs):
        """Méthode finale qui combine scénario de base + optimisations personnelles"""
        # Extraction des optimisations personnelles des kwargs
        per_montant = kwargs.pop('per_montant', per_montant)
        girardin_montant = kwargs.pop('girardin_montant', girardin_montant)
        
        # 1. Calcul du scénario de base (spécifique à chaque forme juridique)
        scenario_base = self.calculer_scenario_base(remuneration, **kwargs)
        
        # 2. Application des optimisations personnelles (communes à toutes les formes)
        scenario_final = self.appliquer_optimisations_personnelles(
            scenario_base, per_montant, girardin_montant
        )
        
        return scenario_final
    
    def get_range_remuneration(self, pas=5000):
        """Retourne la plage de rémunération à tester selon la forme juridique"""
        # Par défaut, teste de 0 au résultat avant rémunération
        return range(0, self.resultat_avant_remuneration + 1, pas)
    
    def is_scenario_valid(self, scenario):
        """Vérifie si un scénario est valide (peut être surchargé)"""
        return scenario.get('total_net', 0) > 0
    
    def get_metric_for_optimization(self, scenario):
        """Retourne la métrique à optimiser (peut être surchargé)"""
        return scenario.get('total_net', 0)
    
    def optimiser(self, pas=5000, per_max=0, madelin_max=0, girardin_max=0, versement_pee=0, acre=False, **kwargs):
        """Méthode commune d'optimisation pour toutes les formes juridiques"""
        meilleur_scenario = None
        tous_scenarios = []

        # Obtient la plage de rémunération à tester
        range_remuneration = self.get_range_remuneration(pas)

        for remuneration in range_remuneration:
            # Prépare les arguments pour calculer_scenario avec les montants exacts de l'interface
            scenario_kwargs = {
                'per_montant': per_max,
                'madelin_montant': madelin_max,
                'girardin_montant': girardin_max,
                'versement_pee': versement_pee,
                'acre': acre
            }
            
            # Ajoute les autres kwargs spécifiques
            scenario_kwargs.update(kwargs)
            
            scenario = self.calculer_scenario(remuneration, **scenario_kwargs)
            
            # Vérifie si le scénario est valide
            if self.is_scenario_valid(scenario):
                tous_scenarios.append(scenario)
        
        # Trouve le meilleur scénario
        if tous_scenarios:
            meilleur_scenario = max(tous_scenarios, key=self.get_metric_for_optimization)
        
        return meilleur_scenario, tous_scenarios
    
    @abstractmethod
    def get_nom_forme_juridique(self):
        """Retourne le nom de la forme juridique"""
        pass
    
    @abstractmethod
    def get_optimisations_disponibles(self):
        """Retourne la liste des optimisations disponibles pour cette forme"""
        pass
    
