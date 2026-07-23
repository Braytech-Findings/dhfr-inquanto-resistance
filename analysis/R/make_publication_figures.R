root <- normalizePath(getwd(), mustWork = FALSE)
if (!file.exists(file.path(root, "README.md"))) {
  root <- normalizePath(file.path(root, "../.."), mustWork = TRUE)
}
if (!requireNamespace("ggplot2", quietly = TRUE)) {
  stop("ggplot2 is required for the public R figure release")
}

library(ggplot2)

out <- file.path(root, "results/publication/figures/r")
dir.create(out, recursive = TRUE, showWarnings = FALSE)

theme_competition <- function() {
  theme_minimal(base_size = 15) +
    theme(
      plot.title = element_text(face = "bold", size = 19, color = "#102A43"),
      plot.subtitle = element_text(size = 12, color = "#486581"),
      plot.caption = element_text(size = 9, color = "#627D98", hjust = 0),
      axis.title = element_text(face = "bold"),
      panel.grid.minor = element_blank(),
      legend.position = "top",
      plot.background = element_rect(fill = "white", color = NA),
      panel.background = element_rect(fill = "white", color = NA)
    )
}

save_plot <- function(name, plot, width = 10, height = 6) {
  ggsave(file.path(out, paste0(name, ".png")), plot, width = width,
         height = height, dpi = 320, bg = "white")
  grDevices::svg(file.path(out, paste0(name, ".svg")), width = width,
                 height = height, bg = "white")
  print(plot)
  grDevices::dev.off()
}

# Figure 1: complete local shot convergence.
shots <- read.csv(file.path(
  root,
  "artifacts/final_public_release/molecular/WT_TMP/local_finite_shot_replicates.csv"
))
shot_summary <- aggregate(
  cbind(energy_hartree, uncertainty_hartree) ~ shots_per_circuit,
  data = shots,
  FUN = mean
)
ideal <- -2587.912001526413
shot_summary$error_millihartree <-
  (shot_summary$energy_hartree - ideal) * 1000
shot_summary$uncertainty_millihartree <-
  shot_summary$uncertainty_hartree * 1000

p_shots <- ggplot(
  shot_summary,
  aes(x = shots_per_circuit, y = error_millihartree)
) +
  geom_hline(yintercept = 0, linewidth = 0.8, linetype = "dashed", color = "#334E68") +
  geom_ribbon(
    aes(
      ymin = error_millihartree - uncertainty_millihartree,
      ymax = error_millihartree + uncertainty_millihartree
    ),
    fill = "#4C78A8", alpha = 0.18
  ) +
  geom_line(linewidth = 1.2, color = "#175676") +
  geom_point(size = 3.4, color = "#D1495B") +
  scale_x_log10(breaks = unique(shot_summary$shots_per_circuit)) +
  labs(
    title = "More shots bring the WT_TMP estimate toward the exact answer",
    subtitle = "Dots are three-replicate means; the blue band is one propagated standard error",
    x = "Shots per measurement circuit (log scale)",
    y = "Error from exact energy (millihartree)",
    caption = paste(
      "LOCAL_FINITE_SHOT_SIMULATION • 576 circuits per replicate •",
      "Researcher interpretation required"
    )
  ) +
  theme_competition()
save_plot("wt_tmp_shot_convergence_r", p_shots)

# Figure 2: four-system compact classical pilot.
classical <- read.csv(file.path(root, "results/tables/classical_interaction_energies.csv"))
classical <- subset(
  classical,
  tier == "compact_primary" & method == "HF" & basis == "sto-3g" &
    nadph_embedding == "True"
)
classical$system <- classical$system_id
if (!"interaction_energy_hartree" %in% names(classical)) {
  energy_col <- grep("energy.*hartree", names(classical), value = TRUE)[1]
  classical$interaction_energy_hartree <- classical[[energy_col]]
}
classical$system <- factor(
  classical$system,
  levels = c("WT_TMP", "WT_4DTMP", "L28R_TMP", "L28R_4DTMP")
)
classical$energy_millihartree <- classical$interaction_energy_hartree * 1000
p_classical <- ggplot(
  classical,
  aes(x = system, y = energy_millihartree, fill = system)
) +
  geom_col(width = 0.68, color = "#102A43", linewidth = 0.35) +
  geom_text(
    aes(y = energy_millihartree / 2, label = sprintf("%.1f", energy_millihartree)),
    color = "white", fontface = "bold", size = 4.2
  ) +
  scale_fill_manual(values = c("#2A9D8F", "#76C893", "#F4A261", "#E76F51")) +
  guides(fill = "none") +
  labs(
    title = "The compact classical pilot separates the four DHFR–ligand models",
    subtitle = "More-negative bars are more stabilizing in this simplified interaction-energy proxy",
    x = NULL,
    y = "Interaction-energy proxy (millihartree)",
    caption = paste(
      "PILOT_ONLY • HF/STO-3G compact clusters • Not binding free energy •",
      "Researcher interpretation required"
    )
  ) +
  theme_competition() +
  theme(axis.text.x = element_text(angle = 15, hjust = 1))
save_plot("four_system_classical_pilot_r", p_classical)

# Figure 3: what evidence exists and what remains missing.
evidence <- data.frame(
  stage = factor(
    c(
      "Four structures", "Four classical pilots", "WT_TMP exact quantum",
      "WT_TMP local shots", "WT_TMP remote pilot", "Four-system quantum"
    ),
    levels = rev(c(
      "Four structures", "Four classical pilots", "WT_TMP exact quantum",
      "WT_TMP local shots", "WT_TMP remote pilot", "Four-system quantum"
    ))
  ),
  status = c("Complete", "Pilot", "Complete", "Complete", "Retry pending", "Missing")
)
p_evidence <- ggplot(evidence, aes(x = status, y = stage, fill = status)) +
  geom_tile(width = 0.88, height = 0.72, color = "white", linewidth = 1.2) +
  geom_text(aes(label = status), color = "white", fontface = "bold", size = 4.6) +
  scale_fill_manual(values = c(
    "Complete" = "#2A9D8F", "Pilot" = "#457B9D",
    "Retry pending" = "#E9C46A", "Missing" = "#8D99AE"
  )) +
  guides(fill = "none") +
  labs(
    title = "Evidence map: what is complete and what is still missing",
    subtitle = "A missing result stays missing—it is never changed to zero",
    x = NULL, y = NULL,
    caption = "COMPUTER MODEL EVIDENCE • Researcher interpretation required"
  ) +
  theme_competition() +
  theme(panel.grid = element_blank(), axis.text.x = element_blank())
save_plot("evidence_completion_map_r", p_evidence, width = 11, height = 5.8)

write.csv(shot_summary, file.path(out, "wt_tmp_shot_convergence_r_source.csv"), row.names = FALSE)
write.csv(classical, file.path(out, "four_system_classical_pilot_r_source.csv"), row.names = FALSE)
write.csv(evidence, file.path(out, "evidence_completion_map_r_source.csv"), row.names = FALSE)
