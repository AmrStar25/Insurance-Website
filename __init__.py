# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash, abort, jsonify
from flask import session as login_session
import os
import MySQLdb
from flask_seasurf import SeaSurf
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
import random, string
import requests
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.rl_config import defaultPageSize
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display
from flask import send_file



#from reportlab.lib.enums import TA_CENTRE, TA_JUSTIFY
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.fonts import addMapping
import pdfkit



#from jinja2 import Environment, PackageLoader
#from werkzeug.debug import DebuggedApplication
#import jinja2



#from werkzeug import secure_filename


app = Flask(__name__)
csrf = SeaSurf(app)
socketio = SocketIO(app)
app.config.update(dict(
	MAIL_SERVER = 'smtp.gmail.com',
	MAIL_PORT = 465,
	MAIL_USERNAME = 'amrstar25@gmail.com',
	MAIL_PASSWORD ='a0882353984a',
	MAIL_USE_TLS = False,
	MAIL_USE_SSL = True,
	MAIL_SUPPRESS_SEND = False,
	MAIL_DEFAULT_SENDER = 'amrstar25@gmail.com'
))
mail = Mail(app)



ALLOWED_EXTENSIONS = set(['jpg','gif'])
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static/site/nationalid/')
							
app.config['Offers_Folder'] = '/static/site/offers/'



@app.route('/insuranceimportant', methods=['GET'])
def InsuranceImportant():
	return render_template('insurance-important.html')

@app.route('/insurancelib', methods=['GET'])
def InsuranceLib():
	return render_template('insurance-lib.html')
	
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@socketio.on('disconnect')
def disconnect_user():
    #logout_user()
    login_session.pop('username', None)
    login_session.pop('userpass', None)
    login_session.pop('type', None)
    login_session.pop('id', None)
    login_session.pop('state',None)

@app.route('/logout', methods=['GET'])
def logout():
	if 'username' not in login_session or request.args.get('state') != login_session['state']:
		#return jsonify(request.args.get('state'), "1aaaaaaaaaa1",login_session['state'])
		return jsonify('error') #render_template('index.html')
	login_session.pop('username', None)
	login_session.pop('userpass', None)
	login_session.pop('type', None)
	login_session.pop('id', None)
	login_session.pop('state', None)
	return redirect(url_for('userlogin'))

@app.route('/', methods=['POST','GET'])
def userlogin():
	if request.method == "GET":
		state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
		login_session['state'] = state
		return render_template('index.html',STATE=state)
	else:
		if request.args.get('state') != login_session['state']:
			return jsonify('error')
		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor=db.cursor()
		query = "SELECT * FROM accounts_users WHERE UserName=%s and UserPass=%s"
		cursor.execute(query,(request.form['name'],request.form['pass']))
		result=cursor.fetchone()
		if cursor.rowcount == 0:
			db.close()
			return jsonify('error')
		else:
			db.close()
			login_session['id']=result[0]
			#user name is email of user
			login_session['username']=result[1]
			login_session['userpass']=result[2]
			login_session['type']=result[3]

			return jsonify(login_session['type'])
			
			# if login_session['type'] == 4:
			# 	return redirect(url_for('CompanyOffersAccess'))
			# else:
			# 	#return redirect(url_for('ClientOffers'))
			# 	return jsonify('error'+login_session['type'])


@app.route('/ethad', methods=['POST','GET'])
def EthadAccess():
	if request.method == 'POST' and request.args.get('state') != login_session['state']:
		return redirect(url_for('userlogin'))
	if request.method == 'GET':
		state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
		login_session['state']=state
		return render_template('ethad.html', STATE=state)
	else:
		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor=db.cursor()
		try:
			# user name is his email
			query = "SELECT * FROM accounts_users WHERE UserName='%s'" % request.form['email']
			cursor.execute(query)
			if cursor.rowcount == 0:
				#user type (1,2,3,4) for (ethad,club,player,company)
				query = "INSERT INTO accounts_users(UserName,UserPass,UserType,UserActive,Notes) Values('%s','%s','%s','%s','%s')"\
				 		%(request.form['email'], login_session['state'][:7], 1, 1, request.form['notes'])
				#return (query,(request.form['email'], login_session['state'][:7], 1, 1, request.form['notes']))
				cursor.execute(query)
				id = cursor.lastrowid

				query = "INSERT INTO ethad(EthadID,EthadName,EthadPhone,EthadFax) Values('%s','%s','%s','%s')"\
				 		%(id,request.form['name'],request.form['phone'],request.form['fax'])
				cursor.execute(query)
			


				msg = Message('',recipients=[])
				text = ("عزيزى ").decode("utf-8")
				text = text + request.form['name']
				text = text + (" \nبرجاء استخدام بريدك الالكترونى وكلمه السر الاتيه لتسجيل الدخول \n").decode("utf-8")
				text = text + login_session['state'][:7]
				msg.body = text
				msg.subject = ("مصر للتامين الرياضى").decode("utf-8")
				msg.add_recipient(request.form['email'])

				# check internet connection
				r =requests.get("https://www.google.com/")
				if r.status_code != 200:
					db.rollback()
					db.close()
					return jsonify('error')

				mail.send(msg)




				db.commit()
				db.close()

				return jsonify('done')
			else:
				db.close()
				return jsonify('duplicate')
		except Exception as e:
			if db.open:
				db.rollback()
				db.close()
			
			return jsonify(str(e))


@app.route('/club', methods=['POST','GET'])
def ClubAccess():
	if request.method == 'POST' and request.args.get('state') != login_session['state']:
		return redirect(url_for('userlogin'))
	if request.method == 'GET':
		state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
		login_session['state']=state
		return render_template('club.html', STATE=state)
	else:
		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor = db.cursor()
		try:
			# user name is his email
			query = "SELECT * FROM accounts_users WHERE UserName='%s'" % request.form['email']
			cursor.execute(query)
			if cursor.rowcount == 0:
				#user type (1,2,3,4) for (ethad,club,player,company)
				query = "INSERT INTO accounts_users(UserName,UserPass,UserType,UserActive,Notes) Values('%s','%s','%s','%s','%s')"\
						%(request.form['email'], login_session['state'][:7], 2, 1, request.form['notes'])
				cursor.execute(query)
				id = cursor.lastrowid

				query = "INSERT INTO club(ClubID,ClubName,ClubPhone,ClubFax,Address) Values('%s','%s','%s','%s','%s')"\
				 		%(id,request.form['name'],request.form['phone'],request.form['fax'],request.form['address'])
				cursor.execute(query)


				msg = Message('',recipients=[])
				text = ("عزيزى ").decode("utf-8")
				text = text + request.form['name']
				text = text + (" \nبرجاء استخدام بريدك الالكترونى وكلمه السر الاتيه لتسجيل الدخول \n").decode("utf-8")
				text = text + login_session['state'][:7]
				msg.body = text
				msg.subject = ("مصر للتامين الرياضى").decode("utf-8")
				msg.add_recipient(request.form['email'])

				# check internet connection
				r =requests.get("https://www.google.com/")
				if r.status_code != 200:
					db.rollback()
					db.close()
					return jsonify('error')

				mail.send(msg)




				db.commit()
				db.close()
				return jsonify('done')
			else:
				db.close()
				return jsonify('duplicate')
			
		except Exception as e:
			if db.open:
				db.rollback()
				db.close()

			return jsonify(str(e))


@app.route('/company', methods=['POST','GET'])
def CompanyAccess():
	if request.method == 'POST' and request.args.get('state') != login_session['state']:
		return redirect(url_for('userlogin'))
	if request.method == 'GET':
		state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
		login_session['state']=state
		return render_template('company.html', STATE=state)
	else:
		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor = db.cursor()
		try:
			# user name is his email
			query = "SELECT * FROM accounts_users WHERE UserName='%s'" % request.form['email']
			cursor.execute(query)
			if cursor.rowcount == 0:
				#user type (1,2,3,4) for (ethad,club,player,company)
				query = "INSERT INTO accounts_users(UserName,UserPass,UserType,UserActive,Notes) Values('%s','%s','%s','%s','%s')"\
						%(request.form['email'], login_session['state'][:7], 4, 1, request.form['notes'])
				cursor.execute(query)
				id = cursor.lastrowid

				query = "INSERT INTO company(CompanyID,CompanyName,CompanyPhone,CompanyFax,Address) Values('%s','%s','%s','%s','%s')"\
				 		%(id,request.form['name'],request.form['phone'],request.form['fax'],request.form['address'])
				cursor.execute(query)


				msg = Message('',recipients=[])
				text = ("عزيزى ").decode("utf-8")
				text = text + request.form['name']
				text = text + (" \nبرجاء استخدام بريدك الالكترونى وكلمه السر الاتيه لتسجيل الدخول \n").decode("utf-8")
				text = text + login_session['state'][:7]
				msg.body = text
				msg.subject = ("مصر للتامين الرياضى").decode("utf-8")
				msg.add_recipient(request.form['email'])

				# check internet connection
				r =requests.get("https://www.google.com/")
				if r.status_code != 200:
					db.rollback()
					db.close()
					return jsonify('error')

				mail.send(msg)




				db.commit()
				db.close()
				return jsonify('done')
			else:
				db.close()
				return jsonify('duplicate')
			
		except Exception as e:
			if db.open:
				db.rollback()
				db.close()

			return jsonify(str(e))


@app.route('/player', methods=['POST','GET'])
def PlayerAccess():
	if request.method == 'POST' and request.args.get('state') != login_session['state']:
		return redirect(url_for('userlogin'))
	if request.method == 'GET':
		state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
		login_session['state']=state
		return render_template('player.html', STATE=state)

	else:
		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor = db.cursor()

		try:
			query = "SELECT * FROM accounts_users WHERE UserName='%s'" % request.form['email']
			cursor.execute(query)
			if cursor.rowcount == 0:
				#user type (1,2,3,4) for (ethad,club,player,company)
				query = "INSERT INTO accounts_users(UserName,UserPass,UserType,UserActive,Notes) Values('%s','%s','%s','%s','%s')"\
						%(request.form['email'], login_session['state'][:7], 3, 1, request.form['notes'])
				cursor.execute(query)
				id = cursor.lastrowid

				query = "INSERT INTO player(PlayerID, PlayerName, PlayerJob, PlayerAddress, PlayerPhone, "\
						"PlayerNationalID, PlayerBirthDate, PlayerGender, PlayerScoialStatus, PlayerNationalty, "\
						"PlayerQualification, PlayerSportActivity) Values('%s', '%s', '%s', '%s', '%s', '%s', "\
						"STR_TO_DATE('%s','%%m-%%d-%%Y'), '%s', '%s', '%s', '%s', '%s')"%(id, request.form['name'],\
						request.form['job'], request.form['address'], request.form['phone'],\
						request.form['nationalid'], request.form['birthdate'], request.form['gender'],\
						request.form['socialstatus'], request.form['nationality'], request.form['qualification'],\
						request.form['sportactivity'])
				
				cursor.execute(query)

				msg = Message('',recipients=[])
				text = ("عزيزى ").decode("utf-8")
				text = text + request.form['name']
				text = text + (" \nبرجاء استخدام بريدك الالكترونى وكلمه السر الاتيه لتسجيل الدخول \n").decode("utf-8")
				text = text + login_session['state'][:7]
				msg.body = text
				msg.subject = ("مصر للتامين الرياضى").decode("utf-8")
				msg.add_recipient(request.form['email'])

				# check internet connection
				r =requests.get("https://www.google.com/")
				if r.status_code != 200:
					db.rollback()
					db.close()

					return jsonify('error')
				else:
					if 'photo' in request.files:
						file = request.files['photo']
						if allowed_file(file.filename):
							file.save(app.config['UPLOAD_FOLDER']+ str(id))

							mail.send(msg)

							db.commit()
							db.close()
							return jsonify('done')
						else:
							db.rollback()
							db.close()

							return jsonify('error')
					else:
						return jsonify("noy")
			else:
				db.close()
				return jsonify('duplicate')

			
		except Exception as e:
			if db.open:
				db.rollback()
				db.close()

			return jsonify(str(e))



@app.route('/companyoffers', methods=['POST','GET'])
def CompanyOffersAccess():
	if 'username' not in login_session or (request.method == 'POST' and request.args.get('state') != login_session['state']):
		#return jsonify(request.args.get('state') , login_session['state'])
		return redirect(url_for('userlogin'))
	
	if login_session['type'] != "4":
		return redirect(url_for('logout', state=login_session['state']))

	if request.method == 'GET':
		if 'offerid' not in request.args:

			state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
			login_session['state']=state

			return render_template('company-add-offer.html', STATE=state, OfferID=-1)
		else:
			state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
			login_session['state']=state

			db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
			cursor = db.cursor()

			query = "SELECT * FROM offers WHERE OfferID = " + str(request.args.get('offerid'))
			cursor.execute(query)

			result = cursor.fetchone()

			offerid = result[0]
			injury = result[2]
			regulations = result[3]
			description = result[4]
			companyid = result[1]

			if companyid != login_session['id']: # ensure that's offerid belongs to this company
				return redirect(url_for('ShowAllOffers'))

			query = "SELECT @n := @n + 1, (select distinct 1 from clients_applied_for where clients_applied_for.RiskID = risks.RiskID)  as Used, "\
					"RiskID, RiskName, Active "\
					"FROM risks, (SELECT @n := -1) Customindex "\
					"WHERE OfferID = " + str(offerid)
			
			cursor.execute(query)

			risks = cursor.fetchall()

			query = "SELECT @n := @n + 1, techniques.TechniqueID, techniques.TechniqueName, "\
					"techniques.TechniqueDescription, techniques.Active, GROUP_CONCAT(risks_techniques.RiskID separator ',') as Risks, "\
					"(select distinct 1 from clients_applied_for where clients_applied_for.TechniqueID= techniques.TechniqueID)  as Used ,1 "\
					"FROM risks, risks_techniques, techniques ,(SELECT @n := -1) Customindex "\
					"WHERE risks.RiskID = risks_techniques.RiskID and techniques.TechniqueID = risks_techniques.TechniqueID "\
					"and risks.OfferID = %s "\
					"group by techniques.TechniqueID"

			cursor.execute(query,(str(offerid),))

			techniques = cursor.fetchall()
			
			# for loop for replace risks covered by tech ids with custom ids we created previously and used in client side
			# convert this tuple to list to be able to change it's items
			techniques = list(techniques)

			for techindex,tech in enumerate(techniques):
				temp = list(tech)
				temp[5] = temp[5].split(',')
				temp[7] = [] # used to show risks names assigned to specific tech
				for i,x in enumerate(temp[5]):
					for r in risks:
						if str(x) == str(r[2]):
							temp[5][i] = r[0] # custom risk id
							temp[7].append(r[3])  #temp[7] = ", " + temp[7] + r[3]
							break

				temp[5] = [str(x) for x in temp[5] ] # this to run correct with jinjia2 without this list passed with L symbol
				temp[7] = ",".join(temp[7])

				techniques[techindex] = temp
			
			


			query = "SELECT @n := @n + 1, services.ServiceID, services.TechniqueID, services.ServiceName, "\
					"services.ServiceDescription, services.Active, "\
					"(select distinct 1 from clients_applied_for where clients_applied_for.ServiceID = services.ServiceID)  as Used "\
					"FROM services,(select @n:=-1) custom "\
					"WHERE services.TechniqueID in "\
					"(SELECT techniques.TechniqueID FROM risks, risks_techniques, techniques "\
					"WHERE risks.RiskID = risks_techniques.RiskID and techniques.TechniqueID = risks_techniques.TechniqueID "\
					"and risks.OfferID = %s group by techniques.TechniqueID)"
			
			cursor.execute(query,(str(offerid),))
			services = cursor.fetchall()

			services = list(services)

			for index,service in enumerate(services):
				temp = list(service)
				for tech in techniques:
					if temp[2] == tech[1]:
						temp[2] = tech[0]
						break
				services[index] = temp

			#return jsonify(t, temp)


			query = "SELECT @n := @n + 1, payments_offers.ID, payments_offers.Period, payments_offers.FirstPayment, "\
					"payments_offers.MonthlyPayment, payments_offers.AddedPercentage, payments_offers.MaxPersonNumbers, "\
					"payments_offers.Active, ((Period * 12 * MonthlyPayment) + FirstPayment) * (1 + AddedPercentage / 100), "\
					"(select distinct 1 from clients_applied_for where clients_applied_for.PaymentID = payments_offers.ID)  as Used "\
					"FROM payments_offers, (select @n:=-1) custom "\
					"WHERE payments_offers.OfferID = " + str(offerid)
			cursor.execute(query)

			payments = cursor.fetchall()

			
			db.close()



			# temprisks = [r[0] for r in risks]#cursor.fetchall()   list comprehensions
			# # for loop for get risk indeces to used in client side that deal upon custom index
			# for i, r_t in enumerate(risks_techniques):
			# 	r_index = temprisks.index(r_t[1])

			# 	list(risks_techniques[i]).append[r_index]


			return render_template('company-add-offer.html', STATE=state, OfferID=offerid, Injury=injury,
			Regulations=regulations, Description=description, Risks=risks, Techniques=techniques, Services=services, Payments=payments )

		
	else:
		typee = request.json['type']
		description = request.json['description']
		regulations = request.json['regulations']
		risks = request.json['risks']
		injury = request.json['injury']
		techniques = request.json['techniques']
		services = request.json['services']
		payments = request.json['payments']

		if typee == "add":
			db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
			cursor = db.cursor()
			try:
				query = "INSERT INTO offers(CompanyID, Injury, Regulations, Description, Active) Values(%s,"\
						"%s, %s, %s, %s)"

				cursor.execute(query,(login_session['id'], injury, regulations, description, 1))
				id = cursor.lastrowid

				temprisks = []
				for r in risks:
					
					query = "INSERT INTO risks(RiskName, OfferID, Active) Values(%s, %s, %s)"
					cursor.execute(query,(r[3], id, r[4]))
					r_id = cursor.lastrowid

					temprisks.append([r_id, r[0]]) # add r_id that's risk id from databasee and id used in client

				temptech = []
				for t in techniques:
					
					query = "INSERT INTO techniques(TechniqueName, TechniqueDescription, Active) Values(%s,"\
							"%s, %s)"
					cursor.execute(query,(t[5], t[4], t[6]))
					t_id = cursor.lastrowid
					# add t_id that's technique id from databasee and id used in client and list of risks ids attach to this technique
					temptech.append([t_id, t[0], t[3]])

				for t in temptech:
					for r_t in t[2]:
						for r in temprisks:
							if str(r[1]) == str(r_t):
								#return jsonify(r_t)
								#return jsonify(str(type(r[1]))+str(type(r_t)))
								query = "INSERT INTO risks_techniques(RiskID, TechniqueID) Values(%s, %s)"
								cursor.execute(query,(r[0], t[0]))
								break

				for s in services:
					for t in temptech:
						if str(s[4]) == str(t[1]):
							query = "INSERT INTO services(TechniqueID, ServiceName, ServiceDescription, Active) Values("\
									"%s, %s, %s, %s)"
							cursor.execute(query,(t[0], s[5], s[3], s[6]))
							break

				for p in payments:
					query = "INSERT INTO payments_offers(OfferID, Period, FirstPayment, MonthlyPayment, AddedPercentage, "\
							"MaxPersonNumbers, Active) Values(%s, %s, %s, %s, %s, %s, %s)"

					cursor.execute(query,(id, p[3], p[5], p[7], p[6], p[4], p[8]))

				db.commit()
				db.close()

				return jsonify('done')
				




			except Exception as e:
				db.rollback()
				db.close()

				return jsonify(str(e))

		elif typee == "update":
			db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
			cursor = db.cursor()
			try:

				offerid = request.json['offerid']

				query = "UPDATE offers SET Injury = %s, Regulations = %s, Description = %s WHERE OfferID = %s"

				cursor.execute(query,(injury, regulations, description, offerid))
						

				updatetemp = []
				inserttemp = []

				for p in payments:
					if p[1] == -1:
						inserttemp.append((offerid, p[3], p[5], p[7], p[6], p[4], p[8]))
					else:
						updatetemp.append((p[3], p[5], p[7], p[6], p[4], p[8], p[1]))

				deletetemp = [ t[6] for t in updatetemp]

				query = "DELETE FROM payments_offers WHERE OfferID = %s and ID NOT IN %s"

				cursor.execute(query,(offerid, deletetemp))

				query = "INSERT INTO payments_offers(OfferID, Period, FirstPayment, MonthlyPayment, AddedPercentage, "\
						"MaxPersonNumbers, Active) Values(%s, %s, %s, %s, %s, %s, %s)"

				cursor.executemany(query,inserttemp)

				query = "UPDATE payments_offers SET Period = %s, FirstPayment = %s, MonthlyPayment = %s, AddedPercentage = %s, "\
						"MaxPersonNumbers = %s, Active = %s WHERE ID = %s"

				cursor.executemany(query,updatetemp)

				

				temprisks = []

				for r in risks:
					if r[1] == -1:
						query = "INSERT INTO risks(RiskName, OfferID, Active) Values(%s, %s, %s)"
						cursor.execute(query,(r[3], offerid, r[4]))
						r_id = cursor.lastrowid

						temprisks.append([r[0], r_id, r[2], r[3], r[4]])
					else:
						query = "UPDATE risks SET RiskName = %s, Active = %s WHERE RiskID = %s"
						cursor.execute(query,(r[3], r[4], r[1]))

						temprisks.append([r[0], r[1], r[2], r[3], r[4]])


				temptech = []

				for t in techniques:
					if t[1] == -1:
						query = "INSERT INTO techniques(TechniqueName, TechniqueDescription, Active) Values(%s,"\
								"%s, %s)"
						cursor.execute(query,(t[5], t[4], t[6]))
						t_id = cursor.lastrowid

						temptech.append([t[0], t_id, t[2], t[3], t[4], t[5], t[6]])

						for r_t in t[3]:
							for r in temprisks:
								if r_t == r[0]:
									query = "INSERT INTO risks_techniques(RiskID, TechniqueID) Values(%s, %s)"
									cursor.execute(query,(r[1], t_id ))
									break
					else:
						query = "UPDATE techniques SET TechniqueName = %s, TechniqueDescription = %s, Active = %s "\
								"WHERE TechniqueID = %s"
						cursor.execute(query,(t[5], t[4], t[6], t[1]))

						temprisks_tech = []

						for r_t in t[3]:
							for r in temprisks:
								if r_t == r[0]:
									temprisks_tech.append([r[1], t[1]])
									break

						query = "DELETE FROM risks_techniques WHERE TechniqueID = %s and RiskID NOT IN %s"


						cursor.execute(query,(t[1], [ aa[0] for aa in temprisks_tech]))

						# this code is true but get error because rid,tid sometimes become the same
						# query = "INSERT INTO risks_techniques(RiskID, TechniqueID) "\
						# 		"SELECT * FROM (SELECT %s, %s) AS TEMP "\
						# 		"WHERE NOT EXISTS (SELECT * FROM risks_techniques WHERE RiskID = %s and TechniqueID = %s)"

						# for index,value in enumerate(temprisks_tech):
						# 	temprisks_tech[index].extend(temprisks_tech[index])
						
						# cursor.executemany(query,(temprisks_tech))

						for value in temprisks_tech:

							query = "SELECT * FROM risks_techniques WHERE RiskID = %s and TechniqueID = %s"
							cursor.execute(query,(value[0], value[1]))

							if cursor.rowcount == 0:
								query = "INSERT INTO risks_techniques(RiskID, TechniqueID) Values (%s, %s)"
								cursor.execute(query,(value[0], value[1]))

						temptech.append([t[0], t[1], t[2], t[3], t[4], t[5], t[6]])

				tempservice = []

				for s in services:
					if s[1] == -1:
						query = "INSERT INTO services(TechniqueID, ServiceName, ServiceDescription, Active) Values("\
								"%s, %s, %s, %s)"
						for t in temptech:
							if t[0] == s[4]:
								cursor.execute(query,(t[1], s[5], s[3], s[6]))
								s_id = cursor.lastrowid

								tempservice.append([s[0], s_id, s[2], s[3], s[4], s[5], s[6]])
								break
					else:
						query = "UPDATE services SET TechniqueID = %s, ServiceName = %s, ServiceDescription = %s, Active = %s "\
								"WHERE ServiceID = %s"
						for t in temptech:
							if t[0] == s[4]:
								cursor.execute(query,(t[1], s[5], s[3], s[6], s[1]))

								tempservice.append([s[0], s[1], s[2], s[3], s[4], s[5], s[6]])
								break


				#delete the record that exist in database and not exist in data come from client after update
				query = "DELETE FROM services WHERE ServiceID IN (SELECT serv.ServiceID FROM (SELECT * FROM services) AS serv "\
						"WHERE serv.TechniqueID in (SELECT techniques.TechniqueID FROM risks, risks_techniques, techniques WHERE "\
						"risks.RiskID = risks_techniques.RiskID and techniques.TechniqueID = risks_techniques.TechniqueID and "\
						"risks.OfferID = %s group by techniques.TechniqueID)) and ServiceID NOT IN %s"

				cursor.execute(query,( offerid, [ x[1] for x in tempservice] ))

				query = "DELETE FROM techniques WHERE TechniqueID IN (SELECT Tech.TechniqueID "\
						"FROM risks, risks_techniques, (SELECT * FROM techniques) AS Tech "\
						"WHERE risks.RiskID = risks_techniques.RiskID "\
						"AND Tech.TechniqueID = risks_techniques.TechniqueID "\
						"AND risks.OfferID = %s GROUP BY Tech.TechniqueID) "\
						"and TechniqueID NOT IN %s"

				cursor.execute(query,( offerid, [ x[1] for x in temptech ] ))

				query = "DELETE FROM risks WHERE OfferID = %s and RiskID NOT IN %s"

				cursor.execute(query,( offerid, [ x[1] for x in temprisks ], ))

				db.commit()
				db.close()

				return jsonify('done')
				
			except Exception as e:
				db.rollback()
				db.close()

				return jsonify(str(e))


		

@app.route('/alloffers', methods=['POST','GET'])
def ShowAllOffers():
	if 'username' not in login_session or (request.method == 'POST' and request.args.get('state') != login_session['state']):
		return redirect(url_for('userlogin'))

	if login_session['type'] != "4":
		return redirect(url_for('logout', state=login_session['state']))

	if request.method == 'GET':
		state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
		login_session['state']=state


		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor = db.cursor()
		try:
			query = "SELECT * FROM offers where CompanyID = " + str(login_session['id'])
			cursor.execute(query)
			alloffers = cursor.fetchall()

			# env = Environment(loader=PackageLoader('static', 'templates'))
			# template = env.get_template('company-offers.html')
   #  		output=template.render(STATE=state)
   #  		return HttpResponse(output)
   			
			return render_template('company-offers.html', STATE=state, Offers=alloffers)

		except Exception as e:
			return jsonify(str(e))

	else:
		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor = db.cursor()
		try:
			query = "UPDATE offers SET Active = '%s' WHERE OfferID = '%s'"
			cursor.execute(query,(request.json.get('status'), request.json.get('id')))
			db.commit()
			

			return jsonify('done')

		except Exception as e:
			return jsonify(str(e))

@app.route('/clientspplyoffer', methods=['GET', 'POST'])
def ClientApplyOffer():
	if 'username' not in login_session or (request.method == 'POST' and request.args.get('state') != login_session['state']):
		return redirect(url_for('userlogin'))

	if login_session['type'] == "4":
		return redirect(url_for('logout', state=login_session['state']))

	if request.method == 'GET':
		state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
		login_session['state']=state


		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor = db.cursor()

		query = "SELECT * FROM offers Where Active = 1"
		cursor.execute(query)

		offers = cursor.fetchall()
		

		# try:
		# 	arbic = arabic_reshaper.reshape(u"السلام عليكم ورحمه الله وبركاته dsf")
		# 	arbic = get_display(arbic)
		# 	c = canvas.Canvas(app.config['UPLOAD_FOLDER'] + "hello.pdf")
		# 	textobject = c.beginText()
 	# 		textobject.setTextOrigin(inch, 2.5*inch)
 	# 		pdfmetrics.registerFont(TTFont('Arabic-bold', app.config['UPLOAD_FOLDER'] + 'PalatinoSansArabic-Bold.ttf'))
 	# 		textobject.setFont("Arabic-bold", 14)
 	# 		#pdfmetrics.registerFont(TTFont('Arabic-bold', '/path-to-your-arabic-font'))
 	# 		textobject.textLines(arbic)
 		
 	# 		c.drawText(textobject)
 	# 		c.save()
 	# 		return send_file(app.config['UPLOAD_FOLDER'] + "hello.pdf")
		# except Exception as e:
		# 	return jsonify(str(e))
		# else:
		# 	pass
		# finally:
		# 	pass

		

		#user type (1,2,3,4) for (ethad,club,player,company)

		if login_session['type'] == "3":
			query = "SELECT * FROM player WHERE PlayerID = " + str(login_session['id'])
			cursor.execute(query)
			persondata = cursor.fetchone()
			db.close()

			return render_template('client-search-offers.html', STATE=state, Offers=offers, Type=login_session['type'], person=persondata)

		elif login_session['type'] == "2":
			query = "SELECT * FROM club WHERE ClubID = " + str(login_session['id'])
			cursor.execute(query)
			clubdata = cursor.fetchone()
			db.close()

			return render_template('client-search-offers.html', STATE=state, Offers=offers, Type=login_session['type'], club=clubdata)

		
		

		
	else:
		if 'getoffercontent' in request.json:

			#return jsonify('ssssssssssssfvffd')

			offerid = request.json['offerid']
			db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
			cursor = db.cursor()

			try:
				query = "SELECT * FROM offers WHERE OfferID = " + str(offerid)
				cursor.execute(query)

				offercontent = cursor.fetchone()

				query = "SELECT * FROM risks WHERE Active = 1 and OfferID = " + str(offerid)
				cursor.execute(query)

				risks = cursor.fetchall()

				query = "SELECT * FROM risks_techniques WHERE RiskID IN ("\
						"SELECT RiskID FROM risks WHERE Active = 1 and OfferID = %s)"
				cursor.execute(query,(offerid,))

				risks_techniques = cursor.fetchall()

				temprisks_tech = [ x[2] for x in risks_techniques]

				query = "SELECT * FROM techniques WHERE Active = 1 and TechniqueID IN %s"
				cursor.execute(query,(temprisks_tech,))

				techniques = cursor.fetchall()

				query = "SELECT * FROM services WHERE Active = 1 and TechniqueID IN %s"
				cursor.execute(query,(temprisks_tech,))

				services = cursor.fetchall()

				query = "SELECT *,ROUND(((Period * 12 * MonthlyPayment) + FirstPayment) * (1 + AddedPercentage / 100), 2) FROM payments_offers "\
						"WHERE Active = 1 and OfferID = " + str(offerid)
				cursor.execute(query)
				
				payments = cursor.fetchall()

				


				

				db.close()

				return jsonify({'offercontent' : offercontent, 'risks' : risks, 'risks_techniques' : risks_techniques,  
							   'techniques' : techniques, 'services' : services, 'payments':payments})




			except Exception as e:
				db.close()
				return jsonify(str(e))
		elif 'applyforoffer' in request.json:
			try:
				#return send_file(app.config['UPLOAD_FOLDER']  + 'hello.pdf')


				db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
				cursor = db.cursor()
				#player account
				if login_session['type'] == "3":
					#return jsonify('ssssssss')
					

					offerid = request.json['offerid']
					techid = request.json['techid']
					riskid = request.json['riskid']
					serviceid = request.json['serviceid']
					paymentid = request.json['periodid']

					q1 = request.json['q1']
					q2 = request.json['q2']
					q2text = request.json['q2text']
					q3 = request.json['q3']
					q3text = request.json['q3text']
					q4text = request.json['q4text']
					q5 = request.json['q5']
					q6 = request.json['q6']
					q6text = request.json['q6text']
					q7 = request.json['q7']
					q7text = request.json['q7text']
					visatype = request.json['visatype']
					visano = request.json['visano']

					

					query = "INSERT INTO clients_applied_for (ClientID, RiskID, TechniqueID, ServiceID, PaymentID) "\
							"SELECT * FROM (SELECT %s, %s, %s, %s, %s) AS TEMP "\
							"WHERE NOT EXISTS (SELECT * FROM clients_applied_for WHERE ClientID = %s and RiskID = %s and "\
							"TechniqueID = %s and ServiceID = %s and PaymentID = %s)"
					cursor.execute(query,(login_session['id'], riskid, techid, serviceid, paymentid,
								  login_session['id'], riskid, techid, serviceid, paymentid))



					applyforid = cursor.lastrowid
					db.commit()



					if cursor.rowcount == 0:
						db.close()
						return jsonify('duplicate')
					else:
						try:


							
							config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
							dirname = os.path.dirname(__file__)
							filename = os.path.join(dirname, 'static/site/offers/players/')

							pdfkit.from_string(request.json['pdf'], filename + 'c' + str(login_session['id']) +'apllyfor'+ str(applyforid) + '.pdf', configuration = config)
							

		 					
		 				# 	doc = SimpleDocTemplate(app.config['UPLOAD_FOLDER'] + "hello.pdf", pagesize=A4,
       #                  							rightMargin=50,leftMargin=50,topMargin=50,bottomMargin=18)
		 				# 	pdfmetrics.registerFont(TTFont('Arabic', app.config['UPLOAD_FOLDER'] + 'Bahij-Palatino-Sans-Arabic-Regular.ttf'))
		 				# 	pdfmetrics.registerFont(TTFont('Arabic-bold', app.config['UPLOAD_FOLDER'] + 'Bahij_TheSansArabic-Bold.ttf'))
		 				# 	#styles = getSampleStyleSheet()
		 				# 	story = []

		 				# 	para_style = ParagraphStyle(name='Jusstify', justifyBreaks=1, fontName='Arabic-bold', alignment=1, backColor='#000000')
		 				# 	#change language of sublim get error but if changed from preferences + settings
							# #and add font-face:"arial" all get well and brackets acts well
							# para = arabic_reshaper.reshape(u"<font size=22 color='white'>بوليصه (عقد) التامين ضد المخاطر الرياضيه عقد فردى <br/><br/><br/></font>")
		 				# 	para = get_display(para)

		 				# 	#en = "<font size=22 color='white'>.(ﻯﺩﺮﻓ ﺪﻘﻋ) ﻪﻴﺿﺎﻳﺮﻟﺍ ﺮﻃﺎﺨﻤﻟﺍ ﺪﺿ ﻦﻴﻣﺎﺘﻟﺍ (ﺪﻘﻋ) ﻪﺼﻴﻟﻮﺑ<br/><br/><br/></font>"

		 					




		 				# 	story.append(Paragraph(para, style = para_style))
		 				# 	story.append(Spacer(1, 12))

		 				# 	para_style = ParagraphStyle(name='Jusstify', fontName='Arabic-bold', alignment=2)
		 				# 	para = arabic_reshaper.reshape(u"<font size=14 color='black'><strong> بيانات شخصيه </strong><br/></font>")
		 				# 	para = get_display(para)

		 				# 	story.append(Paragraph(para, style = para_style))
		 				# 	story.append(Spacer(1, 12))

		 				# 	para_style = ParagraphStyle(name='Jusstify', fontName='Arabic-bold', alignment=2)

		 				# 	query = "SELECT * FROM player WHERE PlayerID = " + str(login_session['id'])
		 				# 	cursor.execute(query)

		 				# 	result = cursor.fetchone()

		 				# 	#para_style = ParagraphStyle(name='Jusstify', fontName='Arabic-bold', alignment=2)

		 				# 	pdfmetrics.registerFont(TTFont('Vera', app.config['UPLOAD_FOLDER'] + 'Bahij-Palatino-Sans-Arabic-Regular.ttf'))
							# pdfmetrics.registerFont(TTFont('Vera-Bold', app.config['UPLOAD_FOLDER'] + 'Bahij_TheSansArabic-Bold.ttf'))

							# addMapping('Vera', 0, 0, 'Vera') #normal
							# #addMapping('Vera', 0, 1, 'Vera-Italic') #italic
							# addMapping('Vera', 1, 0, 'Vera-Bold') #bold
							# #addMapping('Vera', 1, 1, 'Vera-BoldItalic') #italic and bold


		 				# 	#para_style = create_paragraph_style("ms", "SansArabic", normal="Arabic-Regular", bold="Arabic-Bold")
		 				# 	#para_style.alignment = 2

		 				# 	table = []

		 				# 	para_style = ParagraphStyle(name='Jusstify', fontName='Vera', alignment=2)

		 				# 	para = arabic_reshaper.reshape(u"<font>%s &nbsp;&nbsp; :<b>الاسم</b></font><br/> " % result[1] )
		 				# 	para = get_display(para)


		 				# 	#para = "<font> <b>:ﻢﺳﻻﺍ</b> : %s <br/></font><br/>" % "ﻯﺮﺼﻤﻟﺍ ﺩﺎﺤﺗﻻﺍ"
		 				# 	#para = get_display(para)

		 				# 	story.append(Paragraph(para, style = para_style))
		 				# 	#story.append(Spacer(4, 0))
		 				# 	#table.append([Paragraph(para, style = para_style)])

		 				# 	para = arabic_reshaper.reshape(u"%s &nbsp;&nbsp;:<b>بطاقه الرقم القومى</b>" % result[5])
		 				# 	para = get_display(para)
		 				# 	para_style = ParagraphStyle(name='Jusstify', fontName='Vera', alignment=2)

		 				# 	story.append(Paragraph(para, style = para_style))



		 				# 	para = arabic_reshaper.reshape(u"%s &nbsp;&nbsp;:<b>الوظيفه</b>" % result[2])
		 				# 	para = get_display(para)
		 				# 	para_style = ParagraphStyle(name='Jusstify', fontName='Vera', alignment=2)

		 				# 	story.append(Paragraph(para, style = para_style))





		 				# 	# para = arabic_reshaper.reshape(u"%s &nbsp;&nbsp;:<b>العنوان</b>" % result[3])
		 				# 	# para = get_display(para)
		 				# 	# para_style = ParagraphStyle(name='Jusstify', fontName='Vera', alignment=2)

		 				# 	# story.append(Paragraph(para, style = para_style))
		 					

		 				# 	# para = arabic_reshaper.reshape(u"%s&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s &nbsp;&nbsp;:<b>رقم التليفون</b>" % (result[4],result[4]))
		 				# 	# para = get_display(para)
		 				# 	# para_style = ParagraphStyle(name='Jusstify', fontName='Vera', alignment=2)

		 				# 	# story.append(Paragraph(para, style = para_style))



                                							









		 				# 	doc.build(story)

		 				# 	return jsonify('ddddddd')



						except Exception as e:
							return jsonify(str(e))
						

						# try:
		# 	arbic = arabic_reshaper.reshape(u"السلام عليكم ورحمه الله وبركاته dsf")
		# 	arbic = get_display(arbic)
		# 	c = canvas.Canvas(app.config['UPLOAD_FOLDER'] + "hello.pdf")
		# 	textobject = c.beginText()
 	# 		textobject.setTextOrigin(inch, 2.5*inch)
 	# 		pdfmetrics.registerFont(TTFont('Arabic-bold', app.config['UPLOAD_FOLDER'] + 'PalatinoSansArabic-Bold.ttf'))
 	# 		textobject.setFont("Arabic-bold", 14)
 	# 		#pdfmetrics.registerFont(TTFont('Arabic-bold', '/path-to-your-arabic-font'))
 	# 		textobject.textLines(arbic)
 		
 	# 		c.drawText(textobject)
 	# 		c.save()
 	# 		return send_file(app.config['UPLOAD_FOLDER'] + "hello.pdf")
		# except Exception as e:
		# 	return jsonify(str(e))
		# else:
		# 	pass
		# finally:
		# 	pass

						return jsonify('done')
				#club
				elif login_session['type'] == "2":

					offerid = request.json['offerid']
					techid = request.json['techid']
					riskid = request.json['riskid']
					serviceid = request.json['serviceid']
					paymentid = request.json['periodid']

					q1 = request.json['q1']
					q2 = request.json['q2']
					q2text = request.json['q2text']
					q3 = request.json['q3']
					q3text = request.json['q3text']
					q4text = request.json['q4text']
					q5 = request.json['q5']
					q6 = request.json['q6']
					q6text = request.json['q6text']
					q7 = request.json['q7']
					q7text = request.json['q7text']
					visatype = request.json['visatype']
					visano = request.json['visano']

					

					query = "INSERT INTO clients_applied_for (ClientID, RiskID, TechniqueID, ServiceID, PaymentID) "\
							"SELECT * FROM (SELECT %s, %s, %s, %s, %s) AS TEMP "\
							"WHERE NOT EXISTS (SELECT * FROM clients_applied_for WHERE ClientID = %s and RiskID = %s and "\
							"TechniqueID = %s and ServiceID = %s and PaymentID = %s)"
					cursor.execute(query,(login_session['id'], riskid, techid, serviceid, paymentid,
								  login_session['id'], riskid, techid, serviceid, paymentid))



					applyforid = cursor.lastrowid
					db.commit()



					if cursor.rowcount == 0:
						db.close()
						return jsonify('duplicate')
					else:
						try:
							config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
							dirname = os.path.dirname(__file__)
							filename = os.path.join(dirname, 'static/site/offers/clubs/')



							#pdfkit.from_string(request.json['pdf'],'22.pdf',configuration = config)

							pdfkit.from_string(request.json['pdf'], filename + 'c' + str(login_session['id']) +'apllyfor'+ str(applyforid) + '.pdf', configuration = config)
							
						except Exception as e:
							return jsonify(str(e))
						return jsonify('done')
			except Exception as e:
				db.close()
				return jsonify(str(e))

@app.route('/clientoffers', methods=['GET', 'POST'])
def ClientOffers():
	if 'username' not in login_session or (request.method == 'POST' and request.args.get('state') != login_session['state']):
		return redirect(url_for('userlogin'))
	
	if login_session['type'] == "4":
		return redirect(url_for('logout', state=login_session['state']))

	if request.method == 'GET' and 'pdf' not in request.args:
		db = MySQLdb.connect("localhost","root","","Insurance",use_unicode=True, charset='utf8')
		cursor = db.cursor()
		query = "SELECT * FROM clients_applied_for WHERE ClientID = " + str(login_session['id'])
		cursor.execute(query)

		alloffers = cursor.fetchall()

		state = ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase)
                    for x in xrange(32))
		login_session['state']=state
		


		return render_template('client-offers.html', Offers=alloffers, STATE=state)
	elif request.method == 'GET' and 'pdf' in request.args:
		#return jsonify(app.config['Offers_Folder'] + request.args['pdf'] + '.pdf')
		try:
			pdfname = request.args['pdf']
			apllyfor = pdfname.index('apllyfor')
			c = pdfname.index('c')
			if pdfname[ (int(c) + 1) :  int(apllyfor) ] != str(login_session['id']):
				return redirect(url_for('logout', state=login_session['state']))
		except Exception as e:
			return jsonify('notfount')

		dirname = os.path.dirname(__file__)
		filename = ""
		if login_session['type'] == "3":
			filename = os.path.join(dirname, 'static/site/offers/players/')
		elif login_session['type'] == "2":
			filename = os.path.join(dirname, 'static/site/offers/clubs/')

		if os.path.isfile(filename + request.args['pdf'] + '.pdf'):
			return send_file(filename + request.args['pdf'] + '.pdf')
		else:
			return jsonify('notfound')
		
		



			


def create_paragraph_style(name, font_name, **kwargs):
    ttf_path = app.config['UPLOAD_FOLDER'] + "{}.ttf"
    family_args = {}  # store arguments for the font family creation
    for font_type in ("normal", "bold", "italic", "boldItalic"):  # recognized font variants
        if font_type in kwargs:  # if this type was passed...
            font_variant = "{}-{}".format(font_name, font_type)  # create font variant name
            pdfmetrics.registerFont(TTFont(font_variant, ttf_path.format(kwargs[font_type])))
            family_args[font_type] = font_variant  # add it to font family arguments
    pdfmetrics.registerFontFamily(font_name, **family_args)  # register a font family
    return ParagraphStyle(name=name, fontName=font_name, fontSize=10, leading=12)
# if __name__ == '__main__':
# 	app.secret_key = os.urandom(32)
	
# 	#app.config['UPLOAD_FOLDER']	= '/static/assets/uimg'
# 	# reload(sys)
# 	# sys.setdefaultencoding('utf-8')
# 	app.debug = True
# 	app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

# 	app.run()


		








