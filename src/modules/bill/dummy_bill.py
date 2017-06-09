import csv
from datetime import datetime, timedelta, date
from _globals import static_data, Quantity, Price, Amount, static_data_right
from pdfgen import create_pdf


def top():
    with open('ASCO_METER.csv', 'rU') as ascco_world_bill, open('WP_METER.csv') as wp_bill:
        awb = csv.reader(ascco_world_bill)
        wpb = csv.reader(wp_bill)
        for each in zip(awb, wpb):
            # print(each)
            try:
                yield {
                    "energy": min(float(each[0][-2]), float(each[1][-1])),
                    "weekday": datetime.strptime(str(each[1][0]), "%M/%d/%Y").weekday(),
                    "day": datetime.strptime(str(each[1][0] + each[1][1]), "%m/%d/%Y%I:%M:%S %p")
                }

            except ValueError:
                pass


def get_tariff(m):

    if m['weekday'] == 5 or m['weekday'] == 6:
        return 0.3
    else:
        rat_dosta = datetime.strptime(str((m['day'] - timedelta(days=1)).date()) + "22:00:00", "%Y-%m-%d%H:%M:%S")
        sokal_satta = datetime.strptime(str(m['day'].date()) + "07:00:00", "%Y-%m-%d%H:%M:%S")
        if rat_dosta < m['day'] < sokal_satta:
            return 0.3
        else:
            return 0.6


def get_period():
    with open('ASCO_METER.csv', 'rU') as ascco_world_bill:
        awb = csv.reader(ascco_world_bill)
        first = 0
        last = 0
        # length = 0
        for each in enumerate(awb):
            last = each[1][0]
            if each[0] == 1:
                first = each[1][0]
        return first, last


def main():
	metrics = top()
	peak_energy = 0.0
	off_peak_energy = 0.0
	for each in metrics:
	    tariff = get_tariff(each)
	    if tariff == 0.3:
	        off_peak_energy += each['energy']
	        # off_peak_cost += off_peak_energy
	        # print "Hello"
	    else:
	        peak_energy += each['energy']
	        # print "Hi"
	# print (peak_energy, off_peak_energy)
	Quantity[0] = str(off_peak_energy)
	Quantity[1] = str(peak_energy)
	Quantity[2] = str(int(str(datetime.strptime(get_period()[1], "%d/%m/%Y") - datetime.strptime(get_period()[0], "%d/%m/%Y"))[0:2]) + 1)
	# print "Peak Energy %f at tariff %f. Total cost incurred $%f" %(peak_energy, 0.3, peak_energy * 0.3)
	# print "Off Peak Energy %f at tariff %f. Total cost incurred $%f" %(off_peak_energy, 0.6, off_peak_energy * 0.3)
	# print "Total Energy %f and total cost incurred $%f" %(peak_energy + off_peak_energy, peak_energy * 0.3 + off_peak_energy * 0.6)
	static_data[5] = str(get_period()[0]) + " to " + str(get_period()[1])
	static_data[6] = Quantity[2]
	static_data[7] = str(float(peak_energy) + float(off_peak_energy))
	Price[0] = '3.0 c/kWh'
	Price[1] = '6.0 c/kWh'
	Amount[0] = '$' + str(float(off_peak_energy) * 0.03)
	Amount[1] = '$' + str(float(peak_energy) * 0.06)
	Amount[2] = '$' + str(float(Quantity[2]) * 1.9)
	Amount[3] = '$' + str((float(off_peak_energy) * 0.03) + (float(peak_energy) * 0.06))
	Amount[5] = '$' + str(float(Amount[4].split('$')[-1]) + float(Amount[3].split('$')[-1]))
	static_data_right[2] = '$' + str(float(Amount[5].split('$')[-1]) / int(Quantity[2]))
	static_data_right[3] = str(float(static_data[7]) / int(Quantity[2]))
	mi = int(static_data[5].split('to')[0].split('/')[1])
	# print(mi)
	month = '_' + date(1900, mi, 1).strftime('%B') + static_data[5].split('to')[0].split('/')[2]
	# print(month)
	create_pdf(current_month=month.strip())
	# print(month)


if __name__ == '__main__':
	main()
