from pyansys import examples
from pyansys import launch_mapdl

mapdl = launch_mapdl(run_location='D:/CP Test/', override=True, jobname='py_job')
# print(mapdl.directory)

try:
    # load a beam stored as an example archive file and mesh it
    mapdl.prep7()
    filename = 'CPTEST'
    mapdl.cdread('db', filename, 'cdb')
    mapdl.nsel('s', 'NODE', vmin=1, vmax=5)
    mapdl.nlist('all')
    # mapdl.esel('s', 'ELEM', vmin=5, vmax=20)
    # mapdl.cm('ELEM_COMP', 'ELEM')
    # mapdl.nsel('s', 'NODE', vmin=5, vmax=20)
    # mapdl.cm('NODE_COMP', 'NODE')

    # boundary conditions
    # mapdl.allsel()

    # dummy steel properties
    # mapdl.prep7()
    # mapdl.mp('EX', 1, 200E9)  # Elastic moduli in Pa (kg/(m*s**2))
    # mapdl.mp('DENS', 1, 7800)  # Density in kg/m3
    # mapdl.mp('NUXY', 1, 0.3)  # Poissons Ratio
    # mapdl.emodif('ALL', 'MAT', 1)

    # fix one end of the beam
    # mapdl.nsel('S', 'LOC', 'Z')
    # mapdl.d('all', 'all')
    # mapdl.allsel()
    mapdl.esln('s')
    mapdl.mxpand(elcalc='YES')
    mapdl.modal_analysis(nmode=6)

    result = mapdl.result
    # print('aaa', mapdl.post_processing.filename)  # nodal_rotation('all')
    mapdl.post1()
    mapdl.set(1, 1)
    rot = mapdl.post_processing.nodal_rotation('all')
    disp = mapdl.post_processing.nodal_displacement('all')
    print(disp)
    print(rot)
    # print(mapdl.nodes)
    # for i in range(0, 5):
    #     print(nnum[i], disp[i])
    mapdl.finish()

finally:
    mapdl.exit()
