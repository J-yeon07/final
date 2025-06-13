import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("🚇 연도별 지하철 이용자 수 비교")

uploaded_files = st.file_uploader("CSV 파일을 업로드하세요 (2개 이상)", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    data_per_year = {}

    for uploaded_file in uploaded_files:
        try:
            try:
                df = pd.read_csv(
                    uploaded_file,
                    header=0,
                    usecols=[0, 1, 2, 3, 4],
                    names=["사용일자", "노선명", "역명", "승차총승객수", "하차총승객수"],
                    skiprows=1,
                    encoding='utf-8'
                )
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(
                    uploaded_file,
                    header=0,
                    usecols=[0, 1, 2, 3, 4],
                    names=["사용일자", "노선명", "역명", "승차총승객수", "하차총승객수"],
                    skiprows=1,
                    encoding='cp949'
                )

            df["연도"] = df["사용일자"].astype(str).str[:4]
            year = df["연도"].mode()[0]
            data_per_year[year] = df

        except Exception as e:
            st.error(f"{uploaded_file.name} 처리 중 오류 발생: {e}")

    if data_per_year:
        sample_df = list(data_per_year.values())[0]
        selected_line = st.selectbox("노선명을 선택하세요", sorted(sample_df["노선명"].unique()))
        selected_station = st.selectbox(
            f"{selected_line}의 역명을 선택하세요",
            sorted(sample_df[sample_df["노선명"] == selected_line]["역명"].unique())
        )

        compare_data = []
        for year, df in sorted(data_per_year.items()):
            filtered = df[(df["노선명"] == selected_line) & (df["역명"] == selected_station)]
            total_boarding = filtered["승차총승객수"].sum()
            total_alighting = filtered["하차총승객수"].sum()
            compare_data.append({
                "연도": year,
                "총 승차 승객 수": total_boarding,
                "총 하차 승객 수": total_alighting
            })

        result_df = pd.DataFrame(compare_data).sort_values("연도")
        st.subheader(f"📊 {selected_line} {selected_station}역 연도별 이용자 비교")
        st.dataframe(result_df.set_index("연도"))

        # 📈 Plotly 그래프 생성
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=result_df["연도"],
            y=result_df["총 승차 승객 수"],
            name="승차",
            marker_color="royalblue",
            hovertemplate='연도: %{x}<br>승차: %{y:,}명'
        ))
        fig.add_trace(go.Bar(
            x=result_df["연도"],
            y=result_df["총 하차 승객 수"],
            name="하차",
            marker_color="indianred",
            hovertemplate='연도: %{x}<br>하차: %{y:,}명'
        ))
        fig.update_layout(
            barmode='group',
            title=f"{selected_station}역 연도별 승하차 비교",
            xaxis_title="연도",
            yaxis_title="이용자 수",
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

        # 📥 엑셀 저장 버튼
        excel_buffer = BytesIO()
        result_df.to_excel(excel_buffer, index=False, engine='openpyxl')
        st.download_button(
            label="📥 결과를 Excel 파일로 저장",
            data=excel_buffer.getvalue(),
            file_name=f"{selected_station}_연도별_이용자수.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # 🖼️ 그래프 이미지 저장
        img_buf = BytesIO()
        fig.write_image(img_buf, format="png")
        st.download_button(
            label="🖼️ 그래프 PNG로 저장",
            data=img_buf.getvalue(),
            file_name=f"{selected_station}_연도별_그래프.png",
            mime="image/png"
        )

else:
    st.info("2개 이상의 CSV 파일을 업로드해주세요.")
