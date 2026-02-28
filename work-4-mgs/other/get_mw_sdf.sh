#!/bin/bash

output="all_mw_results.txt"
> "$output"  # 清空输出文件

for sdf in *.sdf; do
    if [[ -f "$sdf" ]]; then
        echo "Processing $sdf..."

        # 使用 obabel 输出 SMILES 并附带 MW，提取分子名和 MW
        obabel "$sdf" -osmi --append "MW" 2>/dev/null | while read -r line; do
            smiles=$(echo "$line" | awk '{print $1}')
            name=$(echo "$line" | awk '{print $2}')
            mw=$(echo "$line" | awk '{print $3}')

            if [[ -n "$name" && "$mw" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                echo "$name $mw" >> "$output"
            fi
        done
    fi
done

echo "✅ Done! Results saved to $output"

