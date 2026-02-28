#!/usr/bin/env python3
import sys
from Bio.PDB import PDBParser, NeighborSearch, Selection

# 参数
pdb_file = "out.pdb"      # 输入的PDB文件
ligand_resid = 683             # 小分子残基编号
distance_cutoff = 8.0          # 周围氨基酸的距离，单位 Å
output_file = "pocket_resids.txt"

# 解析PDB
parser = PDBParser(QUIET=True)
structure = parser.get_structure("complex", pdb_file)

# 获取小分子原子
ligand_atoms = []
for model in structure:
    for chain in model:
        for residue in chain:
            if residue.get_id()[1] == ligand_resid:
                ligand_atoms.extend(residue.get_atoms())

# 构建NeighborSearch
all_atoms = [atom for atom in structure.get_atoms() if atom not in ligand_atoms]
ns = NeighborSearch(all_atoms)

# 找到周围残基
neighbor_resids = set()
for atom in ligand_atoms:
    neighbors = ns.search(atom.get_coord(), distance_cutoff, level='R')  # level='R' 返回残基
    for res in neighbors:
        # 排除水分子
        if res.get_resname() not in ['HOH', 'WAT']:
            neighbor_resids.add(res.get_id()[1])

# 保存结果
neighbor_resids = sorted(list(neighbor_resids))
with open(output_file, 'w') as f:
    for resid in neighbor_resids:
        f.write(f"{resid}\n")

print(f"已保存 {len(neighbor_resids)} 个残基到 {output_file}")

