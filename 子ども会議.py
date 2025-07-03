import streamlit as st
import pandas as pd

# --- 質問定義 ---
QUESTIONS = {
    1: {"text": "何か仕事をするときは，自信を持ってやるほうである。", "factor": "行動の積極性", "reverse": False},
    2: {"text": "過去に犯した失敗や嫌な経験を思いだして，暗い気持ちになることがよくある。", "factor": "失敗に対する不安", "reverse": True},
    3: {"text": "友人より優れた能力がある。", "factor": "能力の社会的位置づけ", "reverse": False},
    4: {"text": "仕事を終えた後，失敗したと感じることのほうが多い。", "factor": "失敗に対する不安", "reverse": True},
    5: {"text": "人と比べて心配性なほうである。", "factor": "行動の積極性", "reverse": True},
    6: {"text": "何かを決めるとき，迷わずに決定するほうである。", "factor": "行動の積極性", "reverse": False},
    7: {"text": "何かをするとき，うまくゆかないのではないかと不安になることが多い。", "factor": "失敗に対する不安", "reverse": True},
    8: {"text": "ひっこみじあんなほうだと思う。", "factor": "行動の積極性", "reverse": True},
    9: {"text": "人より記憶力がよいほうである。", "factor": "能力の社会的位置づけ", "reverse": False},
    10: {"text": "結果の見通しがつかない仕事でも，積極的に取り組んでゆくほうだと思う。", "factor": "行動の積極性", "reverse": False},
    11: {"text": "どうやったらよいか決心がつかずに仕事にとりかかれないことがよくある。", "factor": "失敗に対する不安", "reverse": True},
    12: {"text": "友人よりも特に優れた知識を持っている分野がある。", "factor": "能力の社会的位置づけ", "reverse": False},
    13: {"text": "どんなことでも積極的にこなすほうである。", "factor": "行動の積極性", "reverse": False},
    14: {"text": "小さな失敗でも人よりずっと気にするほうである。", "factor": "失敗に対する不安", "reverse": True},
    15: {"text": "積極的に活動するのは，苦手なほうである。", "factor": "行動の積極性", "reverse": True},
    16: {"text": "世の中に貢献できる力があると思う。", "factor": "能力の社会的位置づけ", "reverse": False},
}

FACTOR_MAPPING = {
    "行動の積極性": [1, 5, 6, 8, 10, 13, 15],
    "失敗に対する不安": [2, 4, 7, 11, 14],
    "能力の社会的位置づけ": [3, 9, 12, 16],
}

def score_answer(ans, reverse):
    return 0 if (reverse and ans == "はい") or (not reverse and ans != "はい") else 1

def process_dataframe(df):
    scores = {}
    for person in df.columns:
        row = {}
        for q_num in df.index:
            if q_num in QUESTIONS:
                ans = df.loc[q_num, person]
                row[q_num] = score_answer(ans, QUESTIONS[q_num]["reverse"]) if pd.notna(ans) else 0
        scores[person] = row
    df_score = pd.DataFrame(scores).T
    df_factors = {
        factor: df_score[[q for q in q_nums if q in df_score.columns]].sum(axis=1)
        for factor, q_nums in FACTOR_MAPPING.items()
    }
    return df_score, pd.DataFrame(df_factors)

def read_uploaded_file(file):
    if file is None:
        return None
    try:
        if file.name.endswith("csv"):
            try:
                return pd.read_csv(file, index_col=0, encoding="utf-8")
            except:
                file.seek(0)
                return pd.read_csv(file, index_col=0, encoding="shift_jis")
        elif file.name.endswith("xlsx"):
            return pd.read_excel(file, index_col=0)
    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        return None

# --- Streamlit アプリ ---
st.title("アンケート分析ツール")

file1 = st.file_uploader("初回アンケート", type=["csv", "xlsx"])
file2 = st.file_uploader("最終回アンケート", type=["csv", "xlsx"])

df1 = read_uploaded_file(file1)
df2 = read_uploaded_file(file2)

if df1 is not None and df2 is not None:
    try:
        df1.index = df1.index.astype(int)
        df2.index = df2.index.astype(int)
    except:
        st.error("インデックスは整数である必要があります")
        st.stop()

    s1, f1 = process_dataframe(df1)
    s2, f2 = process_dataframe(df2)

    common = sorted(set(s1.index) & set(s2.index))
    if not common:
        st.warning("共通する回答者が見つかりません")
        st.stop()

    person = st.selectbox("分析対象者を選択", common)

    # --- 修正済み：個人の因子スコア（1つの表にまとめて表示） ---
    st.subheader("個人別の因子スコア比較（初回・最終回・差分）")
    factor_df = pd.DataFrame({
        "初回": f1.loc[person],
        "最終回": f2.loc[person],
    })
    factor_df["差分"] = factor_df["最終回"] - factor_df["初回"]
    st.dataframe(factor_df, use_container_width=True)

    # --- 個人の設問スコア（質問文付き） ---
    st.subheader("個人別の設問スコア比較（質問文付き）")
    row_data = []
    for q in sorted(QUESTIONS):
        text = QUESTIONS[q]["text"]
        init = s1.loc[person].get(q, 0)
        final = s2.loc[person].get(q, 0)
        diff = final - init
        row_data.append({
            "項目No.": q,
            "質問文": text,
            "初回": init,
            "最終回": final,
            "差分": diff
        })
    st.dataframe(pd.DataFrame(row_data), use_container_width=True)

    # --- 全体分析 ---
    st.subheader("因子ごとの全体傾向")
    st.dataframe(pd.DataFrame({
        "初回平均": f1.mean(),
        "最終回平均": f2.mean(),
        "変化": f2.mean() - f1.mean()
    }), use_container_width=True)

    st.subheader("回答者全体の合計スコア傾向")
    total_df = pd.DataFrame({
        "初回合計": f1.sum(axis=1),
        "最終回合計": f2.sum(axis=1)
    })
    total_df["変化"] = total_df["最終回合計"] - total_df["初回合計"]
    st.dataframe(total_df.sort_values("変化", ascending=False), use_container_width=True)

    st.subheader("設問ごとの全体平均スコア（質問文付き）")
    item_summary = []
    for q in sorted(QUESTIONS):
        item_summary.append({
            "項目No.": q,
            "質問文": QUESTIONS[q]["text"],
            "初回平均": s1[q].mean() if q in s1.columns else 0,
            "最終回平均": s2[q].mean() if q in s2.columns else 0
        })
    df_items = pd.DataFrame(item_summary)
    df_items["変化"] = df_items["最終回平均"] - df_items["初回平均"]
    st.dataframe(df_items, use_container_width=True)

else:
    st.info("両方のアンケートファイルをアップロードしてください。")