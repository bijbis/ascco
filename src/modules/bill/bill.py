from datetime import datetime as dt
import csv
import pandas as pd
import numpy as np
from _globals import static_data, Quantity, Price, Amount, static_data_right
from datetime import date
from pdfgen import create_pdf


def label_weekday(row):
	return row['weekday'] in [5, 6]


def get_tariff_on_date_export(row):
	"""
	This handles only weekends
	"""
	if row['weekend']:
		return row[:'23:30'].apply(lambda each: float(each)) * 0.095
	else:
		return row[:'23:30'].apply(lambda each: float(each)) * 0.37


def get_tariff_on_date_import(row):
	"""
	This handles only weekends
	"""
	if row['weekend']:
		return row[:'23:30'].apply(lambda each: float(each)) * 0.095
	else:
		r = row[:'23:30'].apply(lambda each: float(each))
		a = r['00:00': '06:30'] * 0.095
		b = r['07:00': '21:00'] * 0.37
		c = r['21:30': '23:30'] * 0.095
		return a.append(b).append(c)


# ############################################################
temp_bill = []
temp_dates = []
with open('bill.csv', 'r') as billCSV:
	data = csv.reader(billCSV)
	takeValues = False
	for each in data:
		if each[0] == '100':
			continue
		elif each[0] == '200':
			if each[7] == 'KWH':
				takeValues = True
				if each[4] == 'B1':
					ty = 'export'
				else:
					ty = 'import'
			else:
				takeValues = False
		elif each[0] == '300' and takeValues:
			k = each[2: each.index('A')]
			k.append(ty)
			temp_bill.append(k)
			temp_dates.append(each[1])

# for each in temp_bill:
# 	print(each)
# 	print()

temp_cols = ['00:00', '00:30', '01:00', '01:30', '02:00', '02:30', '03:00', '03:30', '04:00', '04:30', '05:00', '05:30',
			'06:00', '06:30', '07:00', '07:30', '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
			'12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
			'18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00', '22:30', '23:00', '23:30', "Import_Export"]
billData = pd.DataFrame(temp_bill, index=temp_dates, columns=temp_cols)
billData.index = pd.to_datetime(billData.index)
billData['weekday'] = billData.index.weekday.values
billData['weekend'] = billData.apply(lambda row: label_weekday(row), axis=1)
import_data = billData[billData['Import_Export'] == 'import']
export_data = billData[billData['Import_Export'] == 'export']
# print(import_data.shape)
export_data = export_data[(export_data.index >= '2017/03/28') & (export_data.index <= '2017/04/24')]
import_data = import_data[(import_data.index >= '2017/03/28') & (import_data.index <= '2017/04/24')]
export_tariff = export_data.apply(lambda row: get_tariff_on_date_export(row), axis=1)
import_tariff = import_data.apply(lambda row: get_tariff_on_date_import(row), axis=1)
tariff1 = (import_tariff.sum(axis=1) - export_tariff.sum(axis=1)).sum()

t2 = []
for each in import_data.index.values:
	if dt.strptime(str(each).split('T')[0], '%Y-%m-%d').weekday() in [5, 6]:
		t2.append(167.0 * 0.095)
	else:
		t2.append(167.0 * 0.37)
tarrif2 = sum(t2) + tariff1
dfb = import_tariff.index.values[-1] - import_tariff.index.values[0]
days_for_bill = dfb.astype('timedelta64[D]') / np.timedelta64(1, 'D')

weekday_import_data = import_data[import_data.weekend == False]
op1 = pd.concat([weekday_import_data.loc[:, '00:00': '06:30'], weekday_import_data.loc[:, '21:30': '23:30']], axis=1).applymap(lambda e: float(e)).values.sum()
op2 = import_data[import_data.weekend == True].loc[:, :'23:30'].applymap(lambda e: float(e)).values.sum()
weekday_export_data = export_data[export_data.weekend == False]
op3 = pd.concat([weekday_export_data.loc[:, '00:00': '06:30'], weekday_export_data.loc[:, '21:30': '23:30']], axis=1).applymap(lambda e: float(e)).values.sum()
op4 = export_data[export_data.weekend == True].loc[:, :'23:30'].applymap(lambda e: float(e)).values.sum()
off_peak_energy = (op1 + op2) - (op3 + op4)

peak_energy = import_data[import_data.weekend == False].loc[:, '07:00':'21:00'].applymap(lambda e: float(e)).values.sum()
peak_energy -= export_data[export_data.weekend == False].loc[:, '07:00':'21:00'].applymap(lambda e: float(e)).values.sum()
off_peak_energy += import_data[import_data.weekend == True].shape[0] * 167
peak_energy += import_data[import_data.weekend == False].shape[0] * 167
# print(off_peak_energy, peak_energy)

Quantity[0] = '%.2f' % (float(off_peak_energy)) + " kWH"
Quantity[1] = '%.2f' % (float(peak_energy)) + " kWH"
Quantity[2] = str(int(days_for_bill)) + " day(s)"
ts1 = pd.to_datetime(str(import_tariff.index.values[0]))
ts2 = pd.to_datetime(str(import_tariff.index.values[-1]))
static_data[5] = ts1.strftime('%d/%m/%Y') + " to " + ts2.strftime('%d/%m/%Y')
static_data[6] = str(int(days_for_bill)) + " day(s)"
static_data[7] = '%.2f' % (float(peak_energy + off_peak_energy)) + " kWH"
# print(static_data)
Price[0] = '9.50 c/kWH'
Price[1] = '37.00 c/kwH'
Amount[0] = "$" + '%.2f' % (float(off_peak_energy * 0.095))  # Off peak charges
Amount[1] = "$" + '%.2f' % (float(peak_energy * 0.37))  # Peak charges
Amount[2] = "$" + str(float(days_for_bill) * 3.51)  # Other charges
Amount[3] = "$" + '%.2f' % (float(off_peak_energy * 0.095) + float(peak_energy * 0.37) + float(days_for_bill) * 3.51)  # Sub total
Amount[4] = "$" + '%.2f' % ((float(off_peak_energy * 0.095) + float(peak_energy * 0.37) + float(days_for_bill) * 3.51) * 0.1)  # GST at 10%
# print()
Amount[5] = "$" + str(float(Amount[3].split('$')[-1]) + float(Amount[4].split('$')[-1]))  # Total bill

static_data_right[2] = '$' + '%.2f' % (float(Amount[5].split('$')[-1]) / int(days_for_bill))
static_data_right[3] = '%.2f' % (float(peak_energy + off_peak_energy) / int(days_for_bill)) + " kWH"
mi = int(static_data[5].split('to')[0].split('/')[1])
month = '_' + date(1900, mi, 1).strftime('%B') + static_data[5].split('to')[0].split('/')[2]
create_pdf(current_month=month.strip())
