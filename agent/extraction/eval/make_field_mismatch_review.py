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
out.to_csv(BASE + 'eval/field_mismatch_review.csv', index=False)
print(out.failure_mode.value_counts(dropna=False))
print(out.groupby(['doi', 'failure_mode']).size())
print(out[out.failure_mode.isna()])
