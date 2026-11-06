# GX3Editor_v0

讓 cc 不必在 GX Works3 裡逐格手打，就能讀取、產生、編輯與編譯三菱 FX5U 的 GX Works3 專案檔（`.gx3`）。`.gx3` 的階梯圖格式已解碼：用 Python 描述各個 rung，就能產生 GX Works3 可直接開啟的專案，再交由 GX 的 Rebuild All 編譯，或用自寫的編譯器產生與 GX 逐位元組相同的機器碼。

## 功能特色

- **產生階梯圖**：`tools/gx3gen.py` 依 rung 模型（OR 分支、串聯接點、輸出）寫入 `*_LDDB.db`，GX 開啟後 Rebuild All 即可轉換（輸送帶範例：Error 0 / Warning 0，163 steps）。
- **一鍵 build**：`tools/build.ps1` 產生未轉換版後，自動驅動 GX Works3 做 Rebuild All 並存檔，產出 `<Name>_uncompiled.gx3` 與 `<Name>_compiled.gx3`。
- **自寫編譯器**：`tools/gx3comp.py` 產出 MIL 文字、step 數與機器碼，輸送帶 23 個 rung 與 GX 輸出逐位元組相同（`tools/verify_comp.py` 驗證）。
- 支援的元件：X、Y（八進位）、M、SM、T、C、D；指令：接點 a/b、線圈、SET、RST、PLS、OUT T/C K、MOV、INC、ZRST。

## 技術棧

- Python 3.13（僅標準函式庫：`zipfile`、`sqlite3`、`uuid`、`re`）
- Windows PowerShell 5.1（UIAutomation、user32 P/Invoke，用來驅動 GX Works3 GUI）
- GX Works3 1.007H（FX5U）

## 開始使用

### 前置需求

- Windows，已安裝 GX Works3（預設 `C:\Program Files (x86)\MELSOFT\GPPW3\GXW3.exe`）
- Python 3.13

### 安裝

不需安裝套件，直接使用 `tools/` 下的腳本。

### 使用方式

只產生未轉換的專案（不需 GX）：

```powershell
python -I tools\conveyor.py TEST_0.gx3 out.gx3
```

產生並由 GX 編譯（執行前先關閉 GX Works3，執行約 30 秒間請勿操作滑鼠鍵盤）：

```powershell
powershell -ExecutionPolicy Bypass -File tools\build.ps1 [-Spec tools\conveyor.py] [-Name FX5U_conveyor] [-Base TEST_0.gx3]
```

把 rung 清單畫成 ASCII 階梯圖：

```powershell
python -I tools\gx3ascii.py [tools\conveyor.py]
```

新程式：仿照 `tools/conveyor.py` 寫一份 rung 清單 `R`，呼叫 `write_project(base, dst, R, tmpdir)`。尚未支援的指令，先在 GX 手打一個範例 rung、存檔，再讀出 LDDB 找出編碼。

## 專案結構

```
TEST_0.gx3                         產生用的基底範本（勿修改）
FX5U_conveyor_uncompiled.gx3       輸送帶範例，未轉換
FX5U_conveyor_compiled.gx3         輸送帶範例，GX 編譯後（Error 0 / Warning 0）
FX5U_輸送帶計數推料_範例程式.md      輸送帶範例程式規格
HANDOFF_GX3Editor.md               格式解碼與 GUI 驅動的完整筆記
tools/                             gx3gen / gx3comp / build.ps1 等工具
gx3_tests/                         早期實驗；S_samples.gx3 是 GX 手打的編碼參考
```

## 限制

- GX Works3 1.007H 無 CSV 匯入、無法模擬 FX5；不使用模擬。
- 自編譯的 `Program.qpg` 未經實機 PLC 驗證。
- 軟元件註解（`*_DC.db`）尚未支援寫入。
