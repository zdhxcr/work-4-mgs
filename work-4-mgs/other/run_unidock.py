
import os
import time
import json
import glob

# 配置参数
config = {
    "target": "cry",
    "nt": 128,
    "ns": 20,
    "seed": 5,
    "sf": "vina",
    "gpu_type": "V100",
    "rs": 3,
    "center_x": 30.949,
    "center_y": 31.005,
    "center_z": 64.178,
    "size_x": 20,
    "size_y": 20,
    "size_z": 20
}

cmdlist = []

# 处理小分子文件
liglist = []
liglist = glob.glob("../ligand/*.pdbqt")

print("找到的小分子文件数量:", len(liglist))
print("前10个小分子文件:", liglist[:10])

# 创建小分子列表文件
with open("{}_ligands.txt".format(config["target"]), "w") as f:
    for lig in liglist:
        f.write(lig + "\n")

# 构建对接命令
if config["sf"] == 'ad4':
    cmd = "unidock_ad4 --maps {} ".format("./{}".format(config["target"]))
else:
    cmd = "unidock --receptor {} ".format("./{}.pdbqt".format(config["target"]))

cmd += "--ligand_index {} ".format("{}_ligands.txt".format(config["target"]))
cmd += "--center_x {:.2f} --center_y {:.2f} --center_z {:.2f} ".format(
    config["center_x"], config["center_y"], config["center_z"])
cmd += "--size_x {} --size_y {} --size_z {} ".format(
    config["size_x"], config["size_y"], config["size_z"])
cmd += "--dir ./result/{} ".format(config["target"])
cmd += "--exhaustiveness {} ".format(config["nt"])
cmd += "--max_step {} ".format(config["ns"])
cmd += "--num_modes 9 --scoring {} --refine_step {} ".format(config["sf"], config.get("rs", 5))

# 创建结果目录
os.makedirs("result/{}".format(config["target"]), exist_ok=True)

# 写入运行脚本
with open("rundock.sh", "w") as f:
    f.write(cmd)

print("对接命令已写入 rundock.sh")
print("命令内容:", cmd)

# 执行对接计算
os.system("echo 'costtime'>> result/costtime.csv")
st = time.time()
os.system("bash rundock.sh")
os.system("echo '{}'>> result/costtime.csv".format(time.time()-st))

# 收集结果
result_dir = "./result/{}".format(config["target"])
fns = []
for _, _, files in os.walk(result_dir):
    fns = files
    break

# 生成结果CSV文件
csv_name = "./result/{}_{}.csv".format(
    config["target"], config["sf"], config["nt"], config["ns"], 
    config["seed"], config.get("gpu_type", 'V100')
)

with open(csv_name, "w") as f:
    f.write("ligand_file,type,score\n")

# 处理每个对接结果
for fn in fns:
    if fn.endswith(".pdbqt"):  # 只处理pdbqt结果文件
        result_file = os.path.join(result_dir, fn)
        try:
            with open(result_file, "r") as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    # 解析对接分数（根据unidock输出格式调整）
                    score_line = lines[1]  # 通常是第二行包含分数信息
                    score_parts = score_line.split()
                    if len(score_parts) >= 4:
                        score = float(score_parts[3])
                        
                        # 根据文件名判断分子类型
                        if "active" in fn.lower():
                            mol_type = "active"
                        else:
                            mol_type = "decoy"
                        
                        # 写入结果
                        with open(csv_name, "a") as csv_f:
                            csv_f.write("{},{},{}\n".format(fn, mol_type, score))
        except Exception as e:
            print(f"处理文件 {fn} 时出错: {e}")

print("对接完成！结果保存在:", csv_name)
