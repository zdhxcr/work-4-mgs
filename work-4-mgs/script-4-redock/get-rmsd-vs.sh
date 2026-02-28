#!/bin/bash
# 简化版 - dock_processing_simple.sh

echo "开始处理对接文件..."

# 步骤1: 复制文件并运行LEDock
echo "步骤1: 复制对接文件并运行LEDock..."
cd rmsd/ligand
cp mol.6pai.dok mol.6q0v.dok mol.6q0w.dok mol.6ue5.dok ..
cd ..
./ledock.sh -spli mol.6pai.dok
./ledock.sh -spli mol.6q0w.dok
./ledock.sh -spli mol.6q0v.dok
./ledock.sh -spli mol.6ue5.dok

# 步骤2: 处理PDB文件
echo "步骤2: 处理PDB文件中的残基名..."
# 处理mol.6q0w文件
for file in mol.6q0w_dock001.pdb mol.6q0w_dock002.pdb mol.6q0w_dock003.pdb; do
    if [ -f "$file" ]; then
        sed -i 's/ CL  LIG/CL   LIG/g' "$file"
        echo "已处理 $file"
    fi
done

# 处理mol.6q0v文件
for file in mol.6q0v_dock001.pdb mol.6q0v_dock002.pdb mol.6q0v_dock003.pdb; do
    if [ -f "$file" ]; then
        sed -i 's/ CL  LIG/CL   LIG/g' "$file"
        sed -i 's/ BR  LIG/BR   LIG/g' "$file"
        sed -i 's/ CL1 LIG/CL1  LIG/g' "$file"
        echo "已处理 $file"
    fi
done

# 步骤3: 准备虚拟筛选
echo "步骤3: 准备虚拟筛选文件..."
cp pro.pdb dock.in ../vs/
cd ../vs
sed -i 's|ligand/ligands.txt|ligand-1/ligands-1.txt|g' dock.in
./get_dockin_ledock.sh

echo "所有步骤完成!"
