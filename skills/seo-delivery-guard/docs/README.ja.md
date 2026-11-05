# SEO Delivery Guard

**Google Search の公式な境界に沿って、AI コーディングエージェントの SEO 開発とリリースを統制する Skill。**

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827?logo=openai&logoColor=white)](../SKILL.md)
[![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-2563eb)](../CHANGELOG.md)
[![MIT License](https://img.shields.io/badge/license-MIT-16a34a)](../LICENSE)
[![Documentation languages: 10](https://img.shields.io/badge/docs-10%20languages-7c3aed)](../README.md#documentation)
[![GitHub source](https://img.shields.io/badge/GitHub-pangxin12345%2Fseo--delivery--guard-181717?logo=github&logoColor=white)](https://github.com/pangxin12345/seo-delivery-guard)
[![Official website](https://img.shields.io/badge/website-once--email.com-0f766e?logo=googlechrome&logoColor=white)](https://once-email.com)
[![skills.sh](https://skills.sh/b/pangxin12345/seo-delivery-guard)](https://skills.sh/pangxin12345/seo-delivery-guard)

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português do Brasil](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Tiếng Việt](README.vi.md)

SEO 監査は問題を見つけます。**SEO Delivery Guard は、採用した指摘を AI コーディングエージェントが実装、レビュー、公開、本番検証まで進めるためのガバナンスを提供します。**

クローラー、性能測定、コンテンツ分析、構造化データ検証、SERP 調査、Search Console データを置き換えるものではありません。利用可能な能力を編成し、プロジェクト固有のルールを適用し、公開を止める問題と任意の改善提案を分離します。

## なぜ必要なのか

- ソースでは正しい canonical が生成物では誤ることがある。
- 専門的な校閲前の翻訳が Sitemap に入ることがある。
- 構造化データが画面に見えない事実を記述することがある。
- robots 指示がアクセス制御と誤解されることがある。
- 総合スコアがインデックスやプライバシーの重大問題を隠すことがある。
- 候補版は合格しても、本番が異なるメタデータを返すことがある。
- 検索エンジンの再クロール前に成功と判断してしまうことがある。

## 主な機能

- 変更内容に応じて必要最小限の SEO 分析を選択。
- 開発、プライバシー、ローカライズ、分析、広告、テスト、公開に関するプロジェクト規則を確認。
- 明確な優先順位で矛盾する提案を裁定。
- 証拠の出典、日時、確度、重大度、対応、検証層、ロールバックへの影響を記録。
- 重大なブロッカーを平均スコアで弱めない。
- 変更前後の検索向け契約を比較。
- ソース、生成物、ブラウザー、公開 HTTP、ラボ、ファーストパーティデータ、第三者推定を区別。
- インデックス、順位、トラフィック、リッチリザルト、広告審査、AI 表示は確認まで保留として扱う。
- コンテンツや URL を維持、改善、統合、`noindex`、削除のいずれにするか明示し、301 は真に同等の移転先がある場合だけ使用し、それ以外は正しい `404/410` を維持する。

## 行わないこと

- 別のサイトクローラーや万能 SEO 監査ではありません。
- 特定ベンダー、API、MCP、補助 Skill を必須にしません。
- タスクの権限なしに URL 送信、プロパティ変更、コード公開、デプロイを行いません。
- インデックス、順位、トラフィック、リッチリザルト、広告承認、AI 引用を保証しません。

## 入力、出力、拒否境界

必要な公開 URL、リポジトリーパス、変更意図、対象者、インデックス意図、言語、機密情報を除いた証拠だけを提供してください。パスワード、Cookie、秘密鍵、完全な分析エクスポート、機密データは渡さないでください。出力は規則、ブロッカー、助言、不明点、証拠の制限、対応、検証層、本番状態、保留中の外部結果を分離します。

ランキング操作、架空の経験や証拠、ドアウェイページ、価値のない大量コンテンツ、アクセス制御の回避、機密情報の露出、虚偽の認定は拒否します。ページや分析器を利用できない場合は不明のままで、合格とは扱いません。

各インデックス対象ページは、既存の最良 URL では満たせない仕事を解決する必要があります。機械翻訳や構造検査だけでは言語品質を証明できず、各公開言語版には事実と表現のレビューが必要です。

## インストール

対応する Skill マーケットから導入するか、完全な `seo-delivery-guard` フォルダーを AI エージェントが認識する Skill ディレクトリへコピーします。Skill を再読み込みするか新しいセッションを開始し、次を呼び出します。

```text
$seo-delivery-guard
```

公開パッケージはテキスト指示とメタデータのみで、実行ファイル、クローラー、API キー、OS 固有コンポーネントを含みません。

## Google Search に関する境界

Google Search に関する結論は、最新の公式文書または検証済みのファーストパーティデータに基づきます。第三者ツールは手掛かりを提供できますが、Google のインデックス判断、ランキング要因、リッチリザルト、AI 機能を定義するものではありません。

SEO Delivery Guard は独立したオープンソースプロジェクトであり、Google との提携、認定、後援、推奨関係はありません。

## 公開者

- 公開者・公式サイト：[once-email.com](https://once-email.com)
- 作成者：helen.jar
- GitHub：[pangxin12345](https://github.com/pangxin12345)
- 公開サポート：[tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

MIT License · バージョン 0.1.0

変更履歴は [CHANGELOG.md](../CHANGELOG.md) を参照してください。
