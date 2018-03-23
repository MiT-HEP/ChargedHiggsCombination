
dir=/afs/cern.ch/user/s/slaurila/public/CombineResults_taujets_180318_165817_RtauCategoriesCombined


#for mhp in 180 200 220 300 400 500 750 800 1000 1500 2000 2500 3000 5000 7000
for mhp in 180 200 220 300 400 500 750 800
do
    python python/bsmCombination.py -C "-M AsymptoticLimits -t -1 --cminDefaultMinimizerStrategy 0 --rAbsAcc 0.0001 --X-rtd FITTER_NEW_CROSSING_ALGO --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND --X-rtd MINIMIZER_analytic --cminDefaultMinimizerTolerance=0.1" --mhp=${mhp} --tb=10:60:0.5 -c Hptn:13TeV:${dir}/combine_datacard_hplushadronic_m${mhp}.txt -d test/mhmodp/TauNu_MHp${mhp}_tb_10_60_0p5 -q 1nh -t ${dir}/combine_histograms_hplushadronic_m${mhp}_a.root -t ${dir}/combine_histograms_hplushadronic_m${mhp}_b.root --debug -m /afs/cern.ch/user/a/amarini/work/ChHiggs2017/CMSSW_9_4_1/src/ChargedHiggsCombination/FeynHiggs-2.14.0/example/LHCHXSWG/mhmodp-LHCHXSWG.in --Hpm

done

# cd test/mhmodp; ../hadd2.sh
#python python/makeLimitPlot.py -f test/mhmodp/all.root -l mhmodp --xaxis=180,800 --yaxis=0,60 -o test/mhmodp/limit --MH125='test/mhmodp/Tau*/feyn*out'
