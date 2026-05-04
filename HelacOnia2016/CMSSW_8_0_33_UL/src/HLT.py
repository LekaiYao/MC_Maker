import FWCore.ParameterSet.Config as cms

from Configuration.StandardSequences.Eras import eras


def _parse_runtime_options():
    options = {
        "inputDIGI": "file:BPH-DIGI-13TeV.root",
        "outputHLT": "file:BPH-HLT-13TeV.root",
        "maxEvents": -1,
    }

    import sys

    for arg in sys.argv[1:]:
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


runtime_options = _parse_runtime_options()

process = cms.Process("HLT", eras.Run2_2016)

process.load("Configuration.StandardSequences.Services_cff")
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.EventContent.EventContent_cff")
process.load("SimGeneral.MixingModule.mixNoPU_cfi")
process.load("Configuration.StandardSequences.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("HLTrigger.Configuration.HLT_25ns15e33_v4_cff")
process.load("Configuration.StandardSequences.EndOfProcess_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")

process.maxEvents = cms.untracked.PSet(
    input=cms.untracked.int32(runtime_options["maxEvents"])
)

process.source = cms.Source(
    "PoolSource",
    dropDescendantsOfDroppedBranches=cms.untracked.bool(False),
    fileNames=cms.untracked.vstring(runtime_options["inputDIGI"]),
    inputCommands=cms.untracked.vstring(
        "keep *",
        "drop *_*_BMTF_*",
        "drop *PixelFEDChannel*_*_*_*",
    ),
    secondaryFileNames=cms.untracked.vstring(),
)

process.options = cms.untracked.PSet()

process.configurationMetadata = cms.untracked.PSet(
    annotation=cms.untracked.string("step1 nevts:{}".format(runtime_options["maxEvents"])),
    name=cms.untracked.string("Applications"),
    version=cms.untracked.string("$Revision: 1.19 $"),
)

process.RAWSIMoutput = cms.OutputModule(
    "PoolOutputModule",
    dataset=cms.untracked.PSet(
        dataTier=cms.untracked.string("GEN-SIM-RAW"),
        filterName=cms.untracked.string(""),
    ),
    eventAutoFlushCompressedSize=cms.untracked.int32(5242880),
    fileName=cms.untracked.string(runtime_options["outputHLT"]),
    outputCommands=process.RAWSIMEventContent.outputCommands,
    splitLevel=cms.untracked.int32(0),
)

from Configuration.AlCa.GlobalTag import GlobalTag

process.GlobalTag = GlobalTag(process.GlobalTag, "80X_mcRun2_asymptotic_2016_TrancheIV_v6", "")
process.RAWSIMoutput.outputCommands.append("keep *_mix_*_*")
process.RAWSIMoutput.outputCommands.append("keep *_genPUProtons_*_*")

process.endjob_step = cms.EndPath(process.endOfProcess)
process.RAWSIMoutput_step = cms.EndPath(process.RAWSIMoutput)

process.schedule = cms.Schedule()
process.schedule.extend(process.HLTSchedule)
process.schedule.extend([process.endjob_step, process.RAWSIMoutput_step])

from HLTrigger.Configuration.customizeHLTforMC import customizeHLTforFullSim

process = customizeHLTforFullSim(process)
process.source.bypassVersionCheck = cms.untracked.bool(True)
