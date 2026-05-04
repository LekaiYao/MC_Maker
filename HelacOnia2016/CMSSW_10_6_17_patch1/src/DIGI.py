import sys

import FWCore.ParameterSet.Config as cms

from Configuration.Eras.Era_Run2_2016_cff import Run2_2016
from Configuration.ProcessModifiers.premix_stage2_cff import premix_stage2


def _read_runtime_options(argv):
    options = {
        "inputSIM": "file:BPH-SIM-13TeV.root",
        "outputDIGI": "file:BPH-DIGI-13TeV.root",
        "maxEvents": -1,
    }

    for arg in argv[1:]:
        if "=" not in arg:
            continue
        key, value = arg.split("=", 1)
        if key not in options:
            continue
        if key == "maxEvents":
            options[key] = int(value)
        else:
            options[key] = value

    return options


runtime_options = _read_runtime_options(sys.argv)

process = cms.Process("DIGI2RAW", Run2_2016, premix_stage2)

process.load("Configuration.StandardSequences.Services_cff")
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.EventContent.EventContent_cff")
process.load("SimGeneral.MixingModule.mixNoPU_cfi")
process.load("Configuration.StandardSequences.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.StandardSequences.DigiDM_cff")
process.load("Configuration.StandardSequences.DataMixerPreMix_cff")
process.load("Configuration.StandardSequences.SimL1EmulatorDM_cff")
process.load("Configuration.StandardSequences.DigiToRawDM_cff")
process.load("Configuration.StandardSequences.EndOfProcess_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")

process.maxEvents = cms.untracked.PSet(
    input=cms.untracked.int32(runtime_options["maxEvents"])
)

process.source = cms.Source(
    "PoolSource",
    dropDescendantsOfDroppedBranches=cms.untracked.bool(False),
    fileNames=cms.untracked.vstring(runtime_options["inputSIM"]),
    inputCommands=cms.untracked.vstring(
        "keep *",
        "drop *_genParticles_*_*",
        "drop *_genParticlesForJets_*_*",
        "drop *_kt4GenJets_*_*",
        "drop *_kt6GenJets_*_*",
        "drop *_iterativeCone5GenJets_*_*",
        "drop *_ak4GenJets_*_*",
        "drop *_ak7GenJets_*_*",
        "drop *_ak8GenJets_*_*",
        "drop *_ak4GenJetsNoNu_*_*",
        "drop *_ak8GenJetsNoNu_*_*",
        "drop *_genCandidatesForMET_*_*",
        "drop *_genParticlesForMETAllVisible_*_*",
        "drop *_genMetCalo_*_*",
        "drop *_genMetCaloAndNonPrompt_*_*",
        "drop *_genMetTrue_*_*",
        "drop *_genMetIC5GenJs_*_*",
    ),
    secondaryFileNames=cms.untracked.vstring(),
)

process.options = cms.untracked.PSet()

process.configurationMetadata = cms.untracked.PSet(
    annotation=cms.untracked.string("step1 nevts:runtime"),
    name=cms.untracked.string("Applications"),
    version=cms.untracked.string("$Revision: 1.19 $"),
)

process.PREMIXRAWoutput = cms.OutputModule(
    "PoolOutputModule",
    dataset=cms.untracked.PSet(
        dataTier=cms.untracked.string("GEN-SIM-DIGI"),
        filterName=cms.untracked.string(""),
    ),
    fileName=cms.untracked.string(runtime_options["outputDIGI"]),
    outputCommands=process.PREMIXRAWEventContent.outputCommands,
    splitLevel=cms.untracked.int32(0),
)

process.mixData.input.fileNames = cms.untracked.vstring([
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/00456BD1-4A4E-6843-AA18-78B56D65EF38.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/00C583B9-1C11-D640-8D2C-F27E2DB5D5E3.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/00CB222A-45EA-7C4C-A5B8-DA43C984CBE9.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/01393487-A130-364D-921F-C43C2EDDF60B.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/016FFD3D-86CA-F24C-B698-04F40783E9CC.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/01E30E35-9DF0-694E-95C1-78C45195085F.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/02605788-6F0A-7441-9151-1F61AFC6C2A6.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/027ACE88-0BFA-C743-A903-802C31487ED3.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/02CAC39A-2176-5D4A-9F79-62C1474A448B.root',
    '/store/mc/RunIISummer20ULPrePremix/Neutrino_E-10_gun/PREMIX/UL16_106X_mcRun2_asymptotic_v13-v1/120000/043218DA-7C52-2C42-89DB-A7AB8D4E0A64.root'
])

from Configuration.AlCa.GlobalTag import GlobalTag

process.GlobalTag = GlobalTag(process.GlobalTag, "106X_mcRun2_asymptotic_v13", "")

process.digitisation_step = cms.Path(process.pdigi)
process.datamixing_step = cms.Path(process.pdatamix)
process.L1simulation_step = cms.Path(process.SimL1Emulator)
process.digi2raw_step = cms.Path(process.DigiToRaw)
process.endjob_step = cms.EndPath(process.endOfProcess)
process.PREMIXRAWoutput_step = cms.EndPath(process.PREMIXRAWoutput)

process.schedule = cms.Schedule(
    process.digitisation_step,
    process.datamixing_step,
    process.L1simulation_step,
    process.digi2raw_step,
    process.endjob_step,
    process.PREMIXRAWoutput_step,
)
from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask

associatePatAlgosToolsTask(process)

from FWCore.ParameterSet.Utilities import convertToUnscheduled

process = convertToUnscheduled(process)

from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete

process = customiseEarlyDelete(process)
