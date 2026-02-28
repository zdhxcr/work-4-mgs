#!/bin/bash

# 目标文件夹
target_dir="./filtered-1"
mkdir -p "$target_dir"

# 限制数量
max_files=1830
count=0

for sdf in *.sdf; do
    if [[ -f "$sdf" ]]; then
        echo "Processing $sdf..."

        # 使用 obabel 获取 SMILES、名称、分子质量
        obabel "$sdf" -osmi --append "MW" 2>/dev/null | while read -r line; do
            smiles=$(echo "$line" | awk '{print $1}')
            name=$(echo "$line" | awk '{print $2}')
            mw=$(echo "$line" | awk '{print $3}')

            # 检查格式和分子量范围
            if [[ -n "$name" && "$mw" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                if (( $(echo "$mw >= 600" | bc -l) )) && (( $(echo "$mw <= 610" | bc -l) )); then
                    # 拷贝文件
                    cp "$sdf" "$target_dir/"
                    ((count++))
                    echo "✔ $name $mw -> copied. Total: $count"

                    # 达到数量上限就退出整个脚本
                    if [[ $count -ge $max_files ]]; then
                        echo "🎯 已复制 $count 个文件，达到目标，脚本终止。"
                        exit 0
                    fi

                    # 匹配后就跳出 while（不再处理该文件的多条结构）
                    break
                fi
            fi
        done
    fi
done

echo "✅ 筛选完成，总共复制了 $count 个文件。"

