import g4basic as g4b

# Create a Copper Cylinder and Silicon Box positioned in sequence

_volumes = {'Spect' : {'material' : 'Cu',
                       'vol_type' : 'Tube',
                      'position' : (0,0,'5m'),
                      'dimensions' : (0.1, '2.5m', '4m'),
                      'colour' : 'red'},
            'BB'   : {'material' : 'Si',
                      'vol_type' : 'Box',
                      'position' : (0, 0, 0),
                      'dimensions' : ('10m', '10m', '3m'),
                      'colour' : 'yellow'}}

# Fire 50GeV proton

_gun_dict = {'particle' : 'proton', 'energy' : '50GeV', 'direction' : (0,0,1),
             'position' : (0,0,'-5m')}

session = g4b.G4Session(volumes_dict=_volumes, gun_opts_dict=_gun_dict, phys_list='FTFP_BERT')

session.runSimulation()
