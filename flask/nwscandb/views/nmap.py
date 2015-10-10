from nwscandb import app
from nwscandb.celeryconfig import CELERY_TASK_EXPIRES
from nwscandb.models import NmapTask, NmapReportDiffer, Contact, AddressDetail, Address
from nwscandb.models import SubNmapReport, NmapReportMeta
from nwscandb.tasks import celery_nmap_scan
from flask import Blueprint, render_template, request, redirect, url_for
from flask import flash, abort, Response
from flask.ext.login import login_required, current_user
from celery.states import READY_STATES
import json
import datetime

from functools import wraps

from xlsx import Workbook

appmodule = Blueprint('nmap', __name__, url_prefix='/nmap')


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/basic_auth')
@requires_auth
def basic_auth():
    return render_template('secret_page.html')


@appmodule.route('/')
@login_required
def index():
    return render_template('nmap_index.html')


@appmodule.route('/scan')
@login_required
def scan():
    return render_template('nmap_scan.html')


@appmodule.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
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

        if 'run_now' in request.form:
            run_now = True
        else:
            run_now = False

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

        """ use either eta OR countdown! """
        _c_eta = datetime.datetime.utcnow() + datetime.timedelta(seconds=0)
        _c_exp = datetime.datetime.utcnow() + CELERY_TASK_EXPIRES
        _celery_task = celery_nmap_scan.apply_async(eta=_c_eta,
                                                    expires=_c_exp,
                                                    kwargs={'targets': str(targets),
                                                            'options': str(options)})
        NmapTask.add(user=current_user,
                     task_id=_celery_task.id,
                     comment=comment)

        return redirect(url_for('nmap.tasks'))

    _nmap_tasks = NmapTask.find(user_id=current_user.id)
    return render_template('nmap_tasks.html', tasks=_nmap_tasks)


@appmodule.route('/tasks/<int:page>')
@login_required
def tasks_paged(page=1):
    abort(404)


@appmodule.route('/jsontasks', methods=['GET', 'POST'])
@login_required
def tasks_json():
    _nmap_tasks = NmapTask.find(user_id=current_user.id)

    _jtarray = []
    for _ntask in _nmap_tasks:
        tdict = {'id': _ntask.task_id,
                'status': _ntask.completed_status,
                'ready': 0}
        if _ntask.completed == 1:
            tdict.update({'status': _ntask.completed_status})
            tdict.update({'progress': 100})
            tdict.update({'ready': 1})
            _jtarray.append(tdict)
        else:
            if _ntask.async_result.result and 'done' in _ntask.async_result.result:
                tdict.update({'progress': float(_ntask.async_result.result['done'])})
            elif _ntask.async_result.result and 'report' in _ntask.async_result.result:
                tdict.update({'progress': 100})
            else:
                tdict.update({'progress': 0})
            if _ntask.completed_status in READY_STATES:
                tdict.update({'ready': 1})
            _jtarray.append(tdict)

    return json.dumps(_jtarray)


@appmodule.route('/task/stop/<task_id>')
@login_required
def task_stop(task_id):
    """
    _nmap_task = NmapTask.get(task_id)
    if _nmap_task is None:
        flash("There is no entry for task_id: " + task_id, 'info')
        return redirect(url_for('nmap.tasks'))

    NmapTask.stop_task_by_id(task_id=task_id)
    """

    try:
        _nmap_task = NmapTask.get_by_task_id(task_id=task_id)
    except Exception as e:
        flash(str(e), "warning")
        return redirect(url_for("nmap.tasks"))

    if _nmap_task.completed == 1:
        flash("Can not stop tasks that are already finished.", 'info')
        return redirect(url_for('nmap.tasks'))

    flash("Sorry.. This feature is not (yet?!) implemented", 'danger')
    return redirect(url_for('nmap.tasks'))

    """
    if NmapTask.stop_task_by_id(task_id=task_id):
        flash("Stopped task: " + task_id, 'success')
        return redirect(url_for('nmap.tasks'))

    else:
        flash("Stop failed?! for task_id: " + task_id, 'danger')
        return redirect(url_for('nmap.tasks'))
    """


@appmodule.route('/task/delete/<task_id>')
@login_required
def task_delete(task_id):
    """task delete"""

    try:
        _nmap_task = NmapTask.get_by_task_id(task_id=task_id)
    except Exception as e:
        flash(str(e), "warning")
        return redirect(url_for("nmap.tasks"))

    if _nmap_task is None:
        flash("There is no entry for task_id: " + task_id, "info")
        return redirect(url_for("nmap.tasks"))

    if _nmap_task.delete():
        flash("Deleted entry for task_id: " + task_id, "success")
        return redirect(url_for("nmap.tasks"))
    else:
        flash("Delete failed. Task_id: " + task_id, "danger")
        return redirect(url_for("nmap.tasks"))


@appmodule.route('/report/<int:report_id>')
@login_required
def report(report_id):
    _report = SubNmapReport.get_report(report_id=report_id)
    if _report:
        return render_template("nmap_report.html", report=_report)
    else:
        abort(404)


@appmodule.route('/report/task_id/<task_id>')
@login_required
def report_task_id(task_id):

    """
    _report = NmapTask.get_report(task_id=task_id)
    """
    _report_id = NmapReportMeta.get_report_id_by_task_id(task_id=task_id)
    print _report_id
    _report = SubNmapReport.get_report(report_id=_report_id)
    return render_template("nmap_report.html", report=_report)


@appmodule.route('/reports')
@appmodule.route('/reports/')
@login_required
def reports():
    return redirect("/nmap/reports/1")


@appmodule.route('/reports/<int:page>')
@login_required
def reports_paged(page=1):
    """reports_paged view """

    _query = NmapReportMeta.query
    _items_per_page = app.config["ITEMS_PER_PAGE"]
    _items_paged = _query.paginate(page, _items_per_page)

    # special:
    _nmap_report_all = SubNmapReport.get_all_reports()

    return render_template('nmap_reports.html',
                           items_paged=_items_paged,
                           endpoint=request.endpoint,
                           reports=_nmap_report_all)


@appmodule.route('/address')
@appmodule.route('/addresses/')
@login_required
def addresses():
    return redirect("/nmap/addresses/1")


@appmodule.route('/addresses/<int:page>')
@login_required
def addresses_paged(page=1):
    _address_detail_all_page = AddressDetail.query.order_by("ip_address").paginate(page,
                                                     app.config["ITEMS_PER_PAGE"])

    return render_template('nmap_addresses.html',
                           address_detail_all_page=_address_detail_all_page)


@appmodule.route('/compare', methods=['GET', 'POST'])
@login_required
def compare():
    """no pagination needed!"""
    if request.method == "POST":
        selected_reports = request.form.getlist('report_meta.id')
        if len(selected_reports) != 2:
            flash('Please select exactly two reports.', 'danger')
            _nmap_report_meta_all = NmapReportMeta.get_report_meta()
            return render_template('nmap_compare_select.html',
                                   nmap_report_meta_all=_nmap_report_meta_all)
        else:
            old = SubNmapReport.get_report(report_id=selected_reports[0])
            new = SubNmapReport.get_report(report_id=selected_reports[1])
            nd = NmapReportDiffer(old_report=old, new_report=new)

            return render_template('nmap_compare.html',
                                   reports_list=selected_reports,
                                   changed=nd.changed,
                                   added=nd.added,
                                   removed=nd.removed)
    else:
        _nmap_report_meta_all = NmapReportMeta.get_report_meta()
        return render_template('nmap_compare_select.html',
                               nmap_report_meta_all=_nmap_report_meta_all)


@appmodule.route('/db')
@login_required
def database():
    Address.discover_from_reports()

    ad = AddressDetail.query.get(4)
    #ad = AddressDetail.query.get_or_404(4) # default 404 page

    return render_template('nmap_database.html', ad=ad)


@appmodule.route('/export')
@login_required
def export():
    return render_template('nmap_export.html')


@appmodule.route('/import', methods=['GET', 'POST'])
@login_required
def importer():
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




