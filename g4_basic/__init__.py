import Geant4 as G4
import g4py.ezgeom
import g4py.NISTmaterials
import g4py.ExN01pl
import g4py.ParticleGun

def init_ui_instance(theta_phi = (80,20), verbose=0):
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

class PGun:
  def __init__(self, name, particle, energy, position, momentum):
      self.__gun_obj = g4py.ParticleGun.Construct()
      self.__gun_obj.SetParticleByName(particle)
      positions = [ parse_units(i) for i in position ]
      self.__gun_obj.SetParticlePosition(G4.G4ThreeVector(*positions))
      momenta = [ parse_units(j) for j in momentum ]
      self.__gun_obj.SetParticlePosition(G4.G4ThreeVector(*momenta))

  def get_gun(self):
      return self.__gun_obj

  __slots__ = ('__gun_obj')

class Geometry:
  g4py.ezgeom.Construct()
  def __init__(self, name, world_material, world_dimensions=None):
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
      self.__volumes[name] = g4py.ezgeom.G4EzVolume(name)
      dimensions = [ parse_units(i) for i in dimensions ]
      position   = [ parse_units(j) for j in position ]
      getattr(self.__volumes[name], 'Create{}Volume'.format(type_of_vol))(G4.G4Material.GetMaterial('G4_{}'.format(material)), *dimensions)
      self.__volumes[name].PlaceIt(G4.G4ThreeVector(*position))
      if color:
        self.__volumes[name].SetColor(G4.G4Color(*color))

  def resize_world(self, dimensions):
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
      ui_vol = init_ui_instance()
      ui_vol.ApplyCommand('/vis/drawVolume')

  __slots__ = ('name', 'world_material', '__volumes', '__materials')


