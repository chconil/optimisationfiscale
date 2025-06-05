"""
Classe de base pour les optimisations fiscales
"""

import numpy as np
from abc import ABC, abstractmethod
from parametres_fiscaux import *


class OptimisationFiscale(ABC):
    """Classe de base pour tous les régimes fiscaux"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1, 
                 per_max=None, madelin_max=None, girardin_max=None):
        self.resultat_initial = resultat_avant_remuneration
        self.charges = charges_existantes
        self.resultat_avant_remuneration = resultat_avant_remuneration - charges_existantes 
        self.parts_fiscales = parts_fiscales
        
        # Paramètres d'optimisation
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
    
    @abstractmethod
    def calculer_scenario(self, remuneration, **kwargs):
        """Méthode abstraite - chaque forme juridique doit l'implémenter"""
        pass
    
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
    
    def optimiser(self, pas=5000, optimisations_selectionnees=None, **kwargs):
        """Méthode commune d'optimisation pour toutes les formes juridiques"""
        meilleur_scenario = None
        tous_scenarios = []
        
        # Si aucune optimisation n'est sélectionnée, utilise un scénario vide
        if optimisations_selectionnees is None:
            optimisations_selectionnees = {}
        
        # Génère le scénario d'optimisation basé sur les sélections
        optimisations = self.get_scenario_optimisations(optimisations_selectionnees)
        
        # Obtient la plage de rémunération à tester
        range_remuneration = self.get_range_remuneration(pas)
        
        for remuneration in range_remuneration:
            # Prépare les arguments pour calculer_scenario
            scenario_kwargs = {
                'per_montant': optimisations.get('per', 0),
                'madelin_montant': optimisations.get('madelin', 0),
                'girardin_montant': optimisations.get('girardin', 0)
            }
            
            # Ajoute l'ACRE si sélectionné
            if optimisations.get('acre', False):
                scenario_kwargs['acre'] = True
            
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
    
    def get_scenario_optimisations(self, optimisations_selectionnees):
        """Retourne un scénario d'optimisation basé sur les sélections de l'utilisateur"""
        scenario = {
            'per': 0,
            'madelin': 0,
            'girardin': 0,
            'acre': False
        }
        
        # Active uniquement les optimisations sélectionnées par l'utilisateur
        if optimisations_selectionnees.get('per', False):
            scenario['per'] = self.per_max
        
        if optimisations_selectionnees.get('madelin', False):
            scenario['madelin'] = self.madelin_max
            
        if optimisations_selectionnees.get('girardin', False):
            scenario['girardin'] = self.girardin_max
            
        if optimisations_selectionnees.get('acre', False):
            scenario['acre'] = True
        
        return scenario