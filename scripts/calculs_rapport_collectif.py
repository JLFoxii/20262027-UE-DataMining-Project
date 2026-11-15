# -*- coding: utf-8 -*-
# Calculs et figures du rapport collectif M2 Data Science 2026-2027.
# Ce fichier est la SOURCE REPRODUCTIBLE des résultats de
# Rapport_collectif_Data_Mining_M2DS_2026_2027.ipynb (lecture sans code).
# Le générateur découpe les marqueurs '# %% source-cell=N' et exécute les
# blocs dans l'ordre via un noyau Jupyter, sans modifier les CSV sources.
# L'exécution est possible depuis la racine du dépôt avec le kernel Python.

# %% source-cell=4
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

# On peut exécuter ce rapport depuis la racine ou depuis le dossier qui le contient.
ROOT = next((p for p in [Path.cwd(), *Path.cwd().parents]
             if (p / "data/public_records/site_access_case_events.csv").is_file()), None)
if ROOT is None:
    raise FileNotFoundError("Fichiers data/ introuvables : ouvrez le notebook dans le dépôt du projet.")
DATA = ROOT / "data"

# Cette première étape retire seulement les copies strictement identiques.
# Les corrections propres à chaque domaine sont précisées ensuite.
def lire_csv(rel):
    return pd.read_csv(DATA / rel, dtype=str, keep_default_na=False).drop_duplicates().reset_index(drop=True)

def nombres(source):
    """Extraire un nombre en gardant les unités dans les colonnes d'origine."""
    s = source.astype(str).str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(s.str.extract(r"(-?\d+(?:\.\d+)?)", expand=False), errors="coerce")

print('Données du dépôt :', DATA)
print('Aucune source CSV ne sera écrite par ce rapport.')

# %% source-cell=6
reg = lire_csv('public_records/regulatory_case_events.csv')
acc = lire_csv('public_records/site_access_case_events.csv')

suivis = []
for label, table, cle in [
    ('Réglementaires', reg, 'case_number'),
    ('Accès aux sites', acc, 'access_case_number'),
]:
    table = table.copy()
    table['horodatage'] = pd.to_datetime(table['event_time'], format='mixed', errors='coerce')
    durees = (table.groupby(cle)['horodatage'].agg(['min', 'max']))
    jours = (durees['max'] - durees['min']).dt.total_seconds() / 86400
    suivis.append({'Type':label, 'Événements':len(table), 'Dossiers':len(durees),
                   'Durée médiane (jours)':jours.median(), 'Dates manquantes':table['horodatage'].isna().sum()})
bilan_dossiers = pd.DataFrame(suivis)
display(bilan_dossiers)
assert bilan_dossiers['Dossiers'].tolist()==[40,60]
assert bilan_dossiers['Durée médiane (jours)'].tolist()==[18.0,17.0]

# %% source-cell=7
# Suivi de processus : à quelles étapes les événements d'accès correspondent-ils ?
etapes = acc['activity'].str.strip().str.lower().value_counts()
fig, ax = plt.subplots(figsize=(9, 4.1))
etapes.sort_values().plot.barh(ax=ax)
ax.set_title('Étapes consignées dans les dossiers d’accès')
ax.set_xlabel('Nombre d’événements')
ax.set_ylabel('Activité')
ax.grid(axis='x', alpha=0.2)
plt.tight_layout()
plt.show()

# %% source-cell=10
licences = lire_csv('public_records/licensed_professionals.csv')
consultations = lire_csv('health/clinical_encounters.csv')
cle_warden = 'LIC-VLN-MED-1001'
fiche_warden = licences.loc[licences['license_number'].eq(cle_warden),
    ['license_number','professional_name','license_issue_date','license_status']]
usages_warden = consultations.loc[consultations['attending_license_number'].eq(cle_warden)]
print('Licence ancienne :')
display(fiche_warden)
print('Nombre de consultations utilisant cette licence :', usages_warden.encounter_number.nunique())
print('Période :', usages_warden.encounter_start.min(), '→', usages_warden.encounter_start.max())
assert len(fiche_warden)==1 and usages_warden.encounter_number.nunique()==147

# %% source-cell=11
# Réseau biparti simple : relations déclarées entre dirigeants et organisations.
import networkx as nx
mandats = lire_csv('public_records/officer_filings.csv')
G_mandats = nx.Graph()
for _, r in mandats.iterrows():
    personne = 'P: '+r['full_name'].strip()
    organisme = 'O: '+r['registration_number'].strip()
    if r['full_name'].strip() and r['registration_number'].strip():
        G_mandats.add_edge(personne, organisme)

# Un lien est un mandat déclaré, pas une preuve de coordination secrète.
principales = sorted(((n, d) for n,d in G_mandats.degree if n.startswith('O: ')),
                      key=lambda x:x[1], reverse=True)[:8]
top_mandats=pd.DataFrame(principales,columns=['Organisation (n° registre)','Nombre de personnes reliées'])
display(top_mandats)
fig, ax=plt.subplots(figsize=(9,3.4))
ax.barh(top_mandats.iloc[::-1,0],top_mandats.iloc[::-1,1])
ax.set_title('Réseau des mandats : principaux organismes par nombre de liens')
ax.set_xlabel('Dirigeants distincts (liens par nom)')
plt.tight_layout()
plt.show()

# %% source-cell=14
patients = lire_csv('health/patient_administration.csv')
obs = lire_csv('health/clinical_observations.csv')
procedures = lire_csv('health/clinical_procedures.csv')
print('Patients',len(patients),'— consultations',len(consultations),'— observations',len(obs),'— procédures',len(procedures))

# Reproduire la comparaison apicale / périphérique sur les consultations.
mesures = obs[obs['observation_code'].isin(['APICAL','PPULSE'])].copy()
mesures['valeur'] = nombres(mesures['numeric_value'])
cles=['patient_number','encounter_number']
a = mesures.loc[mesures['observation_code'].eq('APICAL'),cles+['valeur','unit']]
p = mesures.loc[mesures['observation_code'].eq('PPULSE'),cles+['valeur','unit']]
paires = a.merge(p,on=cles,validate='one_to_one',suffixes=('_apical','_peripherique'))
paires = paires.loc[
    paires['unit_apical'].eq('bpm') & paires['unit_peripherique'].eq('bpm')
    & paires['valeur_apical'].notna() & paires['valeur_peripherique'].notna()
].copy()
paires['écart_pouls_bpm']=paires['valeur_apical']-paires['valeur_peripherique']
print('Paires de pouls comparables :',len(paires),'patients :',paires.patient_number.nunique())
print('Écart médian (bpm) :',round(paires['écart_pouls_bpm'].median(),2))
assert len(paires)==1017

# %% source-cell=15
# Exemple à relier aux notes cliniques : deux enregistrements de PAT-31065.
# Autocorrélation et pics locaux avec NumPy, sans bibliothèque additionnelle.
records = lire_csv('health/cardiac_recordings.csv')
samples = pd.read_csv(DATA/'health/cardiac_signal_samples.csv')
cas = records.loc[records['patient_number'].eq('PAT-31065')].copy()
assert set(cas.recording_id)=={'CRD-410038','CRD-410005'}
resultats=[]
for _, m in cas.iterrows():
    points = samples.loc[samples.recording_id.eq(m.recording_id)].sort_values('time_ms')
    pas = float(m.sampling_interval_ms)/1000
    for canal,col in [('A','channel_a_normalized'),('B','channel_b_normalized')]:
        x = points[col].to_numpy(dtype=float)
        x = x-x.mean()
        acf = np.correlate(x,x,mode='full')[len(x)-1:]
        acf = acf/acf[0]
        dt = np.arange(len(acf))*pas
        pics=np.flatnonzero((acf[1:-1]>acf[:-2]) & (acf[1:-1]>=acf[2:]))+1
        pics=pics[(dt[pics]>0)&(dt[pics]<=2)]
        meilleur=pics[np.argmax(acf[pics])]
        resultats.append({'Enregistrement':m.recording_id,'Canal':canal,
                          'Période (s)':dt[meilleur], 'Cycles/min':60/dt[meilleur]})
periodes_cardiaques=pd.DataFrame(resultats)
display(periodes_cardiaques.round(2))

# %% source-cell=16
fig,ax=plt.subplots(figsize=(9,3.5))
for rid, grp in periodes_cardiaques.groupby('Enregistrement'):
    ax.scatter(grp['Canal'],grp['Cycles/min'],label=rid,s=95)
ax.set_title('PAT-31065 : périodicités estimées par autocorrélation')
ax.set_xlabel('Canal du signal')
ax.set_ylabel('Motif (cycles par minute)')
ax.legend()
ax.grid(axis='y',alpha=.2)
plt.tight_layout()
plt.show()

# %% source-cell=19
bats = lire_csv('ecology/bat_surveys.csv')
sites = lire_csv('ecology/monitoring_sites.csv')
comparaison_eco = pd.read_csv(ROOT/'exports/ecologie/tableaux/comparaison_acces.csv')
comparaison_eco['groupe'] = np.where(
    comparaison_eco.organization.eq('Horizon Field Research Cooperative'),
    'Horizon','Autres organisations')
bilan_eco = comparaison_eco.groupby('groupe').agg(
    acces=('access_case_number','count'),
    sites=('site_code','nunique'),
    variation_saisonniere_mediane=('difference_saisonniere','median'),
    comparateurs_disponibles=('difference_relative','count'))
print('Sites :',len(sites),'relevés :',len(bats),'accès avec fenêtre complète :',len(comparaison_eco))
print('Avec sites comparables :',comparaison_eco['difference_relative'].notna().sum(),
      'dont Horizon :',comparaison_eco.loc[comparaison_eco.groupe.eq('Horizon'),'difference_relative'].notna().sum())
display(bilan_eco.round(3))
assert len(sites)==64 and len(bats)==4992 and len(comparaison_eco)==39
assert comparaison_eco['difference_relative'].notna().sum()==37
assert comparaison_eco.loc[comparaison_eco.groupe.eq('Horizon'),'difference_relative'].notna().sum()==11

# %% source-cell=20
fig,ax=plt.subplots(figsize=(8.5,4.2))
listes=[comparaison_eco.loc[comparaison_eco.groupe.eq(g),'difference_saisonniere'].dropna()
        for g in ['Horizon','Autres organisations']]
ax.boxplot(listes,tick_labels=['Horizon','Autres'],showmeans=True)
ax.axhline(0,color='gray',linestyle='--',linewidth=1)
ax.set_title('Variations de l’activité après les accès, corrigées de la saisonnalité')
ax.set_ylabel('Après − avant (observations/heure, écart à référence)')
ax.grid(axis='y',alpha=.2)
plt.tight_layout()
plt.show()

# %% source-cell=23
commandes = lire_csv('logistics/purchase_order_lines.csv')
receptions = lire_csv('logistics/goods_receipts.csv')
cles=['purchase_order_number','purchase_order_line']
trace = commandes.merge(receptions,on=cles,how='left',validate='one_to_one',
                        suffixes=('_commande','_reception'),indicator=True)
trace['quantite_commandee']=nombres(trace['ordered_quantity'])
trace['quantite_recue']=nombres(trace['received_quantity'])
recu=trace.loc[trace['_merge'].eq('both')].copy()
comparables=recu.loc[recu['ordered_unit'].eq(recu['received_unit'])].copy()
partielles=comparables.loc[comparables['quantite_recue']<comparables['quantite_commandee']].copy()
partielles['part_manquante_%']=100*(1-partielles.quantite_recue/partielles.quantite_commandee)
resume_receptions=pd.DataFrame([{'Lignes de commande':len(commandes),
    'Avec réception':len(recu),'Sans réception':len(trace)-len(recu),
    'Quantités comparables':len(comparables),
    'Réceptions inférieures':len(partielles),
    'Écart médian des partielles (%)':partielles['part_manquante_%'].median()}])
display(resume_receptions.round(2))
assert len(commandes)==650 and len(recu)==610 and len(partielles)==65

# %% source-cell=24
fig,ax=plt.subplots(figsize=(8.5,3.6))
ax.hist(partielles['part_manquante_%'],bins=9,edgecolor='white')
ax.axvline(partielles['part_manquante_%'].median(),color='tab:red',linestyle='--',label='Médiane')
ax.set_title('Quantité manquante dans les 65 réceptions partielles')
ax.set_xlabel('Part non reçue de la commande (%)')
ax.set_ylabel('Nombre de réceptions')
ax.legend()
plt.tight_layout()
plt.show()

# %% source-cell=25
stocks = lire_csv('logistics/inventory_month_end.csv')
for champ in ['opening_stock','received_quantity','outgoing_quantity','documented_internal_use','documented_waste','closing_stock']:
    stocks[champ+'_num']=nombres(stocks[champ])
theorique=(stocks.opening_stock_num+stocks.received_quantity_num-stocks.outgoing_quantity_num
           -stocks.documented_internal_use_num-stocks.documented_waste_num)
ecart=stocks.closing_stock_num-theorique
print('Relevés de stock :',len(stocks))
print('Écarts à l’équation simplifiée :',int((ecart.abs()>1e-7).sum()))
print('Soldes théoriques négatifs :',int((theorique<0).sum()))
assert len(stocks)==500 and int((ecart.abs()>1e-7).sum())==497

flux = lire_csv('logistics/shipments.csv')
trajets = (flux.groupby(['sender_partner_code','receiver_partner_code']).size()
          .nlargest(8).rename('Envois').reset_index())
trajets['Trajet']=trajets.sender_partner_code+' → '+trajets.receiver_partner_code
classes_temp = flux.temperature_control_class.str.strip().str.lower()
controlees = int(classes_temp.isin(['2-8c', 'frozen']).sum())
print('Expéditions :',len(flux),'— à 2–8 °C :',int(classes_temp.eq('2-8c').sum()),
      '— congelées :',int(classes_temp.eq('frozen').sum()),
      '— total à température contrôlée :',controlees)
assert controlees == 107
display(trajets[['Trajet','Envois']])
assert len(flux)==450

# %% source-cell=28
sources = [
    ('public','public_records/public_and_investigative_documents.csv','title'),
    ('institutionnel','public_records/institutional_memos.csv','subject_line'),
    ('clinique','health/clinical_notes.csv','title'),
    ('ecologie','ecology/environmental_field_reports.csv','title'),
]
docs=[]
for source, chemin, titre in sources:
    d=lire_csv(chemin).copy()
    d['origine']=source
    d['titre_affiche']=d[titre]
    docs.append(d[['document_id','origine','titre_affiche','text']])
corpus = pd.concat(docs,ignore_index=True)
print('Documents :',len(corpus))
display(corpus.groupby('origine').agg(documents=('document_id','size')))
assert len(corpus)==130 and corpus.document_id.nunique()==130

# Quelques textes pivots : extraire exactement les enregistrements, pas les inférer par similarité.
pivots=['PUB-510043','PUB-510033','PUB-510076','PUB-510079','PUB-510063',
        'MEM-510100','MEM-510101','CLN-510025','CLN-510027','EFR-510088']
display(corpus.loc[corpus.document_id.isin(pivots),['document_id','origine','titre_affiche']])

# %% source-cell=29
# Contrôle lexical complémentaire, sans refaire le clustering déjà disponible en partie 6.
# Les mots sont des indices de lecture, pas une preuve de relations entre organisations.
expressions=['CHAMELEO','Unwabu','Eonycteris','Chamaeleonidian','Wren Street']
lignes=[]
for mot in expressions:
    mask=corpus['text'].str.contains(re.escape(mot),case=False,regex=True,na=False)
    comptages=corpus.loc[mask,'origine'].value_counts()
    lignes.append({'Expression':mot,**{x:int(comptages.get(x,0))
                                     for x in corpus.origine.unique()}})
lexique=pd.DataFrame(lignes).set_index('Expression')
display(lexique)
fig,ax=plt.subplots(figsize=(9,3.7))
mat=lexique.to_numpy()
im=ax.imshow(mat,aspect='auto')
ax.set_xticks(np.arange(len(lexique.columns)),lexique.columns)
ax.set_yticks(np.arange(len(lexique.index)),lexique.index)
ax.set_title('Présence de termes du narratif dans les quatre corpus')
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        ax.text(j,i,int(mat[i,j]),ha='center',va='center',color=('white' if mat[i,j]>mat.max()/2 else 'black'))
fig.colorbar(im,ax=ax,label='Documents contenant le terme')
plt.tight_layout()
plt.show()

# %% source-cell=33
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Recherche de la racine du dépôt, sans modifier le répertoire de travail.
racine = next((p for p in [Path.cwd(), *Path.cwd().parents]
               if (p / "data/public_records/site_access_case_events.csv").exists()), None)
if racine is None:
    raise FileNotFoundError("Lancer ce notebook depuis le dépôt du projet Data Mining.")

acces = pd.read_csv(racine / "data/public_records/site_access_case_events.csv",
                    dtype=str, keep_default_na=False).drop_duplicates()
expeditions = pd.read_csv(racine / "data/logistics/shipments.csv",
                          dtype=str, keep_default_na=False).drop_duplicates()

fin_horizon = acces.loc[
    acces["activity"].str.lower().eq("access_completed")
    & acces["requesting_organization_name"].eq("Horizon Field Research Cooperative")
].copy()
fin_horizon["fin_acces"] = pd.to_datetime(fin_horizon["event_time"], format="mixed")
fin_horizon["jour"] = fin_horizon["fin_acces"].dt.date

flux_bio = expeditions.loc[
    expeditions["sender_partner_code"].eq("BP-30056")
    & expeditions["receiver_partner_code"].eq("BP-30078")
    & expeditions["item_category"].eq("biological_sample")
].copy()
flux_bio["depart"] = pd.to_datetime(flux_bio["dispatch_time"], format="mixed")
flux_bio["jour"] = flux_bio["depart"].dt.date

correspondances = fin_horizon.merge(
    flux_bio, on="jour", how="inner", validate="one_to_one", suffixes=("_acces", "_expedition")
)
correspondances["delai_h"] = (
    correspondances["depart"] - correspondances["fin_acces"]
).dt.total_seconds() / 3600

print("Accès Horizon terminés :", len(fin_horizon))
print("Expéditions biologiques Horizon vers Meridian :", len(flux_bio))
print("Correspondances le même jour :", len(correspondances))
print("Délais observés (heures) :", sorted(correspondances["delai_h"].unique()))
print("Températures déclarées :", correspondances["temperature_control_class"].value_counts().to_dict())

affichage = correspondances[[
    "access_case_number", "site_code", "fin_acces", "shipment_number", "depart", "delai_h"
]].sort_values("fin_acces").rename(columns={
    "access_case_number": "Dossier d'accès", "site_code": "Site",
    "fin_acces": "Fin de l'accès", "shipment_number": "Expédition",
    "depart": "Départ", "delai_h": "Délai (h)"
})
display(affichage.head(10))  # dix exemples ; les 18 restent dans 'affichage'
assert len(fin_horizon) == 18 and len(correspondances) == 18
assert correspondances["delai_h"].eq(6).all()

# %% source-cell=34
# Répartition des 18 correspondances par année.
comptage = correspondances["fin_acces"].dt.year.value_counts().sort_index()
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.bar(comptage.index.astype(str), comptage.values)
for pos, valeur in enumerate(comptage.values):
    ax.text(pos, valeur + 0.06, str(valeur), ha="center", fontsize=9)
ax.set_ylim(0, comptage.max() + 1)
ax.set_ylabel("Accès avec expédition le même jour")
ax.set_xlabel("Année")
ax.set_title("Correspondances Horizon–Meridian de 2018 à 2025")
ax.grid(axis="y", alpha=0.2)
plt.tight_layout()
plt.show()

# %% source-cell=35
# Comparer les autres demandeurs d'accès.
terminees = acces.loc[acces["activity"].str.lower().eq("access_completed")].copy()
terminees["fin_acces"] = pd.to_datetime(terminees["event_time"], format="mixed")
terminees["jour"] = terminees["fin_acces"].dt.date
comparaison = terminees.assign(
    horizon=terminees["requesting_organization_name"].eq("Horizon Field Research Cooperative")
).merge(flux_bio[["jour", "shipment_number"]], on="jour", how="left")
resume = (comparaison.groupby("horizon", as_index=False)
          .agg(acces_termines=("access_case_number", "nunique"),
               coincidences_avec_flux_horizon_meridian=("shipment_number", "count")))
resume["Groupe"] = resume["horizon"].map({True: "Horizon", False: "Autres demandeurs"})
display(resume[["Groupe", "acces_termines", "coincidences_avec_flux_horizon_meridian"]])
print("Expéditions Horizon–Meridian biologiques sans accès Horizon le même jour :",
      len(flux_bio) - correspondances["shipment_number"].nunique())
assert len(terminees) == 54
assert len(flux_bio) - correspondances["shipment_number"].nunique() == 2

# %% source-cell=42
acces_connus = set(acces["access_case_number"])
references_acc = [
    "ACC-2019-0005", "ACC-2018-0024", "ACC-2023-0047",
    "ACC-2020-0008", "ACC-2023-0028"
]
controle = pd.DataFrame({
    "Référence": references_acc,
    "Retrouvée dans site_access_case_events.csv": [x in acces_connus for x in references_acc]
})
display(controle)
print("Correspondances retrouvées :", controle.iloc[:, 1].sum(), "/", len(controle))
assert controle.iloc[:, 1].all()
