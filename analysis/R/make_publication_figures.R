root <- normalizePath(file.path(getwd()), mustWork=FALSE)
if (!file.exists(file.path(root, "results/publication/data/energy_results.csv"))) root <- normalizePath(file.path(root, "../.."))
if (!requireNamespace("ggplot2", quietly=TRUE)) { message("ggplot2 unavailable; Python publication figures remain authoritative."); quit(status=0) }
d <- read.csv(file.path(root, "results/publication/data/energy_results.csv")); out <- file.path(root, "results/publication/figures/r"); dir.create(out, recursive=TRUE, showWarnings=FALSE)
p <- ggplot2::ggplot(d, ggplot2::aes(method, relative_to_scf_millihartree)) + ggplot2::geom_col(fill="#1976d2") + ggplot2::labs(x=NULL, y="Energy relative to SCF (millihartree)", title="WT_TMP energy estimates") + ggplot2::theme(axis.text.x=ggplot2::element_text(angle=15,hjust=1))
ggplot2::ggsave(file.path(out,"energy_comparison_r.png"), p, width=8, height=4, dpi=300); ggplot2::ggsave(file.path(out,"energy_comparison_r.pdf"), p, width=8, height=4)
