import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


st.set_page_config(page_title="Japan Heatmap", layout="wide")

APP_DIR = Path(__file__).resolve().parent
SHP_PATH = APP_DIR / "N03-20240101_GML/N03-20240101.shp"


@st.cache_data
def load_excel(excel_file):
    return pd.read_excel(excel_file)


@st.cache_data
def load_shapefile(shp_path):
    # 文字化け対策の本体
    # 1) engine を fiona に固定
    # 2) encoding を明示
    return gpd.read_file(shp_path, engine="fiona", encoding="cp932")


def draw_heatmap(gdf, value_col, cmap_name):
    fig = plt.figure(figsize=(12, 8))

    ax_map = fig.add_axes([0.1, 0.1, 0.6, 0.8])
    gdf.plot(column=value_col, cmap=cmap_name, legend=False, ax=ax_map)
    ax_map.axis("off")

    ax_legend = fig.add_axes([0.75, 0.2, 0.03, 0.6])
    sm = plt.cm.ScalarMappable(
        cmap=cmap_name,
        norm=plt.Normalize(vmin=gdf[value_col].min(), vmax=gdf[value_col].max())
    )
    sm._A = []
    fig.colorbar(sm, cax=ax_legend)

    return fig


def main():
    st.title("日本地図 Heatmap")

    if not SHP_PATH.exists():
        st.error(f"shapefile が見つかりません: {SHP_PATH.name}")
        return

    uploaded_excel = st.file_uploader(
        "都道府県データの Excel ファイルを選択してください",
        type=["xlsx", "xls"]
    )

    if uploaded_excel is None:
        st.info("Excel ファイルを指定してください。")
        return

    try:
        df = load_excel(uploaded_excel)
    except Exception as e:
        st.error(f"Excel 読み込みエラー: {e}")
        return

    try:
        gdf = load_shapefile(SHP_PATH)
    except Exception as e:
        st.error(f"shapefile 読み込みエラー: {e}")
        return

    st.subheader("読み込み確認")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Excel**")
        st.write(list(df.columns))
        st.dataframe(df.head())

    with col2:
        st.write("**Shapefile**")
        st.write(list(gdf.columns))
        st.dataframe(gdf.drop(columns="geometry", errors="ignore").head())

    # 元 notebook ベース
    default_excel_key = "prefecture" if "prefecture" in df.columns else df.columns[0]
    default_value_col = "value" if "value" in df.columns else df.select_dtypes(include="number").columns[0]
    default_shp_key = "N03_001" if "N03_001" in gdf.columns else gdf.columns[0]

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        shp_key_col = st.selectbox(
            "Shapefile 側の列",
            options=list(gdf.columns),
            index=list(gdf.columns).index(default_shp_key)
        )

    with col_b:
        excel_key_col = st.selectbox(
            "Excel 側の列",
            options=list(df.columns),
            index=list(df.columns).index(default_excel_key)
        )

    with col_c:
        value_col = st.selectbox(
            "値の列",
            options=list(df.columns),
            index=list(df.columns).index(default_value_col)
        )

    cmap = st.selectbox(
        "Color map",
        ["Reds", "Blues", "Greens", "Purples", "OrRd", "viridis", "plasma"],
        index=0
    )

    gdf = gdf.copy()
    df = df.copy()

    gdf[shp_key_col] = gdf[shp_key_col].astype(str).str.strip()
    df[excel_key_col] = df[excel_key_col].astype(str).str.strip()

    try:
        merged = gdf.merge(df, left_on=shp_key_col, right_on=excel_key_col)
    except Exception as e:
        st.error(f"merge エラー: {e}")
        return

    if merged.empty:
        st.error("merge 結果が空です。Shapefile 側の文字化け、または列の不一致が残っています。")
        return

    st.subheader("merge結果")
    st.dataframe(merged.drop(columns="geometry", errors="ignore").head())

    try:
        fig = draw_heatmap(merged, value_col, cmap)
        st.subheader("Heatmap")
        st.pyplot(fig)
    except Exception as e:
        st.error(f"描画エラー: {e}")


if __name__ == "__main__":
    main()