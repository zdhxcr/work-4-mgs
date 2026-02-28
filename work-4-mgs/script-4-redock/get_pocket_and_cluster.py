#!/usr/bin/env python3
"""
get_pocket_and_cluster.py

Usage:
    python3 get_pocket_and_cluster.py com.pdb LIG_RESID [--cutoff 8.0] [--range 1-498] [--traj traj1.mdcrd,traj2.mdcrd] [--prmtop out.prmtop] [--ref out.pdb]

功能：
1. 提取指定氨基酸序列范围内(默认1-498)小分子附近指定距离(默认8Å)的氨基酸残基
2. 生成一个聚类分析输入文件，同时进行两种聚类：
   - cluster_backbone: 使用主链原子CA,C,N聚类
   - cluster_heavy: 使用所有重原子聚类
3. 所有聚类输出到对应的子目录中

Output:
    pocket_resids.txt  -> 一行一个残基号（按从小到大排序）
    ptrajInput.dat     -> 聚类输入文件
    两个文件夹中的聚类结果文件
"""

import sys
import math
import subprocess
import os
from datetime import datetime

def parse_residue_range(range_str):
    """解析残基范围字符串，如 '1-498'"""
    try:
        start, end = map(int, range_str.split('-'))
        return start, end
    except:
        print(f"Error: 无效的范围格式 '{range_str}'，应使用 'start-end' 格式")
        sys.exit(1)

def parse_trajectory_files(traj_str):
    """解析轨迹文件字符串，如 'traj1.mdcrd,traj2.mdcrd'"""
    if not traj_str:
        return ["prd.mdcrd"]  # 默认轨迹文件
    return [traj.strip() for traj in traj_str.split(',')]

def get_pocket_residues(pdbfile, ligand_resid, residue_range=None, cutoff=8.0):
    """提取口袋残基"""
    
    # standard 20 amino acids 3-letter codes
    AA3 = {"ALA","ARG","ASN","ASP","CYS","GLN","GLU","GLY","HIS","ILE",
           "LEU","LYS","MET","PHE","PRO","SER","THR","TRP","TYR","VAL"}

    ligand_atoms = []   # list of (x,y,z)
    protein_atoms = {}  # key: (resid, resname), value: list of (x,y,z, atomname)

    range_start, range_end = residue_range if residue_range else (None, None)

    with open(pdbfile) as f:
        for line in f:
            if not (line.startswith("ATOM") or line.startswith("HETATM")):
                continue
            
            # 使用固定列格式解析PDB文件，这样更可靠
            try:
                atomname = line[12:16].strip()
                resname = line[17:20].strip()
                resid = int(line[22:26].strip())  # 残基号
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())
            except:
                # 如果固定列解析失败，尝试分割方式
                parts = line.split()
                if len(parts) < 8:
                    continue
                atomname = parts[2]
                resname = parts[3]
                try:
                    resid = int(parts[4])
                except:
                    continue
                try:
                    x = float(parts[5]); y = float(parts[6]); z = float(parts[7])
                except:
                    continue

            # 检测氢原子
            is_h = atomname.strip().startswith("H") or atomname.strip().upper().startswith("DH")

            # 检查是否为配体原子（残基号匹配）
            if resid == ligand_resid:
                ligand_atoms.append((x,y,z))
                continue

            # 只考虑蛋白残基（在指定范围内）和非氢原子
            if residue_range and (resid < range_start or resid > range_end):
                continue
                
            if resname.upper() in AA3 and (not is_h):
                key = (resid, resname)
                protein_atoms.setdefault(key, []).append((x,y,z, atomname))

    if not ligand_atoms:
        print(f"Error: 在 {pdbfile} 中未找到配体残基 {ligand_resid} 的原子")
        print("请检查PDB文件中是否存在该残基号的原子")
        sys.exit(2)

    print(f"找到 {len(ligand_atoms)} 个配体原子")
    print(f"找到 {len(protein_atoms)} 个蛋白残基在指定范围内")

    # 计算每个残基到配体原子的最小距离
    pocket_resids = set()
    cutoff2 = cutoff * cutoff

    for (resid, resname), atoms in protein_atoms.items():
        min2 = None
        for (ax,ay,az,_) in atoms:
            for (lx,ly,lz) in ligand_atoms:
                dx = ax - lx; dy = ay - ly; dz = az - lz
                d2 = dx*dx + dy*dy + dz*dz
                if (min2 is None) or (d2 < min2):
                    min2 = d2
                if min2 is not None and min2 <= cutoff2:
                    pocket_resids.add(resid)
                    break
            if min2 is not None and min2 <= cutoff2:
                break

    return sorted(pocket_resids)

def create_cluster_script(pocket_resids_str, trajectory_files, prmtop="out.prmtop", 
                         reference="out.pdb"):
    """创建聚类分析输入文件 - 同时进行两种聚类"""
    
    # 构建轨迹输入部分
    traj_lines = []
    for traj_file in trajectory_files:
        traj_lines.append(f"trajin {traj_file}")
    
    traj_input = "\n".join(traj_lines)
    
    # 创建输出目录（先创建空目录，cpptraj会创建子目录）
    os.makedirs("cluster_backbone", exist_ok=True)
    os.makedirs("cluster_heavy", exist_ok=True)
    
    cluster_script = f"""### === Load trajectories ===
{traj_input}

### === Imaging + alignment ===
autoimage :{pocket_resids_str}@CA,C,N
reference {reference}
align :{pocket_resids_str}@CA,C,N reference

### === Strip solvent/ions ===
strip :PA:PC:OL:WAT:K+:Na+:Cl- outprefix LIG

#########################################################
### === 1. Clustering A: Protein Backbone (CA/C/N) === ###
#########################################################
cluster bb \\
    hieragglo epsilon 2 averagelinkage \\
    rms :{pocket_resids_str}@CA,C,N nofit \\
    pairdist cluster_backbone/bb_pair-distance.dat \\
    out   cluster_backbone/bb.cnumvtime.dat \\
    info  cluster_backbone/bb.inf.dat \\
    summarysplit cluster_backbone/bb_split.dat splitframe '500,1000,1500,2000,2500,3000' \\
    cpopvtime cluster_backbone/bb_cpopvtime.agr normframe \\
    repout cluster_backbone/bb_rep repfmt pdb \\
    singlerepout cluster_backbone/bb_singlerep.nc singlerepfmt netcdf \\
    avgout cluster_backbone/bb_avg avgfmt pdb

#############################################################
### === 2. Clustering B: Protein Full Heavy Atoms === #######
#############################################################
cluster allatom \\
    hieragglo epsilon 2 averagelinkage \\
    rms :{pocket_resids_str}&!@H= nofit \\
    pairdist cluster_heavy/allatom_pair-distance.dat \\
    out   cluster_heavy/allatom.cnumvtime.dat \\
    info  cluster_heavy/allatom.inf.dat \\
    summarysplit cluster_heavy/allatom_split.dat splitframe '500,1000,1500,2000,2500,3000' \\
    cpopvtime cluster_heavy/allatom_cpopvtime.agr normframe \\
    repout cluster_heavy/allatom_rep repfmt pdb \\
    singlerepout cluster_heavy/allatom_singlerep.nc singlerepfmt netcdf \\
    avgout cluster_heavy/allatom_avg avgfmt pdb
"""
    
    with open("ptrajInput.dat", "w") as f:
        f.write(cluster_script)
    
    return cluster_script

def run_clustering(prmtop="out.prmtop", cpptraj_path="cpptraj"):
    """运行聚类分析"""
    
    # 检查cpptraj是否可用
    cpptraj_cmd = None
    
    # 1. 检查指定的路径
    if cpptraj_path and os.path.exists(cpptraj_path):
        cpptraj_cmd = cpptraj_path
    else:
        # 2. 尝试在PATH中查找
        try:
            result = subprocess.run(["which", "cpptraj"], capture_output=True, text=True)
            if result.returncode == 0:
                cpptraj_cmd = "cpptraj"
        except:
            pass
        
        # 3. 尝试查找MPI版本
        if not cpptraj_cmd:
            try:
                result = subprocess.run(["which", "cpptraj.MPI"], capture_output=True, text=True)
                if result.returncode == 0:
                    cpptraj_cmd = "cpptraj.MPI"
            except:
                pass
        
        # 4. 尝试默认路径
        if not cpptraj_cmd:
            default_paths = [
                "/home3/htlin/amber20/bin/cpptraj",
                "/home3/htlin/amber20/bin/cpptraj.MPI",
                "/usr/local/amber20/bin/cpptraj",
                "/opt/amber20/bin/cpptraj"
            ]
            for path in default_paths:
                if os.path.exists(path):
                    cpptraj_cmd = path
                    break
    
    if not cpptraj_cmd:
        print(f"Warning: 找不到cpptraj")
        print(f"请手动运行: cpptraj -p {prmtop} -i ptrajInput.dat")
        return False
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    logfile = f"cpptraj_cluster_log_{timestamp}.txt"
    
    # 构建命令 - 使用单进程版本，避免MPI问题
    cmd = [cpptraj_cmd, "-p", prmtop, "-i", "ptrajInput.dat"]
    
    print(f"运行聚类分析...")
    print(f"使用命令: {' '.join(cmd)}")
    print(f"日志文件: {logfile}")
    
    try:
        with open(logfile, "w") as log:
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
        
        if result.returncode == 0:
            print("聚类分析完成!")
            return True
        else:
            print("聚类分析可能出错，请检查日志文件")
            return False
    except Exception as e:
        print(f"运行聚类时出错: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 get_pocket_and_cluster.py com.pdb LIG_RESID [options]")
        print("")
        print("选项:")
        print("  --cutoff 8.0          距离cutoff (默认: 8.0 Å)")
        print("  --range 1-498         残基范围 (默认: 1-498)")
        print("  --traj file1,file2    轨迹文件，用逗号分隔 (默认: prd.mdcrd)")
        print("  --prmtop file.prmtop  拓扑文件 (默认: out.prmtop)")
        print("  --ref file.pdb        参考结构文件 (默认: out.pdb)")
        print("")
        print("示例:")
        print("  python3 get_pocket_and_cluster.py com.pdb 608")
        print("  python3 get_pocket_and_cluster.py com.pdb 608 --cutoff 8.0 --range 1-498")
        print("  python3 get_pocket_and_cluster.py com.pdb 608 --traj md1.mdcrd,md2.mdcrd,md3.mdcrd")
        print("  python3 get_pocket_and_cluster.py com.pdb 608 --traj production.mdcrd --prmtop complex.prmtop")
        sys.exit(1)

    pdbfile = sys.argv[1]
    try:
        ligand_resid = int(sys.argv[2])
    except ValueError:
        print("Error: 配体残基号必须为整数")
        sys.exit(1)

    # 解析可选参数
    cutoff = 8.0
    residue_range = (1, 498)
    trajectory_files = ["prd.mdcrd"]  # 默认轨迹文件
    prmtop_file = "out.prmtop"  # 默认拓扑文件
    reference_file = "out.pdb"  # 默认参考结构
    
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--cutoff" and i+1 < len(sys.argv):
            try:
                cutoff = float(sys.argv[i+1])
                i += 2
            except ValueError:
                print("Error: 距离 cutoff 必须为数字")
                sys.exit(1)
        elif sys.argv[i] == "--range" and i+1 < len(sys.argv):
            residue_range = parse_residue_range(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == "--traj" and i+1 < len(sys.argv):
            trajectory_files = parse_trajectory_files(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == "--prmtop" and i+1 < len(sys.argv):
            prmtop_file = sys.argv[i+1]
            i += 2
        elif sys.argv[i] == "--ref" and i+1 < len(sys.argv):
            reference_file = sys.argv[i+1]
            i += 2
        else:
            print(f"Warning: 未知参数 {sys.argv[i]}")
            i += 1

    print(f"参数设置:")
    print(f"  PDB文件: {pdbfile}")
    print(f"  配体残基: {ligand_resid}")
    print(f"  残基范围: {residue_range[0]}-{residue_range[1]}")
    print(f"  距离 cutoff: {cutoff} Å")
    print(f"  拓扑文件: {prmtop_file}")
    print(f"  参考结构: {reference_file}")
    print(f"  轨迹文件: {', '.join(trajectory_files)}")

    # 检查必要的文件是否存在
    if not os.path.exists(pdbfile):
        print(f"Error: PDB文件不存在: {pdbfile}")
        sys.exit(1)

    if not os.path.exists(prmtop_file):
        print(f"Error: 拓扑文件不存在: {prmtop_file}")
        sys.exit(1)

    if not os.path.exists(reference_file):
        print(f"Warning: 参考结构文件不存在: {reference_file}")
        print("将使用输入PDB文件作为参考")
        reference_file = pdbfile

    # 检查轨迹文件是否存在
    missing_trajs = [traj for traj in trajectory_files if not os.path.exists(traj)]
    if missing_trajs:
        print(f"Error: 以下轨迹文件不存在: {', '.join(missing_trajs)}")
        sys.exit(1)

    # 1. 提取口袋残基
    print(f"\n提取口袋残基...")
    pocket_resids = get_pocket_residues(pdbfile, ligand_resid, residue_range, cutoff)
    
    # 写入输出文件
    outname = "pocket_resids.txt"
    with open(outname, "w") as out:
        for r in pocket_resids:
            out.write(f"{r}\n")

    # 打印结果
    print(f"\n在配体残基 {ligand_resid} 周围 {cutoff} Å 内找到 {len(pocket_resids)} 个蛋白残基:")
    print(" ".join(map(str, pocket_resids)))
    print(f"写入: {outname}")

    if not pocket_resids:
        print("Warning: 未找到口袋残基，无法进行聚类分析")
        sys.exit(3)

    # 2. 创建聚类脚本 - 同时进行两种聚类
    pocket_resids_str = ",".join(map(str, pocket_resids))
    print(f"\n创建聚类输入文件...")
    print(f"将同时进行两种聚类:")
    print(f"  1. 主链原子聚类 (CA, C, N) -> cluster_backbone/")
    print(f"  2. 重原子聚类 (所有非氢原子) -> cluster_heavy/")
    
    create_cluster_script(pocket_resids_str, trajectory_files, prmtop_file, reference_file)
    print("写入: ptrajInput.dat")

    # 3. 自动运行聚类分析
    print(f"\n开始自动聚类分析...")
    success = run_clustering(prmtop_file)
    
    if success:
        print(f"\n" + "="*60)
        print("聚类分析完成:")
        print("="*60)
        print(f"✓ 主链原子聚类结果保存在: cluster_backbone/")
        print(f"  主要输出文件:")
        print(f"    - bb_rep*.pdb (代表性结构)")
        print(f"    - bb_avg*.pdb (平均结构)")
        print(f"    - bb.inf.dat (聚类信息)")
        
        print(f"\n✓ 重原子聚类结果保存在: cluster_heavy/")
        print(f"  主要输出文件:")
        print(f"    - allatom_rep*.pdb (代表性结构)")
        print(f"    - allatom_avg*.pdb (平均结构)")
        print(f"    - allatom.inf.dat (聚类信息)")
        
        print(f"\n✓ 口袋残基列表: {outname}")
        print(f"✓ 聚类输入脚本: ptrajInput.dat")
        print(f"✓ 运行日志: cpptraj_cluster_log_*.txt")
    else:
        print("聚类分析遇到问题，请检查日志文件")

if __name__ == "__main__":
    main()
