"""
Test the basic membrane physiology of cell types.

Usage:   python test_cells.py celltype species [--cc | --vc]

This script generates a cell of the specified type and species, then tests the
cell with a series of current/voltage pulses to produce I/V, F/I, and spike
latency analyses.

"""

import argparse
import os, sys
from neuron import h

import cnmodel
import cnmodel.cells as cells
from cnmodel.protocols import IVCurve, VCCurve

debugFlag = True
parser = argparse.ArgumentParser(description=('test_cells.py:',
' Biophysical representations of neurons (mostly auditory), test file'))

cclamp = False
cellinfo = {'types': ['bushy', 'stellate', 'stellatenav11', 'steldend', 'dstellate', 'dstellateeager', 'sgc',
                        'cartwheel', 'pyramidal', 'octopus', 'tuberculoventral'],
            'configs': ['std', 'waxon', 'dendrite'],
            'nav': ['std', 'jsrna', 'nav11'],
            'species': ['guineapig', 'cat', 'rat', 'mouse'],
            'pulse': ['step', 'pulse']}
# Format for ivranges is list of tuples. This allows finer increments in selected ranges, such as close to rest
ccivrange = {'bushy': {'pulse': [(-0.5, 0.5, 0.025)]},
            'stellate': {'pulse': [(-0.2, 0.2, 0.02), (-0.015, 0, 0.005)]},
            'stellatenav11': {'pulse': [(-0.5, 1., 0.1)]}, # , (-0.015, 0, 0.005)]},
            'steldend': {'pulse': [(-1.0, 1.0, 0.1)]},
            'dstellate': {'pulse': [(-0.2, 0.2, 0.0125)]},
            'dstellateeager': {'pulse': [(-0.6, 1.0, 0.025)]},
            'sgc': {'pulse': [(-0.3, 0.3, 0.01)]},
            'cartwheel': {'pulse': [(-0.2, 0.1, 0.02)]},
            'pyramidal': {'pulse': [(-0.3, 0.3, 0.025), (-0.040, 0.025, 0.005)], 'prepulse': [(-0.25, -0.25, 0.25)]},
            'tuberculoventral': {'pulse': [(-0.35, 0.6, 0.02)]},
            'octopus': {'pulse': [(-3., 3., 0.2)]},
            }

# scales holds some default scaling to use in the cciv plots
# argument is {cellname: (xmin, xmax, IVymin, IVymax, FIspikemax,
# offset(for spikes), crossing (for IV) )}
## the "offset" refers to setting the axes back a bit
scale = {'bushy': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'stellate': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'stellatenav11': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'steldend': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'dstellate': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'dstellateeager': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'sgc:': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'cartwheel': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'pyramidal': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'tuberculoventral': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60]),
            'octopus': (-1.0, -160., 1.0, -40, 0, 40, 'offset', 5,
                'crossing', [0, -60])}
ax = None
h.celsius = 22
parser.add_argument('celltype', action='store')
parser.add_argument('species', action='store', default='guineapig')
parser.add_argument('--type', action='store', default=None)
parser.add_argument('--temp', action='store', default=22.0,
                    help=("Temp DegC (22 default)"))
    # species is an optional option....
parser.add_argument('-c', action="store", dest="configuration",
    default='std', help=("Set axon config: %s " %
        [cfg for cfg in cellinfo['configs']]))
parser.add_argument('--nav', action="store", dest="nav", default="na",
    help=("Choose sodium channel: %s " % [ch for ch in cellinfo['nav']]))
parser.add_argument('--ttx', action="store_true", dest="ttx", default=False,
    help=("Use TTX (no sodium current"))
parser.add_argument('-p', action="store", dest="pulsetype", default="step",
    help=("Set CCIV pulse to step or repeated pulse"))
clampgroup = parser.add_mutually_exclusive_group()
clampgroup.add_argument('--vc', action='store_true',
    help="Run in voltage clamp mode")
clampgroup.add_argument('--cc', action='store_true',
    help="Run in current clamp mode")
clampgroup.add_argument('--demo', action='store_true',
    help="Run in  voltage clamp demo")
args = parser.parse_args()
print args.celltype
if args.celltype in cellinfo['types']:
    print 'cell: %s is ok' % args.celltype
else:
    print 'cell: %s is not in our list of cell types' % (args.celltype)
    print 'celltypes: ', cellinfo['types']
    sys.exit(1)

path = os.path.dirname(cnmodel.__file__)
#h.nrn_load_dll(os.path.join(path, 'i386/special'))
h.load_file("stdrun.hoc")
h.load_file(os.path.join(path, "custom_init.hoc"))
# replace init with one that gets closer to steady state

print 'configuration: ', args.configuration
print 'species: ', args.species
sites = None
if args.pulsetype == 'step':
    ptype = None
else:
    ptype = 'pulses'
if args.configuration in cellinfo['configs']:
    print 'Configuration %s is ok' % args.configuration

default_durs = [10., 100., 20.]

#
# Spiral Ganglion cell tests
#
if args.celltype == 'sgc':
    cell = cells.SGC.create(debug=debugFlag, species=args.species, nach=args.nav, ttx=args.ttx, modelType=args.type)

#
# T-stellate tests
#
elif args.celltype == 'stellate':
     cell = cells.TStellate.create(model='RM03', debug=debugFlag, species=args.species, nach=args.nav, modelType=args.type, ttx=args.ttx)

elif args.celltype == 'stellatenav11':  # note this uses a different model...
    print 'test_cells: Stellate NAV11'
    cell = cells.TStellateNav11.create(model='Nav11', debug=debugFlag, species=args.species, modelType=None, ttx=args.ttx)
#
# Bushy tests
#
elif args.celltype == 'bushy' and args.configuration == 'waxon':
    cell = cells.Bushy.create(debug=debugFlag, species=args.species, nach=args.nav, modelType=args.type, ttx=args.ttx)
    cell.add_axon()

elif args.celltype == 'bushy' and args.configuration == 'std':
    cell = cells.Bushy.create(debug=debugFlag, species=args.species, nach=args.nav, modelType=args.type, ttx=args.ttx)

#
# Ocotpus tests
#
elif args.celltype == 'octopus' and args.configuration == 'std':
    cell = cells.Octopus.create(debug=debugFlag, species=args.species, nach='jsrna', modelType=args.type, ttx=args.ttx)
#
# Ocotpus tests
#
elif args.celltype == 'octopus' and args.configuration == 'waxon':
    cell = cells.Octopus.create(debug=debugFlag, morphology='cnmodel/morphology/octopus_spencer_stick.hoc',
        decorator=True,
        species=args.species, nach='jsrna', modelType=args.type, ttx=args.ttx)

#
# D-stellate tests
#
elif args.celltype == 'dstellate':
    cell = cells.DStellate.create(debug=debugFlag, ttx=args.ttx, modelType=args.type)

elif args.celltype == 'dstellateeager':
    cell = cells.DStellateEager.create(debug=debugFlag, ttx=args.ttx, modelType=args.type)

#
# DCN pyramidal cell tests
#
elif args.celltype == 'pyramidal':
    cell = cells.Pyramidal.create(debug=debugFlag, ttx=args.ttx, modelType=args.type)

#
# DCN tuberculoventral cell tests
#
elif args.celltype == 'tuberculoventral':
    cell = cells.Tuberculoventral.create(debug=debugFlag, ttx=args.ttx, modelType='TVmouse', species='mouse',
            morphology='cnmodel/morphology/tv_stick.hoc', decorator=True)
    h.topology()

#
# DCN cartwheel cell tests
#
elif args.celltype == 'cartwheel':
    cell = cells.Cartwheel.create(debug=debugFlag, ttx=args.ttx, modelType=args.type)

else:
    print ("Cell Type %s and configurations nav=%s or config=%s are not available" % (args.celltype, args.nav, args.configuration))
    sys.exit(1)
#    seg = cell()

print("Cell model: %s" % cell.__class__.__name__)
print(cell.__doc__)

import pyqtgraph as pg
app = pg.mkQApp()

#
# define the current clamp electrode and default settings
#
if args.cc is True:
    iv = IVCurve()
    iv.run(ccivrange[args.celltype],  cell, durs=default_durs,
           sites=sites, reppulse=ptype, temp=float(args.temp))
    ret = iv.input_resistance_tau()
    print('    From IV: Rin = {:7.1f}  Tau = {:7.1f}  Vm = {:7.1f}'.format(ret['slope'], ret['tau'], ret['intercept']))
    iv.show(cell=cell)

elif args.vc is True:
    vc = VCCurve()
    vc.run((-120, 40, 5), cell)
    vc.show(cell=cell)

elif args.demo is True:
    run_democlamp(cell, dendrites)

else:
    print("Nothing to run. Specify one of --cc, --vc, --democlamp.")
    sys.exit(1)


#-----------------------------------------------------------------------------
#
# If we call this directly, provide a test with the IV function
#


if sys.flags.interactive == 0:
    pg.QtGui.QApplication.exec_()
