# Verified references — run_2026-09-19 Phase 10.4

Generated 2026-09-19T16:58:00+00:00 by `scripts/verify_citations.py` from `docs/references/registry.yaml`. Every field below is copied from the PubMed (efetch XML) or Crossref (REST JSON) response that confirmed the entry; nothing is written from memory. Raw responses: `data/processed/run_2026-09-19_scratch/citations/` (untracked). Entries marked *lower confidence* were matched on first author + year (+ journal / keywords) with exactly one candidate returned, because the repo gives no title or identifier; Kyle should eyeball those before they go in a manuscript.

## R01_hagstrom_2021

- **Confirmed by:** PubMed by PMID
- **As cited in repo:** Hagström et al., Hepatology 2021;74(1):474–482, doi:10.1002/hep.31726, PMID 33486773  
  files: `docs/sensitivity_5719.md`, `docs/analysis_plan_prespecified.md`, `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`
- **Authors:** Hagström H, Adams LA, Allen AM, Byrne CD, Chang Y, Grønbaek H, Ismail M, Jepsen P, Kanwal F, Kramer J, Lazarus JV, Long MT, Loomba R, Newsome PN, Rowe IA, Ryu S, Schattenberg JM, Serper M, Sheron N, Simon TG, Tapper EB, Wild S, Wong VW, Yilmaz Y, Zelber-Sagi S, Åberg F
- **Title:** Administrative Coding in Electronic Health Care Record-Based Research of NAFLD: An Expert Panel Consensus Statement
- **Journal:** Hepatology (Baltimore, Md.) (Hepatology)
- **Year:** 2021
- **Volume(issue):pages:** 74(1):474-482
- **DOI:** 10.1002/hep.31726
- **PMID:** 33486773
- **Trail:** efetch by PMID 33486773: 1 record; DOI, first author, year agree

## R02_rinella_2023

- **Confirmed by:** PubMed by PMID
- **As cited in repo:** Rinella ME, Lazarus JV, Ratziu V, et al. A multisociety Delphi consensus statement on new fatty liver disease nomenclature. J Hepatol. 2023 Dec;79(6):1542–1556. doi:10.1016/j.jhep.2023.06.003. PMID: 37364790.  
  files: `docs/sld_subclassification.md`, `scripts/sld_report.py`, `docs/aim1a_crosstab.md`, `scripts/cmrf.py`
- **Authors:** Rinella ME, Lazarus JV, Ratziu V, Francque SM, Sanyal AJ, Kanwal F, Romero D, Abdelmalek MF, Anstee QM, Arab JP, Arrese M, Bataller R, Beuers U, Boursier J, Bugianesi E, Byrne CD, Castro Narro GE, Chowdhury A, Cortez-Pinto H, Cryer DR, Cusi K, El-Kassas M, Klein S, Eskridge W, Fan J, Gawrieh S, Guy CD, Harrison SA, Kim SU, Koot BG, Korenjak M, Kowdley KV, Lacaille F, Loomba R, Mitchell-Thain R, Morgan TR, Powell EE, Roden M, Romero-Gómez M, Silva M, Singh SP, Sookoian SC, Spearman CW, Tiniakos D, Valenti L, Vos MB, Wong VW, Xanthakos S, Yilmaz Y, Younossi Z, Hobbs A, Villota-Rivas M, Newsome PN, NAFLD Nomenclature consensus group
- **Title:** A multisociety Delphi consensus statement on new fatty liver disease nomenclature
- **Journal:** Journal of hepatology (J Hepatol)
- **Year:** 2023
- **Volume(issue):pages:** 79(6):1542-1556
- **DOI:** 10.1016/j.jhep.2023.06.003
- **PMID:** 37364790
- **Trail:** efetch by PMID 37364790: 1 record; DOI, first author, year, title agree

## R03_kahn_2016

- **Confirmed by:** PubMed by DOI
- **As cited in repo:** Kahn MG, Callahan TJ, Barnard J, et al. "A Harmonized Data Quality Assessment Terminology and Framework for the Secondary Use of Electronic Health Record Data." EGEMS (Wash DC). 2016;4(1):1244. doi:10.13063/2327-9214.1244  
  files: `docs/cleaning_spec.md`, `scripts/conformance.py`, `scripts/completeness_differential.py`, `scripts/plausibility_atemporal.py`, `scripts/plausibility_temporal.py`, `scripts/masld_config.py`, `scripts/make_tables.py`
- **Authors:** Kahn MG, Callahan TJ, Barnard J, Bauck AE, Brown J, Davidson BN, Estiri H, Goerg C, Holve E, Johnson SG, Liaw ST, Hamilton-Lopez M, Meeker D, Ong TC, Ryan P, Shang N, Weiskopf NG, Weng C, Zozus MN, Schilling L
- **Title:** A Harmonized Data Quality Assessment Terminology and Framework for the Secondary Use of Electronic Health Record Data
- **Journal:** EGEMS (Washington, DC) (EGEMS (Wash DC))
- **Year:** 2016
- **Volume(issue):pages:** 4(1):1244
- **DOI:** 10.13063/2327-9214.1244
- **PMID:** 27713905
- **Trail:** esearch by DOI 10.13063/2327-9214.1244: exactly 1 record with that DOI; first author, year, title agree

## R04_chapman_2001

- **Confirmed by:** PubMed by title
- **As cited in repo:** Chapman WW, et al. A simple algorithm for identifying negated findings and diseases in discharge summaries. J Biomed Inform. 2001;34(5):301-310.  
  files: `docs/note_phenotype_spec.md`, `scripts/note_phenotype.py`
- **Authors:** Chapman WW, Bridewell W, Hanbury P, Cooper GF, Buchanan BG
- **Title:** A simple algorithm for identifying negated findings and diseases in discharge summaries
- **Journal:** Journal of biomedical informatics (J Biomed Inform)
- **Year:** 2001
- **Volume(issue):pages:** 34(5):301-10
- **DOI:** 10.1006/jbin.2001.1029
- **PMID:** 12123149
- **Trail:** esearch by quoted title returned 0 results | esearch by title: 1 result(s); exactly 1 with an identical normalised title; first author and year agree

## R05_harkema_2009

- **Confirmed by:** PubMed by title
- **As cited in repo:** Harkema H, Dowling JN, Thornblade T, Chapman WW. ConText: An algorithm for determining negation, experiencer, and temporal status from clinical reports. J Biomed Inform. 2009;42(5):839-851.  
  files: `docs/note_phenotype_spec.md`, `scripts/note_phenotype.py`
- **Authors:** Harkema H, Dowling JN, Thornblade T, Chapman WW
- **Title:** ConText: an algorithm for determining negation, experiencer, and temporal status from clinical reports
- **Journal:** Journal of biomedical informatics (J Biomed Inform)
- **Year:** 2009
- **Volume(issue):pages:** 42(5):839-51
- **DOI:** 10.1016/j.jbi.2009.05.002
- **PMID:** 19435614
- **Trail:** esearch by quoted title returned 0 results | esearch by title: 1 result(s); exactly 1 with an identical normalised title; first author and year agree

## R06_quan_2005

- **Confirmed by:** PubMed by author+year+journal (unique candidate; lower confidence)
- **As cited in repo:** Charlson computed from the Quan et al. (2005) ICD-9-CM/ICD-10 coding algorithm (Med Care 43:1130) with standard hierarchy rules and Charlson (1987) weights.  
  files: `scripts/comorbid_cluster.py`, `docs/charlson_validation.md`, `docs/predefinition_descriptives.md`
- **Authors:** Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA
- **Title:** Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data
- **Journal:** Medical care (Med Care)
- **Year:** 2005
- **Volume(issue):pages:** 43(11):1130-9
- **DOI:** 10.1097/01.mlr.0000182534.19832.83
- **PMID:** 16224307
- **Trail:** esearch by author/year [Quan[1au] AND 2005[dp] AND "Med Care"[ta] AND 43[vi] AND 1130[pg] AND ICD-9-CM[tiab] AND ICD-10[tiab] AND comorbidities[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree

## R07_charlson_1987

- **Confirmed by:** PubMed by author+year+keywords (unique candidate; lower confidence)
- **As cited in repo:** Charlson (1987) weights  
  files: `scripts/comorbid_cluster.py`, `docs/charlson_validation.md`
- **Authors:** Charlson ME, Pompei P, Ales KL, MacKenzie CR
- **Title:** A new method of classifying prognostic comorbidity in longitudinal studies: development and validation
- **Journal:** Journal of chronic diseases (J Chronic Dis)
- **Year:** 1987
- **Volume(issue):pages:** 40(5):373-83
- **DOI:** 10.1016/0021-9681(87)90171-8
- **PMID:** 3558716
- **Trail:** esearch by author/year [Charlson[1au] AND 1987[dp] AND comorbidity[tiab] AND index[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year agree

## R11_johnson_2023_mimic_iv

- **Confirmed by:** PubMed by author+year+journal (unique candidate; lower confidence)
- **As cited in repo:** MIMIC-IV v3.1  
  files: `docs/aim1a_loose_ends.md`, `docs/data_quality_report.md`, `docs/note_coverage.md`, `scripts/make_tables.py`, `README.md`
- **Authors:** Johnson AEW, Bulgarelli L, Shen L, Gayles A, Shammout A, Horng S, Pollard TJ, Hao S, Moody B, Gow B, Lehman LH, Celi LA, Mark RG
- **Title:** MIMIC-IV, a freely accessible electronic health record dataset
- **Journal:** Scientific data (Sci Data)
- **Year:** 2023
- **Volume(issue):pages:** 10(1):1
- **DOI:** 10.1038/s41597-022-01899-x
- **PMID:** 36596836
- **Trail:** esearch by author/year [Johnson[1au] AND 2023[dp] AND "Sci Data"[ta] AND MIMIC-IV[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree

## R13_collins_2024_tripod_ai

- **Confirmed by:** PubMed by author+year+journal (unique candidate; lower confidence)
- **As cited in repo:** (not in repo; from task brief)  
  files: —
- **Authors:** Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, Ghassemi M, Liu X, Reitsma JB, van Smeden M, Boulesteix AL, Camaradou JC, Celi LA, Denaxas S, Denniston AK, Glocker B, Golub RM, Harvey H, Heinze G, Hoffman MM, Kengne AP, Lam E, Lee N, Loder EW, Maier-Hein L, Mateen BA, McCradden MD, Oakden-Rayner L, Ordish J, Parnell R, Rose S, Singh K, Wynants L, Logullo P
- **Title:** TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods
- **Journal:** BMJ (Clinical research ed.) (BMJ)
- **Year:** 2024
- **Volume(issue):pages:** 385:e078378
- **DOI:** 10.1136/bmj-2023-078378
- **PMID:** 38626948
- **Trail:** esearch by author/year [Collins[1au] AND 2024[dp] AND "BMJ"[ta] AND TRIPOD[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree
