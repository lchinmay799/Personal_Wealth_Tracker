import json
from utils.scheduled_jobs import Jobs
from apscheduler.schedulers.background import BackgroundScheduler
from utils.generic_util import Redis

redis = Redis()

def post_fork(server, worker):
    acquire_lock=redis.redis_client.set('scheduler_lock', 1, nx=True, ex=60)
    if acquire_lock:
        jobs=Jobs()
        worker.scheduler=BackgroundScheduler()
        autoRenewJob=worker.scheduler.add_job(jobs.renewMaturedBankDeposits,'cron',hour=0,minute=5)
        addSipJob=worker.scheduler.add_job(jobs.addNewSip,'cron',hour=9,minute=35)
        worker.scheduler.start()

def worker_exit(server, worker):
    if hasattr(worker, 'scheduler') and worker.scheduler.running:
        worker.scheduler.shutdown(wait=True)
        redis.redis_client.delete('scheduler_lock')