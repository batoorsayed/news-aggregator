import logging

import azure.functions as func

from src.main import main

app = func.FunctionApp()

@app.timer_trigger(schedule="0 0 2 * * *", arg_name="myTimer", run_on_startup=False,
              use_monitor=True) 
def daily_storeheadlines(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('The timer is past due!')
    else:
        logging.info('Python timer trigger function executed.')
        main()