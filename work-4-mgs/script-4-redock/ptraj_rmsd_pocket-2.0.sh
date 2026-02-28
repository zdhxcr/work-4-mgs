#!/bin/sh

# 参数设置
prmtop=out.prmtop
pro_resid=1-682
resid_file="pocket_resids.txt"
output=6sj7_rmsd_pocket-bb-8.dat
output2=6sj7_rmsd_pocket-all-8.dat

# amber20路径
cpptraj=/home3/htlin/amber20/bin/cpptraj.MPI

# 读取残基列表并转换为cpptraj格式
resid_list=$(cat "$resid_file" | tr '\n' ',' | sed 's/,$//')
echo "选择的残基: $resid_list"
resid_count=$(cat "$resid_file" | wc -l)

# 生成cpptraj输入文件
cat > ptrajInput.dat <<EOF
trajin prd1.mdcrd
trajin prd2.mdcrd

autoimage

# 先对整个蛋白主链进行对齐
align :$pro_resid&@CA,C,N,O first  # 假设蛋白编号1-607, 根据你的系统修改

# 计算小分子周围残基主链RMSD
rms :$resid_list&@CA,C,N,O first nofit out $output

# 计算小分子周围残基所有非氢原子RMSD
rms :$resid_list&!@H= first nofit out $output2

EOF

# 运行cpptraj
$cpptraj $prmtop -i ptrajInput.dat

