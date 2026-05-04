import sys

import FWCore.ParameterSet.Config as cms


def _read_runtime_options(argv):
    options = {
        "inputLHE": "file:/eos/home-c/chensh/JPsiPsi2s/HELAC_Onia/HELAC-Onia-2.5.2/PROC_HO_0/P0_calc_0/output/sampleggpsi1psi1.lhe",
        "outputROOT": "/eos/home-c/chensh/JPsiPsi2s/HELAC_Onia/CMSSW_10_6_20_patch1/src/HepMC_GEN-0.root",
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

process = cms.Process("GEN")
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('GeneratorInterface.Core.genFilterSummary_cff')
process.load('Configuration.StandardSequences.Generator_cff')
process.load('Configuration.EventContent.EventContent_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.Generator_cff')
process.load('IOMC.EventVertexGenerators.VtxSmearedRealistic25ns13TeV2016Collision_cfi')
process.load('GeneratorInterface.Core.genFilterSummary_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
# process.genParticles.src= cms.InputTag("source","generator")

process.source = cms.Source(
    # "MCFileSource",
    "LHESource",
    # fileNames = cms.untracked.vstring('file:/eos/home-c/chensh/JPsiPsi2s/HELAC_Onia/condorIO/test/geninputlhe/sampleggpsi1psi1_py8.lhe'),
    fileNames = cms.untracked.vstring(runtime_options["inputLHE"]),
    # firstLuminosityBlockForEachRun = cms.untracked.VLuminosityBlockID([])
)
from Configuration.Generator.Pythia8CommonSettings_cfi import *
from Configuration.Generator.Pythia8aMCatNLOSettings_cfi import *
from Configuration.Generator.PSweightsPythia.PythiaPSweightsSettings_cfi import *
# from Configuration.Generator.MCTunesRun3ECM13p6TeV.PythiaCP5Settings_cfi import *
process.generator = cms.EDFilter("Pythia8ConcurrentHadronizerFilter",
    PythiaParameters = cms.PSet(
        pythia8CommonSettingsBlock,       # Common Pythia8 settings  
        # pythia8CP5SettingsBlock,          # CMS CP5 tune for Pythia8 
        pythia8aMCatNLOSettingsBlock,     # Settings for aMC@NLO matching  
        pythia8PSweightsSettingsBlock,    # Settings for parton shower (PS) weights  

        processParameters = cms.vstring(
            "TimeShower:nPartonsInBorn = -1",     # Number of partons in Born process (-1 = auto)  
            "TimeShower:mMaxGamma = 4",           # Maximum photon energy in final-state QED shower (GeV)  
            "PDF:pSet = 7",                       # Use PDF set ID 7   
            
            # Decay mode settings
            "23:onMode = 0",                      # Disable all decays of Z boson  
            # "23:onIfMatch = 13 -13",              # Allow only Z to mu+mu-
            "443:onMode = 0",                     # Disable all decays of Jpsi 
            "443:onIfMatch = 13 -13",             # Allow only Jpsi to mu+mu- decay
            "20443:onMode = 0",                   # Disable all decays of Chi_c1  
            "20443:onIfAny = 443",                # Allow Chi_c1 to Jpsi decay  
            "445:onMode = 0",                     # Disable all decays of Chi_c2  
            "445:onIfAny = 443",                  # Allow Chi_c2 to Jpsi decay  
            "10441:onMode = 0",                   # Disable all decays of h_c  
            "10441:onIfAny = 443",                # Allow h_c to Jpsi decay  
            "100443:onMode = 0",                  # Disable all decays of psi(2S)  
            "100443:onIfAny = 443",               # Allow psi(2S) to Jpsi decay 
        ),
        pythia8CP5Settings = cms.vstring(
            'Tune:pp 14', 
            'Tune:ee 7', 
            'MultipartonInteractions:ecmPow=0.03344', 
            'MultipartonInteractions:bProfile=2', 
            'MultipartonInteractions:pT0Ref=1.41', 
            'MultipartonInteractions:coreRadius=0.7634', 
            'MultipartonInteractions:coreFraction=0.63', 
            'ColourReconnection:range=5.176', 
            'SigmaTotal:zeroAXB=off', 
            'SpaceShower:alphaSorder=2', 
            'SpaceShower:alphaSvalue=0.118', 
            'SigmaProcess:alphaSvalue=0.118', 
            'SigmaProcess:alphaSorder=2', 
            'MultipartonInteractions:alphaSvalue=0.118', 
            'MultipartonInteractions:alphaSorder=2', 
            'TimeShower:alphaSorder=2', 
            'TimeShower:alphaSvalue=0.118', 
            'SigmaTotal:mode = 0', 
            'SigmaTotal:sigmaEl = 21.89', 
            'SigmaTotal:sigmaTot = 100.309', 
            'PDF:pSet=LHAPDF6:NNPDF31_nnlo_as_0118'
        ),
        parameterSets = cms.vstring(
            "pythia8CommonSettings",      
            "pythia8CP5Settings",         
            "pythia8aMCatNLOSettings",    
            "processParameters",          
            "pythia8PSweightsSettings"    
        )
    ),
    comEnergy = cms.double(13000),                    # Collision energy, needs to be same as the setting in HELAC-Onia.
    maxEventsToPrint = cms.untracked.int32(0),        # Do not print event details  
    pythiaHepMCVerbosity = cms.untracked.bool(False), # Disable HepMC event output verbosity  
    pythiaPylistVerbosity = cms.untracked.int32(0),   # Disable Pythia event listing output  
    filterEfficiency = cms.untracked.double(1.0),     # Set filter efficiency to 1.0 (all events pass)  
)
# process.FourMuonFilter = cms.EDFilter("FourLepFilter",
#     MaxEta = cms.untracked.double(2.5),
#     MaxPt = cms.untracked.double(4000.0),
#     MinEta = cms.untracked.double(0.0),
#     MinPt = cms.untracked.double(3.3),
#     ParticleID = cms.untracked.int32(13)
# )

process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(runtime_options["maxEvents"]))


process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.threshold = 'INFO'

process.GEN = cms.OutputModule(
    "PoolOutputModule",
    # fileName = cms.untracked.string('/eos/home-c/chensh/JPsiPsi2s/HELAC_Onia/condorIO/test/genoutputroot/HepMC_GEN-0.root')
    fileName = cms.untracked.string(runtime_options["outputROOT"])
)


######### Smearing Vertex example

# from IOMC.EventVertexGenerators.VtxSmearedParameters_cfi import GaussVtxSmearingParameters,VtxSmearedCommon
# VtxSmearedCommon.src=cms.InputTag("source","generator")
# process.generatorSmeared = cms.EDProducer("GaussEvtVtxGenerator",
#     GaussVtxSmearingParameters,
#     VtxSmearedCommon
#     )
# process.load('Configuration.StandardSequences.Services_cff')
# process.RandomNumberGeneratorService = cms.Service("RandomNumberGeneratorService",
#         generatorSmeared  = cms.PSet( initialSeed = cms.untracked.uint32(1243987),
#             engineName = cms.untracked.string('TRandom3'),
#             ),
#         )


###################
process.p = cms.Path(process.generator*process.pgen)
process.outpath = cms.EndPath(process.GEN)

### TO DO: add the following
# (amarini/hepmc_portTo9X)
# add the following line after the sim and digi loading
# generator needs to be smeared if you want vertex smearing, you'll have:
#       Type                                  Module               Label         Process   
#       -----------------------------------------------------------------------------------
#       GenEventInfoProduct                   "source"             "generator"   "GEN"     
#       edm::HepMCProduct                     "generatorSmeared"   ""            "GEN"     
#       edm::HepMCProduct                     "source"             "generator"   "GEN"   
# NOT needed to be changed if you smear the generator
#process.g4SimHits.HepMCProductLabel = cms.InputTag("source","generator","GEN")
#process.g4SimHits.Generator.HepMCProductLabel = cms.InputTag("source","generator","GEN")
#process.genParticles.src=  cms.InputTag("source","generator","GEN")


### ADD in the different step the following  (always!)
#
#process.AODSIMoutput.outputCommands.extend([
#		'keep GenRunInfoProduct_*_*_*',
#        	'keep GenLumiInfoProduct_*_*_*',
#		'keep GenEventInfoProduct_*_*_*',
#		])
#
#process.MINIAODSIMoutput.outputcommands.extend([
#       'keep GenRunInfoProduct_*_*_*',
#       'keep GenLumiInfoProduct_*_*_*',
#       'keep GenEventInfoProduct_*_*_*',
#	])
#
# and finally in the ntuples
#process.myanalyzer.generator = cms.InputTag("source","generator")
