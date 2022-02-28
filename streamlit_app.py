import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
import re


@st.cache
def load_data():
    data = pd.read_csv("https://corgis-edu.github.io/corgis/datasets/csv/graduates/graduates.csv")
    data_cols_renamed = rename_columns(data)

    return data_cols_renamed


@st.cache
def rename_columns(data):
    cols = data.columns
    col_name_mapping = {}
    for x in cols:
        y = x
        x = x.replace(".", "_")
        col_name_mapping[y] = x

    data = data.rename(columns=col_name_mapping)
    return data


def get_plotting_data(df, year_range, selected_majors):
    labels = pd.Series([1] * len(df), index=df.index)
    if year_range is not None:
        labels &= df['Year'] >= year_range[0]
        labels &= df['Year'] <= year_range[1]
    if selected_majors:
        labels &= df['Education_Major'].isin(selected_majors)

    return labels


# MAIN CODE
st.set_page_config(layout="wide", page_title='College Graduates Analysis')
st.title("Analysis of National Survey of Recent College Graduates")

with st.spinner(text="Loading data..."):
    data = load_data()

st.write("""
The data being analyzed comes from the National Survey of Recent College Graduates. 
Included is information about employment numbers, major information, and the earnings 
of different majors. Many majors were not available before 2010, so their values have 
been recorded as 0""")

if st.checkbox("Show Raw Data"):
    st.write(data)

data_filled = data[data["Demographics_Total"] > 0]

################################################# Education Analysis  ##################################################

st.subheader("College Graduates Education Analysis")

################################################# Employment Analysis  ##################################################

st.subheader("College Graduates Employment Analysis")

# hover select on line graph
line_hover = alt.selection_single(on="mouseover", fields=["Education_Major"])
# line selector
line_selector = alt.selection_single(fields=["Education_Major"])
# zoom and pan
scales = alt.selection_interval(bind='scales')

cols = st.columns((2, 0.25, 1))
with cols[0]:
    # year range slider
    year_range = st.slider('Year Range',
                           min_value=int(data_filled['Year'].min()),
                           max_value=int(data_filled['Year'].max()),
                           value=(int(data_filled['Year'].min()), int(data_filled['Year'].max())))
with cols[1]:
    st.write("")
with cols[2]:
    # set scale: log or linear
    chart_scale = st.radio("Select scale:", ('linear', 'log'))

# multiselect majors to disply on shart
majors_selected = st.multiselect('Select College Majors:',
                                 data_filled["Education_Major"].unique().tolist(),
                                 ['Biological Sciences',
                                  'Chemical Engineering',
                                  'Computer Science and Math',
                                  'Economics',
                                  'Management & Administration',
                                  'Mechanical Engineering',
                                  'Information Services and Systems',
                                  'Oceanography',
                                  'Political Science and Government',
                                  'Public Policy Studies',
                                  'Statistics'])

st.markdown("""---""")
# get sliced data labels
plotting_labels = get_plotting_data(data_filled, year_range, majors_selected)

plotting_data = data_filled[plotting_labels]

# multi line chart
graduates_multi_line = alt.Chart(plotting_data).mark_line(tooltip=True, strokeWidth=4,
                                                          point=alt.OverlayMarkDef(color="Education_Major", size=200)) \
    .encode(
    alt.X("Year:T"),
    alt.Y("Demographics_Total", scale=alt.Scale(type=chart_scale)),
    opacity=alt.condition(line_hover | line_selector, alt.value(1), alt.value(0.3)),
    color=alt.condition(line_hover | line_selector, "Education_Major", alt.value("lightgray"))
).properties(
    width=1500,
    height=500,
    title='Total Graduates by College Major per Year'
).add_selection(line_hover, line_selector, scales)

st.write(line_selector.to_dict())

# Employer type chart
employer_type_cols = list(filter(lambda x: 'Employer Type' in x, plotting_data))
employer_type_name = ['Business/Industry', 'Educational Institution', 'Government']

# Emplopyer work activity
employment_work_activity = ['Employment_Work Activity_Accounting/Finance/Contracts',
                            'Employment_Work Activity_Applied Research',
                            'Employment_Work Activity_Computer Applications',
                            'Employment_Work Activity_Managing/Supervising People/Projects',
                            'Employment_Work Activity_Productions/Operations/Maintenance',
                            'Employment_Work Activity_Qualitity/Productivity Management',
                            'Employment_Work Activity_Sales, Purchasing, Marketing',
                            'Employment_Work Activity_Teaching']
employment_work_activity_names = ['Accounting/Finance/Contracts',
                                  'Applied Research',
                                  'Computer Applications',
                                  'Managing/Supervising People/Projects',
                                  'Productions/Operations/Maintenance',
                                  'Qualitity/Productivity Management',
                                  'Sales, Purchasing, Marketing',
                                  'Teaching']

# Employment status
employment_status = list(filter(lambda x: 'Employment_Status' in x, data_filled))
employment_status_names = ['Employed', 'Not in Labor Force', 'Unemployed']

base = alt.Chart(plotting_data).mark_bar(tooltip=True, size=20).properties(
    height=270,
    width=440
).interactive().transform_filter(line_selector)

row1 = alt.hconcat().properties(
    title='Employer Type'
)
for y_encoding, label in zip(employer_type_cols, employer_type_name):
    row1 |= base.encode(y=alt.Y(y_encoding, title=label),
                        x="Year:T", color=alt.value("#ff7f0e"))
row1.configure_title(fontSize=50)

emp_work_activity_charts = alt.vconcat()
row2 = alt.hconcat().properties(
    title='Working Field'
)

base2 = alt.Chart(plotting_data).mark_bar(tooltip=True, size=20).properties(
    height=180,
    width=310
).interactive().transform_filter(line_selector)
for y_encoding, label in zip(employment_work_activity[:4], employment_work_activity_names[0:4]):
    row2 |= base2.encode(y=alt.Y(y_encoding, title=label), x="Year:T", color=alt.value("#1f77b4"))
row2.configure_title(fontSize=50)
row3 = alt.hconcat()
for y_encoding, label in zip(employment_work_activity[4:], employment_work_activity_names[4:]):
    row3 |= base2.encode(y=alt.Y(y_encoding, title=label), x="Year:T", color=alt.value("#1f77b4"))
emp_work_activity_charts = row2 & row3


st.write(graduates_multi_line & row1 & emp_work_activity_charts)
