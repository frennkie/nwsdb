from celery import Task, task, current_task
from nwscandb.celeryapp import celery_pipe as celery
from libnmap.process import NmapProcess
from nwscandb.models import NmapReportMeta


@task(name="tasks.nmap_scan")
def celery_nmap_scan(targets, options):
    """celery_nmap_scan task"""

    def status_callback(nmapscan=None):
        """status callback"""
        try:
            current_task.update_state(state="PROGRESS",
                                      meta={"done": nmapscan.progress,
                                            "etc": nmapscan.etc})
        except Exception as e:
            print("status_callback error: " + str(e))

    # scan is not yet finished (or even started).
    # But I need to do this before the NmapProcess is started because
    # otherwise other tasks might be queued in front of this!
    celery_nmap_store_report.delay(task_id=celery_nmap_scan.request.id)

    nm = NmapProcess(targets, options, event_callback=status_callback)
    rc = nm.run()

    if rc == 0 and nm.stdout:
        r = nm.stdout

    else:
        r = None

    return {"rc": rc, "report": r}


@task(name="tasks.nmap_store_report")
def celery_nmap_store_report(task_id):
    """
        after scan is finished get report for scan from celery backend (db)
        and insert into db
    """

    report_meta = NmapReportMeta()
    res = report_meta.save_report(task_id=task_id)

    if res is True:
        return {"rc": 0}
    else:
        return {"rc": 1}


# Class for a task
class CleanupTask(Task):
    """
    Examples:

    >>> from nwscandb.tasks import CleanupTask
    >>> result = CleanupTask.delay()

    """
    # do not store result in backend
    ignore_result = True

    def run(self, **kwargs):
        """ Run method of the class """
        # Cleanup here
        self.backend.cleanup()
