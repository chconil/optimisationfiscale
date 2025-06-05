"""
Optimisation fiscale pour la micro-entreprise
"""

from fiscal_base import OptimisationFiscale
from parametres_fiscaux import *


class Microentreprise(OptimisationFiscale):
    """Optimisation pour micro-entreprise"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=0, parts_fiscales=1,
                 per_max=None, madelin_max=None, girardin_max=None):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales,
                         per_max, madelin_max, girardin_max)
    
    def get_nom_forme_juridique(self):
        return "Micro-entreprise"
    
    def get_optimisations_disponibles(self):
        return get_optimisations_disponibles('Micro-entreprise')
    
    def calculer_scenario(self, chiffre_affaires, type_activite='BIC - Prestations de services', per_montant=0, madelin_montant=0, acre=False, **kwargs):
        """Calcule un scénario micro-entreprise"""
        resultats = {'forme_juridique': 'Micro-entreprise'}
        
        # Configuration selon le type d'activité (sans vérification de seuil)
        if type_activite == 'BIC - Vente de marchandises':
            from parametres_fiscaux import MICRO_BIC_VENTE
            config = MICRO_BIC_VENTE
            type_simple = 'BIC'
        elif type_activite in ['BIC - Prestations de services', 'BIC']:
            from parametres_fiscaux import MICRO_BIC_SERVICES
            config = MICRO_BIC_SERVICES
            type_simple = 'BIC'
        else:  # BNC
            config = MICRO_BNC
            type_simple = 'BNC'
        
        seuil = config['seuil']
        
        # Note : On peut dépasser pendant 2 ans, donc pas de blocage
        if chiffre_affaires > seuil:
            resultats['avertissement'] = f"CA {chiffre_affaires:,.0f}€ dépasse le seuil micro {seuil:,.0f}€ (toléré 2 ans)"
        
        resultats['chiffre_affaires'] = chiffre_affaires
        resultats['type_activite'] = type_activite
        resultats['type_simple'] = type_simple
        
        # Cotisations sociales (avec réduction ACRE si applicable)
        taux_cotisations = config['cotisations']
        if acre:
            taux_cotisations = taux_cotisations * (1 - TAUX_REDUCTION_ACRE)  # Réduction 50%
            resultats['acre_reduction'] = chiffre_affaires * config['cotisations'] * TAUX_REDUCTION_ACRE
        else:
            resultats['acre_reduction'] = 0
            
        cotisations_sociales = chiffre_affaires * taux_cotisations
        resultats['cotisations_sociales'] = cotisations_sociales
        resultats['taux_cotisations_effectif'] = taux_cotisations
        
        # Base imposable après abattement
        base_imposable = chiffre_affaires * (1 - config['abattement'])
        resultats['abattement_micro'] = chiffre_affaires * config['abattement']
        resultats['base_imposable'] = base_imposable
        
        # PER
        per_deduction = min(per_montant, min(base_imposable * 0.10, PLAFOND_PER))
        base_imposable_finale = base_imposable - per_deduction
        resultats['per_deduction'] = per_deduction
        resultats['base_imposable_finale'] = base_imposable_finale
        
        # IR
        ir, ir_detail = self.calculer_ir(base_imposable_finale)
        resultats['ir'] = ir
        resultats['ir_detail'] = ir_detail
        
        # Madelin en micro-entreprise (charge déductible personnelle)
        madelin_charge = min(madelin_montant, PLAFOND_MADELIN_TNS)
        resultats['madelin_charge'] = madelin_charge
        
        # Net final avant déduction des charges réelles
        net_avant_charges = chiffre_affaires - cotisations_sociales - ir - per_montant - madelin_charge
        resultats['net_avant_charges'] = net_avant_charges
        
        # Net final après déduction des charges réelles
        net_final = net_avant_charges - self.charges
        resultats['net_final'] = net_final
        resultats['charges_reelles'] = self.charges
        
        # Taux de prélèvement global (incluant les charges réelles)
        total_prelevements = cotisations_sociales + ir + per_montant + madelin_charge + self.charges
        resultats['taux_prelevement_global'] = (total_prelevements / chiffre_affaires * 100) if chiffre_affaires > 0 else 0
        
        # Ajout des champs pour compatibilité avec l'interface
        resultats['remuneration_nette_apres_ir'] = net_final + per_montant  # Équivalent salaire net
        resultats['dividendes_nets'] = 0  # Pas de dividendes en micro
        resultats['cotisations_tns'] = 0  # Pas de cotisations TNS
        resultats['cotisations_detail'] = {}  # Pas de détail TNS
        resultats['ir_remuneration'] = ir
        resultats['is_sarl'] = 0  # Pas d'IS
        resultats['is_holding'] = 0  # Pas de holding
        resultats['flat_tax'] = 0  # Pas de flat tax
        resultats['total_net'] = net_final
        
        # Champs spécifiques micro pour le résumé
        resultats['remuneration_brute'] = chiffre_affaires
        resultats['remuneration_nette_avant_ir'] = net_avant_charges + per_montant
        resultats['abattement_frais_pro'] = 0  # Pas d'abattement frais pro en micro
        resultats['revenu_imposable'] = base_imposable
        resultats['revenu_imposable_final'] = base_imposable_finale
        resultats['resultat_apres_remuneration'] = 0  # Pas applicable
        resultats['is_detail'] = []
        resultats['dividendes_sarl'] = 0
        resultats['quote_part_imposable'] = 0
        resultats['dividendes_holding'] = 0
        
        resultats['optimisations'] = {
            'per': per_montant,
            'madelin': madelin_montant,
            'girardin': 0,
            'acre': acre,
            'economies_totales': per_deduction * TAUX_ECONOMIE_PER + madelin_charge * TAUX_ECONOMIE_PER + resultats['acre_reduction']
        }
        
        return resultats
    
    def get_range_remuneration(self, pas=5000):
        """Pour micro-entreprise, on optimise sur le CA fixé (pas de plage)"""
        return [self.resultat_initial]  # CA fixé
    
    def get_metric_for_optimization(self, scenario):
        """Pour micro-entreprise, optimise sur net_final"""
        return scenario.get('net_final', 0)
    
    def is_scenario_valid(self, scenario):
        """Pour micro-entreprise, vérifie qu'il n'y a pas d'erreur"""
        return 'erreur' not in scenario