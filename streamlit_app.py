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


@st.cache
def get_salary_dataframe(dataframe):
    diction = {}
    for mu, sigma, label_name in list(zip(dataframe["Salaries_Mean"], dataframe["Salaries_Standard Deviation"],
                                          dataframe["Education_Major"])):  # (mu,sigma)
        diction[label_name] = np.random.normal(mu, sigma, 7000)
    return pd.DataFrame(diction)


# MAIN CODE
st.set_page_config(layout="wide", page_title='College Graduates Analysis')
st.title("Analysis of National Survey of Recent College Graduates")

alt.data_transformers.disable_max_rows()
with st.spinner(text="Loading data..."):
    data = load_data()

st.write("""
The data being analyzed comes from the National Survey of Recent College Graduates. 
Included is information about employment numbers, major information, and the earnings 
of different majors. Many majors were not available before 2010, so their values have 
been recorded as 0. On a high level the data can be subgrouped into data about Education- 
The demographics of college graduates (ethnicity, gender, degree program, etc.) and 
Emplopyment- Salary statistics after graduation, employer type, field of work,etc.""")

st.write("""
Our analysis is also structured in two parts with part 1 focussing on education data
and part 2 focusing on post graduation employment data analysis. Click the button below to
 get a gist of the raw data we are analyzing...""")

if st.checkbox("Show Raw Data"):
    st.write(data)

data_filled = data[data["Demographics_Total"] > 0]

################################################# Education Analysis  ##################################################
st.markdown("""---""")
st.subheader("College Graduates Education Analysis")

st.write("""Our education data analysis delves deeper into the demographics of the student population and the degrees 
they have earned. The below bar chart has a dynamic Y axis that the user can modify to observe how user selected feature
changes across all College Majors for the selected year. The Demo graphics available in the dta include Student Ethnicity
and Gender. We also plot the salary distribution students earned after graduation using the mena and standard deviation 
provided in our dataset.""")

dict_options = {"Total College Graduates": "Demographics_Total",
                "Average Salary": "Salaries_Mean",
                "Ethnicity (Asians) Count": "Demographics_Ethnicity_Asians",
                "Ethnicity (Minorities) Count": "Demographics_Ethnicity_Minorities",
                "Ethnicity (Whites) Count": "Demographics_Ethnicity_Whites",
                "Gender (Males) Count": "Demographics_Gender_Males",
                "Gender (Females) Count": "Demographics_Gender_Females",
                "Education Degree(Bachelors) Count": "Education_Degrees_Bachelors",
                "Education Degree(Doctorates)": "Education_Degrees_Doctorates",
                "Education Degree(Masters)": "Education_Degrees_Masters",
                "Education Degree(Professionals)": "Education_Degrees_Professionals"}

years_edu = list(data_filled['Year'].unique())
# scales_edu = alt.selection_interval(bind="scales", encodings=["x"])
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    option1 = st.selectbox('Select Graduation Year', options=years_edu)
with col2:
    # set scale: log or linear
    option2 = st.selectbox("Select Y axis:", options=dict_options.keys())
with col3:
    # set scale: log or linear
    bar_scale = st.radio("Select scale:", ('linear', 'log'), key='1')

# brush = alt.selection_interval(encodings=['x'], empty='none')
brush = alt.selection_single(encodings=['x'])

hist_data = data_filled[data_filled['Year'] == option1]

st.markdown("""---""")

hist_main = alt.Chart(hist_data).mark_bar(tooltip=True).encode(
    alt.X("Education_Major", sort='-y'),
    alt.Y(dict_options[option2], scale=alt.Scale(type=bar_scale), title=option2),
    alt.Color("Education_Major", legend=None),
    opacity=alt.condition(brush, alt.OpacityValue(1), alt.OpacityValue(0.4))
).add_selection(brush).properties(
    width=600,
    height=300
)

with st.spinner(text="Loading data..."):
    salary_temp_data = hist_data[["Salaries_Mean", "Education_Major", "Salaries_Standard Deviation"]]
    salary_dist_data = get_salary_dataframe(salary_temp_data)

    selection = alt.selection_multi(fields=['Education_Major'], bind='legend')

    salary_chart = alt.Chart(salary_dist_data).transform_fold(
        list(salary_dist_data.columns),
        as_=['Education_Major', 'Measurement']
    ).mark_area(
        opacity=0.3,
        binSpacing=0,
        tooltip=True
    ).encode(
        alt.X('Measurement:Q', bin=alt.Bin(maxbins=50), title="Salary after graduation"),
        alt.Y('count()', stack=None, axis=None),
        alt.Color('Education_Major:N'),
        opacity=alt.condition(brush, alt.value(1), alt.value(0.01)),
        tooltip=['Education_Major:N']
    ).properties(
        height=300,
        width=600,
        title='Salary Distribution for Majors (Normalized)'
    )

    st.write(hist_main | salary_chart)

st.write("""Lets us analyze College major preferences by gender. Do males have different education major preferences 
 than females in the year selected above ?""")

# Gender Plot
middle = alt.Chart(hist_data).encode(
    y=alt.Y('Education_Major', axis=None),
    text=alt.Text('Education_Major'),
).mark_text().properties(width=100)

female = alt.Chart(hist_data).encode(
    alt.X("Demographics_Gender_Females", sort=alt.SortOrder('descending'), title="Females"),
    alt.Y("Education_Major:N", axis=None),
    tooltip=['Education_Major', 'Year', 'Demographics_Gender_Females']
).add_selection(brush).properties(title='Female', width=550)

male = alt.Chart(hist_data).encode(
    alt.X("Demographics_Gender_Males", title="Males"),
    alt.Y("Education_Major:N", axis=None),
    tooltip=['Education_Major', 'Year', 'Demographics_Gender_Males']
).properties(title='Male', width=550)

st.write(alt.concat(
    female.mark_bar(color='pink'),
    middle,
    male.mark_bar(color='lightblue'),
    spacing=5
).resolve_scale(
    color='independent').configure_view(
    stroke=None))

################################################# Employment Analysis  ##################################################
st.markdown("""---""")
st.subheader("College Graduates Employment Analysis")

st.write("""With the rise in automation and robotics, humanity could leave the mundane jobs to the machines 
and focus their time and energy on discovering novel technologies and improving their standard of life. In our analysis 
of employment data we sought to find the majors that most graduate students were opting for, the trends in these majors 
over the years and the employer and work type students after graduation students start working in.""")

st.write("""Our next visualization helps us understand the temporal trend in college majors and how they fared over 
time. You can adjust the year range to  focus on a specific time window and also compare the trend of specific majors by 
selecting multiple college majors from our data to analyze. This chart is further linked to display trends in employer 
type: Business, Educational Instutions and Government and also the trends in field of work- from Accounting/Finance to 
Teaching. Clicking on a specific trend in the line chart will transform the bar charts for Employer Type and Working 
field to display data relevant to the major""")

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
with cols[2]:
    # set scale: log or linear
    chart_scale = st.radio("Select scale:", ('linear', 'log'), key='2')

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
    alt.Y("Demographics_Total", scale=alt.Scale(type=chart_scale), title="Total College Graduates"),
    opacity=alt.condition(line_hover | line_selector, alt.value(1), alt.value(0.3)),
    color=alt.condition(line_hover | line_selector, "Education_Major", alt.value("lightgray"))
).properties(
    width=1100,
    height=400,
    title='Total Graduates by College Major per Year'
).add_selection(line_hover, line_selector, scales)

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
    height=250,
    width=300
).interactive().transform_filter(line_selector)

row1 = alt.hconcat().properties(
    title='Employer Type: Classifies employees working in Business/Industry, Educational Institutions and Government\n'
)
for y_encoding, label in zip(employer_type_cols, employer_type_name):
    row1 |= base.encode(y=alt.Y(y_encoding, title=label),
                        x="Year:T", color=alt.value("#ff7f0e"))
row1.configure_title(fontSize=50)

emp_work_activity_charts = alt.vconcat()
row2 = alt.hconcat().properties(
    title='Working Field: Classifies Graduates for the year by field of work like- Accounting/Finance, Sales, etc.\n'
)

base2 = alt.Chart(plotting_data).mark_bar(tooltip=True, size=15).properties(
    height=160,
    width=200
).interactive().transform_filter(line_selector)
for y_encoding, label in zip(employment_work_activity[:4], employment_work_activity_names[0:4]):
    row2 |= base2.encode(y=alt.Y(y_encoding, title=label), x="Year:T", color=alt.value("#1f77b4"))
row2.configure_title(fontSize=50)
row3 = alt.hconcat()
for y_encoding, label in zip(employment_work_activity[4:], employment_work_activity_names[4:]):
    row3 |= base2.encode(y=alt.Y(y_encoding, title=label), x="Year:T", color=alt.value("#1f77b4"))

emp_work_activity_charts = row2 & row3

base3 = alt.Chart(plotting_data).mark_bar(tooltip=True, size=20).properties(
    height=250,
    width=300
).interactive().transform_filter(line_selector)

row4 = alt.hconcat().properties(
    title='Employee Status: Classifies Graduated student as Employed, Unemployed, Not Participating in Labour Force\n'
)
for y_encoding, label in zip(employment_status, employment_status_names):
    row4 |= base.encode(y=alt.Y(y_encoding, title=label),
                        x="Year:T", color=alt.value("#2ca02c"))
row4.configure_title(fontSize=50)

st.write(graduates_multi_line & row1 & emp_work_activity_charts & row4)

st.write("""The above bar graphs help us observe the trend in Employer Type, Work Field and the Employment Status of 
graduates by Year and Major.""")
