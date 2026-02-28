import os
from rdkit import Chem
from rdkit.Chem import Descriptors, SDWriter

# 输入和输出目录
input_dir = "/home/yxzhang/yxzhang/dock/dock-4/ligand/sdf"
output_dir = "/home/yxzhang/yxzhang/dock/dock-4/ligand/sdf/filter-sdf"

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 分子量范围
min_mw = 250
max_mw = 450

for filename in os.listdir(input_dir):
    if filename.endswith(".sdf"):
        input_path = os.path.join(input_dir, filename)
        suppl = Chem.SDMolSupplier(input_path)
        filtered_mols = []

        for mol in suppl:
            if mol is None:
                continue
            mw = Descriptors.MolWt(mol)
            if min_mw <= mw <= max_mw:
                filtered_mols.append(mol)

        if filtered_mols:
            output_path = os.path.join(output_dir, filename)
            writer = SDWriter(output_path)
            for mol in filtered_mols:
                writer.write(mol)
            writer.close()
            print(f"{filename} ✅ 已筛选并保存")
        else:
            print(f"{filename} ❌ 无符合分子量范围的分子")

