import os
import math 
from Gaudi.Configuration import INFO, DEBUG
from Configurables import EventDataSvc, UniqueIDGenSvc
from Configurables import RndmGenSvc
from Configurables import GeoSvc
import xml.etree.ElementTree as ET

from k4FWCore import IOSvc, ApplicationMgr
from k4FWCore.parseArgs import parser



################## Parser
parser.add_argument("--inputFile", default = "ddsim_output_edm4hep.root", help = "InputFile")
parser.add_argument("--outputFile", default = "output_digi.root", help = "OutputFile")
args = parser.parse_args()

# ################## InputOutput
svc = IOSvc("IOSvc")
svc.Input = args.inputFile
svc.Output = args.outputFile

################ Detector geometry
geoservice = GeoSvc("GeoSvc")
path_to_detector = os.environ.get("K4GEO", "")
detectors_to_use = ['FCCee/ALLEGRO/compact/ALLEGRO_o2_v01/ALLEGRO_o2_v01.xml']
geoservice.detectors = [os.path.join(path_to_detector, _det) for _det in detectors_to_use]
geoservice.OutputLevel = INFO

from Configurables import DDPlanarDigi
from Configurables import WireTrackerDigi_v01

############### Vertex Digitizer

innerVertexResolution_x = 0.003 # [mm], assume 3 µm resolution for ARCADIA sensor
innerVertexResolution_y = 0.003 # [mm], assume 3 µm resolution for ARCADIA sensor
innerVertexResolution_t = 1000 # [ns]
outerVertexResolution_x = 0.050/math.sqrt(12) # [mm], assume ATLASPix3 sensor with 50 µm pitch
outerVertexResolution_y = 0.150/math.sqrt(12) # [mm], assume ATLASPix3 sensor with 150 µm pitch
outerVertexResolution_t = 1000 # [ns]


############### Vertex Digitizer

vtxb_digitizer = DDPlanarDigi(
    "VTXBdigitizer",
    IsStrip=False,
    ResolutionU=[
        innerVertexResolution_x,
        innerVertexResolution_x,
        innerVertexResolution_x,
        outerVertexResolution_x,
        outerVertexResolution_x,
    ],
    ResolutionV=[
        innerVertexResolution_y,
        innerVertexResolution_y,
        innerVertexResolution_y,
        outerVertexResolution_y,
        outerVertexResolution_y,
    ],
    ResolutionT=[
        innerVertexResolution_t,
        innerVertexResolution_t,
        innerVertexResolution_t,
        outerVertexResolution_t,
        outerVertexResolution_t,
    ],
    SimTrackHitCollectionName=["VertexBarrelCollection"],
    SimTrkHitRelCollection=["VTXBSimDigiLinks"],
    SubDetectorName="Vertex",
    TrackerHitCollectionName=["VTXBDigis"],
    ForceHitsOntoSurface=True,
    CellIDBits=32,
    OutputLevel=INFO,
)

vtxd_digitizer = DDPlanarDigi(
    "VTXDdigitizer",
    IsStrip=False,
    ResolutionU=[
        outerVertexResolution_x,
        outerVertexResolution_x,
        outerVertexResolution_x,
    ],
    ResolutionV=[
        outerVertexResolution_y,
        outerVertexResolution_y,
        outerVertexResolution_y,
    ],
    ResolutionT=[
        outerVertexResolution_t,
        outerVertexResolution_t,
        outerVertexResolution_t,
    ],
    SimTrackHitCollectionName=["VertexEndcapCollection"],
    SimTrkHitRelCollection=["VTXDSimDigiLinks"],
    SubDetectorName="VertexDisks",
    TrackerHitCollectionName=["VTXDDigis"],
    ForceHitsOntoSurface=True,
    CellIDBits=32,
    OutputLevel=INFO,
)



############### Wrapper Digitizer
class GeoConstants(dict):
    def __init__(self, expressions, sources):
        super().__init__(mm=1., cm=10., m=1000., um=1.e-3, micrometer=1.e-3, nm=1.e-6,
                            pi=math.pi, sqrt=math.sqrt, sin=math.sin, cos=math.cos, tan=math.tan)
        self.expressions = expressions
        self.sources = sources

    def __missing__(self, name):
        if name not in self.expressions:
            raise RuntimeError(f"Constant {name} not found in {detectors_to_use} or the xml files they include")
        try:
            value = eval(self.expressions[name], {"__builtins__": {}}, self)
        except Exception as e:
            raise RuntimeError(f"Could not evaluate constant {name} = '{self.expressions[name]}' "
                                f"from {self.sources[name]}: {e}") from e
        self[name] = value
        return value
def collectConstants(xmlFile, expressions, sources, visited):
        xmlFile = os.path.normpath(os.path.abspath(xmlFile))
        if xmlFile in visited:
            return
        visited.add(xmlFile)
        if not os.path.isfile(xmlFile):
            # e.g. ${DD4hepINSTALL}/DDDetectors/compact/detector_types.xml if DD4hepINSTALL is not set
            print(f"WARNING: xml file {xmlFile} not found, its constants will not be available")
            return
        # ElementTree drops xml comments, so commented-out includes and constants are ignored
        for element in ET.parse(xmlFile).getroot().iter():
            if element.tag == 'constant':
                name, value = element.get('name'), element.get('value')
                if name not in expressions:
                    expressions[name] = value
                    sources[name] = xmlFile
                elif value != expressions[name]:
                    print(f"WARNING: constant {name} = '{value}' in {xmlFile} ignored, "
                          f"already defined as '{expressions[name]}' in {sources[name]}")
            elif element.tag == 'include' and element.get('ref'):
                ref = os.path.expandvars(element.get('ref'))
                collectConstants(os.path.join(os.path.dirname(xmlFile), ref), expressions, sources, visited)

expressions = {}
sources = {}
for xmlFile in geoservice.detectors:
    collectConstants(xmlFile, expressions, sources, set())
geoConstants = GeoConstants(expressions, sources)

siWrapperNlayers = int(geoConstants['SiWr_nLayers'])
siWrBarrelPitch_x = [geoConstants[f"SiWrB_pitch_phi{layer}"] for layer in range(siWrapperNlayers)]
siWrBarrelPitch_y = [geoConstants[f"SiWrB_pitch_z{layer}"] for layer in range(siWrapperNlayers)]
siWrDisksPitch_x = [geoConstants[f"SiWrD_pitch_r{layer}"] for layer in range(siWrapperNlayers)]
siWrDisksPitch_y = [geoConstants[f"SiWrD_pitch_phi{layer}"] for layer in range(siWrapperNlayers)]

siWrBarrelResolution_x = [pitch / math.sqrt(12) for pitch in siWrBarrelPitch_x]
siWrBarrelResolution_y = [pitch / math.sqrt(12) for pitch in siWrBarrelPitch_y]
siWrDisksResolution_x = [pitch / math.sqrt(12) for pitch in siWrDisksPitch_x]
siWrDisksResolution_y = [pitch / math.sqrt(12) for pitch in siWrDisksPitch_y]
siWrapperResolution_t = 0.040  # [ns]

siwrb_digitizer = DDPlanarDigi(
    "SiWrBdigitizer",
    IsStrip=False,
    ResolutionU=siWrBarrelResolution_x,
    ResolutionV=siWrBarrelResolution_y,
    ResolutionT=[
        siWrapperResolution_t
    ] * len(siWrBarrelResolution_x),
    SimTrackHitCollectionName=["SiWrBCollection"],
    SimTrkHitRelCollection=["SiWrBSimDigiLinks"],
    SubDetectorName="SiWrB",
    TrackerHitCollectionName=["SiWrBDigis"],
    ForceHitsOntoSurface=True,
    CellIDBits=32,
    OutputLevel=INFO,
)

siwrd_digitizer = DDPlanarDigi(
    "SiWrDdigitizer",
    IsStrip=False,
    ResolutionU=siWrDisksResolution_x,
    ResolutionV=siWrDisksResolution_y,
    ResolutionT=[
        siWrapperResolution_t
    ] * len(siWrDisksResolution_x),
    SimTrackHitCollectionName=["SiWrDCollection"],
    SimTrkHitRelCollection=["SiWrDSimDigiLinks"],
    SubDetectorName="SiWrD",
    TrackerHitCollectionName=["SiWrDDigis"],
    ForceHitsOntoSurface=True,
    CellIDBits=32,
    OutputLevel=INFO,
)



############### Straw Tubes (STT) Digitizer

stt_digitizer = WireTrackerDigi_v01(
    "STTdigitizer",
    InputSimHitCollection=["STTCollection"],
    OutputDigihitCollection=["STTDigis"],
    OutputLinkCollection=["STTSimDigiLinks"],
    DCH_name="STT_o1_v01",                  
    zResolution_mm = 30.0,                  # in mm
    xyResolution_mm = 0.1,                  # in mm
    Deadtime_ns = 400.0,                    # in ns
    GasType=0,                              # 0: He(90%)-Isobutane(10%), ecc.
    ReadoutWindowStartTime_ns=1.0,          # in ns
    ReadoutWindowDuration_ns=450.0,         # in ns
    DriftVelocity_um_per_ns=-1.0,           
    SignalVelocity_mm_per_ns=200.0,         # in mm/ns
    isSTT=True,                             
    OutputLevel=INFO,
)


############### Application Manager

mgr = ApplicationMgr(
    TopAlg = [stt_digitizer, vtxb_digitizer, vtxd_digitizer, siwrb_digitizer, siwrd_digitizer],
    EvtSel = "NONE",
    EvtMax = -1,
    ExtSvc = [geoservice, EventDataSvc("EventDataSvc"), UniqueIDGenSvc("uidSvc"), RndmGenSvc()],
    OutputLevel = INFO,
)