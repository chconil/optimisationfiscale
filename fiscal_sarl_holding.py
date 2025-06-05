"""
Optimisation fiscale pour la SARL + Holding
"""

from fiscal_base import OptimisationFiscale
from parametres_fiscaux import *


class SARLHolding(OptimisationFiscale):
    """Optimisation pour SARL + Holding (code existant adapté)"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1,
                 per_max=None, madelin_max=None, girardin_max=None):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales,
                         per_max, madelin_max, girardin_max)
    
    def get_nom_forme_juridique(self):
        return "SARL + Holding"
    
    def get_optimisations_disponibles(self):
        return get_optimisations_disponibles(self.get_nom_forme_juridique())
    
    def calculer_cotisations_tns(self, remuneration_brute):
        """Calcule les cotisations TNS"""
        return calculer_cotisations_tns(remuneration_brute)
    
    def calculer_scenario_base(self, remuneration_gerance, madelin_montant=0, **kwargs):
        """Calcule un scénario SARL + Holding (reprise du code existant)"""
        resultats = {'forme_juridique': 'SARL + Holding'}
        
        # 1. Calcul des cotisations TNS
        cotisations_tns, detail_cotisations = self.calculer_cotisations_tns(remuneration_gerance)
        resultats['remuneration_brute'] = remuneration_gerance
        resultats['cotisations_tns'] = cotisations_tns
        resultats['cotisations_detail'] = detail_cotisations
        resultats['remuneration_nette_avant_ir'] = remuneration_gerance
        
        # 2. Calcul du revenu imposable (après abattement 10%, avant PER)
        abattement = min(resultats['remuneration_nette_avant_ir'] * ABATTEMENT_FRAIS_PRO, 
                         PLAFOND_ABATTEMENT_FRAIS_PRO)
        revenu_imposable = resultats['remuneration_nette_avant_ir'] - abattement
        resultats['abattement_frais_pro'] = abattement
        resultats['revenu_imposable'] = revenu_imposable  # Pour PER dans la base
        
        # 3. IR de base (sans PER/Girardin - sera recalculé dans la base)
        ir_base, ir_detail = self.calculer_ir(revenu_imposable)
        resultats['ir_base'] = ir_base
        resultats['ir_detail'] = ir_detail
        resultats['madelin_deduction'] = 0  # Madelin n'est plus une déduction personnelle
        
        # 4. Calcul du résultat après rémunération et charges Madelin
        # Madelin TNS : charge déductible de la SARL (limité au plafond)
        madelin_charge = min(madelin_montant, PLAFOND_MADELIN_TNS)
        resultat_apres_remuneration = self.resultat_avant_remuneration - remuneration_gerance - cotisations_tns - madelin_charge
        resultats['resultat_apres_remuneration'] = resultat_apres_remuneration
        resultats['madelin_charge'] = madelin_charge
        
        # Optimisations de base (PER/Girardin ajoutés dans la base)
        economie_is_madelin = madelin_charge * 0.25  # Économie d'IS à 25%
        resultats['optimisations'] = {
            'madelin': madelin_montant,
            'economie_is_madelin': economie_is_madelin,
            'economies_totales': economie_is_madelin
        }
        
        # 5. Calcul de l'IS
        is_total, detail_is = self.calculer_is(resultat_apres_remuneration)
        resultats['is_sarl'] = is_total
        resultats['is_detail'] = detail_is
        
        # 6. Dividendes distribuables
        dividendes_sarl = resultat_apres_remuneration - is_total
        resultats['dividendes_sarl'] = dividendes_sarl
        
        # 7. Remontée à la holding (régime mère-fille)
        quote_part_imposable = dividendes_sarl * (1 - TAUX_EXONERATION_MERE_FILLE)
        is_holding = quote_part_imposable * 0.25
        dividendes_holding = dividendes_sarl - is_holding
        
        resultats['quote_part_imposable'] = quote_part_imposable
        resultats['is_holding'] = is_holding
        resultats['dividendes_holding'] = dividendes_holding
        
        # 8. Distribution finale et flat tax
        flat_tax = dividendes_holding * TAUX_FLAT_TAX
        dividendes_nets = dividendes_holding - flat_tax
        
        resultats['flat_tax'] = flat_tax
        resultats['dividendes_nets'] = dividendes_nets
        
        # Calcul du taux de prélèvement sur les dividendes
        prelevements_dividendes = is_total + is_holding + flat_tax
        if resultat_apres_remuneration > 0:
            taux_prelevement_dividendes = (prelevements_dividendes / resultat_apres_remuneration) * 100
        else:
            taux_prelevement_dividendes = 0
        
        resultats['prelevements_dividendes'] = prelevements_dividendes
        resultats['taux_prelevement_dividendes'] = taux_prelevement_dividendes
        
        # 9. Total net de base (avant PER/Girardin)
        remuneration_nette_base = remuneration_gerance - ir_base
        dividendes_distribuables = max(0, dividendes_nets)
        resultats['total_net'] = remuneration_nette_base + dividendes_distribuables
        
        # 10. Calcul du taux de prélèvement global
        total_prelevements = cotisations_tns + ir_base + is_total + is_holding + flat_tax
        if self.resultat_initial > 0:
            taux_prelevement_global = (total_prelevements / self.resultat_initial) * 100
        else:
            taux_prelevement_global = 0
        resultats['taux_prelevement_global'] = taux_prelevement_global
        
        return resultats
    
    def is_scenario_valid(self, scenario):
        """Pour SARL + Holding, vérifie que les dividendes ne sont pas négatifs"""
        return scenario.get('flat_tax', -1) >= 0