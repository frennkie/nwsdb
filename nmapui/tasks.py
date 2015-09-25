from celery import Task, task, current_task
from libnmap.process import NmapProcess
import json
from libnmap.plugins.sql import NmapSqlPlugin
from libnmap.plugins.backendpluginFactory import BackendPluginFactory
from libnmap.objects.report import NmapReport
from nmapui.models import NmapTask, Address
from nmapui.config import LIBNMAP_DB_URI
from nmapui.celeryapp import celery_pipe as celery


@task(name="tasks.nmap_scan")
def celery_nmap_scan(targets, options):
    def status_callback(nmapscan=None, data=""):
        current_task.update_state(state="PROGRESS",
                                  meta={"done": nmapscan.progress,
                                        "etc": nmapscan.etc})

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
    """ after scan is finished get report for scan from celery backend (db)
        and insert into db """
    _report = NmapTask.get_report(task_id=task_id)

    try:
        db = BackendPluginFactory.create(plugin_name="sql",
                                         url=LIBNMAP_DB_URI,
                                         echo=False)

        _id = _report.save(db)
        r = Address.discover_from_report(report_id=_id)

        return {"rc": 0}

    except Exception as e:
        print e
        return {"rc": 1}


# Class for a task
@task(name="tasks.cleanup")
class CleanupTask(Task):
    """
    Examples:

    >>> from nmapui.tasks import CleanupTask
    >>> result = CleanupTask.delay()

    """

    # A Task instance got a backend property

    def run(self,**kwargs):
        """ Running method of the task """
        # Cleanup here
        self.backend.cleanup()
