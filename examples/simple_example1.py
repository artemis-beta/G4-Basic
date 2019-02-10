import g4basic as g4b

volume_dict = {'Box' : {'vol_type' : 'Box', 'position' : (0,0,0),
                        'dimensions' : ('11m', '10m', '10m'), 'material' : 'Si',
                        'colour' : 'blue'}}

gun_dict = {'particle' : 'e-', 'energy' : 1000, 'direction' : (0,0,1),
            'position' : (0,0,'-20m')}

phys_list='FTFP_BERT'

my_sim = g4b.G4Session(volumes_dict=volume_dict, gun_opts_dict=gun_dict, phys_list=phys_list)

my_sim.runSimulation(nevts=False)
