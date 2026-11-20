# Papercraft Stop Motion Skills / 紙藝定格動畫 Skill

做出剪紙角色、分層燈箱場景，以及 30 秒到 3 分鐘的雙語（英文＋繁體中文）兒童故事短片。
Agent skills for cut-paper characters, layered lightbox sets and 30 s – 3 min bilingual (English + Traditional Chinese) children's story shorts.

## 兩個版本 / Two versions

| 資料夾 / Folder | 適合 / For | 做法 / Approach |
| --- | --- | --- |
| [`papercraft-stop-motion/`](papercraft-stop-motion) | 強模型（Claude Opus/Sonnet、GPT-5 級、Gemini Pro 級）<br>Strong models | 完整規則與品質門檻，可自行判斷、擴充腳本<br>Full rules and quality bar; may extend the scripts |
| [`papercraft-stop-motion-lite/`](papercraft-stop-motion-lite) | 較小或較便宜的模型<br>Smaller / cheaper models | 固定 10 步、每步有關卡；模型只寫 JSON 和生圖提示詞<br>10 gated steps; the model only writes JSON and image prompts |

兩版共用同一套腳本：`plan_lint.py`（規劃檢查）、`split_sheet.py`（切動作表）、`render.py`（JSON → 影片）、`mix_audio.py`（混音）、`check_video.py`（成品驗收）、`scan_secrets.py`（金鑰掃描）。
Both share the same scripts: plan lint, sheet slicing, JSON-to-video renderer, audio mixer, final checker and secret scanner.

## 安裝 / Install

把其中一個資料夾複製到 agent 的 skills 目錄，例如：
Copy one folder into your agent's skills directory, e.g.:

```sh
cp -r papercraft-stop-motion ~/.codex/skills/        # Codex
cp -r papercraft-stop-motion ~/.claude/skills/       # Claude Code
cp -r papercraft-stop-motion-lite ~/.codex/skills/   # lite version
```

需求 / Requirements: Python 3.10+, Pillow, NumPy, ffmpeg, an image-generation tool.

## 使用 / Use

> 用 papercraft-stop-motion 做一支 2 分鐘的紙藝定格動畫，主角是小狐狸，單字：beach, shell, wave, crab, boat, lighthouse, whale。
>
> Use papercraft-stop-motion-lite to make a 30-second papercraft weather lesson with the elephant.

## 重點 / What makes the films better

- 前中後三層景深，加上石頭、船這類平台；主角大小跟著位置變化 / Three depth lanes plus raised surfaces; hero scale follows depth.
- 動作密度：2 分鐘至少 12 個鏡頭、48 次動作變換、16 組動作表 / Density: 12+ shots, 48+ action beats, 16+ action sheets per 2 min.
- 先過 `plan_lint.py` 才生圖，最後用 `check_video.py` 驗收 / Lint the plan before generating; check the MP4 before delivering.

## 安全 / Security

API 金鑰只能放環境變數或專案外的檔案，不可寫進 JSON、程式碼、log 或 repo。提交前執行 `python3 scripts/scan_secrets.py .`。
Keep API keys in environment variables or files outside the project; never commit them. Run `scripts/scan_secrets.py` before every commit.

Workflow inspiration: [lemo-animi](https://github.com/lemomo-ai/lemo-animi).
