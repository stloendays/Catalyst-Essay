"""Figures generated only from the corrected unfrozen source-kinetics experiment."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from run_v2 import compare,critical_gain,thermochemistry

OUT=Path(__file__).resolve().parent/"results_v2"
OUT.mkdir(parents=True,exist_ok=True)
gains=np.linspace(1,16,61)
runs=[compare(80.,30.,30.,float(g)) for g in gains]
fig,ax=plt.subplots(figsize=(8.6,5.5))
for key,name in [("all_Fe","All Fe"),("Fe_then_Ru","Fe -> Ru/CeO2"),
                 ("Ru_then_Fe","Ru/CeO2 -> Fe"),("all_Ru","All Ru/CeO2")]:
    ax.plot(gains,[100*r[key] for r in runs],linewidth=2.2,label=name)
parity=critical_gain(80.,30.,30.)
ax.axvline(parity,ls="--",lw=1.2)
ax.annotate(f"Model parity: {parity:.2f}x",xy=(parity,16.7),xytext=(8.7,14.0),
    arrowprops={"arrowstyle":"->"})
ax.set(xlabel="Unmeasured multiplier on Ru/CeO2 fitted rate",
       ylabel="Single-pass N2 conversion (%)",
       title="Conditional bed-order mechanism, 80 bar(abs), 425 C")
ax.grid(alpha=.2)
ax.legend(frameon=False)
fig.text(.11,.015,"60 kg total, Fe and Ru each 30 kg when mixed; no industrial KAAP inference.",fontsize=9)
fig.tight_layout(rect=[0,.04,1,1])
fig.savefig(OUT/"kinetic_conditional_bed_order.png",dpi=200)
fig.savefig(OUT/"kinetic_conditional_bed_order.svg")
plt.close(fig)

temps=(400.,425.,450.)
vals=[thermochemistry(t+273.15) for t in temps]
fig,ax=plt.subplots(figsize=(7.8,5))
ax.plot(temps,[100*r["yNH3_NIST"] for r in vals],marker="o",label="NIST Shomate")
ax.plot(temps,[100*r["yNH3_GB"] for r in vals],marker="s",label="Gillespie-Beattie")
ax.set(xlabel="Temperature (C)",ylabel="Equilibrium NH3 mole fraction (%)",
       title="Independent Gibbs reference check, 90 bar(abs)")
ax.grid(alpha=.2)
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT/"thermodynamics_NIST_GB.png",dpi=200)
fig.savefig(OUT/"thermodynamics_NIST_GB.svg")
plt.close(fig)
print("UNFROZEN diagnostic figures generated")
