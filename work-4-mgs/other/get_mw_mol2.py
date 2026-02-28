import os
from rdkit import Chem
from rdkit.Chem import Descriptors

mol2_folder = "/home/yxzhang/yxzhang/dock/dock-3/random/split_mol2-random/test" 
output_txt = "molecular_weights.txt"


mol2_files = [f for f in os.listdir(mol2_folder) if f.endswith(".mol2")]


with open(output_txt, "w") as out:
    for file in mol2_files:
        file_path = os.path.join(mol2_folder, file)
        mol_name = os.path.splitext(file)[0]
        try:
            mol = Chem.MolFromMol2File(file_path, sanitize=False)
            if mol is not None:
                mw = Descriptors.MolWt(mol)
                out.write(f"{mol_name} {mw:.2f}\n")
            else:
                out.write(f"{mol_name} Error\n")
        except Exception as e:
            out.write(f"{mol_name} Error\n")

