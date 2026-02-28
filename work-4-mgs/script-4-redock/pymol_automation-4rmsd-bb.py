from pymol import cmd
import os
# ======== 参数 ==========
rep_file = "bb_rep.c0.pdb"
obj_name = "target"   # 用 target 替代 rep，避免保留字问题
output_dir = "rmsd"
os.makedirs(output_dir, exist_ok=True)

# ======== 1. 打开 allatom_rep.c0.pdb ========
cmd.load(rep_file, obj_name)

# 去除氢、小分子
cmd.remove(f"{obj_name} and hydro")
cmd.remove(f"{obj_name} and not polymer")

# 保存 protein.pdb
cmd.save(f"{output_dir}/protein.pdb", f"{obj_name} and polymer")

# ======== 2. fetch 并 align 四个结构 ========
pdb_list = ["6pai", "6q0w", "6q0v", "6ue5"]

for pdbid in pdb_list:
    cmd.fetch(pdbid)
    cmd.align(pdbid, obj_name)   # 对齐到 target

# ======== 3. 提取各配体并保存 mol2 ========
lig_dict = {
    "6pai": "O6M",
    "6q0w": "EF6",
    "6q0v": "P7M",
    "6ue5": "Q5J",
}

for pdbid, lig in lig_dict.items():
    sel_name = f"{pdbid}_lig"
    cmd.select(sel_name, f"{pdbid} and resn {lig}")
    cmd.save(f"{output_dir}/mol.{pdbid}.mol2", sel_name)
    cmd.delete(sel_name)

# ======== 4. 保存会话文件 ========
cmd.save(f"{output_dir}/all.pse")

