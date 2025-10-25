# app.py
from dotenv import load_dotenv
load_dotenv()  # .env の OPENAI_API_KEY を読み込む

import os
import streamlit as st

# --- LangChain 新API ---
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="【提出課題】LLM機能を搭載したWebアプリ")
st.title("【提出課題】LLM機能を搭載した Webアプリ")
st.caption(f"OPENAI_API_KEYの有無: {bool(os.getenv('OPENAI_API_KEY'))}")

# ===================== 47都道府県ユーティリティ =====================
PREFECTURES = [
    "北海道","青森","岩手","宮城","秋田","山形","福島",
    "茨城","栃木","群馬","埼玉","千葉","東京","神奈川",
    "新潟","富山","石川","福井","山梨","長野",
    "岐阜","静岡","愛知","三重",
    "滋賀","京都","大阪","兵庫","奈良","和歌山",
    "鳥取","島根","岡山","広島","山口",
    "徳島","香川","愛媛","高知",
    "福岡","佐賀","長崎","熊本","大分","宮崎","鹿児島","沖縄",
]

# 短縮形 → 正式名
_NORMALIZED_MAP = {}
for p in PREFECTURES:
    key = p
    for suf in ("県", "府", "都", "道"):
        if p.endswith(suf):
            key = p[:-len(suf)]
            break
    _NORMALIZED_MAP[key] = p

ENGLISH_MAP = {
    "hokkaido":"北海道","aomori":"青森","iwate":"岩手","miyagi":"宮城","akita":"秋田",
    "yamagata":"山形","fukushima":"福島","ibaraki":"茨城","tochigi":"栃木","gunma":"群馬",
    "saitama":"埼玉","chiba":"千葉","tokyo":"東京","kanagawa":"神奈川","niigata":"新潟",
    "toyama":"富山","ishikawa":"石川","fukui":"福井","yamanashi":"山梨","nagano":"長野",
    "gifu":"岐阜","shizuoka":"静岡","aichi":"愛知","mie":"三重","shiga":"滋賀",
    "kyoto":"京都","osaka":"大阪","hyogo":"兵庫","nara":"奈良","wakayama":"和歌山",
    "tottori":"鳥取","shimane":"島根","okayama":"岡山","hiroshima":"広島","yamaguchi":"山口",
    "tokushima":"徳島","kagawa":"香川","ehime":"愛媛","kochi":"高知",
    "fukuoka":"福岡","saga":"佐賀","nagasaki":"長崎","kumamoto":"熊本","oita":"大分",
    "miyazaki":"宮崎","kagoshima":"鹿児島","okinawa":"沖縄",
}

def _normalize_english(name: str) -> str:
    if not name:
        return ""
    s = name.strip().lower()
    for token in (" prefecture"," prefectures","-prefecture","-ken"," ken","-fu"," fu","-to"," to","-do"," do"):
        if s.endswith(token):
            s = s[: -len(token)]
            break
    return s.replace(".", "").replace(" ", "").replace("_", "").replace("-", "")

def _normalize_pref_name(name: str) -> str:
    if not name:
        return ""
    s = name.strip()
    if s in PREFECTURES:
        return s
    for suf in ("県", "府", "都", "道"):
        if s.endswith(suf):
            candidate = s[:-len(suf)]
            return _NORMALIZED_MAP.get(candidate, candidate)
    eng = _normalize_english(s)
    if eng in ENGLISH_MAP:
        return ENGLISH_MAP[eng]
    if s in _NORMALIZED_MAP:
        return _NORMALIZED_MAP[s]
    return s

def is_valid_prefecture(name: str) -> bool:
    return _normalize_pref_name(name) in PREFECTURES

# ===================== LLM 応答 =====================
def generate_answer(input_text: str, persona_key: str) -> str:
    personas = {
        "伝統文化の専門家": "あなたは伝統文化の専門家です。日本の各都道府県の伝統文化について詳しく説明してください。",
        "ローカルフードの専門家": "あなたはローカルフードの専門家です。日本の各都道府県の特産品や名物料理について詳しく説明してください。",
    }
    system_msg = personas.get(persona_key, personas["伝統文化の専門家"])

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", "{user_input}"),
    ])
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # Prompt → LLM → 文字列 のチェーンを構築
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"user_input": input_text})

# ===================== UI =====================
st.write("このアプリは、以下の2つの相談ができます。")
st.write("1. 47都道府県の **伝統文化** の専門家に相談")
st.write("2. 47都道府県の **ローカルフード** の専門家に相談")

selected_item = st.radio(
    "動作モードを選択してください。",
    ["伝統文化の専門家", "ローカルフードの専門家"]
)

input_message = st.text_input("都道府県名を入力してください。")
persona = "伝統文化の専門家" if selected_item == "伝統文化の専門家" else "ローカルフードの専門家"

if st.button("実行"):
    st.divider()

    # バリデーション
    if not input_message or not input_message.strip():
        st.error("都道府県名を入力してください。Please enter the name of the prefecture.")
    elif not is_valid_prefecture(input_message):
        st.error("都道府県名を正しく入力してください。Please enter a valid prefecture name.")
    else:
        norm = _normalize_pref_name(input_message)
        canonical = _NORMALIZED_MAP.get(norm, norm)

        user_text = (
            f"{canonical}の伝統文化について教えてください。"
            if persona == "伝統文化の専門家"
            else f"{canonical}のローカルフードについて教えてください。"
        )

        with st.spinner("生成中..."):
            try:
                answer = generate_answer(user_text, persona)
                st.success("回答")
                st.write(answer)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

