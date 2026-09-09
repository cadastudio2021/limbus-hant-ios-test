# limbus-hant-ios-test

測試用資源託管：驗證 Limbus Company iOS 客戶端的**韓文語言槽字型**能否正常顯示繁體中文。

## 這是什麼

iOS 版 Limbus Company 的日文語言槽使用日文字型，字庫缺少大量繁體中文常用字
（實測「你」「會」「說」「嗎」等字缺失，約佔繁中文本 12.6% 的漢字出現次數）。

本 repo 將繁體中文語言包塞入**韓文**語言槽，用來判斷韓文槽的字型覆蓋率是否較佳。
純屬個人測試用途，不是可用的漢化發布。

## Release 資產

| 檔案 | 用途 |
|---|---|
| `localize_kr.zip` | 韓文槽全量替換包（2083 檔） |
| `manifest.json` | 對應的 LocalizePatchInfo，僅更動 KR 條目雜湊 |

## 來源與致謝

- 繁體中文文本：[LimbusTraditionalMandarin/storyline](https://github.com/LimbusTraditionalMandarin/storyline)
- iOS 代理改寫方案與 manifest 基礎：[ghcruise/LimbusCompany-IOS-Localization](https://github.com/ghcruise/LimbusCompany-IOS-Localization)
- 上游漢化資源：[LocalizeLimbusCompany](https://github.com/LocalizeLimbusCompany/LocalizeLimbusCompany)（都市零協會）

沿用上游授權 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。
非商業用途。與 Project Moon 無任何隸屬關係。
