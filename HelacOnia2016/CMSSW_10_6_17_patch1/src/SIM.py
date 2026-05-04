import sys

import FWCore.ParameterSet.Config as cms

from Configuration.Eras.Era_Run2_2016_cff import Run2_2016


def _read_runtime_options(argv):
    options = {
        "inputGEN": "file:BPH-GEN-13TeV.root",
        "outputSIM": "file:BPH-SIM-13TeV.root",
        "maxEvents": 1,
        "skipEvents": 0,
    }

    for arg in argv[1:]:
        if "=" not in arg:
            continue
        key, value = arg.split("=", 1)
        if key not in options:
            continue
        if key in {"maxEvents", "skipEvents"}:
            options[key] = int(value)
        else:
            options[key] = value

    return options


runtime_options = _read_runtime_options(sys.argv)

process = cms.Process("SIM", Run2_2016)

process.load("Configuration.StandardSequences.Services_cff")
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.EventContent.EventContent_cff")
process.load("SimGeneral.MixingModule.mixNoPU_cfi")
process.load("Configuration.StandardSequences.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.GeometrySimDB_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.StandardSequences.SimIdeal_cff")
process.load("Configuration.StandardSequences.EndOfProcess_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")

process.maxEvents = cms.untracked.PSet(
    input=cms.untracked.int32(runtime_options["maxEvents"])
)

process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring(runtime_options["inputGEN"]),
    skipEvents=cms.untracked.uint32(runtime_options["skipEvents"]),
    secondaryFileNames=cms.untracked.vstring(),
)

process.options = cms.untracked.PSet()

process.configurationMetadata = cms.untracked.PSet(
    annotation=cms.untracked.string("step1 nevts:runtime"),
    name=cms.untracked.string("Applications"),
    version=cms.untracked.string("$Revision: 1.19 $"),
)

process.RAWSIMoutput = cms.OutputModule(
    "PoolOutputModule",
    compressionAlgorithm=cms.untracked.string("LZMA"),
    compressionLevel=cms.untracked.int32(1),
    dataset=cms.untracked.PSet(
        dataTier=cms.untracked.string("GEN-SIM"),
        filterName=cms.untracked.string(""),
    ),
    eventAutoFlushCompressedSize=cms.untracked.int32(20971520),
    fileName=cms.untracked.string(runtime_options["outputSIM"]),
    outputCommands=process.RAWSIMEventContent.outputCommands,
    splitLevel=cms.untracked.int32(0),
)

process.XMLFromDBSource.label = cms.string("Extended")
from Configuration.AlCa.GlobalTag import GlobalTag

process.GlobalTag = GlobalTag(process.GlobalTag, "106X_mcRun2_asymptotic_v13", "")

process.simulation_step = cms.Path(process.psim)
process.endjob_step = cms.EndPath(process.endOfProcess)
process.RAWSIMoutput_step = cms.EndPath(process.RAWSIMoutput)

process.schedule = cms.Schedule(
    process.simulation_step, process.endjob_step, process.RAWSIMoutput_step
)
from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask

associatePatAlgosToolsTask(process)

from FWCore.ParameterSet.Utilities import convertToUnscheduled

process = convertToUnscheduled(process)

from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete

process = customiseEarlyDelete(process)
