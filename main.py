from apscheduler.schedulers.background import BlockingScheduler

from analyze import AnalyzeNews

if __name__ == '__main__':
    analyzer = AnalyzeNews()
    
    scheduler = BlockingScheduler()
    scheduler.add_job(analyzer.run, trigger='interval', hours=1)
    
    print("[scheduler] Started with 1 hour interval")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("[scheduler] Process killed")