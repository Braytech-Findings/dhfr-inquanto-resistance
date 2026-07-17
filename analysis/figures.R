#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(scales)
  library(cowplot)
})

root <- normalizePath(".", mustWork = TRUE)
fig_dir <- file.path(root, "results", "figures")
if (!dir.exists(fig_dir)) dir.create(fig_dir, recursive = TRUE)

# Read the classical interaction table and endpoint summary
classical_tbl <- read_csv(file.path(root, "results", "tables", "classical_interaction_energies.csv"), show_col_types = FALSE)
endpoint_json <- jsonlite::fromJSON(file.path(root, "results", "tables", "endpoint.json"))

# Prepare a compact system-level summary
system_summary <- classical_tbl %>%
  filter(system_id %in% c("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")) %>%
  group_by(system_id) %>%
  summarise(mean_energy = mean(interaction_energy_hartree, na.rm = TRUE), .groups = "drop") %>%
  mutate(system_id = factor(system_id, levels = c("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")))

# Figure 1: D contrast bar plot with 95% CI
contrast_df <- data.frame(
  label = "D contrast",
  estimate = endpoint_json$estimate_hartree,
  lower = endpoint_json$ci95_hartree[[1]],
  upper = endpoint_json$ci95_hartree[[2]]
)

p1 <- ggplot(contrast_df, aes(x = label, y = estimate)) +
  geom_col(fill = "#2563eb", alpha = 0.9, width = 0.65) +
  geom_errorbar(aes(ymin = lower, ymax = upper), width = 0.15, color = "#0f172a", linewidth = 0.9) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "#111827") +
  annotate("text", x = 1, y = contrast_df$estimate, label = sprintf("D = %.3f Hartree\n95%% CI [%.3f, %.3f]", contrast_df$estimate, contrast_df$lower, contrast_df$upper), vjust = -0.4, hjust = 0.5, size = 3.2) +
  coord_cartesian(ylim = c(min(contrast_df$lower, -0.02) - 0.01, max(contrast_df$upper, 0.02) + 0.01)) +
  labs(
    title = "Difference-in-differences endpoint D",
    subtitle = "Negative values indicate stronger stabilization for 4-DTMP in the L28R background relative to TMP",
    x = "",
    y = expression("D (Hartree)"),
    caption = "Endpoint from the prespecified classical interaction-energy workflow"
  ) +
  theme_minimal(base_size = 13) +
  theme(plot.title = element_text(face = "bold"), plot.subtitle = element_text(color = "#334155"), axis.text.x = element_blank(), axis.ticks.x = element_blank())

# Figure 2: energy comparison by system
p2 <- ggplot(system_summary, aes(x = system_id, y = mean_energy, fill = system_id)) +
  geom_col(width = 0.8, color = "#0f172a", linewidth = 0.35) +
  scale_fill_manual(values = c(
    "WT_TMP" = "#4C78A8",
    "WT_4DTMP" = "#F58518",
    "L28R_TMP" = "#54A24B",
    "L28R_4DTMP" = "#B279A2"
  )) +
  labs(
    title = "Classical HF interaction energies by system",
    subtitle = "More negative values indicate stronger stabilization",
    x = "System",
    y = expression("Interaction energy (Hartree)"),
    caption = "Values were derived from the repo's counterpoise-corrected classical outputs"
  ) +
  theme_minimal(base_size = 13) +
  theme(legend.position = "none", plot.title = element_text(face = "bold"), plot.subtitle = element_text(color = "#334155"))

# Figure 3: robustness/uncertainty summary using sensitivity rows from classical_contrasts.csv
contrast_sensitivity <- read_csv(file.path(root, "results", "tables", "classical_contrasts.csv"), show_col_types = FALSE)
contrast_sensitivity <- contrast_sensitivity %>%
  mutate(label = paste(method, basis, if_else(nadph_embedding, "embed", "noembed"), sep = " / "))

p3 <- ggplot(contrast_sensitivity, aes(x = factor(status, levels = c("pilot_only", "sensitivity")), y = D_hartree, fill = factor(status))) +
  geom_boxplot(width = 0.6, outlier.shape = 21) +
  geom_jitter(width = 0.08, size = 2.2, alpha = 0.8, color = "#111827") +
  scale_fill_manual(values = c("pilot_only" = "#2563eb", "sensitivity" = "#f59e0b")) +
  labs(
    title = "Robustness of the D contrast across sensitivity checks",
    subtitle = "The observed contrast remains negative across the documented sensitivity rows",
    x = "Status",
    y = expression("D (Hartree)"),
    caption = "Sensitivity rows from results/tables/classical_contrasts.csv"
  ) +
  theme_minimal(base_size = 13) +
  theme(legend.position = "none", plot.title = element_text(face = "bold"), plot.subtitle = element_text(color = "#334155"))

# Combine and save
fig <- plot_grid(p1, p2, p3, ncol = 1, rel_heights = c(1, 1, 1))

# Save high-resolution PNG and PDF
ggsave(file.path(fig_dir, "publication_summary.png"), fig, width = 10, height = 11, dpi = 300, bg = "white")
ggsave(file.path(fig_dir, "publication_summary.pdf"), fig, width = 10, height = 11, device = cairo_pdf)

# Save the individual plots too
for (i in seq_along(list(p1, p2, p3))) {
  ggsave(file.path(fig_dir, sprintf("figure_%d.png", i)), get(paste0("p", i)), width = 8, height = 5, dpi = 300, bg = "white")
  ggsave(file.path(fig_dir, sprintf("figure_%d.pdf", i)), get(paste0("p", i)), width = 8, height = 5, device = cairo_pdf)
}

cat("Saved figures to", fig_dir, "\n")
