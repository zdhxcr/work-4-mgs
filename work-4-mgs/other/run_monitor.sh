#!/bin/sh
#
##specify the GPU ID you will use 
GPUID=0

function exam_modify_gpuid(){
   local file=$1
   formalGPUid=$(grep 'CUDA_VISIBLE_DEVICES=' "$file" | awk -F '=' '{print $2}')
   if [[ $formalGPUid -eq $GPUID ]]; then
      echo "The GPU ID in $file is correct."
   else
      echo "The GPU ID in $file is incorrect. It should be $GPUID."
      sed -i "s/CUDA_VISIBLE_DEVICES=$formalGPUid/CUDA_VISIBLE_DEVICES=$GPUID/" "$file"
      echo "The GPU ID in $file has been modified to $GPUID."
   fi
}
# timer
for ((i=3; i>0; i--))
do
    sleep 1 &
    printf "\b\b\b\b\b\b%-3s" $i
    wait
done
printf "\b\b\b\b\b\b"

safe2run=0

while [ $safe2run -ne 1 ]
do

   #mem=`/usr/bin/nvidia-smi | awk 'BEGIN{nline=1}{if ($0 ~/0  GeForce/) {nline = NR} if (NR > 1 && NR == nline+1) {print $9}}'`
   ##echo $mem

   ##tmp=${mem:1:3}
   #tmp=`echo $mem | head -c -4`
   ##echo $tmp

   ##declare -i nm=$tmp
   #nm=$tmp
   #echo $tmp

   #declare -i nm=$tmp
   ####pchen annocated the code above at 2024.5.7, cause in gm41 42 43 31 32 33(which in Room 103), the NVIDIA driver is newer than the machines in 702A, so string "/0  GeForce/" can't be matched.
   ####And it seems difficult to judge whether the GPU is been using by video memory when running MD task. When running a MD task, the video memory won't change much.
   
   if [ $GPUID == 0 ]
   then
      util=$(/usr/bin/nvidia-smi | awk 'BEGIN{nline=1}{if ($0 ~/0  NVIDIA GeForce/) {nline = NR} if (NR > 1 && NR == nline+1) {print $13}}')
     elif [ $GPUID == 1 ]
     then
        util=$(/usr/bin/nvidia-smi | awk 'BEGIN{nline=1}{if ($0 ~/1  NVIDIA GeForce/) {nline = NR} if (NR > 1 && NR == nline+1) {print $13}}')
   else
      echo "wrong GPUID!" 
      break
   fi

   nu=${util%%\%*}


    if [ $nu -gt 15 ]
    then
       echo "job running"
       safe2run=0

       # timer
       for ((i=300; i>0; i--))
       do
           sleep 1 &
           printf "\b\b\b\b%-3s" $i
           wait
       done
       printf "\b\b\b\b"

    else
       echo "no job running"
       safe2run=1

     # echo "running parmGen_box..."
     # ./parmGen_box.sh
     # echo "done parmGen_box..."
     #
      exam_modify_gpuid run_heat.sh
      echo "running heat..."
      ./run_heat.sh
      echo "done heat..."
     
      exam_modify_gpuid run_npt.sh
      echo "running npt..."
      ./run_npt.gpu.sh
      echo "done npt..."

      exam_modify_gpuid run_npt.sh
      echo "running prd1..."
      ./run_prd1.gpu.sh
      echo "done npt..."
      
      exam_modify_gpuid run_npt.sh
      echo "running prd2..."
      ./run_prd2.gpu.sh
      echo "done npt..."
    fi
done

email_notify.py -jn "$(basename $(pwd)) md"
