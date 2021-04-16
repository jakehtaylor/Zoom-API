from flask import Flask, redirect, render_template, request, url_for, abort, json, send_file
import os
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz, process
from statistics import mean
import re

app = Flask(__name__)

app.config['UPLOAD_EXTENSIONS'] = ['.csv', '.xlsx', '.json']
app.config['UPLOAD_PATH'] = 'logs'

@app.route("/")
def home():
    return render_template('index.html')


@app.route("/", methods=['POST'])
def upload_files():
    
    clean_file = False
    changes = []
    files = request.files.getlist("file")

    for f in files:
        filename = f.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
        
        if file_ext == '.xlsx':
            df = pd.read_excel(f, header=3, 
                    usecols=['Participant', 'Join Time', 'Leave Time'], engine='openpyxl')
        elif file_ext == '.csv':
            df = pd.read_csv(f,header=2, 
                    usecols=['Participant', 'Join Time', 'Leave Time'])
        elif file_ext == '.json':
            changes.append(json.load(f))
            clean_file = True

    if clean_file:
        for ch in changes:
            for key in ch.keys():
                df.replace({key : ch[key]}, inplace=True)

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
    jal_display['Total Time'] = [str(x)[:-2] + ":" + str(x)[-2:] if len(str(x)) > 2 else str(x) + " min."
                                for x in jal_display['Total Time']]
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
    peak_time = peak_time[:-5] + ":" + peak_time[-5:]

    metrics = {
        'tables' : [jal_display.to_html(header=False,index=False, classes="table table-hover table-light"), jal_display.to_json(orient="values")],
        'graphs' : [[Times_formatted, Active], [Times_formatted, Cumulative]],
        'stats': [first_hour, last_hour, max(Cumulative), max(Active), peak_time, Mean_att]
    }
    
    return render_template('metrics.html', metrics=metrics)


@app.route("/name-check", methods=['GET'])
def names():
    return render_template('name-check.html')


@app.route("/name-check", methods=['POST'])
def nameCheck():
    uploaded_file = request.files['file']
    filename = uploaded_file.filename
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)
    
    if file_ext == '.xlsx':
        df = pd.read_excel(uploaded_file, header=3, 
                   usecols=['Participant', 'Join Time', 'Leave Time', 'Location'], engine='openpyxl')
    else:
        df = pd.read_csv(uploaded_file,header=2, 
                   usecols=['Participant', 'Join Time', 'Leave Time', 'Location'])

    pairsToCheck = {}
    irregulars = {}
    names = np.sort(df['Participant'].unique())
    for n1 in names:
        if not (n1.replace(" ", "")).isalpha() or n1.replace(" ", "").lower() == n1:
            if re.match('[A-Za-z]+[ ]{1}[A-Za-z]+[-][A-Za-z]+', n1) and n1.count(' ') == 1:
                pass
            elif re.match('[A-Za-z]+[ ]{1}[A-Za-z]{1}\.{1}[ ]{1}[A-Za-z]+', n1) and n1.count(' ') == 2:
                pass
            elif re.match('[A-Za-z]+[ ]{1}[A-Za-z]{1,2}[\']{1}[A-Za-z]+', n1) and n1.count(' ') == 1:
                pass
            else:
                irregulars[n1] = "irregular"
        for check in names:
            if n1 != check:
                score1 = fuzz.token_set_ratio(n1, check)

                score3 = fuzz.partial_ratio(n1.lower(), check.lower())
                score4 = fuzz.ratio(n1.lower().replace(" ", ""), check.lower().replace(" ", ""))

                if score1 >= 85 or (score3 >= 85 and score1 >=50) or (score4 > 85 and score1 > 50):
                    if check not in pairsToCheck.keys():
                        if n1 in pairsToCheck.keys(): 
                            pairsToCheck[n1].append(check)
                        else:
                            pairsToCheck[n1] = [check]
                    elif n1 not in pairsToCheck[check]:
                        if n1 in pairsToCheck.keys(): 
                            pairsToCheck[n1].append(check)
                        else:
                            pairsToCheck[n1] = [check]

    return redirect(url_for('confirm', pairsToCheck=pairsToCheck, irregulars=irregulars))

@app.route("/confirm-changes", methods=['GET'])
def confirm():
    return render_template('confirm-changes.html', pairsToCheck=request.args.get('pairsToCheck'), irregulars=request.args.get("irregulars"))

@app.route("/confirm-changes", methods=['POST'])
def clean_file():
    form_edited = {}
    form = request.form.to_dict()
    for k in form.keys():
        if form[k] != '':
            if 'RADIO' in k:
                vsplit = form[k].split('./.')
                form_edited[vsplit[0]] = vsplit[1]
            else:
                form_edited[k] = form[k]
    return render_template('json_download.html', replace=form_edited, filename="zoom_name_changes.json")
    

@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/demo")
def download_file():
    path = "testing+development/DEMO-FILE-v1.0.xlsx"
    return send_file(path, as_attachment=True)


@app.route("/registration", methods=['POST'])
def reg_check():

    files = request.files.getlist("file")
    for f in files:
        filename = f.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
        
        if file_ext == '.csv':
            try:
                zoom = pd.read_csv(f, 
                        usecols=['Participant', 'Joined', 'Left', 'Time'])
                participants = set(zoom['Participant'].to_list())
            except ValueError:
                reg = pd.read_csv(f)
        elif file_ext == '.xlsx':
            try:
                zoom = pd.read_excel(f,
                   usecols=['Participant', 'Joined', 'Left', 'Time'], engine='openpyxl')
                participants = set(zoom['Participant'].to_list())
            except ValueError:
                reg = pd.read_excel(f, engine='openpyxl')

    firstLast = False

    for col in reg.columns:
            if re.search('name', col.lower()):
                if re.search('first', col.lower()):
                    firsts = col
                    firstLast = True
                elif re.search('last', col.lower()):
                    lasts = col
                else:
                    names = set(reg[col].to_list())
            elif re.search('participant', col.lower()):
                names = set(reg[col].to_list())

    if firstLast:
        reg['Name'] = reg[firsts] + ' ' + reg[lasts]
        regNames = set(reg['Name'].to_list())
        
   
    allMatches = {}

    for p in participants:
        allMatches[p] = []
        matches = process.extract(p, regNames, limit=4)
        for m in matches:
            allMatches[p].append(m[0])
        allMatches[p].append('Cancel')

       
    return redirect(url_for('regMatching', mDict=allMatches))
    

@app.route('/matching', methods=['GET'])
def regMatching():
    return render_template('reg_doc-check.html', mDict=request.args.get('mDict'))

@app.route('/matching', methods=['POST'])
def gen_file():
    form_edited = {}
    form = request.form.to_dict()
    for k in form.keys():
        if form[k] != "Cancel":
            form_edited[k] = form[k]
    return render_template('json_download.html', replace=form_edited, filename="match_registration.json")


@app.route('/merge', methods=['GET'])
def mergeHome():
    return render_template('merge.html')

@app.route('/merge', methods=['POST'])
def merge():
    files = request.files.getlist("file")
    for f in files:
        filename = f.filename
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
        
        if file_ext == '.csv':
            try:
                zoom = pd.read_csv(f, 
                        usecols=['Participant', 'Joined', 'Left', 'Time'])
                participants = set(zoom['Participant'].to_list())
            except ValueError:
                reg = pd.read_csv(f)
        elif file_ext == '.xlsx':
            try:
                zoom = pd.read_excel(f,
                   usecols=['Participant', 'Joined', 'Left', 'Time'], engine='openpyxl')
                participants = set(zoom['Participant'].to_list())
            except ValueError:
                reg = pd.read_excel(f, engine='openpyxl')
        elif file_ext == '.json':
            changes = json.load(f)

    for key in changes.keys():
        zoom.replace({key : changes[key]}, inplace=True)

    firstLast = False

    for col in reg.columns:
            if re.search('name', col.lower()):
                if re.search('first', col.lower()):
                    firsts = col
                    firstLast = True
                elif re.search('last', col.lower()):
                    lasts = col
                else:
                    colName = col
            elif re.search('participant', col.lower()):
                colName = col

    if firstLast:
        reg['Participant'] = reg[firsts] + ' ' + reg[lasts]
    else:
        reg.rename(columns={colName : 'Participant'}, inplace=True)

    master = zoom.merge(reg, how="outer", on='Participant')

    master_display = master.to_html(index=False, classes="table table-hover table-light table-responsive")

    return render_template('display_merge.html', table=master_display, data=master.to_json(orient="split"))

    
