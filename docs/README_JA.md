# 🪟 GlassTranslate

<div align="center">

[简体中文](../README.md) • [English](README_EN.md) • **日本語** • [한국어](README_KO.md)

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4?logo=windows)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**透明な翻訳ガラス：外国語の上に置くと、原文の位置に訳文が表示されます。**

<a href="assets/GlassTranslate-Promo.mp4">
  <img src="assets/preview.gif" alt="GlassTranslate デモ" width="860" />
</a>

[▶️ デモ動画を見る（46 秒・中国語字幕）](assets/GlassTranslate-Promo.mp4)

</div>

GlassTranslate は Windows 向けのリアルタイム画面翻訳ツールです。枠のない透明なファインダーを外国語の上に動かすと、原文の上に訳文が重ねて表示され、ポップアップで画面が隠れることはありません。外国語のウェブページや資料、未翻訳のゲーム、字幕のない動画に便利です。

## 機能

- **その場で翻訳**：各行の位置を認識し、周囲の背景色を取って、原文の上に訳文を描画します。
- **自由に動かせる**：枠内を左ドラッグで移動、四辺でサイズ変更、ホイールでカーソルを中心に拡大縮小。離すとすぐ再認識します。
- **範囲選択翻訳**：`Alt + S` を押してスクリーンショットのように範囲をドラッグすると、ファインダーがそこに合わせて翻訳します。
- **言語の自動判別**：インストール済みの英語・日本語・中国語・韓国語 OCR から自動で選びます。英語混じりの日本語・韓国語にも対応します。
- **API キー不要**：既定では有道のウェブ回線を使います。DeepSeek、OpenAI、ローカルの Ollama も接続できます。
- **高速**：Windows 標準の OCR をローカルで使用。同じ文章に戻したときはキャッシュを使い、通信しません。

> 翻訳回線は中国語向けに調整されています。日本語への翻訳もできますが、主な対象は中国語です。

## ダウンロードと使い方

1. [Releases](https://github.com/newHashub/glass_translate/releases) を開き、最新の `GlassTranslate-vX.Y.Z-Windows-x64.zip` をダウンロードします（リリース下部の Assets にあります）。
2. 任意の場所に展開し、中の `GlassTranslate` フォルダを開いて `GlassTranslate.exe` をダブルクリックします。
3. ファインダーを外国語の上にドラッグします。`Alt + R` でいつでもマウス位置に表示／非表示できます。

展開したフォルダの中身：

```
GlassTranslate/
├── GlassTranslate.exe      ← ダブルクリックで起動
├── 创建桌面快捷方式.vbs     ← 「デスクトップにショートカットを作成」：ダブルクリックでアイコンを作成
├── 使用说明.txt             ← 使い方（中国語）
└── _internal/              ← 実行に必要なファイル。exe と同じ場所に置いてください
```

> リポジトリページのソースコード（Code → Download ZIP）は開発者向けで、そのままでは動きません。Releases の ZIP をダウンロードしてください。

Python は不要です。日本語や韓国語を認識するには対応する OCR 言語パックが必要です。[よくある質問](#よくある質問)をご覧ください。

## ショートカットと操作

| 操作 | 動作 |
| :--- | :--- |
| `Alt + R` | マウス位置にファインダーを表示／非表示 |
| `Alt + S` | 範囲選択翻訳：範囲をドラッグして翻訳。`Esc` または右クリックでキャンセル |
| 枠内を左ドラッグ | ファインダーを移動 |
| 四辺・四隅をドラッグ | サイズ変更 |
| 枠内でホイール | カーソルを中心に拡大縮小（メニューでオフにできます） |
| 枠内／トレイアイコンを右クリック | 設定メニューを開く |
| トレイアイコンをクリック | ファインダーを表示／非表示 |

どちらのショートカットも右クリックメニューの **⌨️ 唤出快捷键**（呼び出しショートカット） で変更でき、すぐに反映されます。

## 設定メニュー

枠内またはトレイアイコンを右クリックすると、次の設定ができます。

- **翻訳言語**：よく使う 12 種類のプリセット（自動／英／日／韓／仏／独／露／西 → 中国語、中国語 → 英／日／韓、自動 → 英語）、または「カスタム」で自由に組み合わせ。
- **翻訳エンジン**：有道ウェブ回線（既定）、MyMemory、カスタム LLM（OpenAI 互換 API）。
- **表示モード**：その場で置換（既定）またはフローティング字幕カード。
- **文字サイズ、認識間隔、最前面表示、ステータス表示、ホイール拡大縮小**。
- **最新の訳文をコピー**、**カスタム API 設定**。

> メニューは現在中国語表記です。

## よくある質問

<details>
<summary><b>「自動」にしても英語しか認識されないのはなぜですか？</b></summary>

Windows にはインストールした言語の OCR しか入っていません。日本語や韓国語が入っていないと、その文字は認識できません。

追加方法：**設定 → 時刻と言語 → 言語と地域 → 言語を追加** で日本語または韓国語を選び、「光学式文字認識」が含まれていることを確認します。表示言語を変える必要はありません。インストール後に GlassTranslate を再起動してください。
</details>

<details>
<summary><b>API キーは必要ですか？既定の回線は安定していますか？</b></summary>

キーは不要です。ただし既定の有道回線は有道のウェブ用エンドポイントを使っており、**公式の公開 API ではありません**。利用が多いと制限されることがあり、サイトの変更で使えなくなる可能性もあります。失敗したときは、有道の別のエンドポイント、次に MyMemory に自動で切り替えます。

長く安定して使いたい場合は、右クリックメニューの **🔑 自定义 API 配置...**（カスタム API 設定） で LLM を接続してください。例：

- DeepSeek：`https://api.deepseek.com/v1/chat/completions`
- ローカル Ollama（完全オフライン）：`http://localhost:11434/v1/chat/completions`
</details>

<details>
<summary><b>ファインダー自体がキャプチャに写り込みませんか？</b></summary>

写り込みません。ウィンドウに `WDA_EXCLUDEFROMCAPTURE` を設定しているため、自分自身のキャプチャには映らず、画面の入れ子やちらつきは起きません。
</details>

<details>
<summary><b>長い段落は途中で切れませんか？</b></summary>

長い文章は小さなブロックに分けて翻訳し、行ごとに照合します。合わない行があれば、その行だけ翻訳し直します。
</details>

<details>
<summary><b>Alt + R が効きません</b></summary>

他のソフトが同じショートカットを使っている可能性があります。トレイメニューの **⌨️ 唤出快捷键**（呼び出しショートカット） で別の組み合わせに変えてください。また、トレイに GlassTranslate が複数起動していないか確認してください。
</details>

## 開発

Windows 10/11 と Python 3.10 以上（3.12 推奨）が必要です。

```bash
git clone https://github.com/newHashub/glass_translate.git
cd glass_translate
pip install -r requirements-dev.txt
python main.py        # 実行
pytest                # テストを実行（オフライン）
```

**ビルド**：`build_exe.bat` をダブルクリックします。`.venv-build` にクリーンな仮想環境を作り、`dist\GlassTranslate\`、デスクトップのショートカット、`dist\GlassTranslate-v<バージョン>-Windows-x64.zip` を生成します。バージョンは `src/version.py` で変更します。

<details>
<summary><b>仕組みとディレクトリ構成</b></summary>

バックグラウンドのスレッドが次を繰り返します：ファインダーの下の画面をキャプチャ → 前のフレームから変化がなければスキップ → Windows OCR で各行の文字と位置を取得 → 行単位のキャッシュを確認し、なければ翻訳を要求 → 各行の位置に訳文を描画。

```
glass_translate/
├── main.py                  # エントリーポイント
├── src/                     # ソースコード
│   ├── main.py              # 起動処理：トレイ、グローバルショートカット、終了処理
│   ├── glass_window.py      # 透明ファインダー、訳文レイアウト、設定ダイアログ
│   ├── region_select.py     # Alt+S 範囲選択オーバーレイ（マルチモニター対応）
│   ├── worker.py            # バックグラウンドスレッド
│   ├── capture_engine.py    # 画面キャプチャと変化検出
│   ├── ocr_engine.py        # Windows OCR ラッパー、言語の自動判別
│   ├── translator_engine.py # 翻訳回線の切り替え、分割、キャッシュ
│   ├── global_hotkey.py     # グローバルショートカット（RegisterHotKey）
│   ├── tray_manager.py      # トレイアイコンと右クリックメニュー
│   ├── win32_utils.py       # キャプチャ除外、ウィンドウスタイル、高 DPI
│   ├── config.py            # 設定の読み書き
│   └── version.py           # バージョン番号
├── tests/                   # pytest テスト
├── packaging/               # ビルド用：PyInstaller 設定、ショートカット・配布 ZIP 作成スクリプト
├── resources/               # アイコン
├── docs/                    # 各言語の README、類似ツール比較、デモ素材
├── build_exe.bat            # ワンクリックビルド
├── requirements.txt         # 実行に必要な依存関係
└── requirements-dev.txt     # 開発・ビルド用の依存関係
```
</details>

## 類似ツール

Gaminik、WinLens、団子翻訳器、LunaTranslator などにもそれぞれ長所があります。GlassTranslate はオープンソース、軽量、キー不要、気軽に動かせることを目指しています。詳しくは [類似ツール比較](COMPARISON.md)（中国語）をご覧ください。

## ライセンス

[MIT](../LICENSE)。Issue や Pull Request を歓迎します。役に立ったら ⭐ をいただけるとうれしいです。
