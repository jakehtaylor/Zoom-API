from flask import Flask, redirect, render_template, request, url_for, abort
import os
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from statistics import mean

app = Flask(__name__)

app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.xlsx']
app.config['UPLOAD_PATH'] = 'logs'

@app.route("/")
def home():
    return render_template('index.html')


@app.route("/", methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = uploaded_file.filename
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)
    
    if file_ext == '.xlsx':
        df = pd.read_excel(uploaded_file, header=2, 
                   usecols=['Participant', 'Join Time', 'Leave Time'])
    else:
        df = pd.read_csv(uploaded_file,header=2, 
                   usecols=['Participant', 'Join Time', 'Leave Time'])

    
    df['Leave Time'] = [str(x)[0:8] for x in df['Leave Time']]

    leave_times = []

    for l in df['Leave Time']:
        l = str(l).replace(':', '')
        if l[0] == '0':
            ll = l[1:]
        if l[-2:] == 'PM':
            l=l[:-2]
            if int(l) < 1200:
                l = int(l) + 1200
        else:
            l=l[:-2]
        leave_times.append(int(l))

    df['Leave Time'] = leave_times

    join_times = []

    for j in df['Join Time']:
        j = str(j).replace(':', '')
        if j[-2:] == 'PM':
            j=j[:-2]
            if int(j) < 1200:
                j = int(j) + 1200
        else:
            j=j[:-2]
        join_times.append(int(j))

    df['Join Time'] = join_times
    
    participants = df.groupby('Participant')

    joins_and_leaves = pd.DataFrame({
        'First Join' : participants['Join Time'].min(),
        'Last Leave' : participants['Leave Time'].max(),
    })

    times = []
    
    first_hour = (joins_and_leaves['First Join'].min() // 100) * 100
    last_hour = ((joins_and_leaves['Last Leave'].max() // 100) + 1) * 100

    for x in range(first_hour, last_hour, 100):
        for y in range(0, 60):
            times.append(x+y)

    active = [0 for x in times]

    for i in range(len(joins_and_leaves['First Join'])):
        join = joins_and_leaves.iloc[i]['First Join']
        leave = joins_and_leaves.iloc[i]['Last Leave']
        for t in times:
            if join < t and leave > t:
                active[(times.index(t))] += 1
        
    graph_data = pd.DataFrame({
        'Time': times,
        'Active' : active
    })

    att_time = []

    for i in range(len(joins_and_leaves['First Join'])):
        join = joins_and_leaves.iloc[i]['First Join']
        leave = joins_and_leaves.iloc[i]['Last Leave']
        
        hour = (leave//100 - join//100) * 100
        minute = (leave-((leave//100)*100)) - (join-((join//100)*100))
        if minute < 0 :
            minute -= 40
        duration = hour+minute
        att_time.append(duration)
        
    joins_and_leaves['Total Time'] = att_time
    
    sorted_jal = joins_and_leaves.sort_values(by='Total Time', ascending=False)

    jal_display = sorted_jal
    jal_display['First Join'] = [str(x)[:-2] + ":" + str(x)[-2:] for x in jal_display['First Join']]
    jal_display['Last Leave'] = [str(x)[:-2] + ":" + str(x)[-2:] for x in jal_display['Last Leave']]
    jal_display['Total Time'] = [str(x)[:-2] + ":" + str(x)[-2:] for x in jal_display['Total Time']]
    jal_display = jal_display.rename(columns={
        'First Join' : 'Joined',
        'Last Leave' : 'Left',
        'Total Time' : 'Duration of Attendance'})
    jal_display['Participant'] = jal_display.index
    jal_display = jal_display [['Participant', 'Joined', 'Left','Duration of Attendance']]
    
    Active = graph_data['Active'].to_list()
    Times = graph_data['Time'].to_list()

    grouped_times = pd.DataFrame({
        'Count': joins_and_leaves.groupby('First Join')['Last Leave'].count()})
    other_ts = list(set(times) - set(grouped_times.index.to_list()))
    other_times = pd.DataFrame({
        'Time': other_ts,
        'Count' : [0 for t in other_ts]
    }).set_index('Time')
    full_times = pd.concat([grouped_times, other_times]).sort_index()

    total_joined = 0
    Cumulative = []
    for count in full_times['Count'].to_list():
        total_joined += count
        Cumulative.append(total_joined)

    Times_formatted = [str(t) + ' AM' if t < 1200 else str(t) + ' PM' for t in times]

    Mean_att = int(mean([a for a in Active if a != 0]))
    peak_time = Times_formatted[Active.index(max(Active))]


    metrics = {
        'tables' : [jal_display.to_html(header=False,index=False, classes="table table-hover table-light table-responsive")],
        'graphs' : [[Times_formatted, Active], [Times_formatted, Cumulative]],
        'stats': [first_hour, last_hour, max(Cumulative), max(Active), peak_time, Mean_att]
    }
    

    return render_template('metrics.html', metrics=metrics)



