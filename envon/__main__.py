
from .cli      import parse_args
from .assembly import disassemble_file
from .analysis import Analysis, Optimizer
from .graph    import make_graph_file, make_graph_memory_file
from .pick     import print_instructions

fi, fo, skip, pick = parse_args()
ens = disassemble_file(fi)
a   = Analysis()
a.analyze(ens, skip)
o   = Optimizer()
o.optimize(a)

make_graph_file(a)
make_graph_memory_file(a.get_entry_block().get_memphi())

if pick:
    print_instructions(fo, a, pick)
