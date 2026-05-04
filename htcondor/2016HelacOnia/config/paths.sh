#!/bin/bash

# AFS submit area
export HTCONDOR_BASE="/afs/cern.ch/user/l/leyao/private/JJ/MC_HTcondor/2016HelacOnia"

# EOS-backed production area, accessed through the logical /afs/work path
export CMSSW_BASE="/afs/cern.ch/user/l/leyao/work/26JJ/MC_Maker/HelacOnia2016/CMSSW_10_6_20_patch1"
export DATA_SRC_DIR="${CMSSW_BASE}/src"
export NTUPLE_CMSSW_BASE="/afs/cern.ch/user/l/leyao/work/26JJ/MC_Maker/HelacOnia2016/CMSSW_10_6_20"
export NTUPLE_DATA_SRC_DIR="${NTUPLE_CMSSW_BASE}/src"
export SIM_CMSSW_BASE="/afs/cern.ch/user/l/leyao/work/26JJ/MC_Maker/HelacOnia2016/CMSSW_10_6_17_patch1"
export SIM_DATA_SRC_DIR="${SIM_CMSSW_BASE}/src"
export HLT_CMSSW_BASE="/afs/cern.ch/user/l/leyao/work/26JJ/MC_Maker/HelacOnia2016/CMSSW_8_0_33_UL"
export HLT_DATA_SRC_DIR="${HLT_CMSSW_BASE}/src"
export LHE_PACKAGED_BASE="/afs/cern.ch/user/l/leyao/work/26JJ/HelacOnia/packaged_runs_test"
export LHE_OUTPUT_BASE="${DATA_SRC_DIR}/LHE"
export GEN_OUTPUT_BASE="${DATA_SRC_DIR}/GEN"
export SIM_OUTPUT_BASE="${SIM_DATA_SRC_DIR}/SIM"
export DIGI_OUTPUT_BASE="${SIM_DATA_SRC_DIR}/DIGI"
export HLT_OUTPUT_BASE="${HLT_DATA_SRC_DIR}/HLT"
export RECO_OUTPUT_BASE="${SIM_DATA_SRC_DIR}/RECO"
export MINIAOD_OUTPUT_BASE="${SIM_DATA_SRC_DIR}/MINIAOD"
export NTUPLE_OUTPUT_BASE="${NTUPLE_DATA_SRC_DIR}/NTUPLE"
export LHE_SPLIT_EVENTS="250"

# HELAC-Onia LHE production
export HELAC_ONIA_BASE="/afs/cern.ch/user/l/leyao/work/26JJ/HelacOnia/HELAC-Onia-2.5.2"
export LHE_RUN_CARD="${HELAC_ONIA_BASE}/JJ_run.sh"

# Current SPS processes enabled for submission
export GEN_PROCESSES="ggpsi1psi1 ggpsi1psi1g"
export SIM_PROCESSES="${GEN_PROCESSES}"
export DIGI_PROCESSES="${GEN_PROCESSES}"
export HLT_PROCESSES="${GEN_PROCESSES}"
export RECO_PROCESSES="${GEN_PROCESSES}"
export MINIAOD_PROCESSES="${GEN_PROCESSES}"
export NTUPLE_PROCESSES="${GEN_PROCESSES}"
export LHE_PROCESSES="ggpsi1psi1 ggpsi1psi1g"
export LHE_JOBS_PER_PROCESS="1"
