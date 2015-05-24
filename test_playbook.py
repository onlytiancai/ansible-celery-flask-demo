from ansible.playbook import PlayBook
from ansible.inventory import Inventory
from ansible import callbacks
from ansible import utils


class PlaybookRunnerCallbacks(callbacks.PlaybookRunnerCallbacks):
    def __init__(self, task, stats, verbose=None):
        super(PlaybookRunnerCallbacks, self).__init__(stats, verbose)
        self.celery_task = task

    def on_ok(self, host, host_result):
        super(PlaybookRunnerCallbacks, self).on_ok(host, host_result)
        self.celery_task.logs.append("ok:[%s]" % host)
        self.celery_task.update_state(state='PROGRESS', meta={'msg': self.celery_task.logs})

    def on_unreachable(self, host, results):
        super(PlaybookRunnerCallbacks, self).on_unreachable(host, results)
        self.celery_task.logs.append("unreachable:[%s] %s" % (host, results))
        self.celery_task.update_state(state='FAILURE', meta={'msg': self.celery_task.logs})

    def on_failed(self, host, results, ignore_errors=False):
        super(PlaybookRunnerCallbacks, self).on_failed(host, results, ignore_errors)
        self.celery_task.logs.append("failed:[%s] %s" % (host, results))
        self.celery_task.update_state(state='FAILURE', meta={'msg': self.celery_task.logs})


class PlaybookCallbacks(callbacks.PlaybookCallbacks):
    def __init__(self, task, verbose=False):
        super(PlaybookCallbacks, self).__init__(verbose);
        self.celery_task = task

    def on_setup(self):
        super(PlaybookCallbacks, self).on_setup()
        self.celery_task.logs.append("GATHERING FACTS")
        self.celery_task.update_state(state='PROGRESS', meta={'msg': self.celery_task.logs})

    def on_task_start(self, name, is_conditional):
        super(PlaybookCallbacks, self).on_task_start(name, is_conditional)
        self.celery_task.logs.append("TASK: [%s]" % name)
        self.celery_task.update_state(state='PROGRESS', meta={'msg': self.celery_task.logs})


hostfile = './hosts.py'
inventory = Inventory(hostfile) 
stats = callbacks.AggregateStats()
vars = {"hosts":['127.0.0.1']}


def get_pb(task):
    if task:
        runner_cb = PlaybookRunnerCallbacks(task, stats, verbose=utils.VERBOSITY)
        playbook_cb = PlaybookCallbacks(task, verbose=utils.VERBOSITY)
    else:
        runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)
        playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)

    pb = PlayBook(playbook='./test.yaml', 
                  callbacks=playbook_cb,
                  runner_callbacks=runner_cb,
                  stats=stats,
                  inventory=inventory,
                  extra_vars=vars,
                  )
    return pb

if __name__ == '__main__':
    get_pb(None).run()
