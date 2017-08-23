import Geant4 as G4 
import g4py.ezgeom
import g4py.NISTmaterials
import g4py.ExN01pl
import g4py.ParticleGun

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
      self._gun_obj = g4py.ParticleGun.Construct()
      self._gun_obj.SetParticleByName(particle)
      positions = [ parse_units(i) for i in position ]
      self._gun_obj.SetParticlePosition(G4.G4ThreeVector(*positions))
      momenta = [ parse_units(j) for j in momentum ]
      self._gun_obj.SetParticlePosition(G4.G4ThreeVector(*momenta))

  def __call__(self):
      return self._gun_obj

class Geometry:
  def __init__(self, name, world_material, world_dimensions=None):
      self._materials = g4py.NISTmaterials.Construct()
      world_material = world_material.replace('G4','')
      g4py.ezgeom.SetWorldMaterial(G4.G4Material.GetMaterial('G4_{}'.format(world_material)))
      if world_dimensions:
         world_dimensions = [ parse_units(i) for i in world_dimensions ]
         g4py.ezgeom.ResizeWorld(*world_dimensions)
      self.volumes = {}

  def add_volume(self, type_of_vol, name, material, dimensions, position, color=None):
      self.volumes[name] = g4py.ezgeom.G4EzVolume(name)
      dimensions = [ parse_units(i) for i in dimensions ]
      position   = [ parse_units(j) for j in position ]
      getattr(self.volumes[name], 'Create{}Volume'.format(type_of_vol))(G4.G4Material.GetMaterial('G4_{}'.format(material)), *dimensions)
      self.volumes[name].PlaceIt(G4.G4ThreeVector(*position))
      if color:
        self.volumes[name].SetColor(G4.G4Color(*color))
      

if __name__ in "__main__":
   G4.gRunManager.SetUserInitialization(G4.QGSP_BERT())
   x = PGun('My Gun', 'e+', '3000MeV', ('0.0', '0.0', '-100.0cm'), ('0.0', '0.0', '2297.0'))
   geo = Geometry('My Geo', 'AIR')
   geo.add_volume('Box', 'My Box', 'Si', ('300.0mm', '300.0mm', '20.0mm'), ('0.0', '0.0', '500.0mm'), (124,252,0))
