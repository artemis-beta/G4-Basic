##############################################################################
#                                                                            #
#                          Geant4 Basic for Python                           #
#                                                                            #
# This module exists to try to simplify the diverse number of brilliant      #
# possibilities within Geant4 into a simple and east to use form. Currently  #
# it strips way many of the advanced features to allow the user to do two    #
# simple things:                                                             #
#                                                                            #
#  - Create a Geometry                                                       #
#  - Create a Particle Gun & Fire at that Geometry                           #
#                                                                            #
# Furthermore it also allows you to use strings to define dimensions, for    #
# example a coordinate can be of the form ('1m', '1m', '1m'), a parser then  #
# converts these into G4 units.                                              #
#                                                                            #
##############################################################################

import Geant4 as G4
import g4py.ezgeom
import g4py.NISTmaterials
import g4py.ExN01pl

import g4py.ParticleGun


_color_dict = { 'Red' : (1,0,0,0), 'Green' : (0,1,0,0),
                'Blue' : (0,0,1,0), 'Yellow' : (1,1,0,0),
                'Cyan' : (0,1,1,0), 'Magenta' : (1,0,1,0),
                'White' : (1,1,1,0), 'Black' : (0,0,0,0)}

def init_ui_instance(theta_phi = (80,20), verbose=0):
    '''
    Initialise a UI instance, this is required first!

    Optional Arguments
    ------------------

    theta_phi      (float, float)         Orientation angles in
                                          theta-phi in degrees.
                                          Default = (80,20)

    verbose        (int)                  Verbosity level.
                                          Default = 0.
    '''
    ui = G4.G4UImanager.GetUIpointer()
    ui.ApplyCommand("/run/verbose {}".format(verbose))
    ui.ApplyCommand("/event/verbose {}".format(verbose))
    ui.ApplyCommand("/tracking/verbose {}".format(verbose))
    ui.ApplyCommand("/run/initialize")
    ui.ApplyCommand("/run/verbose {}".format(verbose))
    ui.ApplyCommand("/vis/open OGLIX")
    ui.ApplyCommand("/vis/scene/create")
    ui.ApplyCommand("/vis/scene/endOfEventAction accumulate")
    ui.ApplyCommand("/vis/scene/add/volume")
    ui.ApplyCommand("/vis/scene/add/trajectories")
    ui.ApplyCommand("/vis/scene/add/hits")
    ui.ApplyCommand("/vis/viewer/set/viewpointThetaPhi {} {}".format(*theta_phi))
    return ui

def parse_units(string):
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

class PGun(object):
  '''Particle Gun Class'''
  def __init__(self, name, particle, energy, position, momentum):
      '''
      Creates a new Particle Gun which can be fired at a Geometry
  
      Arguments
      ---------

      name     (string)                An identifier for the Particle Gun
 
      particle (string)                The type of particle to be fired

      energy   (string)                The energy of the gun, e.g. 1 or '5GeV'
               (float)

      position (float,float,float)     Coordinates of the particle gun
               (string,string,string)

      momentum (float,float,float)     The momentum vector of the gun.
               (string,string,string)  
      '''
      self._name = name
      self.__gun_obj = g4py.ParticleGun.Construct()
      self.__gun_obj.SetParticleByName(particle)
      positions = [ parse_units(i) for i in position ]
      self.__gun_obj.SetParticlePosition(G4.G4ThreeVector(*positions))
      momenta = [ parse_units(j) for j in momentum ]
      self.__gun_obj.SetParticlePosition(G4.G4ThreeVector(*momenta))

  def get_gun(self):
      '''Returns the Geant4 gun object'''
      return self.__gun_obj

  __slots__ = ('__gun_obj')

class Geometry(object):
  '''Geonetry Class'''
  def __init__(self, name, world_material, world_dimensions=None):
      '''
      Firstly creates an environment for the geometry then allows you
      to add volumes/objects.

      Arguments
      ---------

      name             (string)             Unique identifier for the geometry

      world_material   (string)             Geant4 Material (see Geant4 materials database)


      Optional Arguments
      ------------------

      world_dimensions (float,float,float)     Dimensions of the 'world' volume
                       (string,string,string)

      '''
      self.constuct = g4py.ezgeom.Construct()
      self.__materials = g4py.NISTmaterials.Construct()
      world_material_G4 = world_material.replace('G4','')
      self.name = name
      self.world_material = world_material
      g4py.ezgeom.SetWorldMaterial(G4.G4Material.GetMaterial('G4_{}'.format(world_material_G4)))
      if world_dimensions:
         world_dimensions = [ parse_units(i) for i in world_dimensions ]
         g4py.ezgeom.ResizeWorld(*world_dimensions)
      self.__volumes = {}

  def __add__(self, other):
      assert self.world_material == other.world_material, "World Materials do not match"
      temp = Geometry('{}+{}'.format(self.name, other.name), self.world_material)
      volumes = self.volumes.copy()
      volumes.update(other.volumes)
      temp.__volumes = volumes
      return temp

  def add_volume(self, type_of_vol, name, material, dimensions, position, color=None):
      '''
      Add a new volume to the world

      Arguments
      ---------

      type_of_vol    (string)               Type of volume to generate
                                            ('Box'/'Tube'/'Cone'/'Sphere'/'Orb')

      name           (string)               Unique identifier for the volume

      dimensions     (float, ...)           List of dimensions for the particular type
                     (string, ...)

      position       (float, float, float)  Position of the volume
                     (string,string,string)
   
      Optional Arguments
      ------------------

      color          (float,float,float)        R G B A
                     (string)                   'Red'/'Green'/'Blue'/'Yellow'
                                                'Magenta'/'Black'/'White'
      '''
      self.__volumes[name] = g4py.ezgeom.G4EzVolume(name)
      dimensions = [ parse_units(i) for i in dimensions ]
      position   = [ parse_units(j) for j in position ]
      getattr(self.__volumes[name], 'Create{}Volume'.format(type_of_vol))(G4.G4Material.GetMaterial('G4_{}'.format(material)), *dimensions)
      self.__volumes[name].PlaceIt(G4.G4ThreeVector(*position))
      if color:
        if isinstance(color, string):
            for key in _color_dict:
                if key.lower() == string.lower():
                    color = _color_dict[string]
        self.__volumes[name].SetColor(G4.G4Color(*color))

  def resize_world(self, dimensions):
      '''
      Change the dimensions of the world.

      Argument
      --------

      dimensions  (float,float,float)      New world dimensions in x,y,z
                  (string,string,string)
      '''
      dimensions = [ parse_units(i) for i in dimensions ]
      g4py.ezgeom.ResizeWorld(*world_dimensions)

  def __iter__(self):
      for key in self.__volumes:
          yield self.__volumes[key]

  def __getitem__(self, i):
      if isinstance(i, int):
         return self.__volumes[self.__volumes.keys()[i]]
      else:
         return self.__volumes[i]


  def draw(self):
      '''Draw the Simulation'''
      G4.gRunManager.SetUserInitialisation(g4py.ExN01pl.Construct())
      G4.gRunManager.SetUserInitialisation(self.__materials)
      G4.gRunManager.Initialize()
      ui_vol = init_ui_instance()
      ui_vol.ApplyCommand('/vis/drawVolume')

  __slots__ = ('name', 'world_material', '__volumes', '__materials')


