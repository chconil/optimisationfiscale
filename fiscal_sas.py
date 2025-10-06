"""
Optimisation fiscale pour la SAS
"""

from fiscal_base import OptimisationFiscale
from parametres_fiscaux import *


class SAS(OptimisationFiscale):
    """Optimisation pour SAS (dirigeant assimilé salarié)"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1,
                 per_max=None, madelin_max=None, girardin_max=None, plafond_per_disponible=None):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales,
                         per_max, madelin_max, girardin_max, plafond_per_disponible)
    
    def get_nom_forme_juridique(self):
        return "SAS"
    
    def get_optimisations_disponibles(self):
        return get_optimisations_disponibles('SAS')
    
    def calculer_scenario_base(self, salaire_brut, **kwargs):
        """Calcule un scénario SAS"""
        resultats = {'forme_juridique': 'SAS'}
        
        resultats['salaire_brut'] = salaire_brut
        resultats['remuneration_brute'] = salaire_brut  # Alias pour compatibilité avec l'interface
        
        # Cotisations
        cotisations_salariales = salaire_brut * TAUX_COTISATIONS_SALARIE
        cotisations_patronales = salaire_brut * TAUX_COTISATIONS_PATRONALES
        cout_total_salaire = salaire_brut + cotisations_patronales
        
        resultats['cotisations_salariales'] = cotisations_salariales
        resultats['cotisations_patronales'] = cotisations_patronales
        resultats['cout_total_salaire'] = cout_total_salaire
        
        # Salaire net avant IR
        remuneration_nette_avant_ir = salaire_brut - cotisations_salariales
        resultats['remuneration_nette_avant_ir'] = remuneration_nette_avant_ir
        
        # Revenu imposable avec abattement 10% (avant PER)
        abattement = min(remuneration_nette_avant_ir * ABATTEMENT_FRAIS_PRO, PLAFOND_ABATTEMENT_FRAIS_PRO)
        revenu_imposable = remuneration_nette_avant_ir - abattement
        resultats['abattement_frais_pro'] = abattement
        resultats['revenu_imposable'] = revenu_imposable  # Pour PER dans la base
        
        # IR de base (sans PER/Girardin - sera recalculé dans la base)
        ir_base, ir_detail = self.calculer_ir(revenu_imposable)
        resultats['ir_base'] = ir_base
        resultats['ir_detail'] = ir_detail
        
        # Salaire net de base
        resultats['remuneration_nette_avant_ir'] = remuneration_nette_avant_ir
        
        # Résultat après charges sociales et salaires
        resultat_apres_remuneration = self.resultat_avant_remuneration - cout_total_salaire
        resultats['resultat_apres_remuneration'] = resultat_apres_remuneration
        
        # IS
        is_total, is_detail = self.calculer_is(resultat_apres_remuneration)
        resultats['is_total'] = is_total
        resultats['is_sarl'] = is_total  # Alias pour compatibilité avec l'interface
        resultats['is_detail'] = is_detail
        
        # Dividendes
        dividendes_bruts = resultat_apres_remuneration - is_total
        resultats['dividendes_bruts'] = dividendes_bruts
        resultats['dividendes_sarl'] = dividendes_bruts  # Alias pour compatibilité
        
        # Flat tax sur dividendes
        flat_tax = dividendes_bruts * TAUX_FLAT_TAX
        dividendes_nets = dividendes_bruts - flat_tax
        resultats['flat_tax'] = flat_tax
        resultats['dividendes_nets'] = dividendes_nets
        
        # Total net de base (avant PER/Girardin)
        salaire_net_base = remuneration_nette_avant_ir - ir_base
        total_net = salaire_net_base + max(0, dividendes_nets)
        resultats['total_net'] = total_net
        
        # Calcul du taux de prélèvement sur les dividendes
        if resultat_apres_remuneration > 0:
            taux_prelevement_dividendes = (is_total + flat_tax) / resultat_apres_remuneration * 100
        else:
            taux_prelevement_dividendes = 0
        
        # Calcul du taux de prélèvement sur les dividendes
        resultats['taux_prelevement_dividendes'] = taux_prelevement_dividendes
        
        resultats['optimisations'] = {
            'madelin': 0,
            'economies_totales': 0  # Sera calculé dans la base
        }
        
        # Calcul du taux de prélèvement global
        total_prelevements = cotisations_salariales + cotisations_patronales + ir_base + is_total + flat_tax
        if self.resultat_initial > 0:
            taux_prelevement_global = (total_prelevements / self.resultat_initial) * 100
        else:
            taux_prelevement_global = 0
        resultats['taux_prelevement_global'] = taux_prelevement_global
        
        return resultats
    
    def get_range_remuneration(self, pas=5000):
        """Pour SAS, limite le salaire brut maximum selon les cotisations patronales"""
        cout_par_euro_salaire = 1 + TAUX_COTISATIONS_PATRONALES
        salaire_brut_max = int(self.resultat_avant_remuneration / cout_par_euro_salaire)
        return range(0, salaire_brut_max + 1, pas)