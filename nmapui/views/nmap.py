from nmapui import app
from nmapui.models import NmapTask, NmapDiffer
from nmapui.tasks import celery_nmap_scan
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.ext.login import login_required, current_user
from celery.states import READY_STATES
import json

from xlsx import Workbook

appmodule = Blueprint('nmap', __name__, url_prefix='/nmap')

@appmodule.route('/')
@login_required
def nmap_index():
    return render_template('nmap_index.html')

@appmodule.route('/scan')
@login_required
def nmap_scan():
    return render_template('nmap_scan.html')

@appmodule.route('/tasks', methods=['GET', 'POST'])
@login_required
def nmap_tasks():
    scantypes = [ "-sT", "-sT", "-sS", "-sA", "-sW", "-sM",
            "-sN", "-sF", "-sX", "-sU" ]

    if request.method == "POST":
        if 'targets' in request.form:
            targets = request.form["targets"]
        else:
            abort(401)

        if 'comment' in request.form:
            comment = request.form["comment"]
        else:
            pass

        options = ""
        scani = int(request.form['scantype']) if 'scantype' in request.form else 0
        if 'ports' in request.form and len(request.form['ports']):
            portlist = "-p " + request.form['ports']
        else:
            portlist = ''
        noping = '-P0' if 'noping' in request.form else ''
        osdetect = "-O" if 'os' in request.form else ''
        bannerdetect = "-sV" if 'banner' in request.form else ''
        options = "{0} {1} {2} {3} {4}".format(scantypes[scani],
                                                  portlist,
                                                  noping,
                                                  osdetect,
                                                  bannerdetect)
        _celery_task = celery_nmap_scan.delay(targets=str(targets),
                                              options=str(options))
        NmapTask.add(user_id=current_user.id,
                     task_id=_celery_task.id,
                     comment=comment)

        return redirect(url_for('nmap.nmap_tasks'))

    _nmap_tasks = NmapTask.find(user_id=current_user.id)

    return render_template('nmap_tasks.html', tasks=_nmap_tasks)

@appmodule.route('/jsontasks', methods=['GET', 'POST'])
@login_required
def nmap_tasks_json():
    _nmap_tasks = NmapTask.find(user_id=current_user.id)
    _jtarray = []
    for _ntask in _nmap_tasks:
        tdict = {'id': _ntask['task_id'].id,
                 'status': _ntask['task_id'].status,
                 'ready': 0}
        if _ntask['task_id'].result and 'done' in _ntask['task_id'].result:
            tdict.update({'progress': float(_ntask['task_id'].result['done'])})
        elif _ntask['task_id'].result and 'report' in _ntask['task_id'].result:
            tdict.update({'progress': 100})
        else:
            tdict.update({'progress': 0})
        if _ntask['task_id'].status in READY_STATES:
            tdict.update({'ready': 1})
        _jtarray.append(tdict)

    return json.dumps(_jtarray)

@appmodule.route('/task/delete/<task_id>')
@login_required
def nmap_task_delete(task_id):
    if task_id is None:
        # TODO dead code?! How should task_id be None here?
        flash("Can not delete as no task id is given!", 'info')
        return redirect(url_for('nmap.nmap_tasks'))

    _nmap_task = NmapTask.get(task_id)
    if _nmap_task is None:
        flash("There is no entry for task_id: " + task_id, 'info')
        return redirect(url_for('nmap.nmap_tasks'))

    if 'report' not in _nmap_task:
        flash("Not yet finished?! task_id: " + task_id, 'info')
        return redirect(url_for('nmap.nmap_tasks'))

    if NmapTask.remove_task_by_id(task_id=task_id):
        flash("Deleted entry for task_id: " + task_id, 'success')
        return redirect(url_for('nmap.nmap_tasks'))

    else:
        flash("Delete failed?! for task_id: " + task_id, 'danger')
        return redirect(url_for('nmap.nmap_tasks'))

@appmodule.route('/report/<report_id>')
@login_required
def nmap_report(report_id):
    _report = None
    if report_id is not None:
        _report = NmapTask.get_report(task_id=report_id)
    return render_template('nmap_report.html', report=_report)

@appmodule.route('/compare', methods=['GET', 'POST'])
@login_required
def nmap_compare():
    if request.method == "POST":
        selected_tasks = request.form.getlist('task_id')
        if len(selected_tasks) != 2:
            flash('Please select exactly two reports.', 'danger')
            _nmap_tasks = NmapTask.find(user_id=current_user.id)
            return render_template('nmap_compare_select.html',
                                   tasks=_nmap_tasks)
        else:
            nd = NmapDiffer(old_report=NmapTask.get_report(task_id=selected_tasks[0]),
                            new_report=NmapTask.get_report(task_id=selected_tasks[1]))

            return render_template('nmap_compare.html',
                                   reports_list=selected_tasks,
                                   changed=nd.changed,
                                   added=nd.added,
                                   removed=nd.removed)
    else:
        _nmap_tasks = NmapTask.find(user_id=current_user.id)
        return render_template('nmap_compare_select.html', tasks=_nmap_tasks)

@appmodule.route('/db')
@login_required
def nmap_database():
    return render_template('nmap_database.html')

@appmodule.route('/export')
@login_required
def nmap_export():
    return render_template('nmap_export.html')

@appmodule.route('/import', methods=['GET', 'POST'])
@login_required
def nmap_import():
    if request.method == "POST":
        import_file = request.files['file']
        if import_file:
            foo = import_file.filename
            book = Workbook(import_file) #Open xlsx file
            sheets = []
            for sheet in book:
                    print sheet.name
                    sheets.append(sheet)
            content = import_file.read()
            #return render_template('nmap_import_result.html', foo=foo, content=content)
            return render_template('nmap_import_result.html', sheets=sheets)
        else:
            raise Exception("nmap_import failed")

    else:
        return render_template('nmap_import.html')

@appmodule.route('/test', methods=['GET', 'POST'])
#@login_required
def test():
    username = "{0}:{1} {2}".format(current_user.id, current_user.username, type(unicode(current_user.id)))
#    if request.method == 'POST':
#        username = request.args.get('username')
    return render_template('test.html', username=username)
