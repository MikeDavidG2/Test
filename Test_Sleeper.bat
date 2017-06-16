set sleeper=U:\grue\Scripts\GitHub\Test\Test_Sleeper.py
set update=U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\DEV\DEV_branch\Update_DPW_w_MasterData.py

Start /wait %sleeper% 09:16 0 U:\grue\Scripts\GitHub\DPW-Sci-Monitoring\DEV\Data\Logs\Sleeper_Log

Start /wait %update%