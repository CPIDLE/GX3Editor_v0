import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gx3gen import write_project
R = [  # (OR branches, series contacts, outputs)  -- FX5U_輸送帶計數推料_範例程式.md
 ([['SM402']], [], ['RST M20', 'RST C0', 'ZRST M30 M32']),   # 1 init
 ([['X2']], ['X6'], ['M1']),                                   # 2 safety OK
 ([['/X6']], [], ['SET M31']),                                 # 3 overload alarm
 ([['X0'], ['M0']], ['X1', 'M1', '/M39'], ['M0']),             # 4 run self-hold
 ([['M0']], ['/M20'], ['Y0']),                                 # 5 conveyor
 ([['X3']], ['Y0'], ['PLS M10']),                              # 6 count pulse
 ([['M10']], [], ['OUT C0 K10', 'INC D10']),                   # 7 counter, total
 ([['C0']], [], ['SET M20']),                                  # 8 batch done
 ([['M20']], ['/T1', 'M1', '/M39'], ['Y1']),                   # 9 pusher valve
 ([['M20']], ['X4'], ['OUT T1 K10']),                          # 10 hold 1 s
 ([['T1']], ['X5'], ['INC D0', 'RST C0', 'RST M20']),          # 11 cycle done
 ([['Y1']], ['/X4'], ['OUT T2 K30']),                          # 12 pusher timeout timer
 ([['T2']], [], ['SET M32']),
 ([['X3']], ['Y0'], ['OUT T0 K50']),                           # 13 jam timer
 ([['T0']], [], ['SET M30']),
 ([['M30'], ['M31'], ['M32']], [], ['M39']),                   # 14 any alarm
 ([['X7']], [], ['RST M30', 'RST M32']),                       # 15 alarm reset
 ([['X7']], ['X6'], ['RST M31']),
 ([['M0']], [], ['Y2']),                                       # 16 lamps
 ([['M39']], ['SM412'], ['Y3']),
 ([['M39']], [], ['Y4']),
 ([['M20']], [], ['Y5']),
 ([['SM400']], [], ['MOV C0 D1']),                             # 17 HMI
]
write_project(sys.argv[1], sys.argv[2], R, os.path.dirname(os.path.abspath(__file__)))
print(len(R), 'rungs ->', sys.argv[2])
