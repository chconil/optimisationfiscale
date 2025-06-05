"""
Optimisation fiscale pour la SARL
"""

from fiscal_base import OptimisationFiscale
from parametres_fiscaux import *


class SARL(OptimisationFiscale):
    """Optimisation pour SARL seule (sans holding)"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1,
                 per_max=None, madelin_max=None, girardin_max=None):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales,
                         per_max, madelin_max, girardin_max)
    
    def get_nom_forme_juridique(self):
        return "SARL"
    
    def get_optimisations_disponibles(self):
        return get_optimisations_disponibles(self.get_nom_forme_juridique())
    
    def calculer_cotisations_tns(self, remuneration_brute):
        """Calcule les cotisations TNS"""
        return calculer_cotisations_tns(remuneration_brute)
    
    def calculer_scenario(self, remuneration_gerance, per_montant=0, madelin_montant=0, girardin_montant=0, **kwargs):
        """Calcule un scénario SARL"""
        resultats = {'forme_juridique': 'SARL'}
        
        # 1. Cotisations TNS
        cotisations_tns, detail_cotisations = self.calculer_cotisations_tns(remuneration_gerance)
        resultats['remuneration_brute'] = remuneration_gerance
        resultats['cotisations_tns'] = cotisations_tns
        resultats['cotisations_detail'] = detail_cotisations
        resultats['remuneration_nette_avant_ir'] = remuneration_gerance
        
        # 2. Revenu imposable
        abattement = min(remuneration_gerance * ABATTEMENT_FRAIS_PRO, PLAFOND_ABATTEMENT_FRAIS_PRO)
        revenu_imposable = remuneration_gerance - abattement
        resultats['abattement_frais_pro'] = abattement
        resultats['revenu_imposable'] = revenu_imposable
        
        # 3. PER
        per_deduction = min(per_montant, min(revenu_imposable * 0.10, PLAFOND_PER))
        revenu_imposable_final = revenu_imposable - per_deduction
        resultats['per_deduction'] = per_deduction
        resultats['revenu_imposable_final'] = revenu_imposable_final
        
        # 4. IR
        ir_avant_girardin, ir_detail = self.calculer_ir(revenu_imposable_final)
        
        # Girardin
        reduction_girardin = min(girardin_montant * TAUX_GIRARDIN_INDUSTRIEL, ir_avant_girardin)
        ir_final = ir_avant_girardin - reduction_girardin
        
        resultats['ir_avant_girardin'] = ir_avant_girardin
        resultats['reduction_girardin'] = reduction_girardin
        resultats['ir_final'] = ir_final
        resultats['ir_remuneration'] = ir_final  # Alias pour compatibilité avec l'interface
        resultats['ir_detail'] = ir_detail
        resultats['remuneration_nette_apres_ir'] = remuneration_gerance - ir_final
        
        # 5. Madelin (charge déductible du résultat avant rémunération)
        madelin_charge = min(madelin_montant, PLAFOND_MADELIN_TNS)
        self.resultat_avant_remuneration = self.resultat_avant_remuneration - madelin_charge
        resultat_apres_remuneration = self.resultat_avant_remuneration - remuneration_gerance - cotisations_tns
        resultats['madelin_charge'] = madelin_charge
        resultats['resultat_apres_remuneration'] = resultat_apres_remuneration
        
        # 6. IS
        is_total, is_detail = self.calculer_is(resultat_apres_remuneration)
        resultats['is_total'] = is_total
        resultats['is_sarl'] = is_total  # Alias pour compatibilité avec l'interface
        resultats['is_detail'] = is_detail
        
        # 7. Dividendes
        dividendes_bruts = resultat_apres_remuneration - is_total
        resultats['dividendes_bruts'] = dividendes_bruts
        resultats['dividendes_sarl'] = dividendes_bruts  # Alias pour compatibilité
        
        # 8. Imposition dividendes - choisir entre flat tax et barème
        flat_tax = dividendes_bruts * TAUX_FLAT_TAX
        prelevements_sociaux = dividendes_bruts * TAUX_PRELEVEMENTS_SOCIAUX_DIVIDENDES
        ir_dividendes, _ = self.calculer_ir(dividendes_bruts * 0.6)  # Abattement 40%
        option_bareme = prelevements_sociaux + ir_dividendes
        
        if option_bareme < flat_tax and dividendes_bruts > 0:
            resultats['option_fiscale'] = 'barème'
            resultats['prelevements_sociaux'] = prelevements_sociaux
            resultats['ir_dividendes'] = ir_dividendes
            resultats['flat_tax'] = 0
            dividendes_nets = dividendes_bruts - option_bareme
        else:
            resultats['option_fiscale'] = 'flat_tax'
            resultats['prelevements_sociaux'] = 0
            resultats['ir_dividendes'] = 0
            resultats['flat_tax'] = flat_tax
            dividendes_nets = dividendes_bruts - flat_tax
        
        resultats['dividendes_nets'] = dividendes_nets
        
        # 9. Total net
        total_net = resultats['remuneration_nette_apres_ir'] + max(0, dividendes_nets) - girardin_montant
        resultats['total_net'] = total_net
        
        # 10. Taux de prélèvement global
        total_prelevements = self.resultat_avant_remuneration - total_net
        resultats['taux_prelevement_global'] = (total_prelevements / self.resultat_avant_remuneration * 100) if self.resultat_avant_remuneration > 0 else 0
        
        # Calcul du taux de prélèvement sur les dividendes
        if resultat_apres_remuneration > 0:
            if resultats['option_fiscale'] == 'flat_tax':
                prelevements_dividendes = is_total + flat_tax
            else:
                prelevements_dividendes = is_total + prelevements_sociaux + ir_dividendes
            taux_prelevement_dividendes = (prelevements_dividendes / resultat_apres_remuneration) * 100
        else:
            taux_prelevement_dividendes = 0
        
        # Ajouter les champs manquants pour compatibilité avec l'interface holding
        resultats['is_holding'] = 0  # Pas de holding en SARL simple
        resultats['quote_part_imposable'] = 0  # Pas de quote-part en SARL simple
        resultats['dividendes_holding'] = dividendes_nets  # Alias pour dividendes finaux
        resultats['taux_prelevement_dividendes'] = taux_prelevement_dividendes
        
        resultats['optimisations'] = {
            'per': per_montant,
            'madelin': madelin_montant,
            'girardin': girardin_montant,
            'economies_totales': per_deduction * TAUX_ECONOMIE_PER + madelin_charge * TAUX_ECONOMIE_IS_MADELIN + reduction_girardin
        }
        
        return resultats
    
