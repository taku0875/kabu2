import streamlit as st
import pandas as pd
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
from supabase import create_client
from supabase.client import Client

# ========================
# ✅ 環境変数の読み込み
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ========================
# ✅ SupabaseとOpenAI接続
# ========================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

# ========================
# ✅ Streamlit基本設定
# ========================
st.set_page_config(page_title="株式トレード管理＋GPT壁打ち", layout="centered")
st.title("📈 株式トレード記録アプリ + 🤖 GPTアシスタント")

# ========================
# 📝 トレード入力フォーム
# ========================
st.subheader("📝 新規トレード入力")
with st.form("trade_form"):
    date = st.date_input("日付", datetime.today())
    col1, col2 = st.columns(2)
    with col1:
        stock_code = st.text_input("銘柄コード")
    with col2:
        stock_name = st.text_input("銘柄名")
    entry_price = st.number_input("エントリー価格", step=0.01)
    exit_price = st.number_input("エグジット価格", step=0.01)
    volume = st.number_input("株数", step=1, min_value=1)
    entry_reason = st.text_area("エントリー理由", height=100)
    exit_reason = st.text_area("エグジット理由", height=100)
    note = st.text_input("備考")

    submitted = st.form_submit_button("✅ 登録する", use_container_width=True)
    if submitted:
        try:
            profit = (exit_price - entry_price) * volume
            day_of_week = date.strftime("%A")
            data = {
                "date": str(date),
                "day_of_week": day_of_week,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "volume": volume,
                "profit": profit,
                "entry_reason": entry_reason,
                "exit_reason": exit_reason,
                "note": note,
            }
            supabase.table("trades").insert(data).execute()
            st.success("✅ トレード記録を登録しました！")
        except Exception as e:
            st.error(f"❌ データ登録に失敗しました: {e}")

# ========================
# 📊 トレード履歴の表示
# ========================
with st.expander("📊 トレード履歴を表示"):
    try:
        response = supabase.table("trades").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["profit"] = df["profit"].astype(float)
            st.dataframe(df)

            # 曜日別損益のグラフ
            st.markdown("### 📈 曜日別損益")
            summary = df.groupby("day_of_week")["profit"].sum().reindex(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            ).fillna(0)
            st.bar_chart(summary)
        else:
            st.info("現在のトレード記録はありません。")
    except Exception as e:
        st.error(f"❌ データ取得に失敗しました: {e}")

# ========================
# 🤖 GPTアシスタント機能
# ========================
st.subheader("🤖 GPTに相談")
user_input = st.text_area("今のトレードについて相談してみましょう", height=150)
if st.button("💬 GPTに聞く", use_container_width=True) and user_input:
    with st.spinner("GPTが考えています..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "あなたはトレード戦略の優秀なコーチです。戦略・感情・分析をサポートしてください。"},
                    {"role": "user", "content": user_input},
                ]
            )
            answer = response['choices'][0]['message']['content']
            st.markdown(f"**🧠 GPTの回答：**\n\n{answer}")
        except Exception as e:
            st.error(f"❌ GPTからの応答に失敗しました: {e}")
