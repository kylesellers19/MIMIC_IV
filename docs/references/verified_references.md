# Verified references — run_2026-11-10 Phase 8 (registry first built in run_2026-09-19 Phase 10.4)

Generated 2026-11-11T03:44:15+00:00 by `scripts/verify_citations.py` from `docs/references/registry.yaml`. Every field below is copied from the PubMed (efetch XML) or Crossref (REST JSON) response that confirmed the entry; nothing is written from memory. Raw responses: `data/processed/run_2026-11-10_scratch/citations/` (untracked). Entries marked *lower confidence* were matched on first author + year (+ journal / keywords) with exactly one candidate returned, because the repo gives no title or identifier; Kyle should eyeball those before they go in a manuscript.

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
  files: `docs/note_phenotype_spec.md`, `scripts/note_phenotype.py`, `docs/llm_review_protocol.md`
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

## R08_vacs_steatosis_nlp_2024

- **Confirmed by:** PubMed by PMID
- **As cited in repo:** VA/VACS-based hepatic-steatosis NLP algorithm (Hepatology Communications, 2024) — basis for anatomical scoping (exact reference to be confirmed by study team).  
  files: `docs/note_phenotype_spec.md`, `docs/llm_review_protocol.md`
- **Authors:** Torgersen J, Skanderson M, Kidwai-Khan F, Carbonari DM, Tate JP, Park LS, Bhattacharya D, Lim JK, Taddei TH, Justice AC, Lo Re V
- **Title:** Identification of hepatic steatosis among persons with and without HIV using natural language processing
- **Journal:** Hepatology communications (Hepatol Commun)
- **Year:** 2024
- **Volume(issue):pages:** 8(7):—
- **DOI:** 10.1097/HC9.0000000000000468
- **PMID:** 38896066
- **Trail:** efetch by PMID 38896066: 1 record; DOI, first author, year agree

## R09_alsentzer_2019_bio_clinicalbert

- **Confirmed by:** Crossref by DOI
- **As cited in repo:** emilyalsentzer/Bio_ClinicalBERT  
  files: `scripts/run0919_embed.py`, `docs/run_2026-09-19/RUN_LOG.md`, `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`, `scripts/aim1b_gold_cv.py`
- **Authors:** Alsentzer Emily, Murphy John, Boag William, Weng Wei-Hung, Jindi Di, Naumann Tristan, McDermott Matthew
- **Title:** Publicly Available Clinical
- **Journal:** Proceedings of the 2nd Clinical Natural Language Processing Workshop; event: Proceedings of the 2nd Clinical Natural Language Processing Workshop
- **Year:** 2019
- **Volume(issue):pages:** —:72-78
- **DOI:** 10.18653/v1/w19-1909
- **PMID:** —
- **Trail:** esearch by DOI 10.18653/v1/W19-1909: 33219 result(s), 0 with that exact DOI | Crossref /works/10.18653/v1/W19-1909: resolves; first author, year agree | PubMed by DOI for PMID enrichment: 0 record(s) with matching DOI and title; PMID left blank

## R10_li_2022_clinical_longformer

- **Confirmed by:** Crossref by DOI
- **As cited in repo:** Clinical-Longformer  
  files: `docs/run_2026-09-19/DECISIONS_FOR_KYLE.md`, `docs/run_2026-09-19/RUN_LOG.md`
- **Authors:** Li Yikuan, Wehbe Ramsey M, Ahmad Faraz S, Wang Hanyin, Luo Yuan
- **Title:** A comparative study of pretrained language models for long clinical text
- **Journal:** Journal of the American Medical Informatics Association
- **Year:** 2022
- **Volume(issue):pages:** 30(2):340-347
- **DOI:** 10.1093/jamia/ocac225
- **PMID:** —
- **Trail:** esearch by DOI 10.1093/jamia/ocac225: 3789 result(s), 0 with that exact DOI | Crossref /works/10.1093/jamia/ocac225: resolves; first author, year agree | PubMed by DOI for PMID enrichment: 0 record(s) with matching DOI and title; PMID left blank

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
- **As cited in repo:** Collins GS et al. TRIPOD+AI. BMJ 2024;385:e078378  
  files: `docs/llm_review_protocol.md`, `docs/tripod_ai_checklist.md`
- **Authors:** Collins GS, Moons KGM, Dhiman P, Riley RD, Beam AL, Van Calster B, Ghassemi M, Liu X, Reitsma JB, van Smeden M, Boulesteix AL, Camaradou JC, Celi LA, Denaxas S, Denniston AK, Glocker B, Golub RM, Harvey H, Heinze G, Hoffman MM, Kengne AP, Lam E, Lee N, Loder EW, Maier-Hein L, Mateen BA, McCradden MD, Oakden-Rayner L, Ordish J, Parnell R, Rose S, Singh K, Wynants L, Logullo P
- **Title:** TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods
- **Journal:** BMJ (Clinical research ed.) (BMJ)
- **Year:** 2024
- **Volume(issue):pages:** 385:e078378
- **DOI:** 10.1136/bmj-2023-078378
- **PMID:** 38626948
- **Trail:** esearch by author/year [Collins[1au] AND 2024[dp] AND "BMJ"[ta] AND TRIPOD[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree

## R14_gallifant_2025_tripod_llm

- **Confirmed by:** PubMed by DOI
- **As cited in repo:** Gallifant J et al. TRIPOD-LLM. *Nat Med* 2025;31:60–69. doi:10.1038/s41591-024-03425-5  
  files: `docs/llm_review_protocol.md`
- **Authors:** Gallifant J, Afshar M, Ameen S, Aphinyanaphongs Y, Chen S, Cacciamani G, Demner-Fushman D, Dligach D, Daneshjou R, Fernandes C, Hansen LH, Landman A, Lehmann L, McCoy LG, Miller T, Moreno A, Munch N, Restrepo D, Savova G, Umeton R, Gichoya JW, Collins GS, Moons KGM, Celi LA, Bitterman DS
- **Title:** The TRIPOD-LLM reporting guideline for studies using large language models
- **Journal:** Nature medicine (Nat Med)
- **Year:** 2025
- **Volume(issue):pages:** 31(1):60-69
- **DOI:** 10.1038/s41591-024-03425-5
- **PMID:** 39779929
- **Trail:** esearch by DOI 10.1038/s41591-024-03425-5: exactly 1 record with that DOI; first author, year agree

## R15_miao_2025_mi_claim_gen

- **Confirmed by:** PubMed by DOI
- **As cited in repo:** Miao BY et al. MI-CLAIM-GEN. *Nat Med* 2025;31:1394–1398. doi:10.1038/s41591-024-03470-0  
  files: `docs/llm_review_protocol.md`
- **Authors:** Miao BY, Chen IY, Williams CYK, Davidson J, Garcia-Agundez A, Sun S, Zack T, Saria S, Arnaout R, Quer G, Sadaei HJ, Torkamani A, Beaulieu-Jones B, Yu B, Gianfrancesco M, Butte AJ, Norgeot B, Sushil M
- **Title:** The MI-CLAIM-GEN checklist for generative artificial intelligence in health
- **Journal:** Nature medicine (Nat Med)
- **Year:** 2025
- **Volume(issue):pages:** 31(5):1394-1398
- **DOI:** 10.1038/s41591-024-03470-0
- **PMID:** 39915678
- **Trail:** esearch by DOI 10.1038/s41591-024-03470-0: exactly 1 record with that DOI; first author, year agree

## R17_vong_2025_incidental_steatosis_llm

- **Confirmed by:** PubMed by author+year+journal (unique candidate; lower confidence)
- **As cited in repo:** Vong T et al. Incidental hepatic steatosis on ED imaging using LLMs. *Hepatol Commun* 2025;9:e0638  
  files: `docs/llm_review_protocol.md`
- **Authors:** Vong T, Rizer N, Jain V, Thompson VL, Dredze M, Klein EY, Hinson JS, Purnell T, Kwak S, Woreta T, Strauss AT
- **Title:** Automated identification of incidental hepatic steatosis on Emergency Department imaging using large language models
- **Journal:** Hepatology communications (Hepatol Commun)
- **Year:** 2025
- **Volume(issue):pages:** 9(3):—
- **DOI:** 10.1097/HC9.0000000000000638
- **PMID:** 39969431
- **Trail:** esearch by author/year [Vong[1au] AND 2025[dp] AND "Hepatol Commun"[ta] AND 9[vi] AND e0638[pg] AND steatosis[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree

## R18_john_2025_masld_nlp_valid

- **Confirmed by:** PubMed by author+year+journal (unique candidate; lower confidence)
- **As cited in repo:** John BV et al. MASLD by NLP (VALID). *Am J Gastroenterol* 2025;120:2583–91  
  files: `docs/llm_review_protocol.md`
- **Authors:** John BV, Bastaich D, Mezzacappa C, Ferreira RD, Hentschel A, Samos A, Mahmud N, Taddei TH, Kaplan D, Serper M, Dahman B, Veterans Analysis of Liver Disease (VALID) group of investigators
- **Title:** Identifying Metabolic Dysfunction-Associated Steatotic Liver Disease Using Natural Language Processing in a US National Cohort
- **Journal:** The American journal of gastroenterology (Am J Gastroenterol)
- **Year:** 2025
- **Volume(issue):pages:** 120(11):2583-2591
- **DOI:** 10.14309/ajg.0000000000003321
- **PMID:** 39950372
- **Trail:** esearch by author/year [John[1au] AND 2025[dp] AND "Am J Gastroenterol"[ta] AND 120[vi] AND 2583[pg] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree

## R19_van_vleck_2019_nlp_nafld

- **Confirmed by:** PubMed by author+year+journal (unique candidate; lower confidence)
- **As cited in repo:** Van Vleck TT et al. NLP for NAFLD. *Int J Med Inform* 2019;129:334–41  
  files: `docs/llm_review_protocol.md`
- **Authors:** Van Vleck TT, Chan L, Coca SG, Craven CK, Do R, Ellis SB, Kannry JL, Loos RJF, Bonis PA, Cho J, Nadkarni GN
- **Title:** Augmented intelligence with natural language processing applied to electronic health records for identifying patients with non-alcoholic fatty liver disease at risk for disease progression
- **Journal:** International journal of medical informatics (Int J Med Inform)
- **Year:** 2019
- **Volume(issue):pages:** 129:334-341
- **DOI:** 10.1016/j.ijmedinf.2019.06.028
- **PMID:** 31445275
- **Trail:** esearch by author/year [Van Vleck[1au] AND 2019[dp] AND "Int J Med Inform"[ta] AND 129[vi] AND 334[pg] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree

## R20_wiest_2024_privacy_preserving_llm

- **Confirmed by:** PubMed by author+year+journal (unique candidate; lower confidence)
- **As cited in repo:** Wiest IC et al. Privacy-preserving LLMs on MIMIC-IV. *npj Digit Med* 2024;7:257  
  files: `docs/llm_review_protocol.md`
- **Authors:** Wiest IC, Ferber D, Zhu J, van Treeck M, Meyer SK, Juglan R, Carrero ZI, Paech D, Kleesiek J, Ebert MP, Truhn D, Kather JN
- **Title:** Privacy-preserving large language models for structured medical information retrieval
- **Journal:** NPJ digital medicine (NPJ Digit Med)
- **Year:** 2024
- **Volume(issue):pages:** 7(1):257
- **DOI:** 10.1038/s41746-024-01233-2
- **PMID:** 39304709
- **Trail:** esearch by author/year [Wiest[1au] AND 2024[dp] AND "NPJ Digit Med"[ta] AND 7[vi] AND 257[pg] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree

## R21_mukherjee_2023_vicuna_radiology

- **Confirmed by:** PubMed by author+year+journal (unique candidate; lower confidence)
- **As cited in repo:** Mukherjee P et al. Vicuna for labeling radiology reports. *Radiology* 2023;309:e231147  
  files: `docs/llm_review_protocol.md`
- **Authors:** Mukherjee P, Hou B, Lanfredi RB, Summers RM
- **Title:** Feasibility of Using the Privacy-preserving Large Language Model Vicuna for Labeling Radiology Reports
- **Journal:** Radiology (Radiology)
- **Year:** 2023
- **Volume(issue):pages:** 309(1):e231147
- **DOI:** 10.1148/radiol.231147
- **PMID:** 37815442
- **Trail:** esearch by author/year [Mukherjee[1au] AND 2023[dp] AND "Radiology"[ta] AND 309[vi] AND e231147[pg] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: exactly 1 result; first author, year, journal agree

## R23_egami_2023_imperfect_surrogates

- **Confirmed by:** Crossref by author+year+keywords (unique candidate; lower confidence)
- **As cited in repo:** Egami N et al. Using imperfect surrogates for downstream inference. NeurIPS 2023 (arXiv:2306.04746)  
  files: `docs/llm_review_protocol.md`
- **Authors:** Egami Naoki, Hinck Musashi, Stewart Brandon, Wei Hanying
- **Title:** Using Imperfect Surrogates for Downstream Inference: Design-based Supervised Learning for Social Science Applications of Large Language Models
- **Journal:** Advances in Neural Information Processing Systems 36; event: Advances in Neural Information Processing Systems 36
- **Year:** 2023
- **Volume(issue):pages:** —:68589-68601
- **DOI:** 10.52202/075280-3000
- **PMID:** —
- **Trail:** esearch by author/year [Egami[1au] AND 2023[dp] AND surrogates[tiab] NOT "published erratum"[pt] NOT "retraction of publication"[pt]]: 0 result(s) — not exactly one, rejected | Crossref by author/year [Egami 2023  surrogates]: 5 candidates, exactly 1 passes first-author+year+keyword filter: 'Using Imperfect Surrogates for Downstream Inference: Design-based Supe' (2023, proceedings-article) | PubMed by DOI for PMID enrichment: 0 results; PMID left blank
