@echo off
rem Drag-and-drop figure editor (main Figs. 1-6, Extended Data Figs. 1-10). Double-click; switch figures in the page.
rem Also lists QoI Supplementary Fig. 1 (D:\Research\QoI-nc-rev9-20261023\figures\nc\si\figS_order, make_figS_order.py).
"D:\Tools\pur_bridge_env\Scripts\python.exe" "%~dp0figure_tweak.py" --root "%~dp0..\figures" --root "D:\Research\QoI-nc-rev9-20261023\figures\nc\si" %*
pause
