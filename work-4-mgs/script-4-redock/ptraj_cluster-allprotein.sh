#!/bin/sh

# === Input files ===
prmtop=out.prmtop
reference=out.pdb

# trajectory list
traj_list="prd1.mdcrd"

# residue ranges
protein_res="1-646"

# directories for output
out_bb=cluster_backbone
out_all=cluster_allatom

mkdir -p $out_bb
mkdir -p $out_all


########## 1. Create cpptraj input file ##########
cat > ptrajInput.dat <<EOF
### === Load trajectories ===
$(for t in $traj_list; do
echo "trajin $t"
done)

### === Imaging + alignment ===
autoimage :$protein_res
reference $reference
align :$protein_res@CA,C,N reference

### === Strip solvent/ions ===
strip :PA
strip :PC
strip :OL
strip :WAT
strip :K+
strip :Na+
strip :Cl-
strip :EPW


#########################################################
### === 2. Clustering A: Protein Backbone (CA/C/N) === ###
#########################################################
cluster bb \
    hieragglo epsilon 2 averagelinkage \
    rms :$protein_res@CA,C,N \
    out   $out_bb/bb.cnumvtime.dat \
    info  $out_bb/bb.inf.dat \
    summarysplit $out_bb/bb_split.dat splitframe '500,1000,1500,2000,2500,3000' \
    cpopvtime $out_bb/bb_cpopvtime.agr normframe \
    repout $out_bb/bb_rep repfmt pdb \
    singlerepout $out_bb/bb_singlerep.nc singlerepfmt netcdf \
    avgout $out_bb/bb_avg avgfmt pdb


#############################################################
### === 3. Clustering B: Protein Full Heavy Atoms === #######
#############################################################
cluster allatom \
    hieragglo epsilon 2 averagelinkage \
    rms :$protein_res&!@H= \
    out   $out_all/allatom.cnumvtime.dat \
    info  $out_all/allatom.inf.dat \
    summarysplit $out_all/allatom_split.dat splitframe '500,1000,1500,2000,2500,3000' \
    cpopvtime $out_all/allatom_cpopvtime.agr normframe \
    repout $out_all/allatom_rep repfmt pdb \
    singlerepout $out_all/allatom_singlerep.nc singlerepfmt netcdf \
    avgout $out_all/allatom_avg avgfmt pdb


EOF


########## 3. Run cpptraj ##########
cpptraj_bin=/home3/htlin/amber20/bin/cpptraj
logfile=cpptraj_cluster_log_$(date +%F_%T).txt

$cpptraj_bin -p $prmtop -i ptrajInput.dat > $logfile 2>&1

echo "Clustering finished. Results saved in:"
echo "  - $out_bb/    (backbone clustering)"
echo "  - $out_all/   (all-heavy-atom clustering)"

