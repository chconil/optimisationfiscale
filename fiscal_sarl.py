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
    
    def calculer_scenario_base(self, remuneration_gerance, madelin_montant=0, **kwargs):
        """Calcule un scénario SARL"""
        resultats = {'forme_juridique': 'SARL'}
        
        # 1. Cotisations TNS
        cotisations_tns, detail_cotisations = self.calculer_cotisations_tns(remuneration_gerance)
        resultats['remuneration_brute'] = remuneration_gerance
        resultats['cotisations_tns'] = cotisations_tns
        resultats['cotisations_detail'] = detail_cotisations
        resultats['remuneration_nette_avant_ir'] = remuneration_gerance
        
        # 2. Revenu imposable (avant PER)
        abattement = min(remuneration_gerance * ABATTEMENT_FRAIS_PRO, PLAFOND_ABATTEMENT_FRAIS_PRO)
        revenu_imposable = remuneration_gerance - abattement
        resultats['abattement_frais_pro'] = abattement
        resultats['revenu_imposable'] = revenu_imposable  # Pour PER dans la base
        
        # 3. IR de base (sans PER/Girardin - sera recalculé dans la base)
        ir_base, ir_detail = self.calculer_ir(revenu_imposable)
        resultats['ir_base'] = ir_base
        resultats['ir_detail'] = ir_detail
        resultats['remuneration_nette_avant_ir'] = remuneration_gerance
        
        # 4. Madelin (charge déductible du résultat avant rémunération)
        madelin_charge = min(madelin_montant, PLAFOND_MADELIN_TNS)
        resultat_apres_remuneration = self.resultat_avant_remuneration - madelin_charge - remuneration_gerance - cotisations_tns
        resultats['madelin_charge'] = madelin_charge
        resultats['resultat_apres_remuneration'] = resultat_apres_remuneration
        
        # 5. IS
        is_total, is_detail = self.calculer_is(resultat_apres_remuneration)
        resultats['is_total'] = is_total
        resultats['is_sarl'] = is_total  # Alias pour compatibilité avec l'interface
        resultats['is_detail'] = is_detail
        
        # 6. Dividendes
        dividendes_bruts = resultat_apres_remuneration - is_total
        resultats['dividendes_bruts'] = dividendes_bruts
        resultats['dividendes_sarl'] = dividendes_bruts  # Alias pour compatibilité
        
        # 7. Imposition dividendes - choisir entre flat tax et barème
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
        
        # 8. Total net de base (avant PER/Girardin)
        remuneration_nette_base = remuneration_gerance - ir_base
        total_net = remuneration_nette_base + max(0, dividendes_nets)
        resultats['total_net'] = total_net
        
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
            'madelin': madelin_montant,
            'economies_totales': madelin_charge * TAUX_ECONOMIE_IS_MADELIN  # PER/Girardin ajoutés dans la base
        }
        
        # Calcul du taux de prélèvement global
        total_prelevements = cotisations_tns + ir_base + is_total + (flat_tax if resultats['option_fiscale'] == 'flat_tax' else prelevements_sociaux + ir_dividendes)
        if self.resultat_initial > 0:
            taux_prelevement_global = (total_prelevements / self.resultat_initial) * 100
        else:
            taux_prelevement_global = 0
        resultats['taux_prelevement_global'] = taux_prelevement_global
        
        return resultats
    
