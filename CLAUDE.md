# GX3Editor_v0

讀取、產生、編輯與編譯 GX Works3（FX5U）`.gx3` 專案檔，免在 GX 裡逐格手打。格式解碼與 GUI 驅動細節見 `HANDOFF_GX3Editor.md`。

## 架構與核心模組

- `tools/gx3gen.py` — rung 模型 `(branches, series, outputs)` → LDDB 文字；`write_project(base, dst, rungs, tmpdir)` 寫出 `.gx3`
- `tools/gx3comp.py` — rung 模型 → MIL 文字、step 數、機器碼（import gx3gen 的 `dev`、`output_spec`）
- `tools/conveyor.py` — 輸送帶範例 rung 清單 `R`，也是新程式的寫法範本
- `tools/build.ps1` — 產生 → 啟動 GX → Rebuild All → 存檔 → 讀 `Progress.txt` 回報
- `tools/verify_comp.py` / `tools/selfcompile_patch.py` — 編譯器驗證與自編譯實驗
- 資料流：rung 清單 → gx3gen 寫 `*_LDDB.db`（`translated=0`）→ GX Rebuild All 重建其餘檔案

## Build / Test

```bash
# 安裝：無（僅標準函式庫）

# 跑測試（目前沒有測試；hook 的 check.sh 為 no-op）
true

# 產生 + GX 編譯（GX 須先關閉）
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

## 反直覺的坑

- `.gx3` 是 ZIP，entry 名稱用反斜線；重建時要 `zi.filename = i.orig_filename`。
- 任何一個 block 解析失敗，GX 會整個階梯圖空白，且不跳錯誤。
- LDDB 標頭數字是各 token 的長度，不是型別碼（gx3-cli-mcp 的說法是錯的）。
- 軟元件編號 128–255 的編碼尚未觀察到，gx3gen 會直接報錯。
- `Program.qpg` 裡的 V 是每次 build 的 ID，不是 checksum。
- `.ps1` 只能用 ASCII（PS 5.1 把無 BOM 的 UTF-8 當 ANSI）；按鈕用 `*(Y)*` 比對。
- 不用 GX 模擬（1.007H 不支援 FX5，使用者也說不要用）。
- 交檔前要關閉 GX；使用者說「先暫停」立即停止 GUI 操作。
- `TEST_0.gx3` 是基底範本，不要修改。

---

## 修改規則（給 AI）

- **改前**：完整讀目標檔 + 所有 import 它的模組；不准假設 API，用 grep 確認簽名。
- **改中**：禁止 `# ...` 佔位註解；不省略未改動的程式（會截斷就用 Write 全量輸出）。
- **改後**：hook 會自動跑相關測試，失敗立刻停下修；**commit 前**跑完整的 `true`，要看到全綠才 commit。新增或改動編碼時，以 GX 實際輸出比對驗證（例如 `tools/verify_comp.py`）。
- **禁止**：未經要求重構能跑的程式、改既有資料結構欄位定義、擴大 scope。

> 機器強制：`.claude/settings.json` 的 PostToolUse hook 會在 Write/Edit **之後**（檔案已經寫入）自動跑 `.claude/check.sh`——它擋不了「這一次」寫入本身，但測試失敗時會把輸出寫到 stderr 並以 exit 2 結束，失敗明細因此會回饋給 AI（2026-10-08 實測；exit 1 或 stdout 都到不了 AI）。hook 只跑**跟這次改的檔案相關的測試**（改文件／設定不跑；pytest 專案只跑該測試檔或提到該模組的測試檔），通常比整個 suite 快很多；**完整的 `true` 由 AI 在 commit 前自己跑**。
