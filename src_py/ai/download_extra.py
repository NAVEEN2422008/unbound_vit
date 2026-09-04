import urllib.request
import os

dest = r'C:\Users\Naveen S\OneDrive\Documents\vit\src_py\ai\data'

# German Credit from UCI (no auth needed)
url = 'https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data'
dst = os.path.join(dest, 'german_credit.csv')
print('Downloading German Credit from UCI...')
urllib.request.urlretrieve(url, dst)

# Add header
headers = ['checking_account', 'duration', 'credit_history', 'purpose', 'credit_amount',
           'savings', 'employment', 'installment_rate', 'personal_status', 'other_debtors',
           'residence', 'property', 'age', 'other_plans', 'housing', 'existing_credits',
           'job', 'dependents', 'telephone', 'foreign_worker', 'target']
with open(dst, 'r') as f:
    content = f.read()
with open(dst, 'w') as f:
    f.write(','.join(headers) + '\n' + content)

size = os.path.getsize(dst) / 1024
print(f'  German Credit: {size:.1f} KB')
print('\nAll datasets:')
for fn in os.listdir(dest):
    fp = os.path.join(dest, fn)
    print(f'  {fn}: {os.path.getsize(fp) / 1024:.1f} KB')
