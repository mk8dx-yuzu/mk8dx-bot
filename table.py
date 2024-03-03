import pandas as pd
import dataframe_image as dfi
import matplotlib
from matplotlib import colors

df = pd.DataFrame(
    {
        "Name": ["Jordan", "Tario", "Mitsiku", "Leoo", "MintCheetah", "probablyjassin", "Ren", "Kevnkkm", "Juuls_poms", "dankmeme8s", "clarity", "drake"],
        "MMR": [5448, 3763, 2638, 2355, 2320, 2189, 2802, 2647, 1658, 1495, 2000, 1971],
        "Change": [0 for i in range(1, 13)],
        "New MMR": [5524, 3870, 2779, 2471, 2395, 2237, 2750, 2571, 1638, 1446, 1849, 1749],
    }
)
for i in range(len(df['Name'])):
    df.loc[i, "Change"] = df.loc[i, "New MMR"] - df.loc[i, "MMR"]

df.index = range(1, len(df) + 1)
dfi.export(df.style.background_gradient(cmap=colors.LinearSegmentedColormap.from_list("", ["red", "white", "green"]), low=0, high=0.2, subset=["Change"]), "table.png")
