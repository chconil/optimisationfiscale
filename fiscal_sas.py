"""
Optimisation fiscale pour la SAS
"""

from fiscal_base import OptimisationFiscale
from parametres_fiscaux import *


class SAS(OptimisationFiscale):
    """Optimisation pour SAS (dirigeant assimilé salarié)"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1,
                 per_max=None, madelin_max=None, girardin_max=None):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales, 
                         per_max, madelin_max, girardin_max)
    
    def get_nom_forme_juridique(self):
        return "SAS"
    
    def get_optimisations_disponibles(self):
        return get_optimisations_disponibles('SAS')
    
    def calculer_scenario(self, salaire_brut, per_montant=0, girardin_montant=0, **kwargs):
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
        salaire_net_avant_ir = salaire_brut - cotisations_salariales
        resultats['salaire_net_avant_ir'] = salaire_net_avant_ir
        
        # Revenu imposable avec abattement 10%
        abattement = min(salaire_net_avant_ir * ABATTEMENT_FRAIS_PRO, PLAFOND_ABATTEMENT_FRAIS_PRO)
        revenu_imposable = salaire_net_avant_ir - abattement
        resultats['abattement_frais_pro'] = abattement
        resultats['revenu_imposable'] = revenu_imposable
        
        # PER
        per_deduction = min(per_montant, min(revenu_imposable * 0.10, PLAFOND_PER))
        revenu_imposable_final = revenu_imposable - per_deduction
        resultats['per_deduction'] = per_deduction
        resultats['revenu_imposable_final'] = revenu_imposable_final
        
        # IR
        ir_avant_girardin, ir_detail = self.calculer_ir(revenu_imposable_final)
        
        # Girardin
        reduction_girardin = min(girardin_montant * TAUX_GIRARDIN_INDUSTRIEL, ir_avant_girardin)
        ir_final = ir_avant_girardin - reduction_girardin
        
        resultats['ir_avant_girardin'] = ir_avant_girardin
        resultats['reduction_girardin'] = reduction_girardin
        resultats['ir_final'] = ir_final
        resultats['ir_remuneration'] = ir_final  # Alias pour compatibilité avec l'interface
        resultats['ir_detail'] = ir_detail
        
        # Salaire net final
        salaire_net_final = salaire_net_avant_ir - ir_final
        resultats['salaire_net_final'] = salaire_net_final
        resultats['remuneration_nette_avant_ir'] = salaire_net_avant_ir  # Alias pour compatibilité
        resultats['remuneration_nette_apres_ir'] = salaire_net_final  # Alias pour compatibilité
        
        # Résultat après charges sociales et salaires
        resultat_apres_salaire = self.resultat_avant_remuneration - cout_total_salaire
        resultats['resultat_apres_salaire'] = resultat_apres_salaire
        
        # IS
        is_total, is_detail = self.calculer_is(resultat_apres_salaire)
        resultats['is_total'] = is_total
        resultats['is_sarl'] = is_total  # Alias pour compatibilité avec l'interface
        resultats['is_detail'] = is_detail
        
        # Dividendes
        dividendes_bruts = resultat_apres_salaire - is_total
        resultats['dividendes_bruts'] = dividendes_bruts
        resultats['dividendes_sarl'] = dividendes_bruts  # Alias pour compatibilité
        
        # Flat tax sur dividendes
        flat_tax = dividendes_bruts * TAUX_FLAT_TAX
        dividendes_nets = dividendes_bruts - flat_tax
        resultats['flat_tax'] = flat_tax
        resultats['dividendes_nets'] = dividendes_nets
        
        # Total net (en déduisant investissement Girardin)
        total_net = salaire_net_final + max(0, dividendes_nets) - girardin_montant
        resultats['total_net'] = total_net
        
        # Taux de prélèvement global
        total_prelevements = (self.resultat_avant_remuneration - total_net)
        resultats['taux_prelevement_global'] = (total_prelevements / self.resultat_avant_remuneration * 100) if self.resultat_avant_remuneration > 0 else 0
        
        # Calcul du taux de prélèvement sur les dividendes
        if resultat_apres_salaire > 0:
            taux_prelevement_dividendes = (is_total + flat_tax) / resultat_apres_salaire * 100
        else:
            taux_prelevement_dividendes = 0
        
        # Ajouter les champs manquants pour compatibilité avec l'interface SARL
        resultats['cotisations_tns'] = 0  # Pas de cotisations TNS en SAS
        resultats['cotisations_detail'] = {}  # Pas de détail TNS
        resultats['resultat_apres_remuneration'] = resultat_apres_salaire  # Alias
        resultats['madelin_charge'] = 0  # Pas de Madelin en SAS
        resultats['is_holding'] = 0  # Pas de holding
        resultats['quote_part_imposable'] = 0  # Pas de quote-part en SAS simple
        resultats['dividendes_holding'] = dividendes_nets  # Alias pour dividendes finaux
        resultats['taux_prelevement_dividendes'] = taux_prelevement_dividendes
        
        resultats['optimisations'] = {
            'per': per_montant,
            'madelin': 0,
            'girardin': girardin_montant,
            'economies_totales': per_deduction * TAUX_ECONOMIE_PER + reduction_girardin
        }
        
        return resultats
    
    def get_range_remuneration(self, pas=5000):
        """Pour SAS, limite le salaire brut maximum selon les cotisations patronales"""
        cout_par_euro_salaire = 1 + TAUX_COTISATIONS_PATRONALES
        salaire_brut_max = int(self.resultat_avant_remuneration / cout_par_euro_salaire)
        return range(0, salaire_brut_max + 1, pas)