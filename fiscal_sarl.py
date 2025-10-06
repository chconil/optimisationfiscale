"""
Optimisation fiscale pour la SARL
"""

from fiscal_base import OptimisationFiscale
from parametres_fiscaux import *


class SARL(OptimisationFiscale):
    """Optimisation pour SARL seule (sans holding)"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1,
                 per_max=None, madelin_max=None, girardin_max=None, plafond_per_disponible=None):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales,
                         per_max, madelin_max, girardin_max, plafond_per_disponible)
    
    def get_nom_forme_juridique(self):
        return "SARL"
    
    def get_optimisations_disponibles(self):
        return get_optimisations_disponibles(self.get_nom_forme_juridique())
    
    def calculer_cotisations_tns(self, remuneration_brute):
        """Calcule les cotisations TNS"""
        return calculer_cotisations_tns(remuneration_brute)
    
    def calculer_scenario_base(self, remuneration_gerance, madelin_montant=0, versement_pee=0, **kwargs):
        """Calcule un scénario SARL"""
        resultats = {'forme_juridique': 'SARL'}

        # 0. PEE/PERCO : Utilise la méthode commune de la classe de base
        pee_resultats = self.calculer_pee(remuneration_gerance, versement_pee)
        resultats.update(pee_resultats)
        cout_abondement = pee_resultats['cout_abondement_pee']

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
        
        # 4. Madelin Retraite (charge déductible du résultat avant rémunération)
        madelin_charge = min(madelin_montant, PLAFOND_MADELIN_TNS)
        resultat_apres_remuneration = self.resultat_avant_remuneration - madelin_charge - remuneration_gerance - cotisations_tns - cout_abondement
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

        # 7. Imposition dividendes - TOUJOURS flat tax (30%)
        # La flat tax (30%) = 12.8% IR + 17.2% prélèvements sociaux
        flat_tax = dividendes_bruts * TAUX_FLAT_TAX
        dividendes_nets = dividendes_bruts - flat_tax

        resultats['option_fiscale'] = 'flat_tax'
        resultats['flat_tax'] = flat_tax
        resultats['dividendes_nets'] = dividendes_nets
        resultats['prelevements_sociaux'] = 0  # Inclus dans flat_tax
        resultats['ir_dividendes'] = 0  # Inclus dans flat_tax
        
        # 8. Total net de base (avant PER/Girardin)
        remuneration_nette_base = remuneration_gerance - ir_base
        total_net = remuneration_nette_base + max(0, dividendes_nets)
        resultats['total_net'] = total_net
        
        # Calcul du taux de prélèvement sur les dividendes
        if resultat_apres_remuneration > 0:
            prelevements_dividendes = is_total + flat_tax
            taux_prelevement_dividendes = (prelevements_dividendes / resultat_apres_remuneration) * 100
        else:
            taux_prelevement_dividendes = 0

        resultats['taux_prelevement_dividendes'] = taux_prelevement_dividendes

        # Économies totales = Madelin + PEE
        economie_madelin = madelin_charge * TAUX_ECONOMIE_IS_MADELIN
        economie_pee_is = resultats['economie_is_abondement']

        resultats['optimisations'] = {
            'madelin': madelin_montant,
            'pee': resultats['versement_pee'],
            'abondement_pee': resultats['abondement_pee'],
            'economie_is_abondement': economie_pee_is,
            'economies_totales': economie_madelin + economie_pee_is  # PER/Girardin/PEE ajoutés dans la base
        }

        # Calcul du taux de prélèvement global
        total_prelevements = cotisations_tns + ir_base + is_total + flat_tax
        if self.resultat_initial > 0:
            taux_prelevement_global = (total_prelevements / self.resultat_initial) * 100
        else:
            taux_prelevement_global = 0
        resultats['taux_prelevement_global'] = taux_prelevement_global
        
        return resultats
    
    def is_scenario_valid(self, scenario):
        """Pour SARL, vérifie que les dividendes et flat_tax ne sont pas négatifs"""
        return scenario.get('flat_tax', -1) >= 0 and scenario.get('dividendes_nets', -1) >= 0
    
