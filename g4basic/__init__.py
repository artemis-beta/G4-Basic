import Geant4 as G4
import g4py.ezgeom
import g4py.NISTmaterials
import g4py.ParticleGun

import logging

logging.basicConfig()

_phys_lists = [
    'FTFP_BERT',
    'FTFP_BERT_ATL',
    'FTFP_BERT_HP',
    'FTFP_BERT_TRV',
    'FTFP_INCLXX',
    'FTFP_INCLXX_HP',
    'FTF_BIC',
    'LBE',
    'NuBeam',
    'QBBC',
    'QGSP_BERT',
    'QGSP_BERT_HP',
    'QGSP_BIC',
    'QGSP_BIC_AllHP',
    'QGSP_BIC_HP',
    'QGSP_FTFP_BERT',
    'QGSP_INCLXX',
    'QGSP_INCLXX_HP',
    'QGS_BIC',
    'Shielding']

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

def listMaterials():
    g4py.NISTmaterials.Construct()
    print(G4.gMaterialTable)

def isBoostArgumentError(exception):
    if 'Boost.Python.ArgumentError' in str(type(exception)):
        return True
    return False

class G4Session(object):
    def __init__(self, world_material='AIR', volumes_dict=None,
                 gun_opts_dict=None, phys_list='QGSP_BERT'):
        '''
        G4-Basic class to start a session of GEANT4

        Optional Arguments
        ------------------

        world_material   (string)          Name of Geant4 material.
                                           Default: 'AIR'
 
        volumes_dict     (dict)            Dictionary of volumes (see below)

        gun_opts_dict    (dict)            Dictionary of Particle gun parameters
                                           (see below)

        phys_list        (string)          Name of GEANT4 Physics List (see below)


        Volumes Dictionary
        ------------------

        {{
              'Volume1' : {{'vol_type'   : 'Box',
                           'position'   : (0, 0, 0),
                           'dimensions' : ('10m', '10m', '3m'),
                           'material'   : 'Si'}},
              ...
        }}

        Particle Gun Dictionary
        -----------------------

        {{'particle' : 'e-', 'energy' : '100GeV', 'direction' : (0,0,1),
         'position : (0, 0, '-15m')}}

 
        Physics Lists
        -------------

        {}
        '''.format(', '.format(_phys_lists))

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
             assert phys_list in _phys_lists
        except AssertionError as e:
             self._logger.error("Physics List not found, options are: {}".format(' '.join(_phys_list_dict)))
        G4.gRunManager.SetUserInitialization(getattr(G4, phys_list)())
            

    def _create_world(self, material='AIR',
                      dimensions=(50.*G4.m, 50.*G4.m, 50.*G4.m)):

        self._logger.info('Creating New World of {} of size ({}, {}, {})'.format(material, *dimensions))

        g4py.ezgeom.SetWorldMaterial(self._get_material(material))
        g4py.ezgeom.ResizeWorld(*self._parse_units(dimensions))
     
    def addVolume(self, name, material, vol_type, dimensions, position, colour='red'):
        '''
        Add a new volume to the Geometry

        Arguments
        ---------

        name       (string)                  Volume name
        
        material   (string)                  GEANT4 material, e.g. 'Si'

        vol_type   (string)                  Volume type, e.g. 'Box'

        dimensions (float, float, float)     Dimensions as either floats or 
                   (string, string, string)  strings. e.g. (1,1,2) or ('1cm', '1cm', '2cm')

        position   (float, float, float)     Position as either strings or floats
                   (string, string, string)

        Optional Arguments
        ------------------

        colour     (string)                  Colour of volume

        ''' 

        try:
            assert vol_type in _g4_vol_types
        except AssertionError as e:
            self._logger.error("Volume of type '{}' not present in GEANT4".format(vol_type))
            raise e
        
        try:
            self._log_vols[name] = g4py.ezgeom.G4EzVolume(name)
            self._logger.info('Creating {} Volume from {} of size ({}, {}, {})'.format(vol_type, material, *dimensions))
            getattr(self._log_vols[name], 'Create{}Volume'.format(vol_type))(self._get_material(material),
                                                                *self._parse_units(dimensions))
            _color = G4.G4Color(*_colour_dict[colour.lower()])
            self._log_vols[name].SetColor(_color)
            self._log_vols[name].PlaceIt(G4.G4ThreeVector(*self._parse_units(position)))

        except Exception as e:
            if isBoostArgumentError(e):
                self._logger.error('Invalid Arguments for Volume Creation')
                self._logger.error(_g4_vol_types[vol_type])
                self._logger.error('Arguments:\n\tMaterial: {}\n\tDimension: {}\n\tPosition: {}'.format(material, 
                                   ', '.join([str(self._parse_units(i)) for i in dimensions]),
                                   ', '.join([str(self._parse_units(i)) for i in position])))
            raise e

    def addParticleGun(self, particle, position, energy=None, direction=None, momentum=None):
        '''
        Create a particle gun if one has not already been initialised

        Arguments
        ---------

        particle         (string)                  Particle to be fired

        position         (float, float, float)     Position of gun as either
                         (string, string, string)  floats or strings

       
        Optional Arguments
        ------------------

        Note: If momentum is set, energy and momentum direction are ignored


        energy           (float) or (string)       Energy of particle

        direction        (float, float, float)     Direction vector of particle
 
        momentum         (float, float, float)     Momentum of particle
                         (string, string, string)

        '''
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
                      logo=False, view=(80,20), style='wireframe'):
        '''
        Run the simulation, showing the geometry visually and firing the particle gun

        Optional Arguments
        ------------------

        nevts        (int)           Number of events (Default : 1)

        viewer       (string)        Viewer to use (Default : OGLIX)

        hits         (bool)          Show particle hits

        trajectories (bool/string)   Show trajectories, if 'smooth' turn on
                                     smooth trajectories

        logo         (bool/string)   Show the Geant4 logo, option '2d' also included
      
        view         (float, float)  Angle of view (theta, phi)

        style        (string)        'wireframe'/'surface' styles of objects
        '''
        self._ui = G4.G4UImanager.GetUIpointer()
        self._ui.ApplyCommand('/run/initialize')
        self._ui.ApplyCommand('/vis/open {}'.format(viewer))
        self._ui.ApplyCommand('/vis/viewer/set/viewpointThetaPhi {} {}'.format(*view))
        self._ui.ApplyCommand('/viw/viewer/set/style {}'.format(style))
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
