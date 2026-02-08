import streamlit as st
import io
import random
import pandas as pd  # Excelを読み込むためのライブラリ
# PDFを作るためのライブラリ
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# ==========================================
# 🔐 パスワード認証機能
# ==========================================
# Secretsにパスワードが設定されている場合のみ認証を行う安全策
if "MY_PASSWORD" in st.secrets:
    password = st.text_input("パスワードを入力してください", type="password")
    if password != st.secrets["MY_PASSWORD"]:
        st.warning("正しいパスワードを入力するとアプリが使えます。")
        st.stop()

# ==========================================
# 画面の設定
# ==========================================
st.title("みるみる古文単語テスト作成アプリ 📝")
st.write("Excelファイルをアップロードして、範囲を指定してください。")

# ==========================================
# 📂 Excelアップロード機能（ここが変更点！）
# ==========================================
uploaded_file = st.file_uploader("単語リストのExcelファイルをアップロードしてください", type=['xlsx'])

# ファイルがアップロードされていない時は、ここで処理を止める（入力を待つ）
if uploaded_file is None:
    st.info("👆 まずは上にExcelファイル（.xlsx）を置いてください。")
    st.stop()

# ファイルがある場合、読み込み処理に進む
try:
    # Excelを読み込む
    df = pd.read_excel(uploaded_file)
    
    # データが2列以上あるかチェック
    if len(df.columns) < 2:
        st.error("エラー：ExcelファイルにはA列（問題）とB列（答え）が必要です。")
        st.stop()

    # データをリストに変換（1列目を問題、2列目を答えとする）
    # astype(str)ですべて文字として読み込む（数字などが混ざってもエラーにならないように）
    questions_all = df.iloc[:, 0].astype(str).tolist()
    answers_all = df.iloc[:, 1].astype(str).tolist()
    
    total_count = len(questions_all)
    st.success(f"✅ {total_count}個のデータを読み込みました！")

except Exception as e:
    st.error(f"ファイルの読み込みに失敗しました: {e}")
    st.stop()


# ==========================================
# 入力欄（ファイル読み込み後に表示）
# ==========================================
st.write("---")
col1, col2, col3 = st.columns(3)

with col1:
    s = st.number_input('開始番号 (No.)', min_value=1, value=1)
with col2:
    # 終了番号の最大値は、読み込んだデータの数にする
    f = st.number_input('終了番号 (No.)', min_value=1, value=total_count)
with col3:
    q_num = st.number_input('出題数', min_value=1, value=20)


# ==========================================
# PDFを作成する関数
# ==========================================
def create_pdf(questions, answers, start_num, end_num, actual_num, mode="question"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # ★フォントの登録
    try:
        pdfmetrics.registerFont(TTFont('Japanese', 'ipaexg.ttf'))
        font_name = 'Japanese'
    except:
        # フォントがない場合の退避策
        font_name = 'Helvetica'

    width, height = A4
    c.setFont(font_name, 10.5)
    
    # タイトル
    title_text = f"名前:＿＿＿＿＿＿＿＿＿＿＿＿＿＿   範囲：No.{start_num}～{end_num} からランダムに{actual_num}問"
    c.drawString(20*mm, height - 20*mm, title_text)
    c.drawString(20*mm, height - 28*mm, "答えの〔No.～〕は単語番号です。")
    
    y_position = height - 45*mm
    
    for i in range(len(questions)):
        if y_position < 20*mm:
            c.showPage()
            c.setFont(font_name, 10.5)
            y_position = height - 20*mm

        q_text = questions[i]
        a_text = answers[i]
        
        # 問題文
        c.drawString(20*mm, y_position, f"{i+1}:　{q_text}")
        
        if mode == "answer":
            # 答えモードなら答えを表示
            c.drawString(20*mm, y_position - 8*mm, f"      {a_text}")
        else:
            # 問題モードなら下線を表示
            c.drawString(20*mm, y_position - 8*mm, "＿＿" * 25)
        
        y_position -= 20*mm

    c.save()
    return buffer.getvalue()


# ==========================================
# 作成ボタン処理
# ==========================================
if st.button('PDFテストを作成する！'):
    
    # エラーチェック
    if s > f:
        st.error("範囲エラー：開始番号が終了番号より大きいです。")
        st.stop()
    
    # 範囲データの抽出
    # スライス（s-1 : f）を使って範囲を切り取る
    target_questions = questions_all[s-1 : f]
    target_answers = answers_all[s-1 : f]
    
    if len(target_questions) < 1:
        st.error("データなし：指定された範囲にデータがありません。")
        st.stop()

    # ペアにしてシャッフル
    combined_data = list(zip(target_questions, target_answers))
    actual_q_num = min(q_num, len(combined_data))
    
    random.shuffle(combined_data)
    selected_data = combined_data[:actual_q_num]
    
    # 分解してリストに戻す
    final_questions = [item[0] for item in selected_data]
    final_answers = [item[1] for item in selected_data]
    
    # PDFを作成
    # モードを変えて2回呼び出す（問題用と解答用）
    pdf_q = create_pdf(final_questions, final_answers, s, f, actual_q_num, mode="question")
    pdf_a = create_pdf(final_questions, final_answers, s, f, actual_q_num, mode="answer")
    
    # セッションステートに保存
    st.session_state['pdf_q'] = pdf_q
    st.session_state['pdf_a'] = pdf_a
    st.session_state['suffix'] = f"{s}～{f}"
    
    st.success(f"PDF作成完了！({actual_q_num}問)")


# ==========================================
# ダウンロードボタン
# ==========================================
if 'pdf_q' in st.session_state:
    st.write("---")
    col1, col2 = st.columns(2)
    suffix = st.session_state['suffix']
    
    with col1:
        st.download_button(
            label="📄 問題PDFをDL",
            data=st.session_state['pdf_q'],
            file_name=f"テスト_{suffix}.pdf",
            mime="application/pdf"
        )
    with col2:
        st.download_button(
            label="📄 答えPDFをDL",
            data=st.session_state['pdf_a'],
            file_name=f"答え_{suffix}.pdf",
            mime="application/pdf"

        )
