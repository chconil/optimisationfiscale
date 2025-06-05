"""
Définition des différentes formes juridiques et leurs calculs fiscaux
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


class Microentreprise(OptimisationFiscale):
    """Optimisation pour micro-entreprise"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=0, parts_fiscales=1):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales)
        
        # Utilise les paramètres centralisés
        pass
    
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
    
    def optimiser(self, type_activite='BIC - Prestations de services', pas=5000, per_max=None, madelin_max=None, acre=False, **kwargs):
        """Optimise le CA pour la micro-entreprise"""
        if per_max is None:
            per_max = PLAFOND_PER
        if madelin_max is None:
            madelin_max = PLAFOND_MADELIN_TNS
        
        # Pour la micro : on optimise les dispositifs sur le CA donné, pas le CA lui-même
        ca = self.resultat_initial  # Le CA est déjà fixé
        
        meilleur_scenario = None
        tous_scenarios = []
        
        # Test différentes combinaisons d'optimisations
        optimisations_a_tester = [
            {'per': 0, 'madelin': 0, 'acre': False},
            {'per': per_max, 'madelin': 0, 'acre': False},
            {'per': 0, 'madelin': madelin_max, 'acre': False},
            {'per': per_max, 'madelin': madelin_max, 'acre': False}
        ]
        
        # Si ACRE est disponible, tester aussi avec ACRE
        if acre:
            optimisations_avec_acre = [
                {'per': 0, 'madelin': 0, 'acre': True},
                {'per': per_max, 'madelin': 0, 'acre': True},
                {'per': 0, 'madelin': madelin_max, 'acre': True},
                {'per': per_max, 'madelin': madelin_max, 'acre': True}
            ]
            optimisations_a_tester.extend(optimisations_avec_acre)
        
        for optimisations in optimisations_a_tester:
            scenario = self.calculer_scenario(
                ca, 
                type_activite, 
                per_montant=optimisations['per'],
                madelin_montant=optimisations['madelin'],
                acre=optimisations['acre']
            )
            
            if 'erreur' not in scenario:
                tous_scenarios.append(scenario)
                
                if meilleur_scenario is None or scenario['net_final'] > meilleur_scenario['net_final']:
                    meilleur_scenario = scenario
        
        return meilleur_scenario, tous_scenarios


class SAS(OptimisationFiscale):
    """Optimisation pour SAS (dirigeant assimilé salarié)"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales)
        
        # Utilise les paramètres centralisés
        pass
    
    def get_nom_forme_juridique(self):
        return "SAS"
    
    def get_optimisations_disponibles(self):
        return get_optimisations_disponibles('SAS')
    
    def calculer_scenario(self, salaire_brut, per_montant=0, girardin_montant=0, **kwargs):
        """Calcule un scénario SAS"""
        resultats = {'forme_juridique': 'SAS'}
        
        resultats['salaire_brut'] = salaire_brut
        
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
        resultats['ir_detail'] = ir_detail
        
        # Salaire net final
        salaire_net_final = salaire_net_avant_ir - ir_final
        resultats['salaire_net_final'] = salaire_net_final
        
        # Résultat après charges sociales et salaires
        resultat_apres_salaire = self.resultat_avant_remuneration - cout_total_salaire
        resultats['resultat_apres_salaire'] = resultat_apres_salaire
        
        # IS
        is_total, is_detail = self.calculer_is(resultat_apres_salaire)
        resultats['is_total'] = is_total
        resultats['is_detail'] = is_detail
        
        # Dividendes
        dividendes_bruts = resultat_apres_salaire - is_total
        resultats['dividendes_bruts'] = dividendes_bruts
        
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
        
        resultats['optimisations'] = {
            'per': per_montant,
            'madelin': 0,
            'girardin': girardin_montant,
            'economies_totales': per_deduction * TAUX_ECONOMIE_PER + reduction_girardin
        }
        
        return resultats
    
    def optimiser(self, pas=5000, per_max=None, girardin_max=None, **kwargs):
        """Optimise la répartition salaire/dividendes en SAS"""
        if per_max is None:
            per_max = PLAFOND_PER
        if girardin_max is None:
            girardin_max = 50000
        
        meilleur_scenario = None
        tous_scenarios = []
        
        # Test différentes optimisations
        optimisations_a_tester = [
            {'per': 0, 'girardin': 0},
            {'per': per_max, 'girardin': 0},
            {'per': 0, 'girardin': girardin_max},
            {'per': per_max, 'girardin': girardin_max}
        ]
        
        for optimisations in optimisations_a_tester:
            scenarios_optim = []
            
            # Test différents niveaux de salaire
            for salaire in range(0, self.resultat_avant_remuneration, pas):
                scenario = self.calculer_scenario(
                    salaire,
                    per_montant=optimisations['per'],
                    girardin_montant=optimisations['girardin']
                )
                
                if scenario.get('total_net', 0) > 0:
                    scenarios_optim.append(scenario)
            
            if scenarios_optim:
                meilleur_optim = max(scenarios_optim, key=lambda x: x['total_net'])
                tous_scenarios.extend(scenarios_optim)
                
                if meilleur_scenario is None or meilleur_optim['total_net'] > meilleur_scenario['total_net']:
                    meilleur_scenario = meilleur_optim
        
        return meilleur_scenario, tous_scenarios


class SARL(OptimisationFiscale):
    """Optimisation pour SARL seule (sans holding)"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales)
        
        # Utilise les paramètres centralisés
        pass
    
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
        resultats['ir_detail'] = ir_detail
        resultats['remuneration_nette_apres_ir'] = remuneration_gerance - ir_final
        
        # 5. Madelin (charge déductible)
        madelin_charge = min(madelin_montant, PLAFOND_MADELIN_TNS)
        resultat_apres_remuneration = self.resultat_avant_remuneration - remuneration_gerance - cotisations_tns - madelin_charge
        resultats['madelin_charge'] = madelin_charge
        resultats['resultat_apres_remuneration'] = resultat_apres_remuneration
        
        # 6. IS
        is_total, is_detail = self.calculer_is(resultat_apres_remuneration)
        resultats['is_total'] = is_total
        resultats['is_detail'] = is_detail
        
        # 7. Dividendes
        dividendes_bruts = resultat_apres_remuneration - is_total
        resultats['dividendes_bruts'] = dividendes_bruts
        
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
        
        resultats['optimisations'] = {
            'per': per_montant,
            'madelin': madelin_montant,
            'girardin': girardin_montant,
            'economies_totales': per_deduction * TAUX_ECONOMIE_PER + madelin_charge * TAUX_ECONOMIE_IS_MADELIN + reduction_girardin
        }
        
        return resultats
    
    def optimiser(self, pas=5000, per_max=None, madelin_max=None, girardin_max=None, **kwargs):
        """Optimise la SARL"""
        if per_max is None:
            per_max = PLAFOND_PER
        if madelin_max is None:
            madelin_max = PLAFOND_MADELIN_TNS
        if girardin_max is None:
            girardin_max = 50000
        
        meilleur_scenario = None
        tous_scenarios = []
        
        # Test différentes optimisations
        optimisations_a_tester = [
            {'per': 0, 'madelin': 0, 'girardin': 0},
            {'per': per_max, 'madelin': 0, 'girardin': 0},
            {'per': 0, 'madelin': madelin_max, 'girardin': 0},
            {'per': 0, 'madelin': 0, 'girardin': girardin_max},
            {'per': per_max, 'madelin': madelin_max, 'girardin': 0},
            {'per': per_max, 'madelin': 0, 'girardin': girardin_max},
            {'per': 0, 'madelin': madelin_max, 'girardin': girardin_max},
            {'per': per_max, 'madelin': madelin_max, 'girardin': girardin_max}
        ]
        
        for optimisations in optimisations_a_tester:
            scenarios_optim = []
            
            for remuneration in range(0, self.resultat_avant_remuneration, pas):
                scenario = self.calculer_scenario(
                    remuneration,
                    per_montant=optimisations['per'],
                    madelin_montant=optimisations['madelin'],
                    girardin_montant=optimisations['girardin']
                )
                
                if scenario.get('total_net', 0) > 0:
                    scenarios_optim.append(scenario)
            
            if scenarios_optim:
                meilleur_optim = max(scenarios_optim, key=lambda x: x['total_net'])
                tous_scenarios.extend(scenarios_optim)
                
                if meilleur_scenario is None or meilleur_optim['total_net'] > meilleur_scenario['total_net']:
                    meilleur_scenario = meilleur_optim
        
        return meilleur_scenario, tous_scenarios


class SARLHolding(OptimisationFiscale):
    """Optimisation pour SARL + Holding (code existant adapté)"""
    
    def __init__(self, resultat_avant_remuneration=300000, charges_existantes=50000, parts_fiscales=1):
        super().__init__(resultat_avant_remuneration, charges_existantes, parts_fiscales)
        
        # Utilise les paramètres centralisés
        pass
        
        # Utilise les paramètres centralisés
        pass
    
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
    
    def optimiser(self, pas=5000, per_max=None, madelin_max=None, girardin_max=None, **kwargs):
        """Optimise SARL + Holding (reprise méthode existante)"""
        if per_max is None:
            per_max = PLAFOND_PER
        if madelin_max is None:
            madelin_max = PLAFOND_MADELIN_TNS
        if girardin_max is None:
            girardin_max = 50000
        
        meilleur_scenario = None
        meilleur_efficacite = 0
        tous_scenarios = []
        
        # Test différentes combinaisons d'optimisations
        optimisations_a_tester = [
            {'per': 0, 'madelin': 0, 'girardin': 0},  # Sans optimisation
            {'per': per_max, 'madelin': 0, 'girardin': 0},  # PER seul
            {'per': 0, 'madelin': madelin_max, 'girardin': 0},  # Madelin seul
            {'per': 0, 'madelin': 0, 'girardin': girardin_max},  # Girardin seul
            {'per': per_max, 'madelin': madelin_max, 'girardin': 0},  # PER + Madelin
            {'per': per_max, 'madelin': 0, 'girardin': girardin_max},  # PER + Girardin
            {'per': 0, 'madelin': madelin_max, 'girardin': girardin_max},  # Madelin + Girardin
            {'per': per_max, 'madelin': madelin_max, 'girardin': girardin_max},  # Tout
        ]
        
        for optimisations in optimisations_a_tester:
            scenarios_optim = []
            
            for remuneration in range(0, self.resultat_avant_remuneration + 1, pas):
                scenario = self.calculer_scenario(
                    remuneration, 
                    per_montant=optimisations['per'],
                    madelin_montant=optimisations['madelin'],
                    girardin_montant=optimisations['girardin']
                )
                
                # Ne pas inclure les scénarios non plausibles (dividendes négatifs)
                if scenario['flat_tax'] >= 0:
                    scenario['nom_strategie'] = f"PER:{optimisations['per']:,}€ | Madelin:{optimisations['madelin']:,}€ | Girardin:{optimisations['girardin']:,}€"
                    scenarios_optim.append(scenario)
            
            # Mise à jour du meilleur scénario global basé sur le total net
            for scenario in scenarios_optim:
                if scenario['total_net'] > meilleur_efficacite:
                    meilleur_efficacite = scenario['total_net']
                    meilleur_scenario = scenario
            
            tous_scenarios.append({
                'optimisations': optimisations,
                'scenarios': scenarios_optim,
                'meilleur': max(scenarios_optim, key=lambda x: x['total_net']) if scenarios_optim else None
            })
        
        return meilleur_scenario, tous_scenarios


# Factory pour créer les optimiseurs
def creer_optimiseur(forme_juridique, **kwargs):
    """Factory pour créer le bon optimiseur selon la forme juridique"""
    optimiseurs = {
        'Micro-entreprise': Microentreprise,
        'SAS': SAS,
        'SARL': SARL,
        'SARL + Holding': SARLHolding
    }
    
    if forme_juridique not in optimiseurs:
        raise ValueError(f"Forme juridique '{forme_juridique}' non supportée. Choix disponibles: {list(optimiseurs.keys())}")
    
    return optimiseurs[forme_juridique](**kwargs)


# Liste des formes juridiques disponibles
FORMES_JURIDIQUES = ['Micro-entreprise', 'SAS', 'SARL', 'SARL + Holding']