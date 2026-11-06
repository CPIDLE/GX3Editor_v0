# INDEX

<!-- cc: 自動維護。hook 自動 append 新檔，/pm index 全量更新，/pm bye 清理掃描 -->

| 檔名 | 用途 | 狀態 | 日期 | 來源 |
|---|---|---|---|---|
| README.md | 專案說明 | active | 2026-11-06 | — |
| CLAUDE.md | 專案脈絡與修改規則（給 AI） | active | 2026-11-06 | — |
| HANDOFF_GX3Editor.md | 格式解碼、工具、GUI 驅動的技術筆記（自 FX5_PLC session 交接） | active | 2026-11-06 | — |
| FX5U_輸送帶計數推料_範例程式.md | 輸送帶計數推料範例程式規格（I/O、GX 樣式梯形圖、測試步驟） | final | 2026-11-06 | — |
| TEST_0.gx3 | 產生程式用的基底範本（勿修改） | final | 2026-11-06 | — |
| FX5U_conveyor_uncompiled.gx3 | 輸送帶範例，cc 產生、未轉換 | final | 2026-11-06 | — |
| FX5U_conveyor_compiled.gx3 | 輸送帶範例，GX Rebuild All 後（Error 0 / Warning 0，163 steps） | final | 2026-11-06 | ← FX5U_conveyor_uncompiled.gx3 |
| gx3_tests/S_samples.gx3 | GX 手打的參考 rung（編碼對照基準） | final | 2026-11-06 | — |
| tools/gx3gen.py | rung 模型 → LDDB；write_project 寫出 .gx3 | active | 2026-11-06 | — |
| tools/gx3comp.py | 自寫編譯器：MIL、step 數、機器碼 | active | 2026-11-06 | — |
| tools/gx3ascii.py | rung 清單 → GX 樣式 ASCII 階梯圖（步號、聲明、軟元件註解） | active | 2026-11-06 | — |
| tools/conveyor.py | 輸送帶範例 rung 清單、聲明、軟元件註解與產生入口 | active | 2026-11-06 | — |
| tools/build.ps1 | 一鍵產生 + 驅動 GX Rebuild All + 存檔 | active | 2026-11-06 | — |
| tools/verify_comp.py | 驗證 gx3comp 輸出與 GX 逐位元組相同 | active | 2026-11-06 | — |
| tools/selfcompile_patch.py | 不經 GX 修補單一 rung 的自編譯實驗（實機驗證待辦） | active | 2026-11-06 | — |
| .gitignore | 擋 settings.local.json、金鑰、__pycache__ | active | 2026-11-06 | — |
