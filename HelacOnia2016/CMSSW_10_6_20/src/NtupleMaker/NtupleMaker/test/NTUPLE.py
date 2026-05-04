import sys

import FWCore.ParameterSet.Config as cms


def _read_runtime_options(argv):
    options = {
        "inputMINIAOD": "file:BPH-MiniAOD-13TeV.root",
        "outputNTUPLE": "Ntuple_2016_SPS.root",
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

process = cms.Process("NtupleMaker")

process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")
process.load("Configuration.StandardSequences.MagneticField_AutoFromDBCurrent_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")

process.load("Configuration.StandardSequences.Services_cff")
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("Configuration.EventContent.EventContent_cff")
process.load("Configuration.StandardSequences.GeometryRecoDB_cff")
process.load("Configuration.StandardSequences.MagneticField_AutoFromDBCurrent_cff")
process.load("Configuration.StandardSequences.Skims_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")

process.load("FWCore.MessageLogger.MessageLogger_cfi")

process.maxEvents = cms.untracked.PSet(
    input=cms.untracked.int32(runtime_options["maxEvents"])
)

process.source = cms.Source(
    "PoolSource",
    fileNames=cms.untracked.vstring(runtime_options["inputMINIAOD"]),
    secondaryFileNames=cms.untracked.vstring(),
)

process.TFileService = cms.Service(
    "TFileService",
    fileName=cms.string(runtime_options["outputNTUPLE"]),
)

process.options = cms.untracked.PSet(
    wantSummary=cms.untracked.bool(True)
)

from Configuration.AlCa.GlobalTag import GlobalTag

process.GlobalTag = GlobalTag(process.GlobalTag, "106X_mcRun2_asymptotic_v13", "")

process.oniaSelectedMuons.cut = cms.string(
    ""
)

process.onia2MuMuPAT.higherPuritySelection = cms.string(
    "(isGlobalMuon || isTrackerMuon || (innerTrack.isNonnull && genParticleRef(0).isNonnull)) && abs(innerTrack.dxy)<4 && abs(innerTrack.dz)<35 && muonID('TrackerMuonArbitrated')"
)
process.onia2MuMuPAT.lowerPuritySelection = cms.string(
    "(isGlobalMuon || isTrackerMuon || (innerTrack.isNonnull && genParticleRef(0).isNonnull)) && abs(innerTrack.dxy)<4 && abs(innerTrack.dz)<35 && muonID('TrackerMuonArbitrated')"
)

process.BPHSkimSequence = cms.Sequence()

process.load("NtupleMaker.NtupleMaker.NtupleMaker_cfi")
process.p = cms.Path(process.rootuple)
process.schedule = cms.Schedule(process.BPHSkimPath, process.p)
