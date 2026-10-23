import pandas as pd
from pathlib import Path
raw=Path('data/raw')
dfs=[pd.read_csv(raw/x) for x in ['at_urban.csv','at_rural.csv','at_district.csv']]
df=pd.concat(dfs,ignore_index=True)
rec=df[df.device_received==1]
print('Combined rows:',len(df))
print('Device recipients:',len(rec))
print('Abandoned:',int(rec.device_abandoned.sum()))
print('Continued:',int((rec.device_abandoned==0).sum()))
print('Columns:',len(df.columns))
