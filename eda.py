import dart_fss
import pandas as pd
import streamlit as st

def find_corp_code(df,corp_name:str,corp_status:bool,compare:str,compare_status:bool,period:str):
    result=''
    if period not in ["annual","half","quarter"]:
        st.subheader("기간단위를 annual, half, quarter 중 하나로 입력하세요")
        result="해당 기업이 없습니다"
    if compare != "None":
        for company in [[corp_name,corp_status],[compare,compare_status]]:
            if company[1]:
                temp=df[df["stock_code"].notnull()].reset_index(drop=True).copy()
                try:
                    corp_code.append(temp[temp["corp_name"]==company[0].strip()].values[0][0])
                except:
                    result="해당 기업이 없습니다"
            else:
                temp=df[df["stock_code"].isnull()].reset_index(drop=True).copy()
                try:
                    corp_code.append(temp[temp["corp_name"]==company[0].strip()].values[0][0])
                except:
                    result="해당 기업이 없습니다"
    else:
        if corp_status:
            temp=df[df["stock_code"].notnull()].reset_index(drop=True).copy()
            try:
                corp_code.append(temp[temp["corp_name"]==corp_name.strip()].values[0][0])
            except:
                result="해당 기업이 없습니다"
        else:
            temp=df[df["stock_code"].isnull()].reset_index(drop=True).copy()
            try:
                corp_code.append(temp[temp["corp_name"]==corp_name.strip()].values[0][0])
            except:
                result="해당 기업이 없습니다"
    return corp_code,result

st.title("DART API 연결재무제표 조회")
col1,col2,col3,col4=st.columns(4)
with col1:
    corp_name=st.text_input("기업명",placeholder="기업명을 입력하세요")
    corp_status=st.checkbox("상장 상태",value=True,key="corp_status")
with col2:
    compare=st.text_input("비교기업명",placeholder="비교할 기업명을 입력하세요")
    compare_status=st.checkbox("상장 상태",value=True,key="compare_status")
with col3:
    period=st.text_input("기간단위",placeholder="annual, half, quarter")
with col4:
    fin_data=st.multiselect("찾고 싶은 재무데이터",['금융업부채', '금융업자산', '부채총계', '비유동부채','비유동자산', '비지배지분', '유동부채','유동자산', '자본총계', '자산총계', '지배기업 소유주지분'])
graph_type=st.selectbox("그래프 종류",["막대그래프","선그래프"],key="graph_type")
submit_corp=st.button("Submit",key="submit_corp")

dart_fss.set_api_key(api_key=API_KEY)
corp_code=[]
if submit_corp:
    df=pd.DataFrame(dart_fss.api.filings.get_corp_code())
    corp_code,result=find_corp_code(df,corp_name,corp_status,compare,compare_status,period)
    if result=="해당 기업이 없습니다":
        st.write(result)
    else:
        if len(corp_code)==1:
            fs=dart_fss.fs.extract(corp_code=corp_code[0],report_tp=period,bgn_de="20190101",end_de="20240327")
        else:
            fs=dart_fss.fs.extract(corp_code=corp_code[0],report_tp=period,bgn_de="20190101",end_de="20240327")
            fs_compare=dart_fss.fs.extract(corp_code=corp_code[1],report_tp=period,bgn_de="20190101",end_de="20240327")
            df_compare=pd.DataFrame(fs_compare['bs'])
        df=pd.DataFrame(fs['bs'])
        year_list=[]
        for i in df.columns[8:]:
            year,_=i
            year_list.append(year)
        #자본과부채총계 #자산총계 #유동부채 #유동자산 #현금및현금성자산
        for fin in list(fin_data):
            temp_list=df[df[df.columns[5]]==fin].iloc[:,1].values
            st.subheader(fin)
            for f in temp_list:
                if len(corp_code)==1:
                    val=list(df[(df[df.columns[1]]==f) & (df[df.columns[5]]==fin)].values[0][8:]/1000)
                elif len(corp_code)==2:
                    try:
                        val=list(df[(df[df.columns[1]]==f) & (df[df.columns[5]]==fin)].values[0][8:]/1000)
                        val_compare=list(df_compare[(df_compare[df_compare.columns[1]]==f) & (df_compare[df_compare.columns[5]]==fin)].values[0][8:]/1000)
                        if len(val) != len(val_compare):
                            if len(val) > len(val_compare):
                                val_compare= val_compare+[0]*(len(val)-len(val_compare))
                            else:
                                val=val+[0]*(len(val_compare)-len(val))
                    except:
                        pass
                col1,col2,col3=st.columns([0.2,0.4,0.4])                
                with col1:
                    st.write(f)
                with col2:
                    st.write("(천원)")
                    if len(corp_code)==1:
                        st.dataframe(pd.DataFrame({"날짜":year_list,corp_name:val}))
                    elif len(corp_code)==2:
                        st.dataframe(pd.DataFrame({"날짜":year_list,corp_name:val,compare:val_compare}))
                with col3:
                    if len(corp_code)==1:
                        chart_data=pd.DataFrame({
                            "연도":year_list,
                            "금액":val,
                            "구분":[corp_name]*len(year_list)})
                    elif len(corp_code)==2:
                        chart_data=pd.DataFrame({
                            "연도":year_list*2,
                            "금액":val+val_compare,
                            "구분":[corp_name]*len(year_list)+[compare]*len(year_list)})
                    if graph_type=="막대그래프":
                        st.bar_chart(chart_data,x="연도",y="금액",color="구분")
                    elif graph_type=="선그래프":
                        st.line_chart(chart_data,x="연도",y="금액",color="구분")
