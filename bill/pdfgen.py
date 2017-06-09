from reportlab.lib.pagesizes import A4
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.flowables import Spacer, PageBreak
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Image
from Lines import Line
import os
from _globals import __DEBUG__
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT
from _globals import static_data, static_data_right, Quantity, Price, Amount
pdfmetrics.registerFont(TTFont("bitter-bold", "Bitter-Bold.ttf"))
pdfmetrics.registerFont(TTFont("domine", "type_bold.ttf"))
pdfmetrics.registerFont(TTFont("domine-bold", "Domine-Bold.ttf"))
MARGIN_SIZE = 25 * mm
PAGE_SIZE = A4


def give_space(prefix, space_amount):
	return '&nbsp;' * (space_amount - len(prefix))


def create_pdfdoc(pdfdoc, story):
	"""
	Creates PDF doc from story.
	"""
	pdf_doc = BaseDocTemplate(pdfdoc, pagesize=PAGE_SIZE, leftMargin=MARGIN_SIZE, rightMargin=MARGIN_SIZE, topMargin=MARGIN_SIZE, bottomMargin=MARGIN_SIZE)
	main_frame = Frame(MARGIN_SIZE, MARGIN_SIZE, PAGE_SIZE[0] - 2 * MARGIN_SIZE, PAGE_SIZE[1] - 2 * MARGIN_SIZE, leftPadding=0, rightPadding=0, bottomPadding=0, topPadding=0, id='main_frame')
	main_template = PageTemplate(id='main_template', frames=[main_frame])
	pdf_doc.addPageTemplates([main_template])
	pdf_doc.build(story)


def create_pdf(current_month, fileName='bill_export'):
	styleSheet = getSampleStyleSheet()
	styleSheet.add(ParagraphStyle(name='RightAlign', fontName='domine', alignment=TA_RIGHT))

	static_heads = [
		None,
		None,
		"Site Address",
		"NMI",
		"Meter No",
		"Usage Period",
		"Bill days",
		"Total Consumption"
	]

	static_heads_right = [
		None,
		None,
		"Average Daily Cost",
		"Average Daily Usage",
		"Account Number",
		"Invoice Number",
	]

	Charges = [
		"PV Energy Charges",
		"Off Peak PV Energy (Consumed)",
		"Peak PV Energy (Consumed)",
		"Other Charges",
		"Retail Service Charges",
		"Sub-Total",
		"GST",
		"Total"
	]

	styleSheet['BodyText'].leading = 5
	styleSheet['RightAlign'].leading = 1
	content = []
	# ############### Company Logo ##################
	imageFile = './logo.png'
	content.append(Image(imageFile, height=80, width=150))
	###############################################
	content.append(Paragraph("<font face=\"bitter-bold\" fontSize=25>{}</font>".format(static_data[0]), styleSheet['Title']))
	content.append(Spacer(0, 8 * mm))
	content.append(Paragraph("<font color=\"blue\" face=\"bitter-bold\">{}</font>".format(static_data[1]), styleSheet['Heading2']))
	content.append(Line(460))
	for each in zip(static_heads[2::], static_data[2::], static_heads_right, static_data_right):
		content.append(Paragraph("<font face=\"domine\">{} {}<font color=\"grey\">{}</font></font>".format(each[0], give_space(each[0], 19), each[1]), styleSheet['BodyText']))
		if not (each[2] is None and each[3] is None):
			content.append(Paragraph("<font face=\"domine\">{} <font color=\"grey\">{}</font></font>".format(each[2], each[3]), styleSheet['RightAlign']))
	content.append(Paragraph("<font face=\"domine\">{} {}<font color=\"grey\">{}</font></font>".format("Total PV Generation", give_space(each[0], 16), str(static_data[8]) + " kWH"), styleSheet['BodyText']))
	content.append(Spacer(0, 3 * mm))

	content.append(Paragraph("<font color=\"blue\" face=\"bitter-bold\">2. Bill Details</font>".format(static_data[1]), styleSheet['Heading2']))
	content.append(Line(460))
	content.append(Spacer(0, 1 * mm))
	space = give_space("", 20)
	header = "<font face=\"domine\">Charges{s}Quantity{s}Price{s}Amount(ex.GST)</font>".format(s=space)
	content.append(Paragraph(header, styleSheet['BodyText']))
	content.append(Spacer(0, 3 * mm))
	# space1 = give_space("", 12)
	# ###########  roW 1 ###############
	row1 = "<font face=\"domine\">{}</font>".format(Charges[0])
	content.append(Paragraph(row1, styleSheet['BodyText']))
	content.append(Spacer(0, 7 * mm))
	row1 = "<font face=\"domine\">{}{}{}</font>".format("PV Energy Produced", give_space("", 10), str(static_data[8]) + " kWH")
	content.append(Paragraph(row1, styleSheet['BodyText']))
	row1 = "<font face=\"domine\">{}{}{}</font>".format("PV Energy Consumed", give_space("", 10), static_data[7])
	content.append(Paragraph(row1, styleSheet['BodyText']))
	content.append(Spacer(0, 7 * mm))
	# ###########  roW 2 ###############
	row1 = "<font face=\"domine\" color=\"grey\">{}{}{}{}{}{}{}{}</font>".format(
		give_space("", 2),
		Charges[1],
		give_space("", 2),
		Quantity[0],
		give_space("", 13),
		Price[0],
		give_space("", 21),
		Amount[0])
	content.append(Paragraph(row1, styleSheet['BodyText']))
	# ###########  roW 3 ###############
	row2 = "<font face=\"domine\" color=\"grey\">{}{}{}{}{}{}{}{}</font>".format(
		give_space("", 6),
		Charges[2],
		give_space("", 6),
		Quantity[1],
		give_space("", 12),
		Price[1],
		give_space("", 21),
		Amount[1])
	content.append(Paragraph(row2, styleSheet['BodyText']))
	# # ############# roW 4 ####################
	# content.append(Spacer(0, 3 * mm))
	# row3 = "<font face=\"domine\">{}</font>".format(Charges[3])
	# content.append(Paragraph(row3, styleSheet['BodyText']))
	# # ############## roW 5 ###################
	# row5 = "<font face=\"domine\" color=\"grey\">{}{}{}{}{}{}{}{}</font>".format(
	# 	give_space("", 2),
	# 	Charges[4],
	# 	give_space("", 5),
	# 	Quantity[2],
	# 	give_space("", 16),
	# 	Price[2],
	# 	give_space("", 24),
	# 	Amount[2])
	# content.append(Paragraph(row5, styleSheet['BodyText']))
	# ############## roW 6 ###################
	content.append(Spacer(0, 7 * mm))
	row6 = "<font face=\"domine\">{}{}{}</font>".format(
		Charges[5],
		give_space("", 77),
		Amount[3])
	content.append(Paragraph(row6, styleSheet['BodyText']))
	# ############## roW 7 ###################
	row7 = "<font face=\"domine\">{}{}{}</font>".format(
		Charges[6],
		give_space("", 83),
		Amount[4])
	content.append(Paragraph(row7, styleSheet['BodyText']))
	content.append(Spacer(0, 7 * mm))
	# ############## roW 6 ###################
	row8 = "<font face=\"domine\">{}{}{}</font>".format(
		Charges[7] + "(inc. 10%" + give_space("", 1) + "GST)",
		give_space("", 67),
		Amount[5])
	content.append(Line(460))
	content.append(Paragraph(row8, styleSheet['BodyText']))
	content.append(PageBreak())
	fileName += current_month + '.pdf'
	create_pdfdoc(fileName, content)
	if not __DEBUG__:
		os.system('scp -i ~/Downloads/OzKeyPair.pem -r ./' + fileName + ' admin@35.166.113.128:/var/www/')
	# os.system('scp -i ~/Dropbox/Monitoring\ Control/Code_MAYUKH/OzKeyPair.pem -r ./' + fileName + 'admin@35.166.113.128:/var/www/')
