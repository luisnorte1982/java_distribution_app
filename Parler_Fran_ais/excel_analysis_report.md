# Documentation Complète — CONSOLIDE1.xlsx
## Système de Reporting Java Distribution (Business Central → Excel → Streamlit)

**Fichier analysé :** `CONSOLIDE1.xlsx` (15,07 Mo)  
**Date de l'analyse :** 9 mai 2026  
**Société :** Java Distribution (JAVA LU = Luxembourg, JAVA BE = Belgique)

---

### Table des matières
1. [Vue d'ensemble de l'architecture](#1-vue-densemble-de-larchitecture)
2. [Sources de données OData (Business Central)](#2-sources-de-données-odata-business-central)
3. [Requêtes Power Query — Code M complet](#3-requêtes-power-query--code-m-complet)
4. [Tables du modèle de données Power Pivot](#4-tables-du-modèle-de-données-power-pivot)
5. [Relations Power Pivot](#5-relations-power-pivot)
6. [Mesures DAX (Calculated Measures)](#6-mesures-dax-calculated-measures)
7. [Feuilles et Tableaux Croisés Dynamiques (TCD)](#7-feuilles-et-tableaux-croisés-dynamiques-tcd)
8. [Visualisations](#8-visualisations)
9. [Spécifications techniques pour Streamlit](#9-spécifications-techniques-pour-streamlit)

---

## 1. Vue d'ensemble de l'architecture

```
Business Central (ERP)
    │
    ▼  (OData V4 API)
Power Query (M Code)
    │  - 20 requêtes (sources, transformations, fusions)
    │  - 2 sociétés : JAVA BE + JAVA LU (= JAVA Distribution)
    ▼
Power Pivot (Data Model)
    │  - 9 tables principales
    │  - 6 relations entre tables
    │  - 17 mesures DAX calculées
    ▼
6 Feuilles Excel avec TCD
    │  - Chacune contient un tableau croisé dynamique OLAP
    │  - Filtres interactifs (slicers)
    ▼
Reporting mensuel des revenus et marges
```

**Tenant Business Central :**  
`https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/`

**Sociétés :**
| Code interne | Nom BC | Pays |
|---|---|---|
| JAVA LU | `JAVA Distribution` | Luxembourg |
| JAVA BE | `JAVA BE` | Belgique |

---

## 2. Sources de données OData (Business Central)

### 2.1. Endpoints OData utilisés

| # | Endpoint BC | Société(s) | Description | Filtre |
|---|---|---|---|---|
| 1 | `ValueEntries` | JAVA Distribution | Écritures de valeur (ventes) LU | `Posting_Date ge 2026-01-01` |
| 2 | `ValueEntries` | JAVA BE | Écritures de valeur (ventes) BE | `Posting_Date ge 2026-01-01` |
| 3 | `PostedSalesInvoicesP143` | JAVA Distribution | Factures vente comptabilisées LU | `Posting_Date ge 2025-01-01` |
| 4 | `PostedSalesCreditMemosP144` | JAVA Distribution | Avoirs vente comptabilisés LU | `Posting_Date ge 2025-01-01` |
| 5 | `PostedSalesInvoicesP143` | JAVA BE | Factures vente comptabilisées BE | `Posting_Date ge 2025-01-01` |
| 6 | `PostedSalesCreditMemosP144` | JAVA BE | Avoirs vente comptabilisés BE | `Posting_Date ge 2025-01-01` |
| 7 | `Fiche_article_Excel` | JAVA Distribution | Liste des articles | Aucun |
| 8 | `Def_dim` | JAVA Distribution | Dimensions (ACTIVITÉ=DISTRIBUTION) | `Table_ID eq 27 and Dimension_Code eq 'ACTIVITÉ' and Dimension_Value_Code eq 'DISTRIBUTION'` |
| 9 | `Customer` | JAVA BE | Clients BE | Aucun |
| 10 | `Customer` | JAVA Distribution | Clients LU | Aucun |
| 11 | `Item_Vendor_catalog` | JAVA Distribution | Catalogue fournisseurs articles | Aucun |
| 12 | `VendorCard` | JAVA Distribution | Fiche fournisseurs | Aucun |

### 2.2. Source fichier local

| Fichier | Description |
|---|---|
| `N:\Administratif et financier\Comptabilité\2026\Reporting mensuel\Java Distribution\VE_ Figé 2025.xlsx` | Écritures de valeur figées 2025 (données historiques) |

---

## 3. Requêtes Power Query — Code M complet

### 3.1. Liste des 20 requêtes

| # | Nom de la requête | Type | Destination | Description |
|---|---|---|---|---|
| 1 | `IntercoCustomers` | Table manuelle | Power Pivot | Table de référence des clients intercompany |
| 2 | `Value entries LU` | OData | Intermédiaire | VE 2026 JAVA Distribution |
| 3 | `Value entries BE` | OData | Intermédiaire | VE 2026 JAVA BE |
| 4 | `VE_2Socs_2026` | Combinaison | Power Pivot | Combine VE LU + BE 2026 |
| 5 | `PSI_JAVA_Distribution_2026` | OData | Intermédiaire | Factures vente LU |
| 6 | `PSC_JAVA_Distribution_2025` | OData | Intermédiaire | Avoirs vente LU |
| 7 | `PSI_JAVA_BE_2025` | OData | Intermédiaire | Factures vente BE |
| 8 | `PSC_JAVA_BE_2025` | OData | Intermédiaire | Avoirs vente BE |
| 9 | `SalesDoc_JAVA_Distribution_2025` | Combinaison | Intermédiaire | Combine Factures + Avoirs LU |
| 10 | `SalesDoc_JAVA_BE_2025` | Combinaison | Intermédiaire | Combine Factures + Avoirs BE |
| 11 | `SalesDoc_2Socs_2025` | Combinaison | Power Pivot | Combine tous les docs vente BE+LU |
| 12 | `Item list` | OData | Power Pivot | Fiche article |
| 13 | `Dimension - DISTRIBUTION` | OData | Power Pivot | Dimension activité DISTRIBUTION |
| 14 | `Client list BE` | OData | Power Pivot | Clients JAVA BE |
| 15 | `Client list BELU` | OData combiné | Power Pivot | Clients combinés BE+LU (sans doublons) |
| 16 | `vendor catalog` | OData | Power Pivot | Catalogue articles fournisseurs |
| 17 | `Fournisseurs` | OData | Power Pivot | Fiches fournisseurs |
| 18 | `VE_Fige_2025` | Fichier Excel | Power Pivot | VE figées 2025 (historique) |
| 19 | `Combined_VE_2026-2025` | Combinaison | Power Pivot | **Table centrale** : VE 2026 + VE figées 2025 |
| 20 | `Date` | Générée | Power Pivot | Table calendaire (2025-2030) |

### 3.2. Code M de chaque requête

#### `IntercoCustomers` — Table des clients intercompany
```m
shared IntercoCustomers = let
    Source = #table(
        type table [Company = text, Sell_to_Customer_No = text],
        {
            {"JAVA LU", "C376"},     // client = JAVA BE
            {"JAVA BE", "C000200"}   // client = JAVA LU
        }
    ),
    AddKeyCompanyCust = Table.AddColumn(
        Source, "Key_Company_Cust",
        each [Company] & "|" & Text.From([Sell_to_Customer_No]),
        type text
    )
in AddKeyCompanyCust;
```

#### `Value entries LU`
```m
shared #"Value entries LU" = let
    Source = OData.Feed(
        "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/Company('JAVA%20Distribution')/ValueEntries?$filter=Posting_Date ge 2026-01-01",
        null, [Implementation="2.0"]
    ),
    AddCompany = Table.AddColumn(Source, "Company", each "JAVA LU", type text)
in AddCompany;
```

#### `Value entries BE`
```m
shared #"Value entries BE" = let
    Source = OData.Feed(
        "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/Company('JAVA%20BE')/ValueEntries?$filter=Posting_Date ge 2026-01-01",
        null, [Implementation="2.0"]
    ),
    AddCompany = Table.AddColumn(Source, "Company", each "JAVA BE", type text)
in AddCompany;
```

#### `VE_2Socs_2026` — Combinaison Value Entries 2 sociétés
```m
shared VE_2Socs_2026 = let
    Combined = Table.Combine({#"Value entries LU", #"Value entries BE"}),
    AddKeyCompanyDoc = Table.AddColumn(
        Combined, "Key_Company_Doc",
        each [Company] & "|" & Text.From([Document_No]),
        type text
    ),
    AddIsInterco = Table.AddColumn(
        AddKeyCompanyDoc, "IsInterco", each false, type logical
    )
in AddIsInterco;
```

#### `PSI_JAVA_Distribution_2026` — Factures vente LU
```m
shared PSI_JAVA_Distribution_2026 = let
    Source = OData.Feed(
        "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/Company('JAVA%20Distribution')/PostedSalesInvoicesP143?$filter=Posting_Date ge 2025-01-01",
        null, [Implementation="2.0"]
    ),
    AddCompany = Table.AddColumn(Source, "Company", each "JAVA LU", type text),
    AddDocType = Table.AddColumn(AddCompany, "BC_DocumentType", each "Invoice", type text)
in AddDocType;
```

#### `PSC_JAVA_Distribution_2025` — Avoirs vente LU
```m
shared PSC_JAVA_Distribution_2025 = let
    Source = OData.Feed(
        "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/Company('JAVA%20Distribution')/PostedSalesCreditMemosP144?$filter=Posting_Date ge 2025-01-01",
        null, [Implementation="2.0"]
    ),
    AddCompany = Table.AddColumn(Source, "Company", each "JAVA LU", type text),
    AddDocType = Table.AddColumn(AddCompany, "BC_DocumentType", each "Credit Memo", type text)
in AddDocType;
```

#### `PSI_JAVA_BE_2025` — Factures vente BE
```m
shared PSI_JAVA_BE_2025 = let
    Source = OData.Feed(
        "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/Company('JAVA%20BE')/PostedSalesInvoicesP143?$filter=Posting_Date ge 2025-01-01",
        null, [Implementation="2.0"]
    ),
    AddCompany = Table.AddColumn(Source, "Company", each "JAVA BE", type text),
    AddDocType = Table.AddColumn(AddCompany, "BC_DocumentType", each "Invoice", type text)
in AddDocType;
```

#### `PSC_JAVA_BE_2025` — Avoirs vente BE
```m
shared PSC_JAVA_BE_2025 = let
    Source = OData.Feed(
        "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/Company('JAVA%20BE')/PostedSalesCreditMemosP144?$filter=Posting_Date ge 2025-01-01",
        null, [Implementation="2.0"]
    ),
    AddCompany = Table.AddColumn(Source, "Company", each "JAVA BE", type text),
    AddDocType = Table.AddColumn(AddCompany, "BC_DocumentType", each "Credit Memo", type text)
in AddDocType;
```

#### `SalesDoc_JAVA_Distribution_2025` et `SalesDoc_JAVA_BE_2025`
```m
shared SalesDoc_JAVA_Distribution_2025 = let
    SalesDocs = Table.Combine({PSI_JAVA_Distribution_2026, PSC_JAVA_Distribution_2025})
in SalesDocs;

shared SalesDoc_JAVA_BE_2025 = let
    SalesDocs = Table.Combine({PSI_JAVA_BE_2025, PSC_JAVA_BE_2025})
in SalesDocs;
```

#### `SalesDoc_2Socs_2025` — Tous les documents de vente (table finale)
```m
shared SalesDoc_2Socs_2025 = let
    Combined = Table.Combine({
        SalesDoc_JAVA_Distribution_2025,
        SalesDoc_JAVA_BE_2025
    }),
    AddKeyCompanyDoc = Table.AddColumn(
        Combined, "Key_Company_Doc",
        each [Company] & "|" & Text.From([No]),
        type text
    ),
    AddKeyCompanyCust = Table.AddColumn(
        AddKeyCompanyDoc, "Key_Company_Cust",
        each [Company] & "|" & Text.From([Sell_to_Customer_No]),
        type text
    )
in AddKeyCompanyCust;
```

#### `Item list` — Articles
```m
shared #"Item list" = let
    Source = OData.Feed(
        "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/Company('JAVA%20Distribution')/Fiche_article_Excel",
        null, [Implementation="2.0"]
    )
in Source;
```

#### `Dimension - DISTRIBUTION`
```m
shared #"Dimension - DISTRIBUTION" = let
    Source = OData.Feed(
        "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4/Company('JAVA%20Distribution')/Def_dim?$filter=Table_ID eq 27 and Dimension_Code eq 'ACTIVITÉ' and Dimension_Value_Code eq 'DISTRIBUTION'",
        null, [Implementation="2.0"]
    )
in Source;
```

#### `Client list BELU` — Clients combinés BE + LU
```m
shared #"Client list BELU" = let
    Source_BE = OData.Feed(
        ".../Company('JAVA%20BE')/Customer", null, [Implementation="2.0"]
    ),
    Source_DIST = OData.Feed(
        ".../Company('JAVA%20Distribution')/Customer", null, [Implementation="2.0"]
    ),
    Combined = Table.Combine({Source_BE, Source_DIST}),
    DistinctCustomers = Table.Distinct(Combined, {"Name"})
in DistinctCustomers;
```

#### `Client list BE`
```m
shared #"Client list BE" = let
    Source = OData.Feed(
        ".../Company('JAVA%20BE')/Customer", null, [Implementation="2.0"]
    )
in Source;
```

#### `vendor catalog`
```m
shared #"vendor catalog" = let
    Source = OData.Feed(
        ".../Company('JAVA%20Distribution')/Item_Vendor_catalog",
        null, [Implementation="2.0"]
    )
in Source;
```

#### `Fournisseurs`
```m
shared Fournisseurs = let
    Source = OData.Feed(
        ".../Company('JAVA%20Distribution')/VendorCard",
        null, [Implementation="2.0"]
    )
in Source;
```

#### `VE_Fige_2025` — Données figées 2025
```m
shared VE_Fige_2025 = let
    Source = Excel.Workbook(
        File.Contents("N:\Administratif et financier\Comptabilité\2026\Reporting mensuel\Java Distribution\VE_ Figé 2025.xlsx"),
        null, true
    ),
    Data = Source{[Item="VE_Fige_2025", Kind="Table"]}[Data],
    #"Colonnes conservées" = Table.SelectColumns(Data, {
        "Item_No", "Posting_Date", "Document_No", "Item_Ledger_Entry_No",
        "Item_Ledger_Entry_Type", "Valued_Quantity", "Invoiced_Quantity",
        "Cost_Amount_Actual", "Sales_Amount_Actual", "Company",
        "Key_Company_Doc", "IsInterco"
    }),
    -- Types et nettoyage appliqués
in #"Nettoyage texte";
```

#### `Combined_VE_2026-2025` — **Table centrale des Value Entries**
```m
shared #"Combined_VE_2026-2025" = let
    Source = Table.Combine({VE_2Socs_2026, VE_Fige_2025})
in Source;
```

#### `Date` — Table calendaire
```m
shared Date = let
    DateDebut = #date(2025, 1, 1),
    DateFin = #date(2030, 12, 31),
    NbJours = Duration.Days(DateFin - DateDebut) + 1,
    ListeDates = List.Dates(DateDebut, NbJours, #duration(1, 0, 0, 0)),
    TableDates = Table.FromList(ListeDates, Splitter.SplitByNothing(), {"Date"}),
    TypeDate = Table.TransformColumnTypes(TableDates, {{"Date", type date}}),
    AddAnnee = Table.AddColumn(TypeDate, "Année", each Date.Year([Date]), Int64.Type),
    AddMois = Table.AddColumn(AddAnnee, "Mois", each Date.Month([Date]), Int64.Type),
    AddNomMois = Table.AddColumn(AddMois, "Nom du mois", each Date.ToText([Date], "MMMM"), type text),
    AddTrimestre = Table.AddColumn(AddNomMois, "Trimestre", each "T" & Number.ToText(Date.QuarterOfYear([Date])), type text),
    AddAnneeMois = Table.AddColumn(AddTrimestre, "AnnéeMois", each [Année] * 100 + [Mois], Int64.Type),
    AddMoisCourt = Table.AddColumn(AddAnneeMois, "Mois court", each Date.ToText([Date], "MMM"), type text)
in AddMoisCourt;
```

---

## 4. Tables du modèle de données Power Pivot

### 4.1. Tables principales (9 tables actives dans le modèle)

#### Table `Combined_VE_2026-2025` ⭐ (Table de faits principale)
> Contient toutes les écritures de valeur (Value Entries) : ventes 2025 (figées) + 2026 (live)

| Colonne | Type | Description |
|---|---|---|
| Entry_No | Int | N° d'écriture |
| **Item_No** | Text | N° article (FK → Item list) |
| Item_Ledger_Entry_No | Int | N° écriture article |
| Item_Ledger_Entry_Type | Text | Type (Sale, Purchase...) |
| Item_Ledger_Entry_Quantity | Num | Quantité écriture article |
| **Posting_Date** | Date | Date comptabilisation (FK → Date) |
| Valuation_Date | Date | Date valorisation |
| Document_Date | Date | Date document |
| Document_Type | Text | Type document |
| Document_No | Text | N° document |
| Gen_Bus_Posting_Group | Text | Groupe compta marché |
| Gen_Prod_Posting_Group | Text | Groupe compta produit |
| Location_Code | Text | Code emplacement |
| Valued_Quantity | Num | Quantité valorisée |
| Invoiced_Quantity | Num | Quantité facturée |
| Cost_per_Unit | Num | Coût unitaire |
| Cost_Posted_to_G_L | Num | Coût comptabilisé en CG |
| **Cost_Amount_Actual** | Num | **Montant coût réel** |
| Cost_Amount_Expected | Num | Montant coût prévu |
| **Sales_Amount_Actual** | Num | **Montant vente réel (CA)** |
| Sales_Amount_Expected | Num | Montant vente prévu |
| **Company** | Text | Société (JAVA LU / JAVA BE) |
| **Key_Company_Doc** | Text | Clé composite Company\|Document_No (FK → SalesDoc + IntercoCustomers) |
| **IsInterco** | Boolean | Indicateur transaction intercompany |

#### Table `SalesDoc_2Socs_2025` (Factures + Avoirs)
| Colonne | Type | Description |
|---|---|---|
| No | Text | N° document |
| Order_No | Text | N° commande |
| **Sell_to_Customer_No** | Text | N° client |
| **Sell_to_Customer_Name** | Text | Nom client |
| Currency_Code | Text | Code devise |
| Amount | Num | Montant HT |
| Amount_Including_VAT | Num | Montant TTC |
| **Posting_Date** | Date | Date comptabilisation |
| **Salesperson_Code** | Text | Code vendeur |
| Shortcut_Dimension_1_Code | Text | Dimension 1 |
| Shortcut_Dimension_2_Code | Text | Dimension 2 |
| **Location_Code** | Text | Code emplacement |
| **Company** | Text | Société |
| **BC_DocumentType** | Text | Type (Invoice / Credit Memo) |
| **Key_Company_Doc** | Text | Clé Company\|No (PK relation avec VE) |
| **Key_Company_Cust** | Text | Clé Company\|Customer (FK → IntercoCustomers) |

#### Table `Item list` (Articles)
| Colonne clé | Type | Description |
|---|---|---|
| **No** | Text | N° article (PK) |
| **Description** | Text | Description article |
| **Marque_NSI** | Text | Marque (ex: LAVISH, MARSHALL...) |
| Item_Category_Code | Text | Catégorie article |
| **Vendor_No** | Text | N° fournisseur (FK → Fournisseurs) |
| Unit_Cost | Num | Coût unitaire |
| Unit_Price | Num | Prix unitaire |
| Inventory | Num | Stock |
| Gen_Prod_Posting_Group | Text | Groupe compta produit |
| ... | ... | ~181 colonnes au total |

#### Table `Fournisseurs`
| Colonne clé | Type | Description |
|---|---|---|
| **No** | Text | N° fournisseur (PK) |
| **Name** | Text | Nom fournisseur |
| **Location_Code** | Text | Code emplacement |
| Country_Region_Code | Text | Pays |
| ... | ... | ~91 colonnes au total |

#### Table `Date` (Table calendaire)
| Colonne | Type | Description |
|---|---|---|
| **Date** | Date | Date (PK, 2025-01-01 → 2030-12-31) |
| **Année** | Int | Année |
| **Mois** | Int | N° mois (1-12) |
| **Nom du mois** | Text | Nom complet du mois |
| **Trimestre** | Text | T1, T2, T3, T4 |
| **AnnéeMois** | Int | Format AAAAMM |
| **Mois court** | Text | Abréviation (jan, fév...) |

#### Table `IntercoCustomers`
| Colonne | Type | Description |
|---|---|---|
| Company | Text | Société |
| Sell_to_Customer_No | Text | N° client interco |
| **Key_Company_Cust** | Text | Clé composite (PK) |

> **Données :**  
> - `JAVA LU | C376` → C376 = client JAVA BE chez LU  
> - `JAVA BE | C000200` → C000200 = client JAVA LU chez BE

#### Table `Dimension - DISTRIBUTION`
| Colonne | Type | Description |
|---|---|---|
| Table_ID | Int | ID table (27 = Item) |
| **No** | Text | N° article (PK, lien avec Item list) |
| Dimension_Code | Text | ACTIVITÉ |
| **Dimension_Value_Code** | Text | DISTRIBUTION |

#### Table `Client list BELU`
| Colonne clé | Type | Description |
|---|---|---|
| No | Text | N° client |
| **Name** | Text | Nom client |
| Salesperson_Code | Text | Code vendeur |
| Customer_Posting_Group | Text | Groupe compta |
| ... | ... | ~58 colonnes |

#### Table `vendor catalog`
| Colonne | Type | Description |
|---|---|---|
| Vendor_No | Text | N° fournisseur |
| Item_No | Text | N° article |
| Vendor_Item_No | Text | N° article chez le fournisseur |

---

## 5. Relations Power Pivot

### 5.1. Schéma relationnel

```
                    ┌──────────────────┐
                    │      Date        │
                    │  PK: Date        │
                    └────────▲─────────┘
                             │ (Posting_Date → Date)
                             │
┌─────────────┐    ┌────────┴──────────┐    ┌──────────────────┐
│ Fournisseurs│◄───│ Combined_VE_      │───►│ SalesDoc_2Socs_  │
│ PK: No      │    │ 2026-2025         │    │ 2025             │
└──────▲──────┘    │ (Table de faits)  │    │ PK: Key_Company_ │
       │           │                   │    │      Doc          │
       │           └──┬─────┬──────────┘    └──────────────────┘
       │              │     │                        │
       │   (Item_No)  │     │(Key_Company_Doc)       │
       │              ▼     │                        │
┌──────┴──────┐  ┌────────┐ │              ┌─────────▼────────┐
│  Item list  │  │Dim-    │ └─────────────►│ IntercoCustomers │
│  PK: No     │──►DISTRI- │                │ PK: Key_Company_ │
│             │  │BUTION  │                │      Cust         │
│  Vendor_No──┘  │PK: No  │                └──────────────────┘
└─────────────┘  └────────┘
```

### 5.2. Détail des relations

| # | Table source (FK) | Colonne FK | → | Table cible (PK) | Colonne PK | Cardinalité | Description |
|---|---|---|---|---|---|---|---|
| 1 | `Combined_VE_2026-2025` | `Posting_Date` | → | `Date` | `Date` | N:1 | Lien date pour axes temporels |
| 2 | `Combined_VE_2026-2025` | `Item_No` | → | `Item list` | `No` | N:1 | Lien article (marque, description) |
| 3 | `Combined_VE_2026-2025` | `Key_Company_Doc` | → | `SalesDoc_2Socs_2025` | `Key_Company_Doc` | N:1 | Lien doc vente (client, vendeur, location) |
| 4 | `Combined_VE_2026-2025` | `Key_Company_Doc` | → | `IntercoCustomers` | `Key_Company_Cust` | N:1 | Identification transactions interco (**inactive** ou filtre) |
| 5 | `Item list` | `No` | → | `Dimension - DISTRIBUTION` | `No` | 1:1 | Articles avec dimension DISTRIBUTION |
| 6 | `Item list` | `Vendor_No` | → | `Fournisseurs` | `No` | N:1 | Lien article → fournisseur |

---

## 6. Mesures DAX (Calculated Measures)

### 6.1. Mesures identifiées (17 mesures)

Toutes les mesures sont définies sur la table `Combined_VE_2026-2025`.

#### Mesures principales de revenue et marge

| # | Nom | Formule DAX (reconstituée) | Description |
|---|---|---|---|
| 1 | **Revenue External** | `CALCULATE(SUM([Sales_Amount_Actual]), [Sales_Amount_Actual] <> 0, NOT([Key_Company_Doc] IN VALUES('IntercoCustomers'[Key_Company_Cust])))` | **CA externe** (hors interco) |
| 2 | **COGS External (Full)** | `VAR SoldItems = FILTER(VALUES([Item_Ledger_Entry_No]), [Sales_Amount_Actual] <> 0, NOT([Key_Company_Doc] IN VALUES('IntercoCustomers'[Key_Company_Cust]))) RETURN -SUM([Cost_Amount_Actual])` | **Coût des ventes externe** (hors interco) |
| 3 | **Gross Margin External** | `[Revenue External] - [COGS External (Full)]` | **Marge brute externe** = CA - COGS |
| 4 | **Margin % External** | `DIVIDE([Gross Margin External], [Revenue External])` | **% marge brute externe** |
| 5 | **Qty Sold External** | `CALCULATE(-SUM([Invoiced_Quantity]), [Sales_Amount_Actual] <> 0, NOT([Key_Company_Doc] IN VALUES('IntercoCustomers'[Key_Company_Cust])))` | **Quantité vendue externe** |
| 6 | **Actual Selling Price** | `DIVIDE([Revenue External], [Qty Sold External])` | **Prix de vente unitaire moyen** |
| 7 | **Average Actual Cost per Unit** | `DIVIDE([COGS External (Full)], [Qty Sold External])` | **Coût unitaire moyen réel** |

#### Mesures dérivées

| # | Nom | Formule DAX (reconstituée) | Description |
|---|---|---|---|
| 8 | **Actual Unit Margin** | `[Actual Selling Price] - [Average Actual Cost per Unit]` | Marge unitaire |
| 9 | **Actual Margin %** | `DIVIDE([Actual Unit Margin], [Actual Selling Price])` | % marge unitaire |
| 10 | **Revenue** | `SUM([Sales_Amount_Actual])` | CA total (y compris interco) |
| 11 | **COGS External** | Variante de COGS | Coût des ventes (variante) |
| 12 | **Cost Amount Actual External** | `CALCULATE(SUM([Cost_Amount_Actual]), ...)` | Coût réel externe |
| 13 | **Actual Purchase Price** | `DIVIDE([Cost Amount Actual External], [Qty Sold External])` | Prix d'achat réel |
| 14 | **Average Purchase Price per Unit** | Similaire à Actual Purchase Price | Prix d'achat moyen unitaire |
| 15 | **Inbound Qty** | `SUM([Valued_Quantity])` filtre entrées | Quantité entrante |
| 16 | **Inbound Cost** | `SUM([Cost_Amount_Actual])` filtre entrées | Coût entrant |
| 17 | **Actual Cost per Unit** | `DIVIDE([Inbound Cost], [Inbound Qty])` | Coût unitaire entrant |

### 6.2. Logique d'exclusion intercompany

> **Principe clé** : Toutes les mesures "External" excluent les transactions intercompany en vérifiant que le `Key_Company_Doc` de la Value Entry **n'est PAS** dans la table `IntercoCustomers`. Cela permet de ne rapporter que le CA réalisé avec des clients tiers (non JAVA BE ↔ JAVA LU).

---

## 7. Feuilles et Tableaux Croisés Dynamiques (TCD)

### 7.1. Vue d'ensemble des 6 feuilles

| # | Feuille | TCD | Description | Dimensions | Mesures |
|---|---|---|---|---|---|
| 1 | **DIS Monthly external rev** | TCD1 | Revenue mensuel Distribution par fournisseur | Company, Name (fournisseur), Marque_NSI | Revenue External, Gross Margin External |
| 2 | **DIS YTD Monthly external rev** | TCD3 | Revenue YTD Distribution par client × mois | Sell_to_Customer_Name, Name (fournisseur), Mois | Revenue External |
| 3 | **Rev salesP by location** | TCD1 | Revenue par emplacement et marque | Company, Location_Code, Marque_NSI | Revenue External |
| 4 | **ALL Monthly external rev** | TCD4 | Revenue mensuel toutes activités par location | Company, Location_Code | Revenue External |
| 5 | **Rev by vendor name YTD** | TCD3 | Revenue YTD par fournisseur, comparaison N/N-1 | Name (fournisseur) × Mois × Année | Revenue External |
| 6 | **Revenue by salesperson** | TCD2 | Revenue + Marge par client et article | Sell_to_Customer_Name, Description (article) × Mois | Revenue External, Gross Margin External |

### 7.2. Détail de chaque TCD

#### Feuille 1 : `DIS Monthly external rev`
**Objectif** : Revenue mensuel de l'activité DISTRIBUTION par fournisseur et marque, comparaison N-1/N

| Élément | Champs |
|---|---|
| **Filtres (slicers)** | Sell_to_Customer_Name (tous), Dimension_Value_Code = DISTRIBUTION, Mois = 4 |
| **Lignes** | Company, Name (fournisseur), Marque_NSI |
| **Colonnes** | Année (2025, 2026), Mesures (Revenue External, Gross Margin External) |
| **Valeurs** | Revenue External, Gross Margin External |
| **Plage** | A5:G34 |

**Exemple de données :**
| Company | Fournisseur | Marque | Rev 2025 | GM 2025 | Rev 2026 | GM 2026 |
|---|---|---|---|---|---|---|
| JAVA BE | Lavish International | LAVISH | 0 | 0 | 63 871 | 21 619 |
| JAVA LU | Pernod Ricard | ABSOLUT | - | - | 8 109 | 977 |
| **Total** | | | **94 920** | **15 240** | **223 493** | **55 772** |

#### Feuille 2 : `DIS YTD Monthly external rev`
**Objectif** : Revenue cumulé YTD Distribution par client et fournisseur

| Élément | Champs |
|---|---|
| **Filtres** | Dimension_Value_Code = DISTRIBUTION |
| **Lignes** | Sell_to_Customer_Name, Name (fournisseur) |
| **Colonnes** | Mois (1, 2, 3, 4), Année (2026), Company |
| **Valeurs** | Revenue External |
| **Plage** | A4:F14 |

#### Feuille 3 : `Rev salesP by location`
**Objectif** : Revenue par emplacement (entrepôt/site) et marque

| Élément | Champs |
|---|---|
| **Filtres** | Sell_to_Customer_Name (tous), Dimension_Value_Code = DISTRIBUTION, Mois = 4 |
| **Lignes** | Company, Location_Code, Marque_NSI |
| **Colonnes** | Année (2026) |
| **Valeurs** | Revenue External |
| **Plage** | A6:D34 |

**Location Codes observés :** DD, MAR, RB, DD BE, HORS DD, HORS DD BE, AWL, VM

#### Feuille 4 : `ALL Monthly external rev`
**Objectif** : Revenue mensuel TOUTES activités (pas seulement Distribution) par société et location

| Élément | Champs |
|---|---|
| **Filtres** | Sell_to_Customer_Name (tous) |
| **Lignes** | Company, Location_Code |
| **Colonnes** | Mois (= 4), Année (2025, 2026) |
| **Valeurs** | Revenue External |
| **Plage** | A4:D17 |

**Données clés (mois 4) :**
| Société | Location | Rev 2025 | Rev 2026 |
|---|---|---|---|
| JAVA LU | DD | 1 353 251 | 1 495 597 |
| JAVA LU | HORS DD | 416 136 | 543 090 |
| JAVA LU | MAR | 1 112 854 | 1 087 501 |
| **Total** | | **3 046 403** | **3 387 523** |

#### Feuille 5 : `Rev by vendor name YTD`
**Objectif** : Revenue YTD par fournisseur, comparaison glissante par mois entre 2025 et 2026

| Élément | Champs |
|---|---|
| **Filtres** | Sell_to_Customer_Name (tous), Company (tous), Location_Code (tous) |
| **Lignes** | Name (fournisseur) |
| **Colonnes** | Mois (1→4), Année (2025/2026) |
| **Valeurs** | Revenue External |
| **Plage** | A5:I77 |

**Top fournisseurs (YTD mois 4, 2026) :**
| Fournisseur | Rev YTD 2025 | Rev YTD 2026 |
|---|---|---|
| Pernod Ricard Belgium | 2 238 770 | 2 984 236 |
| Prätorius | 1 399 057 | 1 366 416 |
| Caves Wengler | 373 685 | 1 755 020 |
| **Total** | **9 812 496** | **13 617 081** |

#### Feuille 6 : `Revenue by salesperson`
**Objectif** : Revenue + Marge brute détaillés par client et article (granularité la plus fine)

| Élément | Champs |
|---|---|
| **Filtres** | Company (tous), Dimension_Value_Code (tous) |
| **Lignes** | Sell_to_Customer_Name, Description (article) |
| **Colonnes** | Année (2026), Mois (1→4), Mesures |
| **Valeurs** | Revenue External, Gross Margin External |
| **Plage** | A5:J2541 (très volumineux : ~2530 lignes) |

---

## 8. Visualisations

### 8.1. Graphiques
**Aucun graphique (chart) n'est présent dans le fichier.** Les données sont présentées uniquement sous forme de tableaux croisés dynamiques.

### 8.2. Éléments de mise en forme
- Les TCD utilisent les filtres de page (slicers) pour la navigation
- Les colonnes sont organisées en structure hiérarchique (Company > Location/Fournisseur > Marque/Article)
- Comparaisons N vs N-1 sont systématiques

---

## 9. Spécifications techniques pour Streamlit

### 9.1. Architecture cible recommandée

```
Business Central (OData V4)
    │
    ▼
Couche d'ingestion (Python + requests/aiohttp)
    │  - Authentification OAuth2
    │  - Appels OData avec mêmes filtres
    │  - Cache local (SQLite/Parquet/DuckDB)
    ▼
Couche de transformation (Pandas/Polars)
    │  - Logique Power Query reproduite en Python
    │  - Jointures et calculs de mesures
    ▼
Application Streamlit
    │  - 6+ pages correspondant aux feuilles
    │  - Filtres interactifs (st.selectbox, st.multiselect)
    │  - Tableaux interactifs (st.dataframe / AgGrid)
    │  - Graphiques (Plotly)
    ▼
Export (Excel, CSV, PDF)
```

### 9.2. Sources de données à reproduire

#### Appels OData à implémenter

```python
BASE_URL = "https://api.businesscentral.dynamics.com/v2.0/ad140881-5aae-4f5d-8941-89111ecfcdcc/Production/ODataV4"

ENDPOINTS = {
    "value_entries_lu": f"{BASE_URL}/Company('JAVA%20Distribution')/ValueEntries?$filter=Posting_Date ge 2026-01-01",
    "value_entries_be": f"{BASE_URL}/Company('JAVA%20BE')/ValueEntries?$filter=Posting_Date ge 2026-01-01",
    "psi_lu": f"{BASE_URL}/Company('JAVA%20Distribution')/PostedSalesInvoicesP143?$filter=Posting_Date ge 2025-01-01",
    "psc_lu": f"{BASE_URL}/Company('JAVA%20Distribution')/PostedSalesCreditMemosP144?$filter=Posting_Date ge 2025-01-01",
    "psi_be": f"{BASE_URL}/Company('JAVA%20BE')/PostedSalesInvoicesP143?$filter=Posting_Date ge 2025-01-01",
    "psc_be": f"{BASE_URL}/Company('JAVA%20BE')/PostedSalesCreditMemosP144?$filter=Posting_Date ge 2025-01-01",
    "items": f"{BASE_URL}/Company('JAVA%20Distribution')/Fiche_article_Excel",
    "dim_distribution": f"{BASE_URL}/Company('JAVA%20Distribution')/Def_dim?$filter=Table_ID eq 27 and Dimension_Code eq 'ACTIVITÉ' and Dimension_Value_Code eq 'DISTRIBUTION'",
    "customers_be": f"{BASE_URL}/Company('JAVA%20BE')/Customer",
    "customers_lu": f"{BASE_URL}/Company('JAVA%20Distribution')/Customer",
    "vendor_catalog": f"{BASE_URL}/Company('JAVA%20Distribution')/Item_Vendor_catalog",
    "vendors": f"{BASE_URL}/Company('JAVA%20Distribution')/VendorCard",
}
```

### 9.3. Logique de transformation à reproduire

#### Étape 1 : Construction des Value Entries combinées
```python
# VE 2026 (live OData)
ve_lu = fetch_odata("value_entries_lu")
ve_lu["Company"] = "JAVA LU"
ve_be = fetch_odata("value_entries_be")
ve_be["Company"] = "JAVA BE"
ve_2026 = pd.concat([ve_lu, ve_be])
ve_2026["Key_Company_Doc"] = ve_2026["Company"] + "|" + ve_2026["Document_No"]
ve_2026["IsInterco"] = False

# VE 2025 (fichier figé)
ve_2025 = pd.read_excel("VE_Fige_2025.xlsx")

# Combinaison
combined_ve = pd.concat([ve_2026, ve_2025])
```

#### Étape 2 : Construction des Sales Documents
```python
# Factures + Avoirs par société
psi_lu = fetch_odata("psi_lu"); psi_lu["Company"] = "JAVA LU"; psi_lu["BC_DocumentType"] = "Invoice"
psc_lu = fetch_odata("psc_lu"); psc_lu["Company"] = "JAVA LU"; psc_lu["BC_DocumentType"] = "Credit Memo"
psi_be = fetch_odata("psi_be"); psi_be["Company"] = "JAVA BE"; psi_be["BC_DocumentType"] = "Invoice"
psc_be = fetch_odata("psc_be"); psc_be["Company"] = "JAVA BE"; psc_be["BC_DocumentType"] = "Credit Memo"

sales_docs = pd.concat([psi_lu, psc_lu, psi_be, psc_be])
sales_docs["Key_Company_Doc"] = sales_docs["Company"] + "|" + sales_docs["No"]
sales_docs["Key_Company_Cust"] = sales_docs["Company"] + "|" + sales_docs["Sell_to_Customer_No"]
```

#### Étape 3 : Table Interco
```python
interco = pd.DataFrame({
    "Company": ["JAVA LU", "JAVA BE"],
    "Sell_to_Customer_No": ["C376", "C000200"],
})
interco["Key_Company_Cust"] = interco["Company"] + "|" + interco["Sell_to_Customer_No"]
```

#### Étape 4 : Jointures (reproduire le modèle Power Pivot)
```python
# Enrichir VE avec articles
df = combined_ve.merge(items[["No","Description","Marque_NSI","Vendor_No","Item_Category_Code"]],
                       left_on="Item_No", right_on="No", how="left", suffixes=("","_item"))

# Enrichir avec fournisseurs
df = df.merge(vendors[["No","Name","Location_Code"]],
              left_on="Vendor_No", right_on="No", how="left", suffixes=("","_vendor"))

# Enrichir avec docs vente (client, vendeur, location)
df = df.merge(sales_docs[["Key_Company_Doc","Sell_to_Customer_Name","Salesperson_Code","Location_Code"]],
              on="Key_Company_Doc", how="left", suffixes=("","_salesdoc"))

# Dimension DISTRIBUTION
df = df.merge(dim_distrib[["No","Dimension_Value_Code"]],
              left_on="Item_No", right_on="No", how="left", suffixes=("","_dim"))

# Marqueur interco
interco_keys = set(interco["Key_Company_Cust"])
# Via sales_docs
df["IsInterco_computed"] = df["Key_Company_Doc"].isin(
    sales_docs[sales_docs["Key_Company_Cust"].isin(interco_keys)]["Key_Company_Doc"]
)

# Table Date
df["Posting_Year"] = df["Posting_Date"].dt.year
df["Posting_Month"] = df["Posting_Date"].dt.month
df["Posting_Quarter"] = "T" + df["Posting_Date"].dt.quarter.astype(str)
```

### 9.4. Calcul des mesures en Python

```python
def calc_revenue_external(df_filtered):
    """Revenue External = SUM(Sales_Amount_Actual) WHERE NOT interco AND Sales_Amount_Actual != 0"""
    mask = (df_filtered["Sales_Amount_Actual"] != 0) & (~df_filtered["IsInterco_computed"])
    return df_filtered.loc[mask, "Sales_Amount_Actual"].sum()

def calc_cogs_external(df_filtered):
    """COGS External = -SUM(Cost_Amount_Actual) pour les lignes de vente non interco"""
    mask = (df_filtered["Sales_Amount_Actual"] != 0) & (~df_filtered["IsInterco_computed"])
    return -df_filtered.loc[mask, "Cost_Amount_Actual"].sum()

def calc_gross_margin_external(df_filtered):
    return calc_revenue_external(df_filtered) - calc_cogs_external(df_filtered)

def calc_margin_pct_external(df_filtered):
    rev = calc_revenue_external(df_filtered)
    return calc_gross_margin_external(df_filtered) / rev if rev != 0 else 0

def calc_qty_sold_external(df_filtered):
    mask = (df_filtered["Sales_Amount_Actual"] != 0) & (~df_filtered["IsInterco_computed"])
    return -df_filtered.loc[mask, "Invoiced_Quantity"].sum()

def calc_actual_selling_price(df_filtered):
    rev = calc_revenue_external(df_filtered)
    qty = calc_qty_sold_external(df_filtered)
    return rev / qty if qty != 0 else 0

def calc_avg_cost_per_unit(df_filtered):
    cogs = calc_cogs_external(df_filtered)
    qty = calc_qty_sold_external(df_filtered)
    return cogs / qty if qty != 0 else 0
```

### 9.5. Pages Streamlit à créer

| # | Page | Correspond à | Filtres | Contenu |
|---|---|---|---|---|
| 1 | **Distribution - Revenue mensuel** | `DIS Monthly external rev` | Client, Dimension=DISTRIBUTION, Mois | Tableau : Company × Fournisseur × Marque avec Rev & GM par année |
| 2 | **Distribution - Revenue YTD** | `DIS YTD Monthly external rev` | Dimension=DISTRIBUTION | Tableau : Client × Fournisseur avec Revenue cumulé par mois |
| 3 | **Revenue par emplacement** | `Rev salesP by location` | Client, Dimension=DISTRIBUTION, Mois | Tableau : Company × Location × Marque avec Revenue |
| 4 | **Revenue global mensuel** | `ALL Monthly external rev` | Client | Tableau : Company × Location avec Revenue N vs N-1 |
| 5 | **Revenue YTD par fournisseur** | `Rev by vendor name YTD` | Client, Company, Location | Tableau : Fournisseur avec Revenue par mois, comparaison N/N-1 |
| 6 | **Revenue par vendeur / article** | `Revenue by salesperson` | Company, Dimension | Tableau détaillé : Client × Article avec Rev & GM par mois |
| 7 | **Dashboard** *(nouveau)* | N/A | Tous | Vue synthétique avec KPIs et graphiques |

### 9.6. Colonnes essentielles à extraire par endpoint

#### Value Entries (table de faits)
```
Entry_No, Item_No, Posting_Date, Document_No, Item_Ledger_Entry_Type,
Item_Ledger_Entry_No, Valued_Quantity, Invoiced_Quantity,
Cost_Amount_Actual, Sales_Amount_Actual, Location_Code,
Gen_Bus_Posting_Group, Gen_Prod_Posting_Group
```

#### Posted Sales Invoices / Credit Memos
```
No, Sell_to_Customer_No, Sell_to_Customer_Name, Posting_Date,
Salesperson_Code, Location_Code, Shortcut_Dimension_1_Code,
Amount, Amount_Including_VAT, Currency_Code, BC_DocumentType
```

#### Items (Fiche article)
```
No, Description, Marque_NSI, Item_Category_Code, Vendor_No,
Unit_Cost, Unit_Price, Inventory, Gen_Prod_Posting_Group
```

#### Fournisseurs
```
No, Name, Location_Code, Country_Region_Code
```

#### Clients
```
No, Name, Salesperson_Code, Customer_Posting_Group,
Gen_Bus_Posting_Group, Country_Region_Code, Location_Code
```

### 9.7. Considérations de performance

| Problème actuel (Excel) | Solution Streamlit |
|---|---|
| Fichier de 15 Mo, lent à ouvrir | Application web légère, données en cache |
| Rafraîchissement OData bloquant | Rafraîchissement asynchrone en arrière-plan |
| Power Pivot charge tout en mémoire | Chargement partiel / filtres côté requête |
| Pas de partage facile | URL accessible à tous les utilisateurs autorisés |
| Formules DAX complexes | Calculs Pandas/Polars optimisés |
| Fichier réseau partagé (N:\) | Base de données locale ou cloud |

### 9.8. Authentification Business Central

L'accès OData nécessite une authentification **OAuth2** avec Azure AD :
- **Tenant ID** : `ad140881-5aae-4f5d-8941-89111ecfcdcc`
- **Scope** : `https://api.businesscentral.dynamics.com/.default`
- **Grant type** : `client_credentials` (service-to-service) ou `authorization_code` (utilisateur)

---

### Annexe A : Dictionnaire des Location Codes

| Code | Description probable |
|---|---|
| DD | Dépôt Direct (entrepôt principal LU) |
| DD BE | Dépôt Direct Belgique |
| HORS DD | Hors dépôt direct LU |
| HORS DD BE | Hors dépôt direct BE |
| MAR | Marché / Marketplace |
| AWL | Autre entrepôt LU |
| RB | Point de vente / Retail |
| VM | Vente en Marketplace (Belgique) |

### Annexe B : Hiérarchie du modèle de données

```
Combined_VE_2026-2025 (FAIT)
├── Date (DIM temps) — via Posting_Date
├── Item list (DIM articles) — via Item_No
│   ├── Fournisseurs (DIM fournisseurs) — via Vendor_No
│   └── Dimension - DISTRIBUTION (DIM activité) — via No
├── SalesDoc_2Socs_2025 (DIM documents) — via Key_Company_Doc
│   └── IntercoCustomers (DIM interco) — via Key_Company_Cust
└── Client list BELU (DIM clients) — non liée directement
```

### Annexe C : Flux de données Power Query

```
OData BC ─┬─ Value entries LU ─┐
           │                    ├─ VE_2Socs_2026 ─┐
           ├─ Value entries BE ─┘                  │
           │                                       ├─ Combined_VE_2026-2025 ⭐
           │     Fichier Excel ─ VE_Fige_2025 ────┘
           │
           ├─ PSI_JAVA_Distribution_2026 ─┐
           ├─ PSC_JAVA_Distribution_2025 ─┼─ SalesDoc_JAVA_Distribution ─┐
           ├─ PSI_JAVA_BE_2025 ──────────┐│                              ├─ SalesDoc_2Socs_2025 ⭐
           ├─ PSC_JAVA_BE_2025 ──────────┴┘─ SalesDoc_JAVA_BE ──────────┘
           │
           ├─ Item list ⭐
           ├─ Fournisseurs ⭐
           ├─ Dimension - DISTRIBUTION ⭐
           ├─ Client list BELU ⭐
           ├─ Client list BE
           ├─ vendor catalog
           └─ IntercoCustomers ⭐ (table manuelle)
           
           Date ⭐ (table générée, 2025-2030)
```

---

*Document généré automatiquement le 9 mai 2026 par analyse du fichier CONSOLIDE1.xlsx*
