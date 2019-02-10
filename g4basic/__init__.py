import Geant4 as G4
import g4py.ezgeom
import g4py.NISTmaterials
import g4py.ParticleGun

import logging

logging.basicConfig()

_phys_list_dict = ['QGSP_BERT', 'FTFP_BERT']

_colour_dict = { 'red'   : (1,0,0,1), 'green'   : (0,1,0,1),
                 'blue'  : (0,0,1,1), 'yellow'  : (1,1,0,1),
                 'cyan'  : (0,1,1,1), 'magenta' : (1,0,1,1),
                 'white' : (1,1,1,1), 'black'   : (0,0,0,1) }

_g4_vol_types = {'Box'    : 'CreateBoxVolume(G4Material, dx, dy, dz)', 
                 'Tube'   : 'CreateTubeVolume(G4Material, rmin, rmax,'+
                            ' z, phi0=0, phi=360*deg)',
                 'Cone'   : 'CreateConeVolume(G4Material, rmin1, rmax1,'+
                            ' rmin2, rmax2, dz, phi0=0, dphi)', 
                 'Sphere' : 'CreateSphereVolume(G4Material, rmin, rmax, phi0=0, '+
                            'dphi=360*deg, theta0=0, dtheta=180.*deg)', 
                 'Orb'    : 'CreateOrbVolume(G4material, rmax)'}

def isBoostArgumentError(exception):
    if 'Boost.Python.ArgumentError' in str(type(exception)):
        return True
    return False

class G4Session(object):
    def __init__(self, world_material='AIR', volumes_dict=None,
                 gun_opts_dict=None, phys_list='QGSP_BERT'):
        self._logger = logging.getLogger('G4Basic')
        self._logger.setLevel('INFO')
        self._constructs = self._initialise(phys_list)
        self._create_world()
        self._log_vols = {}
        if volumes_dict:
            self._make_vols_from_dict(volumes_dict)
        if gun_opts_dict:
            self._make_gun_from_dict(gun_opts_dict)

    def _parse_units(self, string):
        '''
        The unit parser: converts units as strings into the corresponding
        unit in Geant4
        
        Argument
        --------
        string     (string)             String to be parser, e.g. '5m'
        '''
        dict_units = { 'MeV' : G4.MeV, 'GeV' : G4.GeV, 'keV' : G4.keV,
                       'cm' : G4.cm, 'mm' : G4.mm, 'm' : G4.m }
        out = 1

        if isinstance(string, list) or isinstance(string, tuple):
            _output = [self._parse_units(i) for i in string]
            return _output
        if not isinstance(string, str):
           return string
        for key in dict_units:
            if key in string:
               out *= dict_units[key]
               out *= float(string.replace(key, ''))
               break
        else:
            out = float(string)
        return out

    def _make_gun_from_dict(self, in_dict):
        self.addParticleGun(**in_dict)

    def _make_vols_from_dict(self, in_dict):
        for volume in in_dict:
            self.addVolume(name=volume, **in_dict[volume])

    def _get_material(self, name):
        name = name if 'G4_' in name else 'G4_'+name
        return G4.G4Material.GetMaterial(name)

    def _initialise(self, phys_list):
        g4py.ezgeom.Construct()
        g4py.NISTmaterials.Construct()
        try:
             assert phys_list in _phys_list_dict
        except AssertionError as e:
             self._logger.error("Physics List not found, options are: {}".format(' '.join(_phys_list_dict)))
        G4.gRunManager.SetUserInitialization(getattr(G4, phys_list)())
            

    def _create_world(self, material='AIR',
                      dimensions=(50.*G4.m, 50.*G4.m, 50.*G4.m)):

        self._logger.info('Creating New World of {} of size ({}, {}, {})'.format(material, *dimensions))

        g4py.ezgeom.SetWorldMaterial(self._get_material(material))
        g4py.ezgeom.ResizeWorld(*self._parse_units(dimensions))
     
    def addVolume(self, name, material, vol_type, dimensions, position, colour='red'):
        try:
            assert vol_type in _g4_vol_types
        except AssertionError as e:
            self._logger.error("Volume of type '{}' not present in GEANT4".format(vol_type))
            raise e
        
        try:
            self._log_vols[name] = g4py.ezgeom.G4EzVolume(name)
            _color = G4.G4Color(*_colour_dict[colour.lower()])
        #self._log_vols[name].SetColor(*_colour_dict[colour.lower()][:-1])
            self._logger.info('Creating {} Volume from {} of size ({}, {}, {})'.format(vol_type, material, *dimensions))
            getattr(self._log_vols[name], 'Create{}Volume'.format(vol_type))(self._get_material(material),
                                                                *self._parse_units(dimensions))
            self._log_vols[name].PlaceIt(G4.G4ThreeVector(*position))

        except Exception as e:
            if isBoostArgumentError(e):
                self._logger.error('Invalid Arguments for Volume Creation')
                self._logger.error(_g4_vol_types[vol_type])
                self._logger.error('Arguments:\n\tMaterial: {}\n\tDimension: {}\n\tPosition: {}'.format(material, 
                                   ', '.join([str(i) for i in dimensions]),
                                   ', '.join([str(i) for i in position])))
            raise e

    def addParticleGun(self, particle, position, energy=None, direction=None, momentum=None):
        self._pgun = g4py.ParticleGun.Construct()
        self._pgun.SetParticleByName(particle)
        position = self._parse_units(position)
        self._pgun.SetParticlePosition(G4.G4ThreeVector(*position))
        if momentum:
            self._logger.warning('PGun: Option for Momentum given, will ignore any options'
                                 +'for Direction or Energy')

            momentum = self._parse_units(momentum)
            self._pgun.SetParticlePosition(G4.G4ThreeVector(*momentum))
        elif energy:
            direction = self._parse_units(direction)
            energy = self._parse_units(energy)
            self._pgun.SetParticleEnergy(energy)
            self._pgun.SetParticleMomentumDirection(G4.G4ThreeVector(*direction))
            
    def runSimulation(self, nevts=1, viewer='OGLIX', hits=True, trajectories='smooth',
                      logo=False, view=(80,20)):
        self._ui = G4.G4UImanager.GetUIpointer()
        self._ui.ApplyCommand('/run/initialize')
        self._ui.ApplyCommand('/vis/open {}'.format(viewer))
        self._ui.ApplyCommand('/vis/viewer/set/viewpointThetaPhi {} {}'.format(*view))
        self._ui.ApplyCommand('/vis/drawVolume')
        if hits:
            self._ui.ApplyCommand('/vis/scene/add/hits')
        if trajectories:
            if trajectories.lower() == 'smooth':
                self._ui.ApplyCommand('/vis/scene/add/trajectories smooth')
            else:
                self._ui.ApplyCommand('/vis/scene/add/trajectories')
        if logo:
            if logo.lower() == '2d':
                self._ui.ApplyCommand('/vis/scene/add/2Dlogo')
            else:
                self._ui.ApplyCommand('/vis/scene/add/logo')

        if nevts:
            self._ui.ApplyCommand('/run/beamOn {}'.format(nevts))
