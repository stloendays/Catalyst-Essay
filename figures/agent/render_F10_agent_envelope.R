#!/usr/bin/env Rscript

# Figure 10 — Agent capability-bounded operating envelope with oracle normalization
# 2026-09-20 supervisor update. Reads frozen C1 panel data + oracle summary only.

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args) >= 1) args[[1]] else "."
panel_file <- file.path(root, "data", "agent_figure_panel_data_2026-09-13.csv")
window_file <- file.path(root, "analysis", "supervisor_2026_09_20", "agent_window_summary.csv")
oracle_file <- file.path(root, "analysis", "supervisor_2026_09_20", "agent_oracle_summary.csv")
out_dir <- file.path(root, "figures", "agent")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

p <- read.csv(panel_file, stringsAsFactors = FALSE, check.names = FALSE)
w <- read.csv(window_file, stringsAsFactors = FALSE)
o <- read.csv(oracle_file, stringsAsFactors = FALSE)
ov <- setNames(o$value, o$metric)

ORACLE <- ov[["protocol_oracle_CU"]]; D <- ov[["D_threshold_CU"]]
if (abs(ORACLE - 22) > 1e-12) stop("Protocol oracle anchor changed")
if (abs(D - 206) > 1e-12) stop("Policy-D threshold changed")

ink <- "#111111"; blue <- "#315A8A"; orange <- "#B45F3B"; red <- "#8F3B3B"; green <- "#447A6A"; grey <- "#666666"; light <- "#E6E6E6"
strong <- p[p$tier == "strong" & p$arm == "E" & p$is_non_binding_allowance == 0, ]
strong <- strong[order(strong$budget_CU), ]
mini <- p[p$tier == "mini" & p$arm == "E", ]; mini <- mini[order(mini$budget_CU), ]
nano <- p[p$tier == "nano" & p$arm == "E", ]; nano <- nano[order(nano$budget_CU), ]
nb <- p[p$tier == "strong" & p$is_non_binding_allowance == 1, ][1, ]

render <- function(device = c("svg", "pdf", "png")) {
  device <- match.arg(device)
  stem <- file.path(out_dir, "F10_agent_capability_bounded_envelope")
  if (device == "svg") svg(paste0(stem, ".svg"), width = 12.2, height = 4.2, pointsize = 9, bg = "white")
  if (device == "pdf") pdf(paste0(stem, ".pdf"), width = 12.2, height = 4.2, pointsize = 9, useDingbats = FALSE)
  if (device == "png") png(paste0(stem, ".png"), width = 12.2, height = 4.2, units = "in", res = 500, pointsize = 9, bg = "white")
  on.exit(dev.off(), add = TRUE)
  old <- par(no.readonly = TRUE); on.exit(par(old), add = TRUE)
  layout(matrix(1:4, nrow = 1), widths = c(1.35, 1.35, 1.35, 0.40))
  par(family = "serif", fg = ink, col.axis = ink, col.lab = ink, col.main = ink,
      mgp = c(2.2, 0.7, 0), tcl = -0.25, las = 1)

  # a — completion envelope
  par(mar = c(4.1, 4.3, 2.5, 0.8))
  plot(strong$budget_CU, strong$p_complete_decision, type = "o", log = "x", xlim = c(45, 430), ylim = c(-0.03, 1.06),
       xlab = "Compute budget (CU)", ylab = "P(complete decision)", col = blue, pch = 16, lwd = 1.4, axes = FALSE)
  abline(h = seq(0, 1, 0.2), col = light, lwd = 0.7)
  lines(mini$budget_CU, mini$p_complete_decision, type = "o", col = orange, pch = 15, lwd = 1.2)
  lines(nano$budget_CU, nano$p_complete_decision, type = "o", col = red, pch = 17, lwd = 1.2)
  abline(v = 75, col = blue, lty = 3, lwd = 1.0); abline(v = D, col = grey, lty = 2, lwd = 1.0)
  axis(1, at = c(50, 75, 100, 150, 200, 250, 400), labels = c("50", "75", "100", "150", "200", "250", "400")); axis(2); box(bty = "l")
  legend("bottomright", legend = c("strong", "mini", "nano"), col = c(blue, orange, red), pch = c(16, 15, 17), lty = 1, bty = "n", cex = 0.78)
  text(52, 0.96, sprintf("75 CU = %.2fx oracle\n206 CU = %.2fx oracle", 75 / ORACLE, D / ORACLE), adj = c(0, 1), cex = 0.72)
  mtext("a   Capability-bounded decision recovery", side = 3, adj = 0, line = 0.8, font = 2, cex = 0.95)

  # b — narrow-window mechanism and window size
  par(mar = c(4.1, 4.3, 2.5, 4.5))
  plot(strong$budget_CU, strong$narrow_window_fraction, type = "o", log = "x", xlim = c(45, 430), ylim = c(-0.03, 1.06),
       xlab = "Compute budget (CU)", ylab = "Fraction using narrow window", col = blue, pch = 16, lwd = 1.4, axes = FALSE)
  abline(h = seq(0, 1, 0.2), col = light, lwd = 0.7); abline(v = D, col = grey, lty = 2, lwd = 1.0)
  axis(1, at = c(50, 75, 100, 150, 200, 250, 400), labels = c("50", "75", "100", "150", "200", "250", "400")); axis(2); box(bty = "l")
  par(new = TRUE)
  plot(w$budget_CU[w$budget_CU < 5000], w$median_smallest_window_states[w$budget_CU < 5000], log = "xy",
       xlim = c(45, 430), ylim = c(500, 30000), type = "p", pch = 23, bg = "white", col = grey,
       axes = FALSE, xlab = "", ylab = "")
  axis(4, col.axis = grey); mtext("Median smallest window (states)", side = 4, line = 2.8, col = grey)
  abline(h = 14136, col = grey, lty = 3, lwd = 0.8)
  text(53, 0.05, "non-binding: narrow-window 0/20", adj = c(0, 0), cex = 0.72)
  mtext("b   Binding budgets activate scoped process search", side = 3, adj = 0, line = 0.8, font = 2, cex = 0.95)

  # c — stable/final spend + oracle
  par(mar = c(4.1, 4.3, 2.5, 0.8))
  ok <- !is.na(strong$decision_stable_CU_median)
  ss <- strong[ok, ]
  plot(ss$budget_CU, ss$decision_stable_CU_median, type = "o", log = "xy", xlim = c(45, 430), ylim = c(18, 950),
       xlab = "Compute budget (CU)", ylab = "CU spent", col = blue, pch = 16, lwd = 1.4, axes = FALSE)
  abline(h = pretty(c(20, 900)), col = light, lwd = 0.7)
  for (i in seq_len(nrow(ss))) segments(ss$budget_CU[i], ss$decision_stable_CU_median[i], ss$budget_CU[i], ss$final_used_CU_median[i], col = "#DCE6EF", lwd = 4)
  lines(ss$budget_CU, ss$decision_stable_CU_median, type = "o", col = blue, pch = 16, lwd = 1.4)
  lines(ss$budget_CU, ss$final_used_CU_median, type = "o", col = ink, pch = 25, bg = ink, lwd = 1.2)
  abline(h = ORACLE, col = green, lwd = 1.2); abline(h = D, col = grey, lty = 2, lwd = 1.0)
  axis(1, at = c(50, 75, 100, 150, 200, 250, 400), labels = c("50", "75", "100", "150", "200", "250", "400")); axis(2); box(bty = "l")
  legend("topleft", legend = c("decision-stable", "final used", "22-CU protocol oracle"), col = c(blue, ink, green), pch = c(16, 25, NA), lty = 1, pt.bg = c(NA, ink, NA), bty = "n", cex = 0.72)
  text(405, 23, sprintf("75-cell stable 52.5 CU = %.2fx\nD threshold 206 CU = %.2fx\nnon-binding stable 566 CU = %.2fx\n+148 CU -> 714 CU final", 52.5 / ORACLE, D / ORACLE, 566 / ORACLE), adj = c(1, 0), cex = 0.70)
  mtext("c   Oracle-normalized lower and upper compute boundaries", side = 3, adj = 0, line = 0.8, font = 2, cex = 0.95)

  # non-binding control, deliberately separate from the budget continuum
  par(mar = c(4.1, 1.0, 2.5, 1.0))
  plot(c(1, 1), c(nb$decision_stable_CU_median, nb$final_used_CU_median), type = "n", log = "y", xlim = c(0.7, 1.3), ylim = c(18, 5000), axes = FALSE, xlab = "", ylab = "")
  segments(1, nb$decision_stable_CU_median, 1, nb$final_used_CU_median, col = "#DCE6EF", lwd = 6)
  points(1, nb$decision_stable_CU_median, pch = 16, col = blue); points(1, nb$final_used_CU_median, pch = 25, bg = ink, col = ink)
  points(1, ov[["nonbinding_max_single_run_CU"]], pch = 25, bg = "white", col = ink)
  abline(h = ORACLE, col = green, lwd = 1.0); abline(h = D, col = grey, lty = 2, lwd = 0.9)
  axis(1, at = 1, labels = "non-binding\n5000 CU", tick = FALSE, cex.axis = 0.72)
  box(bty = "l", lty = 3)
  text(1, ov[["nonbinding_max_single_run_CU"]] * 1.10, "3021\n(single run)", cex = 0.62)
}

render("svg"); render("pdf"); render("png")
cat("Rendered F10 with 22-CU protocol oracle and non-binding 566 + 148 decomposition.\n")
