import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import time
import json


firebase_config = dict(st.secrets["FIREBASE"])

# Firebase 초기화 함수
def init_firebase():
    if not firebase_admin._apps:
        try:
            # 1. secrets에서 dict로 가져오기
            config = dict(st.secrets["FIREBASE"])
            
            # 2. 강제로 JSON 문자열로 만들었다가 다시 파싱 (타입 깨짐 방지)
            # 이 과정이 모든 줄바꿈과 특수문자 문제를 가장 깔끔하게 해결합니다.
            json_str = json.dumps(config)
            firebase_config = json.loads(json_str)
            
            # 3. 인증서 초기화
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            
        except Exception as e:
            st.error(f"Firebase 초기화 에러: {e}")
            st.stop()

init_firebase()
db = firestore.client()

# --- 상태 초기화 ---
if 'step' not in st.session_state: st.session_state.step = 1
if 'page' not in st.session_state: st.session_state.page = 'lobby'
if 'amount_input' not in st.session_state: st.session_state.amount_input = ""

# --- 공통 함수 ---
def format_currency():
    raw_val = st.session_state.amount_input.replace(",", "")
    if raw_val.isdigit(): st.session_state.amount_input = f"{int(raw_val):,}"
    else: st.session_state.amount_input = ""

def draw_text_on_image(data):
    img = Image.open("template.png")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("malgun.ttf", 15)
        small_font = ImageFont.truetype("malgun.ttf", 9)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # 입력된 데이터 적용
    draw.text((75, 82), data.get('date', ''), fill="black", font=font)
    draw.text((125, 105), data.get('amount', ''), fill="black", font=font)
    draw.text((125, 218), data.get('amount', ''), fill="black", font=font)
    draw.text((310, 218), data.get('rate', ''), fill="black", font=font)
    draw.text((473, 218), data.get('rate_day', ''), fill="black", font=font)
    draw.text((100, 311), data.get('bank_name', ''), fill="black", font=font)
    draw.text((240, 311), data.get('account_num', ''), fill="black", font=font)
    draw.text((450, 311), data.get('account_holder', ''), fill="black", font=font)
    draw.text((315, 612), data.get('c_name', ''), fill="black", font=small_font)
    draw.text((315, 629), data.get('c_addr', ''), fill="black", font=small_font)
    draw.text((315, 663), data.get('c_phone', ''), fill="black", font=small_font)
    draw.text((315, 691), data.get('d_name', ''), fill="black", font=small_font)
    draw.text((315, 708), data.get('d_addr', ''), fill="black", font=small_font)
    draw.text((315, 742), data.get('d_phone', ''), fill="black", font=small_font)
    return img

def save_to_db():
    # 모든 입력 값을 DB에 저장
    data = {
        "date": st.session_state.get("date_input", ""),
        "amount": st.session_state.get("amount_input", ""),
        "rate": st.session_state.get("rate_input", ""),
        "rate_day": st.session_state.get("rate_day_input", ""),
        "bank_name": st.session_state.get("bank_name_input", ""),
        "account_num": st.session_state.get("account_num_input", ""),
        "account_holder": st.session_state.get("account_holder_input", ""),
        "c_name": st.session_state.get("c_name_input", ""),
        "c_addr": st.session_state.get("c_addr_input", ""),
        "c_id": st.session_state.get("c_id_input", ""),
        "c_phone": st.session_state.get("c_phone_input", ""),
        "d_name": st.session_state.get("d_name_input", ""),
        "d_addr": st.session_state.get("d_addr_input", ""),
        "d_id": st.session_state.get("d_id_input", ""),
        "d_phone": st.session_state.get("d_phone_input", "")
    }
    db.collection('contracts').document(contract_id).set(data, merge=True)

# URL 파라미터 및 DB 데이터 로드
params = st.query_params
is_debtor_mode = params.get("mode") == "debtor"
contract_id = params.get("contract_id") or str(uuid.uuid4())
doc = db.collection('contracts').document(contract_id).get()
if doc.exists:
    for k, v in doc.to_dict().items():
        st.session_state[f"{k}_input"] = v

# 페이지 로직
st.title("차용증 작성")

# [채무자 모드라면 4단계로 바로 점프]
if is_debtor_mode and st.session_state.step < 4:
    st.session_state.step = 4

# 1단계: 기본 정보 + 이자 계산
if st.session_state.step == 1:
    st.subheader("1단계: 기본 정보")
    st.text_input("날짜", key="date_input")
    amt = st.text_input("금액 (원)", key="amount_input")
    rate = st.text_input("연 이자율 (%)", key="rate_input")
    day = st.text_input("이자 지급일 (매월 O일)", key="rate_day_input")
    
    # 이자 계산 로직
    try:
        if amt and rate:
            clean_amt = int(amt.replace(",", ""))
            interest = int(clean_amt * (float(rate) / 100) / 12)
            st.info(f"월 이자는 약 {interest:,}원입니다.")
    except: pass
    
    if st.button("다음 (계좌 정보)"): save_to_db(); st.session_state.step = 2; st.rerun()

# 2단계: 계좌 정보
elif st.session_state.step == 2:
    st.subheader("2단계: 계좌 정보")
    st.text_input("은행명", key="bank_name_input")
    st.text_input("계좌번호", key="account_num_input")
    st.text_input("예금주", key="account_holder_input")
    if st.button("다음 (채권자 상세)"): save_to_db(); st.session_state.step = 3; st.rerun()

# 3단계: 채권자 상세
elif st.session_state.step == 3:
    if not is_debtor_mode:
        st.subheader("3단계: 채권자 상세 정보")
        st.text_input("채권자 이름", key="c_name_input")
        st.text_input("채권자 주소", key="c_addr_input")
        st.text_input("채권자 주민번호(앞 7자리)", key="c_id_input", type="password")
        st.text_input("채권자 연락처", key="c_phone_input")
        if st.button("차용증 생성 및 링크 만들기"):
            save_to_db()
            st.session_state.step = 4
            st.rerun()
    
# 4단계: 링크 공유 (채권자) 또는 정보 입력 (채무자)
elif st.session_state.step == 4:
    if is_debtor_mode:
        # --- [채무자용 화면] ---
        st.subheader("채무자 정보 입력")
        st.text_input("채무자 이름", key="d_name_input")
        st.text_input("채무자 주소", key="d_addr_input")
        st.text_input("채무자 주민번호", key="d_id_input", type="password")
        st.text_input("채무자 연락처", key="d_phone_input")
        
        if st.button("완료"):
            save_to_db() # 여기서 DB에 채무자 정보가 저장됨
            st.success("차용증이 완성되었습니다!")
            st.stop() # 채무자는 여기서 멈춤

    else:
        # --- [채권자용 화면 (자동 감지 루프)] ---
        st.subheader("4단계: 링크 공유 및 채무자 대기")
        share_link = f"http://192.168.10.44:8501/?contract_id={contract_id}&mode=debtor"
        st.info(f"채무자에게 아래 링크를 공유하세요:\n{share_link}")
        
        # 실시간 감지 메시지
        with st.empty():
            while True:
                # DB에서 최신 데이터 가져오기
                updated_doc = db.collection('contracts').document(contract_id).get().to_dict()
                
                # 채무자 정보(예: 이름)가 들어왔는지 확인
                if updated_doc and updated_doc.get("d_name"):
                    st.session_state.step = 5
                    st.rerun() # 즉시 5단계(차용증 결과)로 화면 전환
                
                st.write("⏳ 채무자가 정보를 입력할 때까지 대기 중...")
                time.sleep(1) # 1초마다 데이터 확인

# 5단계: 결과 출력
elif st.session_state.step == 5:
    st.subheader("완성된 차용증")
    
    # 1. DB에서 문서 가져오기
    doc_ref = db.collection('contracts').document(contract_id)
    doc = doc_ref.get()
    
    # 2. 문서가 존재하는지 확실히 확인 후 데이터 변환
    if doc.exists:
        final_data = doc.to_dict()
        # 3. 데이터가 있을 때만 이미지 생성
        st.image(draw_text_on_image(final_data), caption="완성된 차용증")
        st.success("채무자 정보가 성공적으로 반영되었습니다.")
    else:
        # 데이터가 없다면 에러 메시지 대신 잠시 대기 혹은 새로고침 유도
        st.error("차용증 데이터를 불러오는 중입니다... 잠시만 기다려주세요.")
        time.sleep(1)
        st.rerun()
