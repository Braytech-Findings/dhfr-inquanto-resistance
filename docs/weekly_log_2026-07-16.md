# Weekly log - 2026-07-16

## Completed

- Froze a Boys--Bernardi counterpoise interaction-energy proxy with consistent
  full-cluster ghost bases and fixed NADPH point-charge embedding.
- Completed all four compact-primary HF counterpoise calculations at STO-3G,
  3-21G, and def2-SVP, plus a STO-3G NADPH-embedding sensitivity.
- Recorded the contrast as a screening result only; it is not a binding free
  energy or a statistically supported biological conclusion.
- Rejected broad N/O AVAS as a protein-valence selection and replaced it with
  an explicit ligand-frontier orbital-character workflow.
- Generated system-specific candidate CAS(6,6) orbital maps for all four
  systems. A visual re-render identified a map/checkpoint consistency issue;
  this was corrected by regenerating the four singlet density-fitted CASCI
  checks from one fixed selection rule and linking each result to a SHA-256
  selection checksum.

## Decisions

- The candidate active space is registered for ideal-state benchmarking only.
  It must be rechecked at the production electronic-structure level, visually
  reviewed, and compared with neighboring spaces before a production claim.
- The primary PBE0/def2-SVP counterpoise series and structural sensitivities
  remain incomplete.
- No Nexus emulator job has been submitted and no hardware credits have been
  consumed.

## Next

- Resume and complete the PBE0/def2-SVP compact-primary series.
- Generate Hamiltonians only after the production-level orbital recheck.
- Run ideal VQE against exact active-space diagonalization before any noisy or
  remote-backend work.
