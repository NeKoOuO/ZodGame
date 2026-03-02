# ZodGame 每日自動簽到

自動完成 [ZodGame](https://zodgame.xyz) 論壇的每日簽到，透過 GitHub Actions 排程執行。

## 功能

- 每天台灣時間 **08:00** 自動簽到
- 支援手動觸發
- 自動重試機制（失敗最多重試 3 次）
- 已簽到、未登入等狀態自動識別

## 設定方式

### 1. Fork 此 Repo

### 2. 取得 Cookie

1. 登入 [zodgame.xyz](https://zodgame.xyz)
2. 前往簽到頁面：`https://zodgame.xyz/plugin.php?id=dsu_paulsign:sign`
3. 開啟瀏覽器開發人員工具（F12）→ Network
4. 重新整理頁面，點第一個請求
5. 找到 Request Headers 中的 `Cookie` 欄位，複製整串內容

> ⚠️ 確認 Cookie 中包含 `qhMq_2132_saltkey` 和 `qhMq_2132_auth`，缺少這兩個會導致 403 錯誤。

### 3. 設定 GitHub Secret

1. 進入你的 Repo → Settings → Secrets and variables → Actions
2. 新增 Secret：
   - **Name**：`ZODGAME_COOKIE`
   - **Value**：貼上剛才複製的 Cookie 字串

### 4. 啟用 Actions

確認 Repo 的 Actions 功能已開啟（Settings → Actions → Allow all actions）。

## 手動觸發

前往 Actions → ZodGame 每日簽到 → Run workflow

## 注意事項

- Cookie 有時效性，若出現 **403 錯誤**，請重新取得 Cookie 並更新 Secret
- 若使用 Cloudflare 保護的連線，`cf_clearance` cookie 可能數小時至數天內失效
- GitHub 若超過 60 天未有 commit，排程 Actions 會自動停用，需手動重新啟用

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `sign.py` | 主要簽到腳本 |
| `.github/workflows/zodgame-daily-sign.yml` | GitHub Actions 排程設定 |
