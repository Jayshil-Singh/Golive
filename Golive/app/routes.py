from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .models import MasterData, ServerStatus, GoLiveDate, Note, db
from .forms import MasterDataForm, ServerStatusForm, GoLiveDateForm, NoteForm
import os
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def dashboard():
    masterdata = MasterData.query.order_by(MasterData.date_received.desc()).all()
    server_status = ServerStatus.query.order_by(ServerStatus.date_ready.desc()).first()
    golive_dates = GoLiveDate.query.order_by(GoLiveDate.date.desc()).all()
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('dashboard.html', masterdata=masterdata, server_status=server_status, golive_dates=golive_dates, notes=notes)

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
