#!/bin/bash
# ===========================================================
# Automated MDpocket preparation and analysis pipeline
# Steps:
#   1. Align trajectories (cpptraj)
#   2. Generate DCD file and snapshots
#   3. Run mdpocket pocket analysis
# ===========================================================

# === 路径与输入设置 ===
AMBER_CPPTRAJ=/home3/htlin/amber20/bin/cpptraj.MPI
MDPOCKET_BIN=/home/yxzhang/yxzhang/system/fpocket2/bin/mdpocket

prmtop=../out.prmtop          # Amber 拓扑文件
refpdb=../out.pdb             # 参考结构
mdcrd1=../prd1.mdcrd          # 轨迹1
mdcrd2=../prd2.mdcrd          # 轨迹2
protein_range="1-347"         # 蛋白编号范围（根据体系调整）
aligned_mdcrd=align.mdcrd     # 对齐后的轨迹
out_dcd=trajectory_superimposed.dcd
snap_dir=snapshots
total_frames=2000
interval=20                   # 每隔多少帧取一帧
pdb_list=pdb_list.txt

# === 并行 CPU 核心数 ===
NCPU=4

# ===========================================================
echo "🚀 Step 1: Aligning trajectories..."
cat > ptraj_align.dat <<EOF
parm $prmtop
trajin $mdcrd1
trajin $mdcrd2
autoimage
reference $refpdb
align :$protein_range@CA,C,N,O,S
trajout $aligned_mdcrd crd
EOF

mpirun -np $NCPU $AMBER_CPPTRAJ -i ptraj_align.dat > ptraj_align.log 2>&1
if [ $? -ne 0 ]; then
  echo "❌ Error during alignment. Check ptraj_align.log"
  exit 1
fi
echo "✅ Alignment completed: $aligned_mdcrd"

# ===========================================================
echo "🧬 Step 2: Generating DCD and snapshots..."
mkdir -p $snap_dir

# --- 生成 DCD ---
cat > ptraj_dcd.dat <<EOF
parm $prmtop
trajin $aligned_mdcrd
reference $refpdb
strip !:$protein_range
rms reference :$protein_range
trajout $out_dcd charmm
EOF

# --- 生成 snapshots ---
cat > ptraj_snapshots.dat <<EOF
parm $prmtop
trajin $aligned_mdcrd 1 $total_frames $interval
reference $refpdb
strip !:$protein_range
rms reference :$protein_range
trajout $snap_dir/frame.pdb pdb multi
EOF

mpirun -np $NCPU $AMBER_CPPTRAJ -i ptraj_dcd.dat > ptraj_dcd.log 2>&1
mpirun -np $NCPU $AMBER_CPPTRAJ -i ptraj_snapshots.dat > ptraj_snapshots.log 2>&1

if [ $? -ne 0 ]; then
  echo "❌ Error during DCD/snapshot generation. Check ptraj logs."
  exit 1
fi

echo "✅ DCD generated: $out_dcd"
echo "✅ Snapshots saved to: $snap_dir"

# ===========================================================
echo "🔍 Step 3: Running mdpocket..."
ls $snap_dir/frame.pdb* > $pdb_list

$MDPOCKET_BIN -L $pdb_list -o mdpout_snapshots > mdpocket.log 2>&1

if [ $? -ne 0 ]; then
  echo "❌ Error during mdpocket execution. Check mdpocket.log"
  exit 1
fi

echo "✅ mdpocket analysis complete!"
echo "📂 Results saved in: mdpout_snapshots/"
echo "📝 Log: mdpocket.log"

# ===========================================================
echo "🎉 Pipeline finished successfully!"

