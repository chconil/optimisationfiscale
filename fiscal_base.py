"""
Classe de base pour les optimisations fiscales
"""

import numpy as np
from abc import ABC, abstractmethod
from parametres_fiscaux import *


class OptimisationFiscale(ABC):
    """Classe de base pour tous les régimes fiscaux"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1):
        self.resultat_initial = resultat_avant_remuneration
        self.charges = charges_existantes
        self.resultat_avant_remuneration = resultat_avant_remuneration - charges_existantes
        self.parts_fiscales = parts_fiscales
    
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
    
    @abstractmethod
    def optimiser(self, **kwargs):
        """Méthode abstraite - chaque forme juridique doit l'implémenter"""
        pass
    
    @abstractmethod
    def get_nom_forme_juridique(self):
        """Retourne le nom de la forme juridique"""
        pass
    
    @abstractmethod
    def get_optimisations_disponibles(self):
        """Retourne la liste des optimisations disponibles pour cette forme"""
        pass