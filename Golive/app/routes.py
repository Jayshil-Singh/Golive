from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, make_response, send_file, render_template_string
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import MasterData, ServerStatus, GoLiveDate, Note, db, User
from .forms import MasterDataForm, ServerStatusForm, GoLiveDateForm, NoteForm
import os
from datetime import datetime
import pandas as pd
from io import BytesIO
from weasyprint import HTML

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def dashboard():
    masterdata = MasterData.query.order_by(MasterData.date_received.desc()).all()
    server_status = ServerStatus.query.order_by(ServerStatus.date_ready.desc()).first()
    golive_dates = GoLiveDate.query.order_by(GoLiveDate.date.desc()).all()
    notes = Note.query.order_by(Note.created_at.desc()).all()

    # Progress calculation
    steps = [
        {'name': 'Master Data Received', 'done': bool(masterdata)},
        {'name': 'Server Ready', 'done': bool(server_status)},
        {'name': 'Go Live Date Set', 'done': bool(golive_dates)},
    ]
    progress = int(100 * sum(step['done'] for step in steps) / len(steps))

    # Timeline data with event type and details
    timeline = []
    if masterdata:
        timeline.append({
            'id': 1,
            'content': '<i class="bi bi-file-earmark-arrow-up"></i> Master Data',
            'start': masterdata[0].date_received.strftime('%Y-%m-%d'),
            'title': f"Master Data received: {masterdata[0].filename} ({masterdata[0].filetype})"
        })
    if server_status:
        timeline.append({
            'id': 2,
            'content': '<i class="bi bi-hdd-network"></i> Server Ready',
            'start': server_status.date_ready.strftime('%Y-%m-%d'),
            'title': f"Server ready on {server_status.date_ready.strftime('%Y-%m-%d')}"
        })
    for i, d in enumerate(golive_dates, start=3):
        timeline.append({
            'id': i,
            'content': '<i class="bi bi-flag"></i> Go Live',
            'start': d.date.strftime('%Y-%m-%d'),
            'title': f"Go Live scheduled: {d.date.strftime('%Y-%m-%d')}"
        })
    timeline = sorted(timeline, key=lambda x: x['start'])

    return render_template('dashboard.html', masterdata=masterdata, server_status=server_status, golive_dates=golive_dates, notes=notes, steps=steps, progress=progress, timeline=timeline)

@main.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_masterdata():
    form = MasterDataForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        filetype = filename.split('.')[-1].lower()
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        masterdata = MasterData(filename=filename, filetype=filetype, uploaded_by=current_user.id)
        db.session.add(masterdata)
        db.session.commit()
        flash('Master data file uploaded successfully.')
        return redirect(url_for('main.dashboard'))
    return render_template('upload.html', form=form)

@main.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main.route('/server_status', methods=['GET', 'POST'])
@login_required
def server_status():
    form = ServerStatusForm()
    if form.validate_on_submit():
        status = ServerStatus(date_ready=form.date_ready.data, set_by=current_user.id)
        db.session.add(status)
        db.session.commit()
        flash('Server ready date set.')
        return redirect(url_for('main.dashboard'))
    return render_template('server_status.html', form=form)

@main.route('/golive_dates', methods=['GET', 'POST'])
@login_required
def golive_dates():
    form = GoLiveDateForm()
    if form.validate_on_submit():
        golive = GoLiveDate(date=form.date.data, added_by=current_user.id)
        db.session.add(golive)
        db.session.commit()
        flash('Go live date added.')
        return redirect(url_for('main.golive_dates'))
    dates = GoLiveDate.query.order_by(GoLiveDate.date.desc()).all()
    return render_template('golive_dates.html', form=form, dates=dates)

@main.route('/golive_dates/delete/<int:id>', methods=['POST'])
@login_required
def delete_golive_date(id):
    date = GoLiveDate.query.get_or_404(id)
    db.session.delete(date)
    db.session.commit()
    flash('Go live date removed.')
    return redirect(url_for('main.golive_dates'))

@main.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    form = NoteForm()
    if form.validate_on_submit():
        note = Note(text=form.text.data, user_id=current_user.id)
        db.session.add(note)
        db.session.commit()
        flash('Note added.')
        return redirect(url_for('main.notes'))
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('notes.html', form=form, notes=notes)

@main.route('/report/pdf')
@login_required
def report_pdf():
    # Gather data
    masterdata = MasterData.query.order_by(MasterData.date_received.desc()).all()
    server_status = ServerStatus.query.order_by(ServerStatus.date_ready.desc()).first()
    golive_dates = GoLiveDate.query.order_by(GoLiveDate.date.desc()).all()
    notes = Note.query.order_by(Note.created_at.desc()).all()
    users = {u.id: u.username for u in User.query.all()}
    steps = [
        {'name': 'Master Data Received', 'done': bool(masterdata)},
        {'name': 'Server Ready', 'done': bool(server_status)},
        {'name': 'Go Live Date Set', 'done': bool(golive_dates)},
    ]
    progress = int(100 * sum(step['done'] for step in steps) / len(steps))
    timeline = []
    if masterdata:
        timeline.append({'label': 'Master Data', 'date': masterdata[0].date_received.strftime('%Y-%m-%d')})
    if server_status:
        timeline.append({'label': 'Server Ready', 'date': server_status.date_ready.strftime('%Y-%m-%d')})
    for d in golive_dates:
        timeline.append({'label': 'Go Live', 'date': d.date.strftime('%Y-%m-%d')})
    timeline = sorted(timeline, key=lambda x: x['date'])
    # Summary stats
    stats = {
        'total_files': len(masterdata),
        'total_golive': len(golive_dates),
        'total_notes': len(notes),
        'server_ready': bool(server_status),
        'days_to_golive': (golive_dates[0].date - masterdata[0].date_received).days if masterdata and golive_dates else None
    }
    # Chart images (QuickChart.io)
    progress_chart_url = (
        'https://quickchart.io/chart?c='
        '{"type":"doughnut","data":{"labels":["Complete","Incomplete"],"datasets":[{"data":[%d,%d],"backgroundColor":["#27ae60","#e0e0e0"]}]},'
        '"options":{"plugins":{"legend":{"display":false}},"cutout": "80%%","elements":{"center":{"text":"%d%%"}}}}'
        % (progress, 100 - progress, progress)
    )
    timeline_labels = [e['label'] for e in timeline]
    timeline_chart_url = (
        'https://quickchart.io/chart?c='
        '{"type":"bar","data":{"labels":%s,"datasets":[{"label":"Event Date","data":[%s],"backgroundColor":"#2980b9"}]}}'
        % (timeline_labels, ','.join(str(i+1) for i in range(len(timeline_labels))))
    )
    from datetime import datetime as dt
    report_date = dt.now().strftime('%Y-%m-%d %H:%M')
    # Render HTML report
    html = render_template('report.html', masterdata=masterdata, server_status=server_status, golive_dates=golive_dates, notes=notes, steps=steps, progress=progress, timeline=timeline, users=users, stats=stats, progress_chart_url=progress_chart_url, timeline_chart_url=timeline_chart_url, report_date=report_date)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=golive_report.pdf'
    return response

@main.route('/report/excel')
@login_required
def report_excel():
    # Gather data
    masterdata = MasterData.query.order_by(MasterData.date_received.desc()).all()
    server_status = ServerStatus.query.order_by(ServerStatus.date_ready.desc()).first()
    golive_dates = GoLiveDate.query.order_by(GoLiveDate.date.desc()).all()
    notes = Note.query.order_by(Note.created_at.desc()).all()
    # Prepare dataframes
    df_master = pd.DataFrame([{ 'File Name': m.filename, 'Type': m.filetype, 'Date Received': m.date_received, 'Uploaded By': m.uploaded_by } for m in masterdata])
    df_golive = pd.DataFrame([{ 'Go Live Date': d.date, 'Added By': d.added_by } for d in golive_dates])
    df_notes = pd.DataFrame([{ 'Note': n.text, 'Created At': n.created_at, 'User': n.user_id } for n in notes])
    df_server = pd.DataFrame([{ 'Server Ready Date': server_status.date_ready, 'Set By': server_status.set_by }] if server_status else [])
    # Write to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_master.to_excel(writer, index=False, sheet_name='Master Data')
        df_server.to_excel(writer, index=False, sheet_name='Server Status')
        df_golive.to_excel(writer, index=False, sheet_name='Go Live Dates')
        df_notes.to_excel(writer, index=False, sheet_name='Notes')
    output.seek(0)
    return send_file(output, download_name='golive_report.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
