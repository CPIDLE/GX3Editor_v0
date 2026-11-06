# GX3Editor_v0

用 Python 讀取、產生、編譯三菱 FX5U 的 GX Works3 專案檔（`.gx3`），免在 GX 裡逐格手打階梯圖。
Read, generate and compile Mitsubishi FX5U GX Works3 projects (`.gx3`) from Python, without drawing ladder rungs by hand in GX.

## 功能 / Features

- **產生 / Generate** — `tools/gx3gen.py`：rung 清單 → `.gx3`，GX 開啟後 Rebuild All 即可。Rung list → `.gx3` that GX opens and rebuilds.
- **一鍵 build / One-step build** — `tools/build.ps1`：產生後自動驅動 GX 編譯並存檔。Generates, then drives GX to Rebuild All and save.
- **編譯器 / Compiler** — `tools/gx3comp.py`：輸出與 GX 逐位元組相同的機器碼（`verify_comp.py` 驗證）。Machine code byte-identical to GX.
- **階梯圖 / Ladder view** — `tools/gx3ascii.py`：GX 樣式 ASCII 階梯圖。GX-style ASCII ladder diagram.
- 元件 / Devices：X、Y、M、SM、T、C、D；指令 / Instructions：a/b 接點、OUT、SET、RST、PLS、OUT T/C K、MOV、INC、ZRST。

## 需求 / Requirements

Windows、Python 3.13（僅標準函式庫 / stdlib only）、GX Works3 1.007H。

## 使用 / Usage

```powershell
# 只產生（不需 GX）/ Generate only (no GX needed)
python -I programs\conveyor\conveyor.py templates\TEST_0.gx3 out.gx3

# 產生 + GX 編譯（先關閉 GX，執行中勿動滑鼠鍵盤）/ Generate + compile in GX (close GX first; hands off while it runs)
powershell -ExecutionPolicy Bypass -File tools\build.ps1 -Spec programs\conveyor\conveyor.py -Name FX5U_conveyor

# ASCII 階梯圖 / ASCII ladder
python -I tools\gx3ascii.py programs\conveyor\conveyor.py
```

新程式：仿照 `programs/conveyor/conveyor.py` 在 `programs/<name>/` 寫 rung 清單 `R`。
New program: copy `programs/conveyor/conveyor.py` into `programs/<name>/` and edit the rung list `R`.

## 結構 / Layout

| 路徑 / Path | 內容 / Contents |
|---|---|
| `tools/` | 產生器、編譯器、build 腳本 / generator, compiler, build script |
| `programs/` | 各 PLC 程式的 spec 與 `.gx3` / per-program specs and outputs |
| `templates/TEST_0.gx3` | 基底範本（勿改）/ base template (do not edit) |
| `reference/` | GX 手打的編碼參考 / hand-made encoding reference |
| `docs/gx3-format-notes.md` | 格式解碼筆記 / format notes |

## 限制 / Limitations

- 不使用 GX 模擬（1.007H 不支援 FX5）/ No simulation (1.007H can't simulate FX5).
- 自編譯的 `Program.qpg` 未經實機驗證 / Self-compiled `Program.qpg` not tested on a real PLC.
- 尚不支援寫入軟元件註解（`*_DC.db`）/ Device comments (`*_DC.db`) not written yet.
