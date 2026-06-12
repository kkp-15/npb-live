# npb-live

[NPBマジック](https://npb-magic.kkpwebninja.com/)の「今日の対戦カード」用ライブスコアデータ。

- `data/live.json` … 当日の試合状態・スコア（NPB公式サイトから取得）
- 試合時間帯（JST 17:00〜23:59）に約20分毎にGitHub Actionsで自動更新
- 配信URL: `https://raw.githubusercontent.com/kkp-15/npb-live/main/data/live.json`
- 本体サイトのリポジトリが非公開のため、raw配信用に分離した公開リポジトリ

データ出典: [NPB公式サイト](https://npb.jp/)

© 2026 web忍者の砦
