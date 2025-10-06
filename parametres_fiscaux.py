"""
Paramètres fiscaux centralisés pour toutes les formes juridiques
Année fiscale 2024
"""

# Barème IR 2024 (par part fiscale)
TRANCHES_IR = [
    {'limite': 11294, 'taux': 0},
    {'limite': 28797, 'taux': 0.11},
    {'limite': 82341, 'taux': 0.30},
    {'limite': 177106, 'taux': 0.41},
    {'limite': float('inf'), 'taux': 0.45}
]

# Tranches IS 2024
TRANCHES_IS = [
    {'limite': 42500, 'taux': 0.15},
    {'limite': float('inf'), 'taux': 0.25}
]

# Cotisations TNS (SARL gérant majoritaire)
TAUX_COTISATIONS_TNS = {
    'maladie': 0.065,
    'allocations_familiales': 0.031,
    'retraite_base': 0.1775,
    'retraite_complementaire': 0.07,
    'invalidite_deces': 0.013,
    'csg_crds': 0.097,
    'formation': 0.0025
}

# Cotisations assimilé salarié (SAS)
TAUX_COTISATIONS_SALARIE = 0.22  # Approximation cotisations salariales
TAUX_COTISATIONS_PATRONALES = 0.42  # Approximation cotisations patronales

# Micro-entreprise BIC - Activités de vente
MICRO_BIC_VENTE = {
    'seuil': 188700,
    'abattement': 0.71,  # 71% d'abattement
    'cotisations': 0.126  # 12.6% de cotisations sociales
}

# Micro-entreprise BIC - Prestations de services
MICRO_BIC_SERVICES = {
    'seuil': 77700,
    'abattement': 0.50,  # 50% d'abattement
    'cotisations': 0.212  # 21.2% de cotisations sociales
}

# Pour compatibilité - par défaut on prend les services
MICRO_BIC = MICRO_BIC_SERVICES

# Micro-entreprise BNC (Bénéfices Non Commerciaux)
# Professions libérales
MICRO_BNC = {
    'seuil': 77700,
    'abattement': 0.34,  # 34% d'abattement
    'cotisations': 0.246  # 24.6% de cotisations sociales
}

# Dividendes et flat tax
TAUX_FLAT_TAX = 0.30
TAUX_PRELEVEMENTS_SOCIAUX_DIVIDENDES = 0.172
TAUX_EXONERATION_MERE_FILLE = 0.95  # Régime mère-fille

# Abattements et plafonds
ABATTEMENT_FRAIS_PRO = 0.10  # 10%
PLAFOND_ABATTEMENT_FRAIS_PRO = 13522  # 2024

# Dispositifs d'optimisation fiscale
PLAFOND_PER = 32419  # Plan Épargne Retraite (8 x PASS 2024)
PLAFOND_MADELIN_TNS = 84000  # Madelin Retraite TNS 2024
TAUX_GIRARDIN_INDUSTRIEL = 1.10  # 110% de réduction d'impôt

# Plafonds retraite et allocations familiales
PLAFOND_RETRAITE_BASE = 46368  # 1 PASS 2024
SEUIL_ALLOCATIONS_FAMILIALES_REDUIT = 162288  # 3.5 PASS 2024

# Taux d'économie approximatifs pour les calculs
TAUX_ECONOMIE_PER = 0.30  # Approximation économie fiscale PER
TAUX_ECONOMIE_IS_MADELIN = 0.25  # Économie IS pour charge Madelin Retraite

# ACRE (Aide à la Création ou à la Reprise d'une Entreprise)
TAUX_REDUCTION_ACRE = 0.50  # 50% de réduction des cotisations sociales la 1ère année

# Configuration par forme juridique
FORMES_JURIDIQUES_CONFIG = {
    'Micro-entreprise': {
        'optimisations_disponibles': ['per', 'girardin', 'acre'],
        'calcul_cotisations': 'micro',
        'type_revenus': 'ca'
    },
    'SAS': {
        'optimisations_disponibles': ['per', 'girardin'],
        'calcul_cotisations': 'assimile_salarie',
        'type_revenus': 'salaire_dividendes'
    },
    'SARL': {
        'optimisations_disponibles': ['per', 'madelin', 'girardin'],
        'calcul_cotisations': 'tns',
        'type_revenus': 'remuneration_dividendes'
    },
    'SARL + Holding': {
        'optimisations_disponibles': ['per', 'madelin', 'girardin'],
        'calcul_cotisations': 'tns',
        'type_revenus': 'remuneration_dividendes_holding'
    }
}

def get_config_forme_juridique(forme_juridique):
    """Retourne la configuration pour une forme juridique donnée"""
    return FORMES_JURIDIQUES_CONFIG.get(forme_juridique, {})

def get_optimisations_disponibles(forme_juridique):
    """Retourne les optimisations disponibles pour une forme juridique"""
    config = get_config_forme_juridique(forme_juridique)
    return config.get('optimisations_disponibles', [])

# NOTE: Les fonctions calculer_ir() et calculer_is() sont définies dans fiscal_base.py
# pour éviter la duplication de code. Utilisez les méthodes de la classe OptimisationFiscale.

def calculer_cotisations_tns(remuneration_brute):
    """Calcule les cotisations TNS"""
    assiette = remuneration_brute * 0.9  # Abattement 10% frais pro

    cotisations = {}
    total = 0

    for nom, taux in TAUX_COTISATIONS_TNS.items():
        if nom == 'retraite_base':
            base = min(assiette, PLAFOND_RETRAITE_BASE)
            cotisations[nom] = base * taux
        elif nom == 'allocations_familiales':
            # Barème progressif 2024 :
            # 0% jusqu'à 46,368€ (1 PASS)
            # Progressif de 46,368€ à 64,915€ (1.4 PASS)
            # 3.1% au-delà de 64,915€
            PASS_1 = 46368  # 1 PASS
            PASS_1_4 = 64915  # 1.4 PASS

            if assiette <= PASS_1:
                # Exonération totale en dessous de 1 PASS
                cotisations[nom] = 0
            elif assiette <= PASS_1_4:
                # Taux progressif entre 1 et 1.4 PASS
                taux_progressif = 0.031 * (assiette - PASS_1) / (PASS_1_4 - PASS_1)
                cotisations[nom] = assiette * taux_progressif
            else:
                # Taux plein au-delà de 1.4 PASS
                cotisations[nom] = assiette * 0.031
        else:
            cotisations[nom] = assiette * taux

        total += cotisations[nom]

    return total, cotisations