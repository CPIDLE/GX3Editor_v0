# INDEX

<!-- cc: 自動維護。hook 自動 append 新檔，/pm index 全量更新，/pm bye 清理掃描 -->

| 檔名 | 用途 | 狀態 | 日期 | 來源 |
|---|---|---|---|---|
| README.md | 專案說明 | active | 2026-11-06 | — |
| CLAUDE.md | 專案脈絡與修改規則（給 AI） | active | 2026-11-06 | — |
| HANDOFF_GX3Editor.md | 從 FX5_PLC session 交接：格式解碼、工具、GUI 驅動筆記 | active | 2026-11-06 | — |
| FX5U_輸送帶計數推料_範例程式.md | 輸送帶計數推料範例程式規格（I/O、17 rung 指令表、測試步驟） | final | 2026-11-06 | — |
| TEST_0.gx3 | 產生程式用的基底範本（勿修改） | final | 2026-11-06 | — |
| FX5U_conveyor_uncompiled.gx3 | 輸送帶範例，cc 產生、未轉換 | final | 2026-11-06 | — |
| FX5U_conveyor_compiled.gx3 | 輸送帶範例，GX Rebuild All 後（Error 0 / Warning 0，163 steps） | final | 2026-11-06 | ← FX5U_conveyor_uncompiled.gx3 |
| FX5U_conveyor.gx3 | 早期 GX build 的同一程式（與 compiled 等效） | archived | 2026-11-06 | — |
| FX5U_conveyor_selfcompiled.gx3 | 自編譯實驗：M39→Y4 改成 SM400→Y4，蜂鳴器常亮，僅供測試 | one-off | 2026-11-06 | ← FX5U_conveyor_compiled.gx3 |
| TEST_0_edit.gx3 | 早期直接編輯實驗 | one-off | 2026-11-06 | ← TEST_0.gx3 |
| TEST_0_rung_a.gx3 | 早期 rung 實驗 | one-off | 2026-11-06 | ← TEST_0.gx3 |
| TEST_0_rung_b.gx3 | 早期 rung 實驗 | one-off | 2026-11-06 | ← TEST_0.gx3 |
| gx3_tests/S_samples.gx3 | GX 手打的參考 rung（編碼對照基準） | final | 2026-11-06 | — |
| gx3_tests/C_csvtest.gx3 | CSV 匯入測試（1.007H 無此功能） | one-off | 2026-11-06 | — |
| gx3_tests/T_g1_X_contact.gx3 | 產生測試：X 接點 | one-off | 2026-11-06 | — |
| gx3_tests/T_g2_NC_contact.gx3 | 產生測試：b 接點 | one-off | 2026-11-06 | — |
| gx3_tests/T_g3_SM_contact.gx3 | 產生測試：SM 接點 | one-off | 2026-11-06 | — |
| gx3_tests/T_g4_series.gx3 | 產生測試：串聯 | one-off | 2026-11-06 | — |
| gx3_tests/T_g5_timer_sK.gx3 | 產生測試：計時器 K 值 | one-off | 2026-11-06 | — |
| gx3_tests/T_g6_timer_pair.gx3 | 產生測試：計時器成對 | one-off | 2026-11-06 | — |
| tools/gx3gen.py | rung 模型 → LDDB；write_project 寫出 .gx3 | active | 2026-11-06 | — |
| tools/gx3comp.py | 自寫編譯器：MIL、step 數、機器碼 | active | 2026-11-06 | — |
| tools/conveyor.py | 輸送帶範例 rung 清單與產生入口 | active | 2026-11-06 | — |
| tools/build.ps1 | 一鍵產生 + 驅動 GX Rebuild All + 存檔 | active | 2026-11-06 | — |
| tools/verify_comp.py | 驗證 gx3comp 輸出與 GX 逐位元組相同 | active | 2026-11-06 | — |
| tools/selfcompile_patch.py | 不經 GX 修補單一 rung 的自編譯實驗 | one-off | 2026-11-06 | — |
| .gitignore | 擋 settings.local.json、金鑰、__pycache__ | active | 2026-11-06 | — |
| tools/gx3ascii.py | rung 清單 → ASCII 階梯圖（讀 spec 不執行） | active | 2026-11-06 | — |
