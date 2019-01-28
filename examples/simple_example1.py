import g4basic as g4b


my_geo = g4b.Geometry('MyGeo', 'AIR')

my_geo.add_volume('Box', 'TestBox', 'Si', ('5m', '5m', '1m'), (0,0,0))

my_gun = g4b.PGun('MyPGun', 'e-', '100GeV', (0,0,'-1m'), (0,0,'100GeV')) 
my_geo.draw()
