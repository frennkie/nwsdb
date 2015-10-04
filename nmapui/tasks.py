from celery import Task, task, current_task
from nmapui.celeryapp import celery_pipe as celery
from libnmap.process import NmapProcess
from nmapui.models import NmapReportMeta


@task(name="tasks.nmap_scan")
def celery_nmap_scan(targets, options):
    def status_callback(nmapscan=None, data=""):
        print nmapscan
        print data
        try:
            current_task.update_state(state="PROGRESS",
                                      meta={"done": nmapscan.progress,
                                            "etc": nmapscan.etc})
        except Exception, e:
            print("status_callback error: " + e)

    nm = NmapProcess(targets, options, event_callback=status_callback)
    rc = nm.run()

    if rc == 0 and nm.stdout:
        r = nm.stdout

        # scan is finished. Now call task to insert Report into persistent db
        celery_nmap_store_report.delay(task_id=celery_nmap_scan.request.id)

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
    rc = report_meta.save_report(task_id=task_id)
    return {"rc": rc}


# Class for a task
class CleanupTask(Task):
    """
    Examples:

    >>> from nmapui.tasks import CleanupTask
    >>> result = CleanupTask.delay()

    """
    # do not store result in backend
    ignore_result = True

    def run(self, **kwargs):
        """ Run method of the class """
        # Cleanup here
        self.backend.cleanup()
