from nmapui import app
from nmapui.models import NmapTask, NmapReportDiffer, Contact, AddressDetail, Address
from nmapui.models import NmapReportMeta
from nmapui.tasks import celery_nmap_scan
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask.ext.login import login_required, current_user
from celery.states import READY_STATES
import json
from nmapui.celeryconfig import CELERY_TASK_EXPIRES
import datetime

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
            comment = ""

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
        """
        _celery_task = celery_nmap_scan.delay(targets=str(targets),
                                              options=str(options),
                                              expires=CELERY_TASK_EXPIRES,
                                              countdown=120)
        """

        """ use either eta OR countdown! """

        _celery_task = celery_nmap_scan.apply_async(eta=datetime.timedelta(seconds=10),
                                                    expires=CELERY_TASK_EXPIRES,
                                                    kwargs={'targets': str(targets),
                                                            'options': str(options)})

        NmapTask.add(user=current_user,
                     task_id=_celery_task.id,
                     comment=comment)

        return redirect(url_for('nmap.nmap_tasks'))

    _nmap_tasks = NmapTask.find(user_id=current_user.id)
    return render_template('nmap_tasks.html', tasks=_nmap_tasks)


@appmodule.route('/tasks/<int:page>')
@login_required
def nmap_tasks_paged(page=1):
    abort(404)


@appmodule.route('/jsontasks', methods=['GET', 'POST'])
@login_required
def nmap_tasks_json():
    _nmap_tasks = NmapTask.find(user_id=current_user.id)

    _jtarray = []
    for _ntask in _nmap_tasks:
        tdict = {'id': _ntask.task_id,
                 'status': _ntask.async_result.status,
                 'ready': 0}
        if _ntask.async_result.result and 'done' in _ntask.async_result.result:
            tdict.update({'progress': float(_ntask.async_result.result['done'])})
        elif _ntask.async_result.result and 'report' in _ntask.async_result.result:
            tdict.update({'progress': 100})
        else:
            tdict.update({'progress': 0})
        if _ntask.async_result.status in READY_STATES:
            tdict.update({'ready': 1})
        _jtarray.append(tdict)

    return json.dumps(_jtarray)


@appmodule.route('/task/stop/<task_id>')
@login_required
def nmap_task_stop(task_id):
    """
    _nmap_task = NmapTask.get(task_id)
    if _nmap_task is None:
        flash("There is no entry for task_id: " + task_id, 'info')
        return redirect(url_for('nmap.nmap_tasks'))

    NmapTask.stop_task_by_id(task_id=task_id)
    """
    flash("Sorry.. This feature is not implemented", 'danger')
    return redirect(url_for('nmap.nmap_tasks'))

    """
    if NmapTask.stop_task_by_id(task_id=task_id):
        flash("Stopped task: " + task_id, 'success')
        return redirect(url_for('nmap.nmap_tasks'))

    else:
        flash("Stop failed?! for task_id: " + task_id, 'danger')
        return redirect(url_for('nmap.nmap_tasks'))
    """


@appmodule.route('/task/delete/<task_id>')
@login_required
def nmap_task_delete(task_id):
    _nmap_task = NmapTask.get(task_id)

    if _nmap_task is None:
        flash("There is no entry for task_id: " + task_id, 'info')
        return redirect(url_for('nmap.nmap_tasks'))

    if NmapTask.remove_task_by_id(task_id=task_id):
        flash("Deleted entry for task_id: " + task_id, 'success')
        return redirect(url_for('nmap.nmap_tasks'))

    else:
        flash("Delete failed. Entry might still be in Celery cache but is \
              already deleted from Database. Task_id: " + task_id, 'danger')
        return redirect(url_for('nmap.nmap_tasks'))


@appmodule.route('/report/<report_id>')
@login_required
def nmap_report(report_id):
    _report = None
    if report_id is not None:
        try:
            int(report_id)
            _report = NmapReportMeta.get_report(report_id=report_id)
        except:
            _report = NmapTask.get_report(task_id=report_id)

    return render_template('nmap_report.html', report=_report)


@appmodule.route('/reports')
@appmodule.route('/reports/')
@login_required
def nmap_reports():
    return redirect("/nmap/reports/1")


@appmodule.route('/reports/<int:page>')
@login_required
def nmap_reports_paged(page=1):
    _meta_all_page = NmapReportMeta.query.paginate(page,
                                                   app.config["ITEMS_PER_PAGE"])
    _nmap_report_all = NmapReportMeta.getall_reports()

    return render_template('nmap_reports.html',
                           meta_all_page=_meta_all_page,
                           reports=_nmap_report_all)


@appmodule.route('/compare', methods=['GET', 'POST'])
@login_required
def nmap_compare():
    """no pagination needed!"""
    if request.method == "POST":
        selected_reports = request.form.getlist('report_meta.id')
        if len(selected_reports) != 2:
            flash('Please select exactly two reports.', 'danger')
            #_nmap_tasks = NmapTask.find(user_id=current_user.id)
            _nmap_report_meta_all = NmapReportMeta.get_report_meta()
            return render_template('nmap_compare_select.html',
                                   nmap_report_meta_all=_nmap_report_meta_all)
        else:
            old=NmapReportMeta.get_report(report_id=selected_reports[0])
            new=NmapReportMeta.get_report(report_id=selected_reports[1])
            nd = NmapReportDiffer(old_report=old, new_report=new)

            return render_template('nmap_compare.html',
                                   reports_list=selected_reports,
                                   changed=nd.changed,
                                   added=nd.added,
                                   removed=nd.removed)
    else:
        #_nmap_tasks = NmapTask.find(user_id=current_user.id)
        _nmap_report_meta_all = NmapReportMeta.get_report_meta()
        return render_template('nmap_compare_select.html', nmap_report_meta_all=_nmap_report_meta_all)


@appmodule.route('/db')
@login_required
def nmap_database():
    Address.discover_from_reports()

    ad = AddressDetail.query.get(4)
    #ad = AddressDetail.query.get_or_404(4) # default 404 page

    return render_template('nmap_database.html', ad=ad)


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


@appmodule.route("/profile")
@login_required
def profile():
    return render_template("nmap_profile.html")

