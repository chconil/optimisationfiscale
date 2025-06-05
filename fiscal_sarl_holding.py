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
    
    def calculer_scenario(self, remuneration_gerance, per_montant=0, madelin_montant=0, girardin_montant=0, **kwargs):
        """Calcule un scénario SARL + Holding (reprise du code existant)"""
        resultats = {'forme_juridique': 'SARL + Holding'}
        
        # 1. Calcul des cotisations TNS
        cotisations_tns, detail_cotisations = self.calculer_cotisations_tns(remuneration_gerance)
        resultats['remuneration_brute'] = remuneration_gerance
        resultats['cotisations_tns'] = cotisations_tns
        resultats['cotisations_detail'] = detail_cotisations
        resultats['remuneration_nette_avant_ir'] = remuneration_gerance
        
        # 2. Calcul du revenu imposable (après abattement 10%)
        abattement = min(resultats['remuneration_nette_avant_ir'] * ABATTEMENT_FRAIS_PRO, 
                         PLAFOND_ABATTEMENT_FRAIS_PRO)
        revenu_imposable = resultats['remuneration_nette_avant_ir'] - abattement
        resultats['abattement_frais_pro'] = abattement
        resultats['revenu_imposable'] = revenu_imposable
        
        # 3. Optimisations fiscales sur le revenu
        # PER : déduction du revenu imposable
        per_deduction = min(per_montant, min(revenu_imposable * 0.10, PLAFOND_PER))
        revenu_imposable_final = revenu_imposable - per_deduction
        
        resultats['per_deduction'] = per_deduction
        resultats['madelin_deduction'] = 0  # Madelin n'est plus une déduction personnelle
        resultats['revenu_imposable_final'] = revenu_imposable_final
        
        # 4. Calcul de l'IR sur la rémunération
        ir_remuneration, detail_ir = self.calculer_ir(revenu_imposable_final)
        
        # Girardin : réduction d'impôt (110% de l'investissement)
        reduction_girardin_brute = girardin_montant * TAUX_GIRARDIN_INDUSTRIEL
        reduction_girardin = min(reduction_girardin_brute, ir_remuneration)
        ir_final = ir_remuneration - reduction_girardin
        
        resultats['ir_avant_girardin'] = ir_remuneration
        resultats['reduction_girardin'] = reduction_girardin
        resultats['ir_remuneration'] = ir_final
        resultats['ir_detail'] = detail_ir
        resultats['remuneration_nette_apres_ir'] = resultats['remuneration_nette_avant_ir'] - ir_final
        
        # 5. Calcul du résultat après rémunération et charges Madelin
        # Madelin TNS : charge déductible de la SARL (limité au plafond)
        madelin_charge = min(madelin_montant, PLAFOND_MADELIN_TNS)
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
        quote_part_imposable = dividendes_sarl * (1 - TAUX_EXONERATION_MERE_FILLE)
        is_holding = quote_part_imposable * 0.25
        dividendes_holding = dividendes_sarl - is_holding
        
        resultats['quote_part_imposable'] = quote_part_imposable
        resultats['is_holding'] = is_holding
        resultats['dividendes_holding'] = dividendes_holding
        
        # 9. Distribution finale et flat tax
        flat_tax = dividendes_holding * TAUX_FLAT_TAX
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
    
    def is_scenario_valid(self, scenario):
        """Pour SARL + Holding, vérifie que les dividendes ne sont pas négatifs"""
        return scenario.get('flat_tax', -1) >= 0