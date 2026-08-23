# UnpackFlow：多重圧縮を無人で連続展開

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [हिन्दी](README.hi.md) · [العربية](README.ar.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [日本語](README.ja.md) · [Русский](README.ru.md)

UnpackFlow はソフトウェア配布物、データセット、バックアップ、メディア素材、ディスクイメージなどの大規模アーカイブを処理します。先頭ボリュームを判定し、入れ子の層を順に展開しながら段階、層、時間を表示します。

## 使用方法とインストール

`unpack-flow list 'Archive*'`、`plan`、`unpack-flow 'Archive*'`、`status`。Linux は Bash、Windows は PowerShell と 7-Zip、macOS は PowerShell 7+ と `7zz` が必要です。`scripts/build-release.sh` が3 OS用パッケージと SHA-256 を作ります。

`unpack-flow` の実行やアーカイブ展開に Python は不要です。Python 3 が必要なのは、Linux/macOS で `install_local.py` または `install_local.sh` を使って Skill を自動インストールする場合と、Python 監査を実行する場合だけです。Windows の `install_local.ps1` は PowerShell のみを使い、手動コピーにも Python は不要です。

## 対応する展開処理

UnpackFlow はディレクトリやワイルドカード指定を一括処理し、入れ子のアーカイブを層ごとに展開し、分割 RAR の先頭ボリュームを判定します。不明な EXE を実行せずに RAR 自己展開形式も調べます。ソフトウェア配布物、データセット、バックアップ、メディア、ログ、ISO・WIM イメージに利用できます。

既定では内部を最大10層まで処理します。破損または欠落のある内部アーカイブは保持して記録し、残りの処理を続行します。最初のエラーで停止するには `-StopOnError` を使用します。

## 学習用の例

バックアップ、データセット、ログ、ソフトウェア、分割アーカイブには `list`、`plan`、`start`、`status`、`log`、`wait` を使います。ゲームは一例であり、製品範囲を限定しません。

3つのOSすべてで、`run` は進捗を表示しながらフォアグラウンドで実行し、`start` はバックグラウンドジョブを開始してIDを返します。

7-Zip または UnRAR の長時間処理中は、経過時間を毎秒更新し、30秒ごとに実行中のハートビートをログへ記録します。

macOS/Windows の `start` は対話端末から完全に切り離され、進捗はログだけに記録されるため、ANSI 制御文字や端末のビープ音は発生しません。

`-r` または `-Recursive` を使うと、サブフォルダー内の全アーカイブと内側の階層を再帰展開します。出力名が既にある場合は元フォルダー名を加え、例として `sample-backup-legacy-set-unpacked` にし、さらに競合すれば `-2`、`-3` を付けて上書きやスキップを防ぎます。

小型の `unpack-flow-minimal-testcases-v1.zip` は ZIP、TAR.GZ、Unicode、入れ子、分割 `part01.exe`、欠落ボリュームの想定失敗を網羅し、大型アプリを含まず SFX を実行しません。

ネイティブ受け入れ試験では `/data/unpack-flow-testcases` の合成データを使用し、`UNPACK_FLOW_TEST_ROOT` で別のパスを指定できます。大型スイートは任意で、性能または追加形式互換性の試験だけに使います。

`unpack-flow run *` も利用できます。シェルが `*` を展開した後でも、スキャンは単独アーカイブと `part1.exe`、`part1.rar`、`.7z.001`、`.zip.001` などの先頭ボリュームだけを残し、`.sha256`、無関係なファイル、後続ボリュームを除外します。

`unpack-flow help` は英語と簡体字中国語を併記したコマンドヘルプを表示します。

## バックグラウンド処理とログ

`unpack-flow start "アーカイブ" -Output "出力先"` はバックグラウンド展開を開始してジョブIDを返します。`unpack-flow status [ID]`、`unpack-flow log [ID]`、`unpack-flow wait [ID]` で確認でき、ID省略時は最新ジョブが対象です。ログは Windows の `%LOCALAPPDATA%\unpack-flow\state`、macOS/Linux の `~/.local/state/unpack-flow` に保存されます。

TAR、TAR.GZ/TGZ、単独 GZ に対応します。7-Zip の後は形式に応じて UnRAR、システム `tar`、GZip、ネイティブ ZIP を順に試し、失敗時の一時出力を削除します。すべて失敗しても元アーカイブとログを残して次へ進み、無限再試行はしません。

Linux x64 版には公式 UnRAR 7.23、Windows x64/ARM64 版には公式の完全版 7-Zip 26.02 が含まれ、x64 版には UnRAR も含まれます。元の公式パッケージとライセンスも保持します。

## 完全なクイックスタート

```bash
unpack-flow list '/data/archives/*'
unpack-flow plan '/data/archives/backup.part1.rar'
unpack-flow run '/data/archives/*' -Output '/data/extracted'
```

バックグラウンドで実行する場合：

```bash
unpack-flow start '/data/archives/*' -Output '/data/extracted'
unpack-flow status
unpack-flow log
unpack-flow wait
```

`run` は現在の端末で完了まで動作し、`start` は直ちにジョブ ID を返します。どちらも元アーカイブを保持します。

## コマンドラインツールのインストール

### Linux

```bash
./install-linux.sh --check
./install-linux.sh
unpack-flow version
```

### macOS

```bash
./install-macos.sh --check
./install-macos.sh
unpack-flow version
```

### Windows

```bat
install.bat -Check
install.bat
unpack-flow version
```

確認コマンドは不足している依存関係を表示しますが、システムソフトウェアを自動インストールしません。

## 再帰処理、ログ、失敗時の動作

サブフォルダーと内部アーカイブを処理するには `-r` または `-Recursive` を使用します。既定では内部 10 層までです。

| プラットフォーム | 既定の状態ディレクトリ |
|---|---|
| Windows | `%LOCALAPPDATA%\unpack-flow\state` |
| Linux/macOS | `${XDG_STATE_HOME:-$HOME/.local/state}/unpack-flow` |

UnpackFlow は 7-Zip、RAR 用 UnRAR、TAR・GZ・ZIP 用のネイティブツールという有限の順序で試行します。不完全な出力は試行ごとに削除します。すべて失敗した場合も元アーカイブを保持し、エラーを記録して次へ進みます。最初のエラーで停止する場合だけ `-StopOnError` を使います。

## テストと Agent Skill のインストール

```bash
bash tests/generate-minimal-public-suite.sh
bash tests/test-minimal-public-suite.sh
pwsh -NoProfile -File tests/test-minimal-public-suite.ps1
scripts/install_local.sh .
```

Windows では `scripts/install_local.ps1` で Skill をインストールします。展開処理に Python は不要で、Linux/macOS の自動 Skill インストーラーと Python 監査にだけ使用します。

## 安全性とサポート

元ファイルを保持し、出力を上書きせず、不明な EXE を実行しません。サポート：[once-email.com](https://once-email.com)。MIT、バージョン 2.1.2。

発行元・メンテナー・公式サイト：[once-email.com](https://once-email.com)。作成者・開発者：helen.jar。GitHub プロジェクト：[pangxin12345/unpack-flow](https://github.com/pangxin12345/unpack-flow)。ご質問は [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com) へメールしてください。
