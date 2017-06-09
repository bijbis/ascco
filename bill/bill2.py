# from datetime import datetime as dt
from influxdb import InfluxDBClient
import csv
import pandas as pd
import numpy as np
from _globals import static_data, Quantity, Price, Amount, static_data_right
from datetime import date
from pdfgen import create_pdf

offset = 0


def approximate_timestamp(each):
	global offset
	if abs(each.minute - offset) <= 5:
		offset ^= 30
		return each


def label_weekday(row):
	return row['weekday'] in [5, 6]


# def get_tariff_on_date_export(row):
# 	"""
# 	This handles only weekends
# 	"""
# 	if row['weekend']:
# 		return row[:'23:30'].apply(lambda each: float(each)) * 0.0926
# 	else:
# 		return row[:'23:30'].apply(lambda each: float(each)) * 0.3764


# def get_tariff_on_date_import(row):
# 	"""
# 	This handles only weekends
# 	"""
# 	if row['weekend']:
# 		return row[:'23:30'].apply(lambda each: float(each)) * 0.0926
# 	else:
# 		r = row[:'23:30'].apply(lambda each: float(each))
# 		a = r['00:00': '06:30'] * 0.0926
# 		b = r['07:00': '21:00'] * 0.3764
# 		c = r['21:30': '23:30'] * 0.0926
# 		return a.append(b).append(c)


def round_off_time(each):
	minOffset1 = abs(each.time.minute - 0)
	minOffset2 = abs(each.time.minute - 30)
	if minOffset1 < minOffset2:
		return '%4d-%02d-%02d T%02d:%02d' % (each.time.year, each.time.month, each.time.day, each.time.hour, 0)
	else:
		return '%4d-%02d-%02d T%02d:%02d' % (each.time.year, each.time.month, each.time.day, each.time.hour, 30)


def put_export_data(each):
	_date = each.local_time.split('T')[0]
	time = each.local_time.split('T')[-1]
	Date = pd.to_datetime(_date).strftime('%Y-%m-%d')
	return export_data.loc[Date, time]


# ############################################################
temp_bill = []
temp_dates = []
with open('NEM12_8002180729_01-MAY-16-06-JUN-17.csv', 'r') as billCSV:
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
# import_data = billData[billData['Import_Export'] == 'import']
export_data = billData[billData['Import_Export'] == 'export']
# print(import_data.shape)
export_data = export_data[(export_data.index >= '2017/05/03') & (export_data.index <= '2017/05/31')]
# import_data = import_data[(import_data.index >= '2017/05/03') & (import_data.index <= '2017/05/16')]
# export_tariff = export_data.apply(lambda row: get_tariff_on_date_export(row), axis=1)
# import_tariff = import_data.apply(lambda row: get_tariff_on_date_import(row), axis=1)
# tariff1 = (import_tariff.sum(axis=1) - export_tariff.sum(axis=1)).sum()

# t2 = []
# for each in import_data.index.values:
# 	if dt.strptime(str(each).split('T')[0], '%Y-%m-%d').weekday() in [5, 6]:
# 		t2.append(167.0 * 0.0926)
# 	else:
# 		t2.append(167.0 * 0.3764)
# tarrif2 = sum(t2) - export_tariff.sum(axis=1).sum()
# print(tarrif2)
# #######  Calculation of number of days for the bill ################
dfb = export_data.index.values[-1] - export_data.index.values[0]
days_for_bill = dfb.astype('timedelta64[D]') / np.timedelta64(1, 'D')
# ####################################################################

client = InfluxDBClient('35.166.113.128', 8086, 'root', 'root', 'ascco_world')
row = client.query("SELECT * FROM energy_consumption WHERE time >= '2017-05-03' AND time < '2017-05-31'")
pv_data = pd.DataFrame.from_dict(list(row)[0]).drop(['ac_time', 'host', 'region'], axis=1)
pv_data['time'] = pd.to_datetime(pv_data.time) + pd.DateOffset(hours=8)
pv_data['weekend'] = pv_data.time.dt.dayofweek.isin([5, 6])
pv_data['time'] = pv_data['time'].apply(approximate_timestamp)
pv_data_half_hourly = pv_data.dropna().reset_index().drop('index', axis=1)
pv_data_half_hourly['generated_energy'] = pv_data_half_hourly.total_energy.diff(1)
pv_data_half_hourly.dropna(inplace=True)
pv_data_half_hourly['local_time'] = pv_data_half_hourly.apply(round_off_time, axis=1)
pv_data_half_hourly = pv_data_half_hourly[(pv_data_half_hourly.time >= '2017/05/03') & (pv_data_half_hourly.time <= '2017/05/31')]
report_data = pv_data_half_hourly.drop(['weekend'], axis=1)
cols = ['time', 'local_time', 'total_energy', 'generated_energy', 'exported_energy (kwh)', 'consumed_unit']
report_data = report_data.loc[:, cols]
report_data.rename(index=str, columns={"total_energy": "cumulative_generated_energy (kwh)",
	"generated_energy": "actual_generated_energy (kwh)",
	"consumed_unit": "consumed_energy (kwh)"}, inplace=True)
report_data['exported_energy (kwh)'] = report_data.apply(put_export_data, axis=1)
report_data['exported_energy (kwh)'] = report_data['exported_energy (kwh)'].apply(float)
report_data['actual_generated_energy (kwh)'] = report_data['actual_generated_energy (kwh)'].apply(float)

# report_data['consumed_energy (kwh)'].apply(float)
report_data['consumed_energy (kwh)'] = report_data['actual_generated_energy (kwh)'] - report_data['exported_energy (kwh)']
off_peak_energy1 = report_data[report_data.time.dt.weekday >= 5]['consumed_energy (kwh)'].sum()
weekday_data = report_data[report_data.time.dt.weekday < 5]
peak_energy = weekday_data[(weekday_data.time.dt.hour < 21) & (weekday_data.time.dt.hour >= 7)]['consumed_energy (kwh)'].sum()
off_peak_energy2 = weekday_data[~((weekday_data.time.dt.hour < 21) & (weekday_data.time.dt.hour >= 7))]['consumed_energy (kwh)'].sum()


off_peak_energy = float(off_peak_energy1 + off_peak_energy2)
peak_energy = float(peak_energy)
peak_tarrif = 0.3764
off_peak_tariff = 0.0926
pv_energy_produced = float(report_data['actual_generated_energy (kwh)'].sum())
Quantity[0] = '%.2f' % (off_peak_energy) + " kWH"
Quantity[1] = '%.2f' % (peak_energy) + " kWH"
Quantity[2] = str(int(days_for_bill)) + " day(s)"
ts1 = pd.to_datetime(str(export_data.index.values[0]))
ts2 = pd.to_datetime(str(export_data.index.values[-1])) - pd.DateOffset(1)
static_data[5] = ts1.strftime('%d/%m/%Y') + " to " + ts2.strftime('%d/%m/%Y')
static_data[6] = str(int(days_for_bill)) + " day(s)"
static_data[7] = '%.2f' % (peak_energy + off_peak_energy) + " kWH"
static_data[8] = pv_energy_produced
# # # print(static_data)
Price[0] = '09.26 c/kWH'
Price[1] = '37.64 c/kwH'
Amount[0] = "$" + '%.2f' % (off_peak_energy * off_peak_tariff)  # Off peak charges
Amount[1] = "$" + '%.2f' % (peak_energy * peak_tarrif)  # Peak charges
# # Amount[2] = "$" + str(float(days_for_bill) * 3.51)  # Other charges
Amount[3] = "$" + '%.2f' % ((off_peak_energy * off_peak_tariff) + (peak_energy * peak_tarrif))  # Sub total
Amount[4] = "$" + '%.2f' % ((off_peak_energy * off_peak_tariff + peak_energy * peak_tarrif) * 0.1)  # GST at 10%
# print()
Amount[5] = "$" + '%.2f' % (float(Amount[3].split('$')[-1]) + float(Amount[4].split('$')[-1]))  # Total bill

static_data_right[2] = '$' + '%.2f' % (float(Amount[5].split('$')[-1]) / int(days_for_bill))
static_data_right[3] = '%.2f' % ((peak_energy + off_peak_energy) / int(days_for_bill)) + " kWH"
mi = int(static_data[5].split('to')[0].split('/')[1])
month = '_' + date(1900, mi, 1).strftime('%B') + static_data[5].split('to')[0].split('/')[2]
create_pdf(current_month=month.strip(), fileName='bill_ASCO')
report_data = report_data.drop(['time'], axis=1)
report_data.to_csv('May2017.csv')
