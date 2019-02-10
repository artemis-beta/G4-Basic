# G4-Basic

The purpose of this module is to greatly simplify the creation of basic geometries and the firing of particle guns at these geometries. This method features a single class which can create a simulation by using just three parameters.

## Trying it out with Docker

Even without GEANT4 installed on your system you can still try out G4-Basic via Docker, I have prepared a docker image with the software [here](https://hub.docker.com/r/artemisbeta/geant4). Make sure you run the container with `-u 0` so you can install git and clone this repository.

## Parsing of Units

Before discussing G4-Basic I would firstly like to introduce the unit parser. Traditionally units can be imported from the `Geant4` module and then used multiplicatively, e.g. 10 metres being `10*G4.m`. To cut back further the requirements for running GEANT4 I have built in string parsing which is able to recognise a unit, and if it exists within the module, do the multiplication for you. For example `'10m'` as an argument would yield the same result.

## The G4Session Class

To create a simulation in one statement you need to create two dictionaries, one containing all the parameters for the geometry objects, and one which will be used to initialise the particle gun. Optionally you can add volumes and create particle guns later using `addVolume` and `addParticleGun`.

For the volume dictionary the required arguments are the type of volume `vol_type` of which there are five types: `Box`, `Tube`, `Cone`, `Sphere` and `Orb`, the position of the shape `position` which can be expressed either as floats or strings which are parsed, the material of the shape `material` and the optional parameter `colour`. 
A list of materials is given by running:
```
g4basic.listMaterials()
```
You can view the required parameters for the shapes [here](http://www.apc.univ-paris7.fr/~franco/g4doxy4.10/html/class_g4_ez_volume.html), however if the parameters are invalid when running the script the information will be expressed within the logging information also. 

To create a 10x10x3m cuboid of lead:
```
volume_dict = {'Calo' : {'vol_type'   : 'Box',
                         'position'   : (0., 0., '-20m'),
                         'dimensions' : ('10m', '10m', '3m'),
                         'material'   : 'Pb',
                         'colour'     : 'blue'}}

```

For the particle gun dictionary the arguments are the particle to be fired `particle`, the position of the particle gun `position` and one of two possibilities for defining the energy. The first option is to specify `energy` and `direction`, the second is to supply the `momentum`:

To create a particle gun firing electrons at 3GeV:

```
pgun_dict = {'particle' : 'e-', 'energy' : '3GeV', 'direction' : (0,0,1),
             'position' : (0, 0, '-20m')}
```

or

```
pgun_dict = {'particle' : 'e-', 'momentum' : (0, 0, '3GeV'),
             'position' : (0, 0, '-20m')}
```

you can also choose to add geometry or the particle later, for the same examples:

```
import g4basic as g4b

my_session = g4b.G4Session()

my_session.addVolume('Calo', 'Pb', 'Box', ('10m', '10m', '3m'), (0., 0., '-20m'), colour='blue')

my_session.addParticleGun('e-', (0, 0, '-20m'), energy='3GeV', direction=(0,0,1))
```

An instance of the `G4Session` class also allows specification of Physics List `phys_list` a full list of which is available in the `help` function for this class:

```
my_session = g4basic.G4Session(volumes_dict=volume_dict, guns_opt_dict=pgun_dict, phys_list='QGSP_BERT')
```

To run the simulation we use the `runSimulation` command, by default the viewer utilised uses OpenGL `OGLIX`, shows the particle hits and trajectories, creates a single event and positions the camera at a theta-phi angle of (80,20) displaying the objects in style `wireframe`:

```
x.runSimulation(nevts=10, viewer='OGLIX', hits=True, trajectories='smooth', logo=False, view=(80,20), style='surface')
```

the `logo` option simply displays the 3D G4 logo or the 2D logo if `'2d'` is used as an argument.

See the `examples` folder in this module for a working example.
