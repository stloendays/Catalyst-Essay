"""Builds eval/field_mismatch_review.csv: one row per strict field mismatch (adjudicated), with the PDF
reading and the failure mode. Plot readings below are my own readings of the PDF figures at 4x render."""
import pandas as pd

BASE = 'D:/论文-AI4S/Catalyst-Essay/agent/extraction/'
f = pd.read_csv(BASE + 'eval/field_scores.csv')
e = pd.read_csv(BASE + 'out/records_normalized.csv')
f = f[(f.truth == 'adjudicated') & (f.strict == 'wrong')].copy()
f['T_K'] = f.ex_id.map(e.T_K).round(0)
M = 32.042e-3  # mmol -> g

TS = [513, 533, 553, 573]
cphc_X = {'In0.12Cr1.88O3': [1.45, 1.8, 2.2, 3.5], 'In0.25Cr1.75O3': [1.75, 3.25, 4.75, 7.25],
          'In0.72Cr1.28O3': [2.15, 3.65, 5.55, 8.2], 'In1.25Cr0.75O3': [3.9, 5.5, 7.8, 12.4],
          'In1.67Cr0.33O3': [3.25, 4.2, 6.6, 9.1], 'In2O3': [0.35, 2.75, 3.35, 7.0]}
cphc_STY = {'In0.12Cr1.88O3': [.51, .62, .76, 1.22], 'In0.25Cr1.75O3': [.57, .81, 1.02, 1.01],
            'In0.72Cr1.28O3': [.29, .95, 1.20, 1.29], 'In1.25Cr0.75O3': [1.20, 1.56, 1.64, 2.03],
            'In1.67Cr0.33O3': [1.12, 1.15, 1.24, 1.47], 'In2O3': [.12, .57, .43, .72]}
TS5 = [523, 533, 543, 553, 563]
acs_S = {'bulk In2O3 (In2O3-b)': [69.3, 67, 63.2, 60.6, 55.7], 'In10/ZrO2': [76, 73.5, 70.3, 66, 60.8],
         'In5/ZrO2': [78, 75.5, 72.8, 68.2, 61.7], 'In2.5/ZrO2': [73.8, 72, 67, 60, 51],
         'In1/ZrO2': [64, 58.2, 55.7, 49.5, 42.8], 'In0.5/ZrO2': [50.3, 46.8, 44, 38.8, 32.4],
         'In0.1/ZrO2': [23.1, 23.8, 21.4, 21.4, 20.5]}
acs_S280_bar = {'In0.25/ZrO2': 27.0}  # Fig. 5b diamonds at 280 C
acs_STY553 = {'In0.1/ZrO2': .37, 'In0.25/ZrO2': .54, 'In0.5/ZrO2': 1.21, 'In1/ZrO2': 1.61, 'In2.5/ZrO2': 2.25, 'In5/ZrO2': 2.00}


def nearest(table, ts, val):
    best = min(((abs(v - val), k, t) for k, vs in table.items() for t, v in zip(ts, vs)))
    return best[1], best[2]


rows = []
for _, r in f.iterrows():
    doi, cat, fld, T = r.doi, r.catalyst, r.field, int(r.T_K)
    ext, cur = r.extracted, r.curated
    reading, mode, note = None, None, ''
    if doi == '10.1002/cphc.202300530':
        tab, fs, scale, loc = (cphc_X, 14, 1, 'p7 Fig. 9a') if fld == 'X_CO2' else (cphc_STY, 3.0, M, 'p7 Fig. 9b')
        i = TS.index(T)
        reading = tab[cat][i] * scale
        if abs(ext - reading) <= 0.05 * fs * scale:
            mode = 'plot_precision'
        else:
            k, t = nearest({c: [v * scale for v in vs] for c, vs in tab.items()}, TS, ext)
            mode = 'series_or_point_confusion' if (k, t) != (cat, T) else 'plot_precision'
            note = f'extracted value lies on {k} at {t} K' if (k, t) != (cat, T) else ''
        reading_txt = f'{tab[cat][i]}' + (' mmol g-1 h-1' if fld == 'STY' else ' %')
    elif doi == '10.1021/acscatal.9b01869' and fld == 'S_MeOH':
        loc = 'p6 Fig. 5a/5b'
        if cat in acs_S:
            reading = acs_S[cat][TS5.index(T)]
            if abs(ext - reading) <= 2.0:
                mode = 'plot_precision'
            else:
                k, t = nearest(acs_S, TS5, ext)
                mode = 'series_or_point_confusion'
                note = f'extracted value lies on {k} at {t} K'
        else:  # In0.25/ZrO2 is not plotted in Fig. 5a
            reading = acs_S280_bar.get(cat) if T == 553 else None
            k, t = nearest(acs_S, TS5, ext)
            mode = 'series_or_point_confusion'
            note = f'In0.25/ZrO2 has no curve in Fig. 5a; extracted value lies on {k} at {t} K'
        reading_txt = '' if reading is None else f'{reading} %'
    elif doi == '10.1021/acscatal.9b01869' and fld == 'STY':
        loc = 'p6 Fig. 5b'
        reading = acs_STY553[cat] * M
        reading_txt = f'{acs_STY553[cat]} mmol g-1 h-1'
        if abs(cur - reading) > 0.05 * 3.0 * M * 0.5 and abs(ext - reading) <= abs(cur - reading):
            mode = 'unresolved_figure_vs_SI'
            note = 'TheMeCat (SI Table S5) differs from the main-text bar; extraction is closer to the bar'
        else:
            mode = 'plot_precision'
    else:
        reading_txt = ''
        loc = ''
    rows.append(dict(doi=doi, ex_id=r.ex_id, catalyst=cat, T_K=T, field=fld, extracted=round(ext, 5),
                     themecat_adjudicated=cur, pdf_reading=reading_txt, pdf_location=loc,
                     failure_mode=mode, note=note))

out = pd.DataFrame(rows)
manual = {
    # anie Fig. 4a bars (p8): CP-CP 72.5, AP-AP 76, PD-PD 88 % methanol selectivity
    ('10.1002/anie.202401168', 'Ir1Pd1-In2O3(CP-CP)', 'S_MeOH'): ('72.5 %', 'p8 Fig. 4a', 'plot_precision', ''),
    ('10.1002/anie.202401168', 'Ir1Pd1-In2O3(AP-AP)', 'S_MeOH'): ('76 %', 'p8 Fig. 4a', 'plot_precision', ''),
    ('10.1002/anie.202401168', 'Ir1Pd1-In2O3(PD-PD)', 'S_MeOH'): ('88 %', 'p8 Fig. 4a', 'plot_precision', ''),
    ('10.1002/anie.202401168', 'Ir1Pd1-In2O3(PM)', 'S_MeOH'): ('73.5 %', 'p8 Fig. 4a', 'series_or_point_confusion', 'GM and PM bars swapped (extracted PM = GM bar 5.9 / 69)'),
    ('10.1002/anie.202401168', 'Ir1Pd1-In2O3(PM)', 'X_CO2'): ('6.5 %', 'p8 Fig. 4a', 'series_or_point_confusion', 'GM and PM bars swapped'),
    ('10.1002/anie.202401168', 'Ir1Pd1-In2O3(GM)', 'S_MeOH'): ('68.5 %', 'p8 Fig. 4a', 'series_or_point_confusion', 'GM and PM bars swapped and selectivity misread (87)'),
    ('10.1002/anie.202401168', 'Ir1Pd1-In2O3(GM)', 'X_CO2'): ('5.85 %', 'p8 Fig. 4a', 'series_or_point_confusion', 'GM and PM bars swapped'),
    ('10.1002/anie.202401168', 'Ir1Pd1-In2O3(CP-PD)', 'STY'): ('43.7 / 187.1 g gmetal-1 h-1 printed (p7, p9); Ir 0.44 + Pd 0.25 wt% (p9)', 'p7, p9 text', 'basis_derivation', 'paper prints STY per g metal; per g catalyst = x 0.69 wt%. TheMeCat values imply 0.67-0.68 wt%'),
    ('10.1002/ente.201800747', 'Cat-1.5', 'STY'): ('0.14 g g-1 h-1 printed (p5 text, p4 Fig. 4c bar label)', 'p5 text', 'rounded_main_text', 'TheMeCat 0.1472 from SI Table S1'),
    ('10.1002/ente.201800747', 'Cat-4.5', 'STY'): ('0.20 g g-1 h-1 printed (p1 abstract, p5 text)', 'p5 text', 'rounded_main_text', 'TheMeCat 0.2139 from SI Table S1'),
    ('10.1002/ente.201800747', 'Cat-6.0', 'STY'): ('0.11 g g-1 h-1 printed (p5 text)', 'p5 text', 'rounded_main_text', 'TheMeCat 0.1124 from SI Table S1'),
    ('10.1002/ente.201800747', 'Cat-3.0', 'STY'): ('0.16 printed on the Fig. 4c bar (p4)', 'p4 Fig. 4c', 'rounded_main_text', 'TheMeCat 0.1707 from SI Table S1'),
    ('10.1039/c2cy20604h', 'Cu/Al2O3', 'S_MeOH'): ('Fig. 6 reading', 'p6 Fig. 6', 'plot_precision', 'first batch'),
    ('10.1039/c2cy20604h', 'Cu–Ba/Al2O3', 'S_MeOH'): ('Fig. 8 reading', 'p7 Fig. 8', 'plot_precision', 'first batch'),
}
for i, r in out.iterrows():
    key = (r.doi, r.catalyst, r.field)
    if key in manual:
        out.loc[i, ['pdf_reading', 'pdf_location', 'failure_mode', 'note']] = manual[key]

# ---- batch 3 (Elsevier papers): classified by hand against the PDF, keyed by (doi, ex_id, field);
# ex_id is the row of out/records_normalized.csv for the 20-paper set ----
PP, CONF, ROUND, UNRES, BASIS, INCONS, TROUND = ('plot_precision', 'series_or_point_confusion', 'rounded_main_text',
    'unresolved_figure_vs_SI', 'basis_derivation', 'paper_internal_inconsistency', 'themecat_rounding')
b3 = {
    ('10.1016/j.cej.2022.135090', 70, 'S_MeOH'): ('Fig. 2b p5: about 1.0 %', CONF, 'extracted S(CH3OH) series rises 0.2 -> 0.9 % with T; the plotted bars fall (0, 1.0, 0.8, 0.9, 0.7, 0.6, 0.5 %)'),
    ('10.1016/j.cej.2022.135090', 75, 'S_MeOH'): ('Fig. 2b p5: about 0.5 %', CONF, 'same reversed series'),
    ('10.1016/j.cej.2022.135090', 71, 'X_CO2'): ('Fig. 2c p5: 7.3 %', PP, ''),
    ('10.1016/j.cej.2022.135090', 74, 'X_CO2'): ('Fig. 2c p5: 17.6 %; Fig. 8b p12 (same 2:1 bed): 22.3 %', INCONS, 'the paper plots two different conversions for the same bed and condition; TheMeCat took Fig. 2c'),
    ('10.1016/j.cej.2022.135090', 75, 'X_CO2'): ('p11 text: 25 % CO2 conversion', ROUND, 'TheMeCat 26 read from Fig. 2c'),
    ('10.1016/j.fuel.2022.125878', 88, 'S_MeOH'): ('p8 text: 68 % (rounded)', ROUND, 'TheMeCat 68.8 read from Fig. 10'),
    ('10.1016/j.jcat.2012.05.020', 118, 'GHSV'): ('p11 Table 2: 10 mmol gcat-1 min-1', BASIS, 'molar space velocity; 22.414 NL/mol (0 C) gives 13.4, TheMeCat uses about 24.4 L/mol (25 C) = 14.6'),
    ('10.1016/j.jcat.2012.05.020', 119, 'GHSV'): ('p11 Table 2: 10 mmol gcat-1 min-1', BASIS, 'as above'),
    ('10.1016/j.jcat.2012.05.020', 120, 'GHSV'): ('p11 Table 2: 10 mmol gcat-1 min-1', BASIS, 'as above'),
    ('10.1016/j.jcat.2012.05.020', 120, 'STY'): ('p11 Table 2: 0.3 umol min-1 gcat-1 = 0.000577 g g-1 h-1', TROUND, 'TheMeCat stores 4 decimals (0.0006)'),
    ('10.1016/j.jcat.2020.01.014', 151, 'S_MeOH'): ('Fig. 1b-2 p4: 78.5 %', PP, ''),
    ('10.1016/j.jes.2023.05.010', 164, 'S_MeOH'): ('Fig. 6a p9: 64.5 %', PP, ''),
    ('10.1016/j.jes.2023.05.010', 165, 'S_MeOH'): ('Fig. 6a p9: about 54 %', CONF, 'extracted 60 % is the Au/In2O3-NS point (58-60 %) at 300 C'),
    ('10.1016/j.jes.2023.05.010', 170, 'S_MeOH'): ('Fig. 6a p9: 56 %', PP, ''),
    ('10.1016/j.jes.2023.05.010', 169, 'STY'): ('Fig. 6b p9: 0.089', PP, ''),
    ('10.1016/j.jscs.2019.09.002', 171, 'STY'): ('p6 Table 2: 48 mmol/kgcat.h', INCONS, 'printed methanol yield is about 3x X x S x F from the same table; TheMeCat recomputes it'),
    ('10.1016/j.jscs.2019.09.002', 172, 'STY'): ('p6 Table 2: 660 mmol/kgcat.h', INCONS, 'printed yield 2.7x X x S x F; TheMeCat recomputes it'),
    ('10.1016/j.jscs.2019.09.002', 173, 'STY'): ('p7 Table 3: 777 mmol/kgcat.h', INCONS, 'as above'),
    ('10.1016/j.jscs.2019.09.002', 174, 'STY'): ('p7 Table 3/4: 1703 mmol/kgcat.h', INCONS, 'as above'),
    ('10.1016/j.jscs.2019.09.002', 175, 'STY'): ('p8 Table 4: 1194 mmol/kgcat.h', INCONS, 'as above'),
}
chou_plot = {44: 0.14, 46: 0.465, 47: 0.377, 48: 0.08, 49: 0.163, 51: 0.42, 52: 0.072, 53: 0.133, 54: 0.234, 55: 0.37,
             56: 0.062, 57: 0.115, 58: 0.208, 59: 0.33, 60: 0.148, 61: 0.241, 62: 0.345, 63: 0.42}
for k, v in chou_plot.items():
    b3[('10.1016/j.apcata.2019.117144', k, 'STY')] = (f'Fig. 5c p6 (Table 1 p3 at 573 K and 3La 543 K): {v} g gcat-1 h-1', INCONS,
        "the paper's methanol rates are about 25-30 % below its own X x S x F (e.g. In2O3/ZrO2 573 K: 0.465 printed vs 0.64); TheMeCat recomputes from X x S x F, the extraction follows the paper")
b3[('10.1016/j.apcata.2019.117144', 50, 'STY')] = ('Fig. 5c p6: 0.27 g gcat-1 h-1', PP, 'extracted 0.30')
for k, v in {54: 80, 58: 81, 59: 74}.items():
    b3[('10.1016/j.apcata.2019.117144', k, 'S_MeOH')] = (f'Fig. 5b p6: {v} %', PP, '')
hou_sty = {156: 0.008, 157: 0.019, 158: 0.078, 162: 0.017, 165: 0.189, 166: 0.006, 167: 0.015, 168: 0.035, 170: 0.156}
for k, v in hou_sty.items():
    b3[('10.1016/j.jes.2023.05.010', k, 'STY')] = (f'Fig. 6b p9: {v} g/(hr gcat)', UNRES,
        'TheMeCat computes STY from X x S x feed instead of using the plotted bars; extraction follows the bars (difference below the 5 % of axis threshold used for errata)')
for _, r in f.iterrows():
    pass
for i, r in out.iterrows():
    key = (r.doi, int(r.ex_id), r.field)
    if key in b3:
        out.loc[i, ['pdf_reading', 'failure_mode', 'note']] = b3[key]
        out.loc[i, 'pdf_location'] = b3[key][0].split(':')[0]
    elif r.doi in ('10.1016/j.fuel.2023.127927', '10.1016/j.jes.2023.05.010') and pd.isna(r.failure_mode):
        out.loc[i, ['pdf_reading', 'pdf_location', 'failure_mode', 'note']] = (
            'Zaman Fig. 6A/7b p7-8' if 'fuel' in r.doi else 'Hou Fig. 6a p9', 'figure', PP,
            'right series and point; reading error' + (' (TheMeCat reading also differs from the plot)' if r.field == 'X_CO2' else ''))

# ---- recall passes (figures, SI, SI figures): a value that comes from another pass, or a row created by one,
# is classified here and overrides the batch 1-3 key (whose value may have been replaced by the merge) ----
AXIS = 'axis_misread'
rec = pd.read_csv(BASE + 'out/records_normalized.csv')
fs_all = pd.read_csv(BASE + 'eval/field_scores.csv')
fs_all = fs_all[(fs_all.truth == 'adjudicated')]


def from_new_pass(ex_id, field):
    row = rec.loc[ex_id]
    filled = row['filled'] if isinstance(row['filled'], str) else ''
    return row['pass'] != 'main' or (field + '<-') in filled


RP = {  # (doi, ex_id, field): (pdf reading, mode, note)
    ('10.1016/j.apcatb.2017.06.069', 416, 'S_MeOH'): ('Fig. 1a p3: In2O3 at 200 C, X = 0', UNRES, 'TheMeCat stores S = 0 where conversion is zero; the extraction read the plotted 99 %'),
    ('10.1016/j.fuel.2022.125878', 86, 'STY'): ('Fig. 11 p9 (dual STY axes)', UNRES, 'In2O3 STY axis assignment cannot be fixed from the figure'),
    ('10.1016/j.fuel.2022.125878', 450, 'S_MeOH'): ('Fig. 10b p9: In2O3 98 % at 493 K', CONF, 'extracted 60 % belongs to another series'),
    ('10.1016/j.fuel.2022.125878', 456, 'S_MeOH'): ('Fig. 10b p9: In1/CeO2 64 % at 553 K', PP, 'extraction closer to the plot than TheMeCat (62.4)'),
    ('10.1016/j.jcat.2020.01.014', 151, 'STY'): ('Fig. 1b-1 p4: 1.65 mol kg-1 h-1', PP, ''),
}
for k in (417, 418, 419, 420, 421, 422, 423):
    RP[('10.1016/j.apcatb.2017.06.069', k, 'S_MeOH')] = ('Fig. 1a p3 (selectivity on the right axis, 0-100)', AXIS,
                                                         'extracted selectivity is 4-5 pp off on the right-hand axis; TheMeCat matches the plot')
    RP[('10.1016/j.apcatb.2017.06.069', k, 'STY')] = ('Fig. 1b p3', UNRES,
                                                      'extraction equals the plotted STY (0.01-0.79); TheMeCat recomputes STY and differs by 5-10 %, below the errata threshold')
for k in (458, 459, 460, 462, 463):
    RP[('10.1016/j.fuel.2022.125878', k, 'S_MeOH')] = ('Fig. 10b p9 (red series on the right axis)', AXIS,
                                                       'the figure pass read the red ZrO2 / In1/ZrO2 series on the left axis; adjudicated values use the right axis')
for k in (482, 486, 488):
    RP[('10.1126/sciadv.1701290', k, 'S_MeOH')] = ('Fig. 1A p2', CONF, 'composition labels shifted along the x axis (a 17 % point was invented, 29/38 % skipped)')
for k in (495, 497):
    RP[('10.1126/sciadv.1701290', k, 'S_MeOH')] = ('Fig. 1B p2', PP, '2-3 pp reading error')
for k, f in ((570, 'S_MeOH'), (572, 'X_CO2'), (573, 'X_CO2'), (574, 'X_CO2'), (574, 'S_MeOH'), (576, 'X_CO2')):
    RP[('10.1126/sciadv.1701290', k, f)] = ('SI p4 fig. S2 (broken right axis: 0-10 for X, 40-90 for S)', AXIS,
                                            'X read about 30 % high on the broken axis; TheMeCat (4.0/6.2/8.1/9.6/11.0 %) matches the plot')
for k in range(540, 560):
    RP[('10.1016/j.jes.2023.05.010', k, 'S_MeOH')] = ('SI Fig. S4 p10', PP, 'both values are readings of the same SI plot (difference up to 4.3 pp)')

keep = []
for i, r in out.iterrows():
    if from_new_pass(int(r.ex_id), r.field):
        key = (r.doi, int(r.ex_id), r.field)
        loose = fs_all[(fs_all.ex_id == r.ex_id) & (fs_all.field == r.field)].loose.iloc[0]
        if key in RP:
            out.loc[i, ['pdf_reading', 'failure_mode', 'note']] = RP[key]
        elif loose == 'correct':
            out.loc[i, ['pdf_reading', 'failure_mode', 'note']] = ('', PP, 'value from a recall pass, within the loose tolerance')
        else:
            out.loc[i, ['pdf_reading', 'failure_mode', 'note']] = ('', 'unreviewed', '')
        out.loc[i, 'pass_origin'] = rec.loc[int(r.ex_id), 'pass'] if rec.loc[int(r.ex_id), 'pass'] != 'main' else 'filled'
out.to_csv(BASE + 'eval/field_mismatch_review.csv', index=False)
print('recall-pass rows:', out['pass_origin'].notna().sum() if 'pass_origin' in out else 0)
print(out.failure_mode.value_counts(dropna=False))
print(out.groupby(['doi', 'failure_mode']).size())
print(out[out.failure_mode.isna()])
