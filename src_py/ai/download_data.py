import kagglehub
import shutil
import os

dest = r'C:\Users\Naveen S\OneDrive\Documents\vit\src_py\ai\data'

# Download Credit Risk Dataset (32,581 records, 12 features)
print('Downloading Credit Risk Dataset...')
path1 = kagglehub.dataset_download('laotse/credit-risk-dataset')
src1 = os.path.join(path1, 'credit_risk_dataset.csv')
dst1 = os.path.join(dest, 'credit_risk.csv')
shutil.copy(src1, dst1)
size1 = os.path.getsize(dst1) / 1024
print(f'  Credit Risk: {size1:.1f} KB')

# Download Loan Default Dataset (255,347 records, 18 features)
print('Downloading Loan Default Dataset...')
path2 = kagglehub.dataset_download('yasserh/loan-default-dataset')
src2 = os.path.join(path2, 'Loan_Default.csv')
dst2 = os.path.join(dest, 'loan_default.csv')
shutil.copy(src2, dst2)
size2 = os.path.getsize(dst2) / 1024
print(f'  Loan Default: {size2:.1f} KB')

# Download Credit Card Default (30K records, 23 features) - UCI
print('Downloading UCI Credit Card Default...')
path3 = kagglehub.dataset_download('uciml/default-of-credit-card-clients-taiwan')
src3 = os.path.join(path3, 'UCI_Credit_Card.csv')
dst3 = os.path.join(dest, 'credit_card_default.csv')
shutil.copy(src3, dst3)
size3 = os.path.getsize(dst3) / 1024
print(f'  Credit Card Default: {size3:.1f} KB')

print('\nAll datasets downloaded!')
for f in os.listdir(dest):
    fp = os.path.join(dest, f)
    print(f'  {f}: {os.path.getsize(fp) / 1024:.1f} KB')
