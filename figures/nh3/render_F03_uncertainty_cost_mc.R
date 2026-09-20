#!/usr/bin/env Rscript

# Figure 3 — NH3 descriptor uncertainty + cost-side Monte Carlo
# 2026-09-20 supervisor extension. Rendering only; no scientific values are recomputed.

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args) >= 1) args[[1]] else "."
summary_file <- file.path(root, "analysis", "supervisor_2026_09_20", "f3_panel_summary.csv")
hist_file <- file.path(root, "analysis", "supervisor_2026_09_20", "nh3_cost_mc_histogram.csv")
meoh_file <- file.path(root, "analysis", "supervisor_2026_09_20", "meoh_rank_probability_matrix.csv")
out_dir <- file.path(root, "figures", "nh3")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

s <- read.csv(summary_file, stringsAsFactors = FALSE)
h <- read.csv(hist_file, stringsAsFactors = FALSE, check.names = FALSE)
m <- read.csv(meoh_file, stringsAsFactors = FALSE, check.names = FALSE)
val <- setNames(s$value, s$metric)

need <- c("Fe_feasible_descriptor_MC", "Fe_economic_top1_descriptor_MC",
          "top1_survival_descriptor_MC", "Fe_top3_actionable_descriptor_MC",
          "P_C_Fe_lt_C_Ru_cost_MC", "min_Ru_minus_Fe_cost_MC",
          "median_Ru_minus_Fe_cost_MC", "alpha_star_p05",
          "alpha_star_median", "alpha_star_p95", "alpha_star_canonical")
if (!all(need %in% names(val))) stop("F3 summary metrics incomplete")
if (abs(val[["Fe_economic_top1_descriptor_MC"]] - 0.681) > 1e-12) stop("Fe economic Top-1 anchor changed")
if (abs(val[["top1_survival_descriptor_MC"]] - 0.282) > 1e-12) stop("Top-1 survival anchor changed")
if (abs(val[["P_C_Fe_lt_C_Ru_cost_MC"]] - 1.0) > 1e-12) stop("Cost-MC Fe/Ru preference anchor changed")

ink <- "#111111"; blue <- "#315A8A"; orange <- "#B45F3B"; grey <- "#666666"; light <- "#E6E6E6"

render <- function(device = c("svg", "pdf", "png")) {
  device <- match.arg(device)
  stem <- file.path(out_dir, "F03_uncertainty_cost_mc_2026-09-20")
  if (device == "svg") svg(paste0(stem, ".svg"), width = 10.6, height = 6.7, pointsize = 9, bg = "white")
  if (device == "pdf") pdf(paste0(stem, ".pdf"), width = 10.6, height = 6.7, pointsize = 9, useDingbats = FALSE)
  if (device == "png") png(paste0(stem, ".png"), width = 10.6, height = 6.7, units = "in", res = 500, pointsize = 9, bg = "white")
  on.exit(dev.off(), add = TRUE)

  old <- par(no.readonly = TRUE); on.exit(par(old), add = TRUE)
  layout(matrix(1:4, nrow = 2, byrow = TRUE), widths = c(1, 1), heights = c(1, 1))
  par(family = "serif", fg = ink, col.axis = ink, col.lab = ink, col.main = ink,
      mgp = c(2.2, 0.7, 0), tcl = -0.25, las = 1)

  # a — descriptor endpoints
  par(mar = c(4.1, 7.2, 2.7, 1.0))
  x <- c(val[["Fe_feasible_descriptor_MC"]], val[["Fe_economic_top1_descriptor_MC"]],
         val[["top1_survival_descriptor_MC"]], val[["Fe_top3_actionable_descriptor_MC"]])
  labs <- c("Fe feasible", "Fe economic Top-1", "Atomic -> economic\nTop-1 survival", "Fe Top-3 actionable")
  yy <- 4:1
  plot(0, 0, type = "n", xlim = c(0, 1.02), ylim = c(0.4, 4.6), axes = FALSE,
       xlab = "Probability across 1,000 descriptor draws", ylab = "")
  abline(v = seq(0, 1, 0.2), col = light, lwd = 0.7)
  rect(0, yy - 0.28, x, yy + 0.28, col = c(blue, blue, "#B7B7B7", blue), border = ink, lwd = 0.6)
  axis(1, at = seq(0, 1, 0.2), labels = paste0(seq(0, 100, 20), "%"))
  axis(2, at = yy, labels = labs, tick = FALSE, hadj = 1)
  box(bty = "l")
  text(x + 0.018, yy, sprintf("%.1f%%", 100 * x), adj = 0, cex = 0.86)
  mtext("a   Descriptor uncertainty separates distinct decision endpoints", side = 3, adj = 0, line = 0.8, font = 2, cex = 0.95)
  mtext("68.1% = P(Fe economic Top-1); 28.2% = P(atomic Top-1 = economic Top-1)", side = 3, adj = 0, line = -0.35, cex = 0.70)

  # b — Ru-Fe cost gap histogram
  par(mar = c(4.1, 4.5, 2.7, 1.0))
  ok <- !is.na(h$delta_left) & !is.na(h$delta_right) & !is.na(h$delta_count)
  left <- h$delta_left[ok]; right <- h$delta_right[ok]; cnt <- h$delta_count[ok]
  ylim <- c(0, max(cnt) * 1.12)
  plot(range(c(left, right)), ylim, type = "n", xlab = "C_Ru - C_Fe (USD t-1 NH3)", ylab = "Draw count", axes = FALSE)
  abline(h = pretty(ylim), col = light, lwd = 0.7)
  rect(left, 0, right, cnt, col = "#B8C5D1", border = "white", lwd = 0.5)
  abline(v = 0, lty = 2, lwd = 1.0)
  abline(v = val[["median_Ru_minus_Fe_cost_MC"]], col = blue, lwd = 1.3)
  axis(1); axis(2); box(bty = "l")
  legend("topright", legend = c("P(C_Fe < C_Ru) = 5,000/5,000",
                                sprintf("minimum gap = %.2f USD/t", val[["min_Ru_minus_Fe_cost_MC"]]),
                                sprintf("median gap = %.2f USD/t", val[["median_Ru_minus_Fe_cost_MC"]])),
         bty = "o", bg = "white", box.col = "#B0B0B0", cex = 0.72)
  mtext("b   Joint cost uncertainty does not reverse Fe versus Ru", side = 3, adj = 0, line = 0.8, font = 2, cex = 0.95)

  # c — alpha* histogram
  par(mar = c(4.1, 4.5, 2.7, 1.0))
  ok <- !is.na(h$alpha_left) & !is.na(h$alpha_right) & !is.na(h$alpha_count)
  left <- h$alpha_left[ok]; right <- h$alpha_right[ok]; cnt <- h$alpha_count[ok]
  plot(range(c(left, right)), c(0, max(cnt) * 1.12), type = "n", log = "x",
       xlab = "Ru activity multiplier at parity, alpha*", ylab = "Draw count", axes = FALSE)
  abline(h = pretty(c(0, max(cnt))), col = light, lwd = 0.7)
  rect(left, 0, right, cnt, col = "#D6C1B6", border = "white", lwd = 0.5)
  abline(v = c(val[["alpha_star_p05"]], val[["alpha_star_p95"]]), col = grey, lty = 2, lwd = 0.9)
  abline(v = val[["alpha_star_median"]], col = orange, lwd = 1.3)
  abline(v = val[["alpha_star_canonical"]], lty = 3, lwd = 0.9)
  axis(1); axis(2); box(bty = "l")
  legend("topleft", legend = c(sprintf("p05 %.2fx", val[["alpha_star_p05"]]),
                                sprintf("median %.2fx", val[["alpha_star_median"]]),
                                sprintf("p95 %.2fx", val[["alpha_star_p95"]]),
                                sprintf("canonical %.2fx", val[["alpha_star_canonical"]])),
         bty = "n", cex = 0.75)
  mtext("c   Cost uncertainty broadens the activity-parity target", side = 3, adj = 0, line = 0.8, font = 2, cex = 0.95)

  # d — MeOH rank probability matrix
  par(mar = c(4.1, 7.2, 2.7, 1.0))
  mm <- m[m$boundary == "canonical_D01", , drop = FALSE]
  order <- c("5wtRe_200C", "1wtRe_200C", "1wtRe_250C", "5wtRe_250C")
  mm <- mm[match(order, mm$candidate), ]
  M <- as.matrix(mm[, c("rank_1", "rank_2", "rank_3", "rank_4")])
  image(1:4, 1:4, t(M[4:1, ]), col = grey.colors(101, start = 1, end = 0), zlim = c(0, 1), axes = FALSE,
        xlab = "", ylab = "")
  axis(1, at = 1:4, labels = paste("Rank", 1:4))
  axis(2, at = 1:4, labels = rev(c("5 wt% Re / 200 C", "1 wt% Re / 200 C", "1 wt% Re / 250 C", "5 wt% Re / 250 C")), tick = FALSE, hadj = 1)
  box()
  for (i in 1:4) for (j in 1:4) {
    v <- M[i, j]; y <- 5 - i
    text(j, y, sprintf("%.0f%%", 100 * v), col = if (v > 0.5) "white" else "black", cex = 0.82)
  }
  mtext("d   MeOH economic ranking is stable to the tested cost envelope", side = 3, adj = 0, line = 0.8, font = 2, cex = 0.95)
  mtext("Canonical D01: 5,000/5,000 retain the same order; the active-Re replacement extension does too.", side = 1, line = 3.0, adj = 0, cex = 0.68)
}

render("svg"); render("pdf"); render("png")
cat("Rendered F03 uncertainty + cost-MC extension from frozen summary/histogram tables.\n")
