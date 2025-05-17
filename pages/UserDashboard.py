 # الخيارات الخاصة بالصلاة
        options_1 = {
            "🕌 في المسجد جماعة (🟥 5 نقاط)": 5,
            "🏠 في المنزل جماعة (🟥 4 نقاط)": 4,
            "🧍‍♂️ في المسجد منفرد (🟥 4 نقاط)": 4,
            "🏠 في المنزل منفرد (🟥 3 نقاط)": 3,
            "⏰ خارج الوقت (🟥 0 نقاط)": 0
        }
        
        for col in columns[1:6]:
            st.markdown(f"<h4 style='font-weight: bold;'>{col}</h4>", unsafe_allow_html=True)
            selected = st.radio("", list(options_1.keys()), index=0, key=col)
            values.append(str(options_1[selected]))
        
        # خيارات الأذكار
        checkbox_options = {
            "الفجر (🟥 1 نقطة)": 1,
            "الظهر القبلية (🟥 1 نقطة)": 1,
            "العصر القبلية (🟥 1 نقطة)": 1,
            "المغرب (🟥 1 نقطة)": 1,
            "العشاء (🟥 1 نقطة)": 1
        }
        
        st.markdown(f"<h4 style='font-weight: bold;'>{columns[6]}</h4>", unsafe_allow_html=True)
        checkbox_cols = st.columns(1)
        selected_checkboxes = []
        
        for option, value in checkbox_options.items():
            with checkbox_cols[0]:
                if st.checkbox(label=option, key=f"{columns[6]}_{option}"):
                    selected_checkboxes.append(value)
        
        score_checkbox = len(selected_checkboxes)
        values.append(str(score_checkbox))
        
        # قراءة القرآن
        time_read_options = {
            "📖 قرأته لفترتين (🟥 4 نقاط)": 4,
            "📖 قرأته مرة واحدة في اليوم (🟥 2 نقطة)": 2,
            "🚫 لم أتمكن من قراءته لهذا اليوم (🟥 0 نقاط)": 0
        }
        
        for col_name in columns[7:9]:
            st.markdown(f"<h4 style='font-weight: bold;'>{col_name}</h4>", unsafe_allow_html=True)
            selected = st.radio("", list(time_read_options.keys()), key=col_name)
            values.append(str(time_read_options[selected]))
        
        # المجموعة الأولى: نعم = 2 نقطة
        yes_no_options_2pts = {
            "✅ نعم (🟥 2 نقطة)": 2,
            "❌ لا (🟥 0 نقطة)": 0
        }
        
        for col_name in columns[9:13]:
            st.markdown(f"<h4 style='font-weight: bold;'>{col_name}</h4>", unsafe_allow_html=True)
            selected = st.radio("", list(yes_no_options_2pts.keys()), horizontal=True, key=col_name)
            values.append(str(yes_no_options_2pts[selected]))
        
        # المجموعة الثانية: نعم = 1 نقطة
        yes_no_options_1pt = {
            "✅ نعم (🟥 1 نقطة)": 1,
            "❌ لا (🟥 0 نقطة)": 0
        }
        
        if len(columns) > 13:
            remaining_columns = columns[13:]
            for col_name in remaining_columns:
                st.markdown(f"<h4 style='font-weight: bold;'>{col_name}</h4>", unsafe_allow_html=True)
                selected = st.radio("", list(yes_no_options_1pt.keys()), horizontal=True, key=col_name)
                values.append(str(yes_no_options_1pt[selected]))
                
