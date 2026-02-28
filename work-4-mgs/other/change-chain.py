from Bio import PDB
import sys

def rename_chains(input_pdb, output_pdb):
    # 定义链 ID 映射关系
    chain_map = {"A": "A", "C": "B", "D": "C", "E": "D"}

    parser = PDB.PDBParser(QUIET=True)
    structure = parser.get_structure("model", input_pdb)

    for model in structure:
        for chain in model:
            old_id = chain.id
            if old_id in chain_map:
                chain.id = chain_map[old_id]

    io = PDB.PDBIO()
    io.set_structure(structure)
    io.save(output_pdb)
    print(f"链 ID 已修改并保存到 {output_pdb}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python rename_chain.py input.pdb output.pdb")
        sys.exit(1)

    input_pdb = sys.argv[1]
    output_pdb = sys.argv[2]
    rename_chains(input_pdb, output_pdb)


