＃League of Legendsデータ分析プロジェクト

transformer モデルと
CBOW、Skip-gramを活用してチャンピオン埋め込みを訓練し、結果を可視化したプロジェクト



使用したデータ: Riot API master レイヤー全データ
目的：チャンピオンの類似度を反映したベクトルを取得し、それに基づいて最も類似したチャンピオンを見つけるためのコード


data preparation example(MatchDatamaster.csv):
(You can prepare dataframe by preprocessing Riot API)

```
champion0,champion1,champion2,champion3,champion4,champion5,champion6,champion7,champion8,champion9,winner
Yone,Rell,Swain,Aphelios,Rakan,Leblanc,Viego,TwistedFate,Ezreal,Alistar,red
KSante,Belveth,Ryze,Cassiopeia,Swain,Darius,Graves,Akali,Zeri,Rakan,red
Yasuo,Gragas,Zed,Sivir,Soraka,KSante,Rell,Yone,Zeri,Yuumi,blue


...
```

Transformer-based embedding visualization command


Transformerモデルに基づいて勝敗を予測し、それに基づいて埋め込みマップを形成します。 （CBOWと比較して明確に埋め込みを形成しない）
-> 事前訓練された埋め込みを持っていれば、Transformerモデルの埋め込みレイヤーをスキップしてすぐにその埋め込みをinputにして勝敗予測モデルも性能向上を成し遂げることが期待される。

```
python transformer.py
```


CBOW-based embedding visualization command


このコードを実行すると、収集したcsvファイルに基づいて各チャンピオンのベクトルを抽出し、抽出したベクトルに基づいてt-SNEベースの可視化データを出力します。


```
python cbow.py
```

t-SNE Embedding example


<img width="80%" src="https://github.com/Leehongseok-code/RiotAI/assets/52267586/c2a9cf0b-ab2f-4f72-8a33-e5c60a35e5a7"/>



参考資料（Item2Vecベースチャンピオン埋め込み抽出アイデア）: https://queez0405.github.io/lol-project/
