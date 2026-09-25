# 五竜ダウンヒル

白馬五竜（エイブル白馬五竜）の実際の地形を滑るスマホ向けスキーゲーム。
画面の右側をホールド＝右足（外足）に荷重して左ターン、左側をホールド＝右ターン。上スワイプでストックを突いて加速。

- プレイ（PWA）: https://nisino25.github.io/goryu-ski/ — スマホで開いて「ホーム画面に追加」
- 技術: Vue 3（CDN）+ Tailwind CSS（Play CDN）+ three.js r128

## 構成

| パス | 内容 |
|---|---|
| `goryu-ski.html` | ゲーム本体（Claude アーティファクト版と同じソース） |
| `assets/` | コース・地形データ、3Dモデル（base64 JSON）、雪テクスチャ |
| `docs/` | PWA 版（GitHub Pages の公開元）。`python3 build_pwa.py` で生成 |
| `tools/` | 地形・コースデータの生成スクリプト |

## 更新手順

```bash
python3 build_pwa.py
git add -A && git commit -m "Update" && git push
```

## データの作り直し（tools/）

`tools/build_data.py` は国土地理院の標高タイル（`dem5a` z15 と `dem` z13 のテキストタイル）を `tools/` に置いた状態で動く。
タイルは https://cyberjapandata.gsi.go.jp/xyz/dem5a/15/{x}/{y}.txt などから取得する。`osm.json` は Overpass API で取得したコース線とリフト。

## 出典・ライセンス

- 標高：国土地理院（基盤地図情報 数値標高モデル）
- とおみゲレンデの幅・森の配置：国土地理院 シームレス空中写真（地理院タイル）から判定
- コース線・リフト・建物：© OpenStreetMap contributors（ODbL）
- コース名・公式の距離と斜度：エイブル白馬五竜 コースガイド
- スキーヤー：自作の関節付きモデル（プログラムで生成）
- リフト「Chairlift」「Ski lift pole」by Poly by Google — CC-BY 3.0（Poly Pizza）
- 雪テクスチャ「snow_02」— Poly Haven（CC0）
