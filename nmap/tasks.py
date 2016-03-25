# import of celery
from celery.decorators import task

# wo denn?
from nwscandb import celery_app
from celery import current_task

# NWScanDB Classes and library Classes
from models import NmapReportMeta
from libnmap.process import NmapProcess


@task(name="tasks.nmap_scan")
def celery_nmap_scan(targets, options):
    """celery_nmap_scan task"""

    def status_callback(nmapscan=None):
        """status callback"""
        try:
            celery_nmap_scan.update_state(state="PROGRESS",
                                          meta={"progress": nmapscan.progress,
                                                "ready": 0,
                                                "etc": nmapscan.etc})

        except Exception as e:
            print("status_callback error: " + str(e))

    # scan is not yet finished (or even started).
    # But I need to do this before the NmapProcess is started because
    # otherwise other tasks might be queued in front of this!
    _nmap_task_id = celery_nmap_scan.request.id
    store_nmap_report_meta.apply_async(kwargs={'nmap_task_id': str(_nmap_task_id)})

    print("tasks.py: Targets and Options")
    print(targets)
    print(options)

    nm = NmapProcess(targets, options, event_callback=status_callback)
    rc = nm.sudo_run()

    if rc == 0 and nm.stdout:
        r = nm.stdout

    else:
        r = None

    return r


def get_scan_task_result(nmap_task_id):
    """get scan task result"""

    # If you have a task_id, this is how you query that task
    task = celery_nmap_scan.AsyncResult(nmap_task_id)
    try:
        if task.ready():
            return task.result
        else:
            return None
    except Exception as err:
        print("Something went wrong... " + err)
        return False


def get_scan_task_status(nmap_task_id):
    """get scan task status"""

    # If you have a task_id, this is how you query that task
    task = celery_nmap_scan.AsyncResult(nmap_task_id)
    _status = task.status

    if _status == "PENDING":
        return {'id': str(nmap_task_id),
                'status': _status,
                'progress': 0,
                'ready': 0,
                'etc': 0}
    else:
        try:
            _etc = task.info['etc']
        except:
            _etc = 0

        _progress = 0
        _ready = 0

        if _status == u'SUCCESS':
            _progress = 100
            _ready = 1
        elif _status == u'FAILURE':
            _progress = 0
            _ready = 1
        elif _status == 'PROGRESS':
            _etc = task.info['etc']
            _progress = task.info['progress']

        return {'id': str(nmap_task_id),
                'status': _status,
                'progress': _progress,
                'ready': _ready,
                'etc': _etc}


@task(name="tasks.store_nmap_report_meta")
def store_nmap_report_meta(nmap_task_id=None):
    """
        after scan is finished get scan report from celery backend (db)
        and insert into db. Save both an instance of NmapReportMeta and
        NmapReport (TODO: or SubNmapReport ?!)

    """

    # print("Trying to store NmapReportMeta for TaskID: " + nmap_task_id)
    res = NmapReportMeta.save_report(task_id=nmap_task_id)

    # discover and save nw service objects
    res.discover_network_services()

    """ TODO do I need this? For celery table?
        How do I cleanly communicate result back to celery
    """

    """ TODO 2016-03-22 (RH) disabled
    if res is True:
        return {"rc": 0}
    else:
        return {"rc": 1}

    """

    return {"rc": 0}
