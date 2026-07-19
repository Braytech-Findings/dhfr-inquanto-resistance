load data/processed/WT_TMP_minimized.pdb, wt_tmp
select ligand, resn TOP
select pocket, byres (chain A within 5 of ligand)
show cartoon, chain A
show sticks, ligand or pocket
color yellow, ligand
color salmon, pocket
zoom ligand, 10
