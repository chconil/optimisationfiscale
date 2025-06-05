"""
Définition des différentes formes juridiques et leurs calculs fiscaux
Point d'entrée principal pour les optimisations fiscales
"""

# Imports des classes depuis les fichiers séparés
from fiscal_base import OptimisationFiscale
from fiscal_microentreprise import Microentreprise
from fiscal_sas import SAS
from fiscal_sarl import SARL
from fiscal_sarl_holding import SARLHolding


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