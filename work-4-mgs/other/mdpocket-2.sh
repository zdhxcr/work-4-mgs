#!/bin/bash

# 检查是否提供了输入参数
if [ $# -eq 0 ]; then
    echo "使用方法: $0 <前缀名称>"
    exit 1
fi

PREFIX=$1
OUTPUT_DIR="${PREFIX}-p1p2l-pocket"

# 创建输出目录
mkdir -p $OUTPUT_DIR

# 运行 mdpocket 命令
/home/yxzhang/yxzhang/system/fpocket2/bin/mdpocket -L pdb_list.txt -f my_pocket-cry-1.pdb -o $OUTPUT_DIR

echo "分析完成！结果保存在 $OUTPUT_DIR 目录中"
