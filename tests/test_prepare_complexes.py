import importlib.util
from pathlib import Path

import numpy as np
import pytest

Chem = pytest.importorskip(
    "rdkit.Chem", reason="requires licensed/local chemistry stack"
)
pytest.importorskip("openmm", reason="requires local molecular-modeling stack")
pytest.importorskip("openff.toolkit", reason="requires local molecular-modeling stack")

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_complexes", ROOT / "scripts" / "01_prepare_complexes.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_4dtmp_generation_preserves_retained_coordinates(tmp_path):
    output = tmp_path / "WT_4DTMP.sdf"
    module.write_ligand_sdf("WT_4DTMP", output)

    mol = next(
        mol
        for mol in Chem.SDMolSupplier(str(output), removeHs=False)
        if mol is not None
    )
    heavy = Chem.RemoveHs(mol)
    assert heavy.GetNumAtoms() == 20

    source = module.load_ligand_from_pdb(
        ROOT / "data/raw/pdbs/6XG5.pdb", residue_name="TOP"
    )
    source_h = Chem.RemoveHs(source)
    assert source_h.GetNumAtoms() == 21

    source_h = Chem.RemoveHs(source)
    match = source_h.GetSubstructMatch(heavy)
    assert len(match) == heavy.GetNumAtoms()
    src_conf = np.asarray(source_h.GetConformer().GetPositions())[list(match)]
    new_conf = np.asarray(heavy.GetConformer().GetPositions())
    assert np.allclose(src_conf, new_conf, atol=1e-6)
