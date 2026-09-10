#!/usr/bin/env Rscript

# Figure 8 — MeOH selectivity–recycle pathway
# Scientific design frozen in docs/F8_METHANOL_FIGURE_LOCK_SPEC.md
# Inputs are frozen D01 v3 extracted CSVs; this script performs rendering only.

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args) >= 1) args[[1]] else "."

purge_file <- file.path(root, "data", "meoh", "meoh_purge_robustness_D01v3.csv")
cand_file  <- file.path(root, "data", "meoh", "meoh_candidate_ranking_D01v3.csv")
out_dir    <- file.path(root, "figures", "meoh")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

purge <- read.csv(purge_file, check.names = FALSE, stringsAsFactors = FALSE)
cand  <- read.csv(cand_file, check.names = FALSE, stringsAsFactors = FALSE)

npc_cols <- c(
  "NPC_1 wt% Re | 200 C",
  "NPC_5 wt% Re | 200 C",
  "NPC_1 wt% Re | 250 C",
  "NPC_5 wt% Re | 250 C"
)
labels <- c(
  "1 wt% Re / 200 C",
  "5 wt% Re / 200 C",
  "1 wt% Re / 250 C",
  "5 wt% Re / 250 C"
)

if (!all(npc_cols %in% names(purge))) stop("Required purge/NPC columns missing")
if (nrow(purge) != 396) stop(sprintf("Expected 396 purge levels, found %d", nrow(purge)))
if (abs(min(purge$purge) - 0.005) > 1e-12 || abs(max(purge$purge) - 0.40) > 1e-12) {
  stop("Purge range is not the frozen 0.5–40% envelope")
}

bench <- cand[cand$candidate == "5 wt% Re | 250 C", , drop = FALSE]
if (nrow(bench) != 1) stop("Frozen benchmark row 5 wt% Re | 250 C not uniquely found")
lev <- c(
  STY = bench$L_STY,
  `Single-pass conversion` = bench$L_conversion,
  `CH4 suppression` = bench$L_CH4_suppression
)
expected <- c(0.00289430146472775, 0.05882776006061632, 0.3757939247335326)
if (any(abs(unname(lev) - expected) > 1e-12)) stop("Leverage values differ from frozen D01 v3 values")

# Colorblind-safe candidate palette. All text/axes remain black.
cols <- c("#0072B2", "#D55E00", "#009E73", "#CC79A7")

render_figure <- function(device = c("svg", "pdf", "png")) {
  device <- match.arg(device)
  base <- file.path(out_dir, "F08_MeOH_selectivity_recycle_D01v3")
  if (device == "svg") {
    svg(paste0(base, ".svg"), width = 7.4, height = 3.7, pointsize = 9, bg = "white")
  } else if (device == "pdf") {
    pdf(paste0(base, ".pdf"), width = 7.4, height = 3.7, pointsize = 9, useDingbats = FALSE)
  } else {
    png(paste0(base, ".png"), width = 7.4, height = 3.7, units = "in", res = 400, pointsize = 9, bg = "white")
  }

  old <- par(no.readonly = TRUE)
  on.exit({par(old); dev.off()}, add = TRUE)
  layout(matrix(c(1, 2), nrow = 1), widths = c(1.55, 1.0))

  # Panel A — purge-dependent NPC curves.
  par(mar = c(4.0, 4.3, 1.2, 0.8), mgp = c(2.25, 0.70, 0), tcl = -0.25,
      family = "sans", las = 1, xaxs = "i", yaxs = "r")
  x <- purge$purge * 100
  ymat <- as.matrix(purge[, npc_cols])
  yr <- range(ymat, finite = TRUE)
  plot(x, ymat[, 1], type = "n", xlim = c(0.5, 40), ylim = yr,
       xlab = "Purge fraction (%)", ylab = "Net production cost (EUR t-1)",
       axes = FALSE)
  axis(1, at = c(0.5, 2, 10, 20, 30, 40), labels = c("0.5", "2", "10", "20", "30", "40"))
  axis(2)
  box(bty = "l")
  abline(h = pretty(yr), col = "#E6E6E6", lwd = 0.7)
  abline(v = 2, lty = 2, lwd = 1.0, col = "#666666")
  for (i in seq_along(npc_cols)) lines(x, ymat[, i], col = cols[i], lwd = 1.7)
  points(rep(2, length(npc_cols)), sapply(npc_cols, function(z) purge[purge$purge == 0.02, z]),
         pch = 21, bg = "white", col = cols, cex = 0.85, lwd = 1.2)
  legend("topleft", legend = labels, col = cols, lwd = 1.7, bty = "n", cex = 0.70,
         inset = c(0.015, 0.015))
  text(2.25, yr[2] - 0.03 * diff(yr), "2% canonical", adj = c(0, 1), cex = 0.68)
  mtext("a", side = 3, line = 0.1, at = par("usr")[1], adj = 0, font = 2, cex = 1.05)

  # Panel B — local economic leverage at frozen benchmark state.
  par(mar = c(4.0, 6.2, 1.2, 1.0), mgp = c(2.25, 0.70, 0), tcl = -0.25,
      family = "sans", las = 1, xaxs = "r", yaxs = "i")
  yy <- 3:1
  xlim <- c(0.0015, 0.65)
  plot(unname(lev), yy, log = "x", xlim = xlim, ylim = c(0.5, 3.5),
       xlab = "Local economic leverage, |d ln C / d ln x|", ylab = "",
       yaxt = "n", axes = FALSE, pch = 21, bg = "white", cex = 1.2, lwd = 1.2)
  axis(1, at = c(0.002, 0.01, 0.05, 0.1, 0.5), labels = c("0.002", "0.01", "0.05", "0.1", "0.5"))
  axis(2, at = yy, labels = names(lev), las = 1, tick = FALSE, hadj = 1)
  box(bty = "l")
  abline(v = c(0.01, 0.1), col = "#E6E6E6", lwd = 0.7)
  segments(x0 = 0.0017, y0 = yy, x1 = unname(lev), y1 = yy, col = "#777777", lwd = 1.0)
  points(unname(lev), yy, pch = 21, bg = c("white", "white", "black"), col = "black",
         cex = 1.2, lwd = 1.1)
  text(unname(lev) * 1.12, yy, labels = sprintf("%.3g", unname(lev)), adj = 0, cex = 0.72)
  text(0.0032, 0.72, "5 wt% Re / 250 C", adj = 0, cex = 0.70)
  mtext("b", side = 3, line = 0.1, at = par("usr")[1], adj = 0, font = 2, cex = 1.05)
}

render_figure("svg")
render_figure("pdf")
render_figure("png")

cat("Rendered Figure 8 from frozen D01 v3 CSVs.\n")
cat(sprintf("CH4 suppression / conversion = %.3f\n", lev[["CH4 suppression"]] / lev[["Single-pass conversion"]]))
cat(sprintf("CH4 suppression / STY = %.3f\n", lev[["CH4 suppression"]] / lev[["STY"]]))
