import sys

import FWCore.ParameterSet.Config as cms

from Configuration.Eras.Era_Run2_2016_cff import Run2_2016


def _read_runtime_options(argv):
    options = {
        "inputHLT": "file:BPH-HLT-13TeV.root",
        "outputRECO": "file:BPH-RECO-13TeV.root",
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

process = cms.Process("RECO", Run2_2016)

process.load("Configuration.StandardSequences.Services_cff")
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.EventContent.EventContent_cff")
process.load("SimGeneral.MixingModule.mixNoPU_cfi")
process.load("Configuration.StandardSequences.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.StandardSequences.RawToDigi_cff")
process.load("Configuration.StandardSequences.L1Reco_cff")
process.load("Configuration.StandardSequences.Reconstruction_cff")
process.load("Configuration.StandardSequences.RecoSim_cff")
process.load("Configuration.StandardSequences.EndOfProcess_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")

process.maxEvents = cms.untracked.PSet(
    input=cms.untracked.int32(runtime_options["maxEvents"])
)

process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring(runtime_options["inputHLT"]),
    secondaryFileNames=cms.untracked.vstring(),
)

process.options = cms.untracked.PSet()

process.configurationMetadata = cms.untracked.PSet(
    annotation=cms.untracked.string("step1 nevts:runtime"),
    name=cms.untracked.string("Applications"),
    version=cms.untracked.string("$Revision: 1.19 $"),
)

process.AODSIMoutput = cms.OutputModule(
    "PoolOutputModule",
    compressionAlgorithm=cms.untracked.string("LZMA"),
    compressionLevel=cms.untracked.int32(4),
    dataset=cms.untracked.PSet(
        dataTier=cms.untracked.string("AODSIM"),
        filterName=cms.untracked.string(""),
    ),
    eventAutoFlushCompressedSize=cms.untracked.int32(31457280),
    fileName=cms.untracked.string(runtime_options["outputRECO"]),
    outputCommands=process.AODSIMEventContent.outputCommands,
)

from Configuration.AlCa.GlobalTag import GlobalTag

process.GlobalTag = GlobalTag(process.GlobalTag, "106X_mcRun2_asymptotic_v13", "")

process.raw2digi_step = cms.Path(process.RawToDigi)
process.L1Reco_step = cms.Path(process.L1Reco)
process.reconstruction_step = cms.Path(process.reconstruction)
process.recosim_step = cms.Path(process.recosim)
process.endjob_step = cms.EndPath(process.endOfProcess)
process.AODSIMoutput_step = cms.EndPath(process.AODSIMoutput)

process.schedule = cms.Schedule(
    process.raw2digi_step,
    process.L1Reco_step,
    process.reconstruction_step,
    process.recosim_step,
    process.endjob_step,
    process.AODSIMoutput_step,
)

from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask

associatePatAlgosToolsTask(process)

from FWCore.ParameterSet.Utilities import convertToUnscheduled

process = convertToUnscheduled(process)

from FWCore.Modules.logErrorHarvester_cff import customiseLogErrorHarvesterUsingOutputCommands

process = customiseLogErrorHarvesterUsingOutputCommands(process)

from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete

process = customiseEarlyDelete(process)
