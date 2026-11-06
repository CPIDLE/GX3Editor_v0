import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gx3gen import write_project
# Rung comments are drawn by gx3ascii.py: "# <title> | <note>"; a comment with only "| <note>" continues the rung group above.
R = [  # (OR branches, series contacts, outputs)  -- FX5U_輸送帶計數推料_範例程式.md
 ([['SM402']], [], ['RST M20', 'RST C0', 'ZRST M30 M32']),   # 列 1：開機初始化
 ([['X2']], ['X6'], ['M1']),                                   # 列 2：安全條件 | X2 急停正常、X6 過載正常
 ([['/X6']], [], ['SET M31']),                                 # 列 3：過載異常
 ([['X0'], ['M0']], ['X1', 'M1', '/M39'], ['M0']),             # 列 4：系統運轉自保持 | X0 啟動、M0 自保持、X1 停止(NC)、M1 安全 OK、M39 無異常
 ([['M0']], ['/M20'], ['Y0']),                                 # 列 5：輸送帶馬達 | M20 推料中停止輸送
 ([['X3']], ['Y0'], ['PLS M10']),                              # 列 6：產品計數脈衝
 ([['M10']], [], ['OUT C0 K10', 'INC D10']),                   # 列 7：計數器、累計產量
 ([['C0']], [], ['SET M20']),                                  # 列 8：批次完成
 ([['M20']], ['/T1', 'M1', '/M39'], ['Y1']),                   # 列 9：推料電磁閥 | T1 保持時間到即縮回、M1 急停時立即縮回
 ([['M20']], ['X4'], ['OUT T1 K10']),                          # 列 10：推到底保持 1 秒
 ([['T1']], ['X5'], ['INC D0', 'RST C0', 'RST M20']),          # 列 11：推料完成、回原點 | INC D0 批次數 +1
 ([['Y1']], ['/X4'], ['OUT T2 K30']),                          # 列 12：推料逾時偵測
 ([['T2']], [], ['SET M32']),
 ([['X3']], ['Y0'], ['OUT T0 K50']),                           # 列 13：卡料偵測
 ([['T0']], [], ['SET M30']),
 ([['M30'], ['M31'], ['M32']], [], ['M39']),                   # 列 14：異常總合
 ([['X7']], [], ['RST M30', 'RST M32']),                       # 列 15：異常復歸
 ([['X7']], ['X6'], ['RST M31']),                              # | X6 過載已排除才可復歸
 ([['M0']], [], ['Y2']),                                       # 列 16：指示燈、蜂鳴器
 ([['M39']], ['SM412'], ['Y3']),
 ([['M39']], [], ['Y4']),
 ([['M20']], [], ['Y5']),
 ([['SM400']], [], ['MOV C0 D1']),                             # 列 17：HMI 監看用
]
write_project(sys.argv[1], sys.argv[2], R, os.path.dirname(os.path.abspath(__file__)))
print(len(R), 'rungs ->', sys.argv[2])
