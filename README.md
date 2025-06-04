# 🎯 Optimisation Fiscale SARL + Holding

Application web interactive pour optimiser la rémunération d'un gérant de SARL avec holding, incluant les dispositifs d'optimisation fiscale (PER, Madelin, Girardin).

## 🚀 Démarrage rapide

### Installation
```bash
pip install -r requirements.txt
```

### Lancement de l'interface graphique
```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse `http://localhost:8501`

## 📊 Fonctionnalités

### ✅ Interface graphique intuitive
- Configuration via sidebar avec explications
- Cases à cocher pour activer/désactiver les optimisations
- Sliders pour ajuster les montants
- Graphiques interactifs intégrés

### ✅ Optimisations fiscales supportées

#### 📈 PER (Plan d'Épargne Retraite)
- Déduction fiscale sur le revenu imposable
- Plafond légal : 32,419€ (8 × PASS 2024)
- Économie d'impôt selon tranche marginale

#### 🏥 Contrat Madelin TNS
- Déduction fiscale complémentaire pour les TNS
- Plafond légal : 84,000€ pour 2024
- Cumul possible avec le PER

#### 🏭 Girardin Industriel
- ⚠️ **ATTENTION : Il s'agit d'une DÉPENSE d'investissement**
- Réduction d'impôt après investissement réel
- Nécessite un engagement financier

### ✅ Analyses visuelles
- **Optimisation du revenu** : Courbe de gain net selon la rémunération
- **Comparaison stratégies** : Toutes les combinaisons d'optimisations
- **Répartition revenus** : Graphique en secteurs des prélèvements
- **Analyses détaillées** : Ventilation des coûts par type

## 🎯 Objectif principal

**Visualiser quel est le revenu optimal** pour un gérant de SARL avec holding, en tenant compte de :
- Cotisations TNS (gérant majoritaire)
- Impôt sur le revenu (IR) progressif
- Impôt sur les sociétés (IS) SARL et holding
- Flat tax sur les dividendes (30%)
- Optimisations fiscales disponibles

## 📁 Structure du projet

```
fiscalite/
├── app.py              # Interface Streamlit
├── calculs.py          # Moteur de calcul fiscal
├── requirements.txt    # Dépendances Python
└── README.md          # Documentation
```

## 🔧 Paramètres par défaut

- **Résultat avant rémunération** : 300,000€
- **Charges existantes** : 50,000€
- **Parts fiscales** : 1
- **Précision de calcul** : 2,500€ (pas)

## 💡 Mode d'emploi

1. **Configurez vos paramètres** dans la sidebar
2. **Activez les optimisations** souhaitées avec les cases à cocher
3. **Ajustez les montants** avec les sliders
4. **Lancez le calcul** avec le bouton "🚀 Calculer l'optimisation"
5. **Analysez les résultats** dans les graphiques interactifs

## ⚠️ Avertissements importants

- **Girardin Industriel** : Nécessite un investissement réel et comporte des risques
- **Paramètres fiscaux** : Basés sur la législation 2024
- **Conseil professionnel** : Consultez un expert-comptable avant mise en œuvre

## 🔄 Historique des versions

- **v2.0** : Interface graphique Streamlit avec graphiques intégrés
- **v1.0** : Version CLI avec optimisations fiscales avancées

---

💼 *Outil d'aide à la décision pour l'optimisation fiscale des SARL + Holdings*