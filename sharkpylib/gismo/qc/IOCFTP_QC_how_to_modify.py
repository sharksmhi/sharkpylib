#!/usr/bin/python

try:
	import numpy
except:
	pass

import logging
import os
from math import radians, cos, sin, sqrt, atan2
import datetime
import re

#-------------------------------------------------------
# if 'linux' in os.sys.platform:
# 	if os.environ["SMHI_MODE"]=='utv':
# 		PATH='/data/proj/iocftp/'
# 	elif os.environ["SMHI_MODE"]=='test':
# 		PATH='/data/prodtest/iocftp/'
# 	elif os.environ["SMHI_MODE"]=='prod':
# 		PATH='/data/24/iocftp/'
#
# 	if os.environ["SMHI_MODE"]=='prod':
# 		CFG_FILE_PATH='/data/prod/Obs_Oceanografi/Arkiv/CMEMS/data/cfg/'
# 		QC_FILE_PATH='/data/prod/Obs_Oceanografi/Arkiv/CMEMS/data/qc/'
# 	else:
# 		CFG_FILE_PATH=PATH + 'QC/config/'
# 		QC_FILE_PATH=PATH + 'QC/config/'
# elif 'win' in os.sys.platform:
# 	#CFG_FILE_PATH=r'\\winfs\data\prod\Obs_Oceanografi\Arkiv\CMEMS\data\cfg\\' #\\winfs-proj\data\proj\iocftp\QC\config\\'
# 	#QC_FILE_PATH=r'\\winfs\data\prod\Obs_Oceanografi\Arkiv\CMEMS\data\qc\\' #\\winfs-proj\data\proj\iocftp\QC\config\\' #

	
	

CFG_FILE_PATH = None
QC_FILE_PATH = None

def set_config_path(config_path):
	global CFG_FILE_PATH
	CFG_FILE_PATH = config_path
    
def set_qc_path(qc_path):
	global QC_FILE_PATH
	QC_FILE_PATH = qc_path

#-------------------------------------------------------

def distance_haversine(LAT1,LONG1,LAT2,LONG2):
	radius=6371000
	""" note that the default distance is in meters """
	dLat = radians(LAT2-LAT1)
	dLon = radians(LONG2-LONG1)
	lat1 = radians(LAT1)
	lat2 = radians(LAT2)
	a = sin(dLat/2) * sin(dLat/2) + sin(dLon/2) * sin(dLon/2) * cos(lat1) * cos(lat2)
	c = 2 * atan2(sqrt(a), sqrt(1-a)) 
	return c * radius
#-------------------------------------------------------
	
# Ferrybox_cfg.txt
def load_FERRYBOX_CFG(FILE,LOGGER):
	global cfg_FERRYBOX_Basin
	global cfg_FERRYBOX_Harbour
	global cfg_flowMin
	global cfg_speedMin
	global cfg_tempDiffMax
	global cfg_tempDiffMaxCO2
	global SST_NR
	global PSAL_NR
	global COX_NR	
	global BOX9_NR		
	Log = logging.getLogger(LOGGER)
	Log.debug('')
	Log.debug('load_FERRYBOX_CFG')	
	Log.debug('Open file : ' + FILE)
	try:
		cfg_file=open(FILE)
	except:
		Log.critical('Error read file: ' + FILE)
		cfg_file=[]
		
	cfg_FERRYBOX_Basin=[]
	cfg_FERRYBOX_Harbour=[]
	SST_NR=[]
	PSAL_NR=[]
	COX_NR=[]
	BOX9_NR=[]
	for line in cfg_file:
		data=line.split(',')
		if len(data)>0:
			if data[0] == '1':
				row=[]
				row.append(float(data[1]))
				row.append(float(data[2]))
				row.append(float(data[3]))
				row.append(float(data[4]))
				row.append(float(data[5]))
				cfg_FERRYBOX_Basin.append(row)		
			if data[0] == '2':
				row=[]
				row.append(float(data[1]))
				row.append(float(data[2]))
				row.append(float(data[3]))
				row.append(float(data[4]))
				cfg_FERRYBOX_Harbour.append(row)	
			if data[0] == '3':
				cfg_flowMin=float(data[1])
			if data[0] == '4':
				cfg_speedMin=float(data[1])
			if data[0] == '5':
				cfg_tempDiffMax=float(data[1])
			if data[0] == '6':
				cfg_tempDiffMaxCO2=float(data[1])
			if data[0] == '7':
				temp2=line.split(',')[1].replace('[','').replace(']','').split()
				SST_NR.append(temp2)
			if data[0] == '8':
				temp2=line.split(',')[1].replace('[','').replace(']','').split()
				PSAL_NR.append(temp2)
			if data[0] == '9':
				temp2=line.split(',')[1].replace('[','').replace(']','').split()
				COX_NR.append(temp2)				
			if data[0] == '10':
				temp2=line.split(',')[1].replace('[','').replace(']','').split()
				BOX9_NR.append(temp2)				
				
	cfg_FERRYBOX_Basin=numpy.squeeze(numpy.asarray(cfg_FERRYBOX_Basin))			
	cfg_FERRYBOX_Harbour=numpy.squeeze(numpy.asarray(cfg_FERRYBOX_Harbour))	
	
	
#-------------------------------------------------------
	
# Example: CMEMS_QC_FB_TEMP.txt
def load_FERRYBOX_CMEMS_QC_CONSTANT(FILE,LOGGER):	
	global FERRYBOX_CMEMS_QC_dict_constant
	Log = logging.getLogger(LOGGER)	
	Log.debug('Open file (FERRYBOX_QC) : ' + FILE)
	try:
		qc_file=open(FILE)
	except:
		Log.critical('Error read file: ' + FILE)
		qc_file=[]
	for line in qc_file:
		row=line.split()
		try:
			#FERRYBOX_CMEMS_QC_dict_constant[row[0]+row[1]+row[3] +row[2]] = row
			FERRYBOX_CMEMS_QC_dict_constant[row[0]+row[1]+  '%02.0f' % int(row[3]) +row[2]] = row
		except:
			Log.error('Error read row in: ' + FILE) 
			Log.error(row)	
#-------------------------------------------------------
			
# Example: CMEMS_QC_MO_SLEV.txt
def load_CMEMS_QC_CONSTANT(FILE,STATION_NR,LOGGER):	
	global CMEMS_QC_dict_constant
	Log = logging.getLogger(LOGGER)	
	Log.debug('Open file (CMEMS_QC) : ' + FILE)
	try:
		qc_file=open(FILE)
	except:
		Log.critical('Error read file: ' + FILE)
		qc_file=[]
	for line in qc_file:
		row=line.split()
		try:
			if row[0] == STATION_NR:
				CMEMS_QC_dict_constant[row[0]+row[3]+row[5] +row[4]] = row
		except:
			Log.error('Error read row in: ' + FILE) 
			Log.error(row)
#-------------------------------------------------------
			
# Load STATION_STATUS.txt
def load_STATION_STATUS(FILE,STATION_NR,LOGGER):	
	global cfg_STATION_STATUS
	Log = logging.getLogger(LOGGER)
	Log.debug('')
	Log.debug('load_STATION_STATUS')	
	Log.debug('Open file : ' + FILE)
	try:
		cfg_file=open(FILE)
	except:
		Log.critical('Error read file: ' + FILE)
		cfg_file=[]
	cfg_STATION_STATUS=[]
	for line in cfg_file:
		row=line.split()
		if row[0] == STATION_NR:
			rad=[]
			try:
				rad.append(row[0])
				rad.append(row[1].replace('[','').replace(']','').split())
				rad.append(datetime.datetime.strptime(row[2],'%Y-%m-%dT%H:%M:%S'))
				if len(row)==4:
					rad.append(datetime.datetime.strptime(row[3],'%Y-%m-%dT%H:%M:%S'))
				else:
					rad.append(datetime.datetime.now())
				cfg_STATION_STATUS.append(rad)
				Log.debug('Add row: ')
				Log.debug(rad)
			except:
				Log.warning('Error read STATION_STATUS row: ')
				Log.warning(line)
#-------------------------------------------------------
				
# load CMEMS_CORRECTIONS.txt
def load_vst_corrections(FILE,STATION_NR,LOGGER):	
	global cfg_vst_corrections_dict
	Log = logging.getLogger(LOGGER)	
	Log.debug('Open file : ' + FILE)
	Log.debug('Try to find STATION_NR : ' + str(STATION_NR))
	try:
		cfg_file=open(FILE)
	except:
		Log.critical('Error read file: ' + FILE)
		cfg_file=[]
	for line in cfg_file:
		row=line.split()
		if row[0] == STATION_NR:
			cfg_vst_corrections_dict[row[0]+row[1]] = row		
	Log.debug('Get cfg_vst_corrections_dict2 : ' + str(cfg_vst_corrections_dict))
#-------------------------------------------------------
	
# load QC_setup_cfg.txt	
def load_QC_SETUP_FILE(FILE,LOGGER):	
	global CMEMS_QC_FILE_dict
	global FERRYBOX_CMEMS_QC_FILE_dict
	global CMEMS_QC_SETUP_DEPTH_dict
	global WISKI_QC0
	WISKI_QC0=[]
	Log = logging.getLogger(LOGGER)
	Log.debug('load_QC_SETUP_FILE')	
	Log.debug('Open file : ' + FILE)
	try:
		qc_setup_file=open(FILE)
	except:
		Log.critical('Error read file: ' + FILE)
		qc_setup_file=[]
		
	for line in qc_setup_file:
		row=line.split()
		if len(row)>0:
			if row[0]=='CMEMS_QC':
				if ":" in line:
					value=row[1].replace('[','').replace(']','').split(':')
					for parameter in range(int(value[0]),int(value[1])+1,1):
						CMEMS_QC_FILE_dict[str(parameter)]=row[2]
				else:	
					parameters=row[1].replace('[','').replace(']','').split(',')					
					for parameter in parameters:
						CMEMS_QC_FILE_dict[parameter]=row[2]							
			if row[0]=='CMEMS_QC_FERRYBOX':
				if ":" in line:
					value=row[1].replace('[','').replace(']','').split(':')
					for parameter in range(int(value[0]),int(value[1])+1,1):
						FERRYBOX_CMEMS_QC_FILE_dict[str(parameter)]=row[2]
				else:	
					parameters=row[1].replace('[','').replace(']','').split(',')	
					for parameter in parameters:
						FERRYBOX_CMEMS_QC_FILE_dict[parameter]=row[2]						
			if row[0]=='DEPTH':
				if ":" in line:
					value=row[1].replace('[','').replace(']','').split(':')
					for parameter in range(int(value[0]),int(value[1])+1,1):
						CMEMS_QC_SETUP_DEPTH_dict[str(parameter)+row[2]]=row[3]
				else:	
					parameters=row[1].replace('[','').replace(']','').split(',')					
					for parameter in parameters:
						CMEMS_QC_SETUP_DEPTH_dict[str(parameter)+row[2]]=row[3]
			if row[0]=='WISKI_QC0':
				if ":" in line:
					value=row[1].replace('[','').replace(']','').split(':')
					for parameter in range(int(value[0]),int(value[1])+1,1):
						WISKI_QC0.append(float(parameter))
				else:	
					parameters=row[1].replace('[','').replace(']','').split(',')					
					for parameter in parameters:
						WISKI_QC0.append(float(parameter))
#-------------------------------------------------------				

def get_cfg_data(STATION_NR, HEADER, QC_FILE_PATH, QC_SETUP_FILE, LOGGER):
	global CMEMS_QC_FILE_dict
	global cfg_vst_corrections_dict
	global CMEMS_QC_dict_constant
	global CMEMS_QC_SETUP_DEPTH_dict
	global FERRYBOX_CMEMS_QC_FILE_dict
	LLogging=0
	if len(LOGGER)>0:
		# Logger
		Log = logging.getLogger(LOGGER)
		Log.debug('')
		Log.debug('get_cfg_data')
		LLogging=1

	CMEMS_QC_dict_constant={}	
	cfg_vst_corrections_dict={}
	CMEMS_QC_FILE_dict={}
	CMEMS_QC_SETUP_DEPTH_dict={}
	FERRYBOX_CMEMS_QC_FILE_dict={}
	
	# Load correction to convert vst-height SW -> RW
	Log.debug('load_vst_corrections')
	load_vst_corrections(CFG_FILE_PATH + 'CMEMS_CORRECTIONS.txt',STATION_NR,LOGGER)	
	# Load QC_setup_cfg.txt 
	load_QC_SETUP_FILE(CFG_FILE_PATH + QC_SETUP_FILE, LOGGER)
	
	# Get a list of unique CMEMS_QC_files
	# For t.ex. WTEMP load that file only once
	
	Log.debug('Check CMEMS_QC_FILE_dict')
	revDict = {}
	QC_files=[]
	for k, v in CMEMS_QC_FILE_dict.items():
		if v in revDict:
			revDict[v] = None
		else:
			revDict[v] = k
			QC_files.append(v)

	[ x for x in revDict.values() if x != None ]
	for i in range(HEADER.shape[0]):
		Log.debug('Looking for CMEMS_QC_CONSTANT_FILE for: ' + str(int(HEADER[i])))
		key=str(int(HEADER[i]))
		res=CMEMS_QC_FILE_dict.get(key,'-999')	
		if res != '-999':
			if res in QC_files:
				QC_files=filter(lambda a: a != res, QC_files) 
				Log.debug('load_CMEMS_QC_CONSTANT: ' + QC_FILE_PATH + res + ' ,STATION_NR: ' + STATION_NR)
				load_CMEMS_QC_CONSTANT(QC_FILE_PATH + res,STATION_NR,LOGGER)
		else:
			Log.debug('No CMEMS_QC_CONSTANT_FILE for: ' + str(int(HEADER[i])))
	Log.debug('Finish get_cfg_data')
	Log.debug('')
	return CMEMS_QC_dict_constant
#-------------------------------------------------------

def get_cfg_data_FERRYBOX(STATION_NR,HEADER,QC_FILE_PATH,QC_SETUP_FILE,LOGGER):
	global CMEMS_QC_FILE_dict
	global FERRYBOX_CMEMS_QC_FILE_dict
	global FERRYBOX_CMEMS_QC_dict_constant
	global CMEMS_QC_SETUP_DEPTH_dict
	if len(LOGGER)>0:
		# Logger
		Log = logging.getLogger(LOGGER)
		Log.debug('')
		Log.debug('get_cfg_data_FERRYBOX')

	CMEMS_QC_dict_constant={}	
	CMEMS_QC_FILE_dict={}
	FERRYBOX_CMEMS_QC_dict_constant={}
	FERRYBOX_CMEMS_QC_FILE_dict={}
	CMEMS_QC_SETUP_DEPTH_dict={}
	
	# Load QC_setup_cfg.txt 
	load_QC_SETUP_FILE(CFG_FILE_PATH + QC_SETUP_FILE, LOGGER)
	
	
	# Get a list of unique CMEMS_QC_files
	# For t.ex. WTEMP load that file only once
	revDict = {}
	QC_files=[]
	for k, v in FERRYBOX_CMEMS_QC_FILE_dict.items():
		if v in revDict:
			revDict[v] = None
		else:
			revDict[v] = k
			QC_files.append(v)

	[ x for x in revDict.values() if x != None ]
	
	for i in range(HEADER.shape[0]):
		key=str(int(HEADER[i]))
		res=FERRYBOX_CMEMS_QC_FILE_dict.get(key,'-999')	
		if res != '-999':
			if res in QC_files:
				QC_files=filter(lambda a: a != res, QC_files) #
				Log.debug('load_FERRYBOX_CMEMS_QC_CONSTANT: ' + QC_FILE_PATH + res + ' ,STATION_NR: ' + STATION_NR)
				load_FERRYBOX_CMEMS_QC_CONSTANT(QC_FILE_PATH + res,LOGGER)
				
	return FERRYBOX_CMEMS_QC_dict_constant


### QC test5 ### Gross Range Test / Climatology Test
def QC_TEST5(VALUE,RANGE_TEST_MIN,RANGE_TEST_MAX,STD):
	
	# QC=1, Range +-1*SD
	RANGE_TEST_MIN_QC1=RANGE_TEST_MIN-1*STD	
	RANGE_TEST_MAX_QC1=RANGE_TEST_MAX+1*STD
	
	# QC=2, Range +-2*SD
	RANGE_TEST_MIN_QC2=RANGE_TEST_MIN-2*STD	
	RANGE_TEST_MAX_QC2=RANGE_TEST_MAX+2*STD

	# QC=3, Range +-3*SD
	RANGE_TEST_MIN_QC3=RANGE_TEST_MIN-3*STD	
	RANGE_TEST_MAX_QC3=RANGE_TEST_MAX+3*STD

	if RANGE_TEST_MIN_QC1 <= VALUE <= RANGE_TEST_MAX_QC1:
		QC_T5=1
	elif RANGE_TEST_MIN_QC2 <= VALUE <= RANGE_TEST_MAX_QC2:
		QC_T5=2
	elif RANGE_TEST_MIN_QC3 <= VALUE <= RANGE_TEST_MAX_QC3:
		QC_T5=3
	else:
		QC_T5=4
		
	return QC_T5

## QC test6 ### Spike Test
def QC_TEST6(VALUES,THRSHLD_LOW,THRSHLD_HIGH):
	SPK_REF=0.5*(VALUES[0]+VALUES[2])
	# THRSHLD_HIGH
	if abs(VALUES[1]-SPK_REF) > THRSHLD_HIGH:
		QC_T6=4
	elif THRSHLD_LOW < abs(VALUES[1]-SPK_REF) <= THRSHLD_HIGH:
		QC_T6=3
	else:
		QC_T6=1			
	return QC_T6

## QC test7 ### Rate of Change Test
def QC_TEST7(VALUES,NDEV):
	SD=numpy.std(VALUES[:-1])
	if abs(VALUES[-1]-VALUES[-2]) > NDEV*SD:
		QC_T7=3
	else:
		QC_T7=1
		
	return QC_T7

## QC test8 ### Flat line test
def QC_TEST8(VALUES,VALUEF,RCNTS,RCNTF,TEPS):
	if abs(max(VALUEF) - min(VALUEF)) < TEPS:
		QC_T8=4
	elif abs(max(VALUES) - min(VALUES)) < TEPS:
		QC_T8=3
	else:
		QC_T8=1
		
	return QC_T8


def QC_CHECK(STATION,STATION_NR,DATA,HEADER_NR,LOGGER,PARAMETERS):
	global cfg_vst_corrections_dict
	#cfg_vst_corrections_dict=[0,0]
	LLogging=0
	if len(LOGGER)>0:
		# Logger
		Log = logging.getLogger(LOGGER)
		Log.info('')
		Log.info('QC_CHECK: ' + STATION + ' ' + STATION_NR)
		LLogging=1
	if len(PARAMETERS)==2:
		pass
		#LAT=PARAMETERS[0]  
		#LONG=PARAMETERS[1]    

	if HEADER_NR.ndim==2:
		header_np=HEADER_NR[0]
	else:
		header_np=HEADER_NR
			
	data_np=DATA #numpy.squeeze(numpy.asarray(DATA))
	
	dim_corr=0
	if data_np.ndim==1:
		dim_corr=1
		data_np=numpy.vstack([data_np,data_np])
		if LLogging==1:
			Log.debug('only one observation make data-matrix 2-dimensional for proper work')
		else:
			print('only one observation make data-matrix 2-dimensional for proper work')

	# Create a dictionery with range mm 
	Log.debug('Get CMEMS_QC_dict_constant')
	CMEMS_QC_dict_constant=get_cfg_data(STATION_NR,header_np,QC_FILE_PATH,'QC_setup_cfg.txt',LOGGER)
	
	# Load QC_setup_cfg.txt 
	#load_QC_SETUP_FILE(CFG_FILE_PATH + 'QC_setup_cfg.txt',LOGGER)
	
	# Get station_status
	Log.debug('load_STATION_STATUS')
	load_STATION_STATUS(CFG_FILE_PATH + 'STATION_STATUS.txt',STATION_NR,LOGGER)
	
	# Get default position from QC-files
	try: LAT= float(CMEMS_QC_dict_constant.get(CMEMS_QC_dict_constant.keys()[0],'-999')[1])
	except: LAT=-999
	Log.debug('LAT ' + STATION + ': ' + str(LAT))
	
	try: LONG=float(CMEMS_QC_dict_constant.get(CMEMS_QC_dict_constant.keys()[0],'-999')[2])
	except: LONG=-999
	Log.debug('LONG ' + STATION + ': ' + str(LONG))

	# Check if position exist in observations 
	try: Lat_ind=int(numpy.nonzero(header_np==8002)[0])   
	except: Lat_ind=-1
	
	try: Long_ind=int(numpy.nonzero(header_np==8003)[0])
	except: Long_ind=-1
	
	# Loop rows
	for row in range(data_np.shape[0]):
		Pos='OK'
		QC_POS=1
		# Test 3, Position test		
		if Lat_ind > -1 and Long_ind > -1:
			if data_np[row,Lat_ind] > -999 and data_np[row,Long_ind]> -999 and LAT > -999 and LONG > -999:
				#Log.debug('Lat obs: ' + str(data_np[row,Lat_ind]))
				#Log.debug('Long obs: ' + str(data_np[row,Long_ind]))
				#Log.debug('Dist: ' + str(distance_haversine(LAT,LONG,data_np[row,Lat_ind],data_np[row,Long_ind])))
				if distance_haversine(LAT,LONG,data_np[row,Lat_ind],data_np[row,Long_ind]) < 1500:
					Pos='OK' # Make QC-test
					QC_POS=1
				else:
					Pos='BAD' # Mark data as bad
					QC_POS=4
					
		#if Pos=='OK':
		# Read date and time wit the datetime-function
		if len('%.0f' % data_np[row,0])==12:
			dt=datetime.datetime.strptime('%.0f' % data_np[row,0], '%Y%m%d%H%M')
		elif 	len('%.0f' % data_np[row,0])==14:
			dt=datetime.datetime.strptime('%.0f' % data_np[row,0], '%Y%m%d%H%M%S')									
		try:
			month=int(dt.strftime('%m'))
			year=int(dt.strftime('%Y'))
		except:
			Log.error('Error get year/month from timestamp: ' + str(data_np[row,0]))
			month=13
				
		# Loop columns		
		for col_ind in range(1,header_np.shape[0],2):
			QC_default=float(data_np[row,col_ind+1])
			
			# Check station status
			for line in cfg_STATION_STATUS:
				if len(line[1])==0:
					if float(line[2]) <= float(data_np[row,0]) <=  float(line[3]):
						Log.debug('Time_data: ' + str(line[2]) + ',' + str(data_np[row,0]) + ',' + str(line[3]))
						QC_default=4	
				#elif re.search(header_np[col_ind],cfg_STATION_STATUS[0][1][0]) and float(line[2]) <= float(data_np[row,0]) <=  float(line[3]):
				#elif re.search(str(int(header_np[col_ind])),str(line[1])) and float(line[2]) <= float(data_np[row,0]) <=  float(line[3]):
				elif str(int(header_np[col_ind])) in str(line[1]) and line[2] <= dt <=  line[3]:
					Log.debug('STATION_STATUS set QC_default=4')
					QC_default=4
				else:
					Log.debug('STATION_STATUS do not match: ' + str(line[1]))
					Log.debug('STATION_STATUS do not match: ' + str(line[2]))
					Log.debug('STATION_STATUS do not match: ' + str(line[3]))
				
			# If QC_default=4, bad indata no quality-controll QC=4						
			if QC_default==4:
				QC=4
				
			# Get constants
			elif Pos=='OK':								
				
				key3=str(STATION_NR) + str(int(header_np[col_ind]))
				res3=CMEMS_QC_SETUP_DEPTH_dict.get(key3,'-999')
				
				# Get depth of observation
				if res3!='-999':
					Depth=str(res3)
				elif float(header_np[col_ind])>=8600 and float(header_np[col_ind])<=8699:					
					Depth='%2.1f'% (float(header_np[col_ind])-8600)
				elif float(header_np[col_ind])>=8700 and float(header_np[col_ind])<=8799:					
					Depth='%2.1f'% (float(header_np[col_ind])-8700)	
				elif float(header_np[col_ind])>=8800 and float(header_np[col_ind])<=8899:					
					Depth='%2.1f'% (float(header_np[col_ind])-8800)
				elif float(header_np[col_ind])>=8900 and float(header_np[col_ind])<=8999:
					Depth='%2.1f'% (float(header_np[col_ind])-8900)					
				else:
					Depth='0.0'
					
				# Find row with qc-value in CMEMS Qc-files
				key=str(STATION_NR) + str(int(header_np[col_ind])) + str(month)  + Depth
				#Log.debug('Key:' + str(key))
				res=CMEMS_QC_dict_constant.get(key,'-999')
				
				if res!='-999':
					
					# QC-values test 4-5					
					LAT=float(res[1])
					LONG=float(res[2])
					
					# Check for land-uplift corrections
					key2=str(STATION_NR) + str(int(header_np[col_ind]))
					res2=cfg_vst_corrections_dict.get(key2,'-999')
					
					if res2!= '-999': 
						if float(res2[3])==0:
							RANGE_TEST_MIN=float(res[6]) 
							RANGE_TEST_MAX=float(res[7])					
						else:
							RANGE_TEST_MIN=float(res[6]) + float(res2[2]) - float(res2[3])*(year-1986)
							RANGE_TEST_MAX=float(res[7])	 + float(res2[2]) - float(res2[3])*(year-1986)
						
						"""
						Log.debug('')
						Log.debug(res2)
						Log.debug('float(res[6]): ' + str(float(res[6])))
						Log.debug('float(cfg_vst_corrections_dict[0]): ' + str(float(res2[2])))
						Log.debug('RANGE_TEST_MIN_QC2: ' + str(header_np[col_ind]) + ' ' + str(RANGE_TEST_MIN_QC2))
						Log.debug('RANGE_TEST_MAX_QC2: ' + str(header_np[col_ind]) + ' '+ str(RANGE_TEST_MAX_QC2))
						#print float(header_np[col_ind]), float(res[6]), RANGE_TEST_MIN	
						"""
					else:
						RANGE_TEST_MIN=float(res[6])
						RANGE_TEST_MAX=float(res[7])
						
					STD=float(res[9])		
					
					# QC=2, Range +-2*SD if value < 0, value=0 
					RANGE_TEST_MIN_QC2=RANGE_TEST_MIN-2*STD	
					RANGE_TEST_MAX_QC2=RANGE_TEST_MAX+2*STD					
					if RANGE_TEST_MIN_QC2 < 0 and not ((float(header_np[col_ind])>=8600 and float(header_np[col_ind])<=8699) or float(header_np[col_ind])==8033 or float(header_np[col_ind])==8195):
						RANGE_TEST_MIN_QC2=0
					elif RANGE_TEST_MIN_QC2 < -2 and (float(header_np[col_ind])>=8600 and float(header_np[col_ind])<=8699):
						RANGE_TEST_MIN_QC2=-2
					
					# QC=3, Range +-3*SD if value < 0, value=0 
					RANGE_TEST_MIN_QC3=RANGE_TEST_MIN-3*STD	
					RANGE_TEST_MAX_QC3=RANGE_TEST_MAX+3*STD					
					if RANGE_TEST_MIN_QC3 < 0 and not ((float(header_np[col_ind])>=8600 and float(header_np[col_ind])<=8699) or float(header_np[col_ind])==8033 or float(header_np[col_ind])==8195):
						RANGE_TEST_MIN_QC3=0
					elif RANGE_TEST_MIN_QC3 < -2 and (float(header_np[col_ind])>=8600 and float(header_np[col_ind])<=8699):
						RANGE_TEST_MIN_QC3=-2

					# QC=4, Range +-4*SD
					RANGE_TEST_MIN_QC4=RANGE_TEST_MIN-4*STD
					RANGE_TEST_MAX_QC4=RANGE_TEST_MAX+4*STD
					if RANGE_TEST_MIN_QC4 < 0 and not ((float(header_np[col_ind])>=8600 and float(header_np[col_ind])<=8699) or float(header_np[col_ind])==8033 or float(header_np[col_ind])==8195):
						RANGE_TEST_MIN_QC4=0
					elif RANGE_TEST_MIN_QC4 < -2 and (float(header_np[col_ind])>=8600 and float(header_np[col_ind])<=8699):
						RANGE_TEST_MIN_QC4=-2

					# If SD=Nan the get first limit
					if numpy.isnan(RANGE_TEST_MIN_QC4):
						RANGE_TEST_MIN_QC4=RANGE_TEST_MIN_QC2
						
					if numpy.isnan(RANGE_TEST_MAX_QC4):
						RANGE_TEST_MAX_QC4=RANGE_TEST_MAX_QC2
					
					if 1==2: #LLogging==1:
						Log.debug('')
						Log.debug('STNR ' + str(header_np[col_ind]))
						Log.debug('STD ' + str(STD))
						Log.debug('RANGE_TEST_MIN ' + str(RANGE_TEST_MIN))
						Log.debug('RANGE_TEST_MAX ' + str(RANGE_TEST_MAX))
						Log.debug('')
						Log.debug('RANGE_TEST_MIN_QC3 ' + str(RANGE_TEST_MIN_QC3))
						Log.debug('RANGE_TEST_MAX_QC3 ' + str(RANGE_TEST_MAX_QC3))
						Log.debug('')
						Log.debug('RANGE_TEST_MIN_QC4 ' + str(RANGE_TEST_MIN_QC4))
						Log.debug('RANGE_TEST_MAX_QC4 ' + str(RANGE_TEST_MAX_QC4))
						
					# Test 6					
					THRSHLD_HIGH=float(res[10])
					# Test 7
					N_DEV=3 #!!! NOT DEFINED!!!					
					# Test 8
					try: REP_CNT_FAIL=float(res[11])
					except: REP_CNT_FAIL=5 #-999 
					
					try: EPS=float(res[12]) 
					except: EPS=-999
					
				# --------------------------------------------------------
				# Make QC-test
				# Start with QC=1	 value change if som test is not approved
				# If sealevel QC=0
				if float(header_np[col_ind]) in WISKI_QC0:
					QC=1 #0
				else:
					QC=1  
				
				#Log.debug('QC start, test1: ' + str(QC)) 
            
				if header_np[col_ind] == 8002 or header_np[col_ind] == 8003:
					if data_np[row,col_ind]==-999:
						QC=9
					else:
						QC=QC_POS	
					#Log.debug('QC position: ' + str(QC)) 
				elif res=='-999':
					if float(data_np[row,col_ind])==-999:
						QC=9
					else: # If settings is missing in QC-file, QC=0 
						QC=0
                        
				else:
					if float(data_np[row,col_ind])==-999:
						QC=9
					else:
						# Test 4,5. Gross Range Test,Climatology test for QC=4
						if QC != 4 and RANGE_TEST_MIN != -999 and RANGE_TEST_MAX != -999:
							if data_np[row,col_ind] < RANGE_TEST_MIN_QC4 or data_np[row,col_ind] > RANGE_TEST_MAX_QC4:
								QC=4
							elif data_np[row,col_ind] < RANGE_TEST_MIN_QC3 or data_np[row,col_ind] > RANGE_TEST_MAX_QC3:
								QC=3
							elif data_np[row,col_ind] < RANGE_TEST_MIN_QC2 or data_np[row,col_ind] > RANGE_TEST_MAX_QC2:
								QC=2
							#else:
							#	QC=1
						
						#Log.debug('QC test4-5: ' + str(QC))
						
						# Test 6 Spike Test for QC=4
						#if QC != 4 and THRSHLD_HIGH != -999 and row > 1 and row < header_np.shape[0]:		
						if QC != 4 and THRSHLD_HIGH != -999 and row >= 1 and row < data_np.shape[0]-1:	
							try:
								#SPK_REF=0.5*(data_np[row-1,col_ind]+data_np[row+1,col_ind])
								#if abs(data_np[row,col_ind] - SPK_REF) > THRSHLD_HIGH:
								#	QC=4	
								if len('%.0f' % data_np[row-1,0])==12:
									dt_1=datetime.datetime.strptime('%.0f' % data_np[row-1,0], '%Y%m%d%H%M')
								elif len('%.0f' % data_np[row-1,0])==14:
									dt_1=datetime.datetime.strptime('%.0f' % data_np[row-1,0], '%Y%m%d%H%M%S')
								if len('%.0f' % data_np[row+1,0])==12:	
									dt1=datetime.datetime.strptime('%.0f' % data_np[row+1,0], '%Y%m%d%H%M')
								elif len('%.0f' % data_np[row+1,0])==14:
									dt1=datetime.datetime.strptime('%.0f' % data_np[row+1,0], '%Y%m%d%H%M%S')
								diff=dt1-dt_1
								minutes=diff.seconds/(2*60.0)	
								QC6=QC_TEST6(data_np[row-1:row+2,col_ind],THRSHLD_HIGH*minutes,THRSHLD_HIGH*minutes) #THRSHLD_LOW not defined
								if QC6==4:
									QC=QC6
							except:
								Log.error('Error make QC-test 6', exc_info=True)
								Log.error('%.0f' % data_np[row-1,0])
								if data_np.ndim==1:
									Log.error('More info1 len Data: ' + str(len(data_np)))
								else:
									Log.error('More info2 len Data: ' + str(len(data_np[0,])))	
									
						#Log.debug('QC test6: ' + str(QC))
											
						# Test 8 Flat line test for QC=4
						if QC != 4 and REP_CNT_FAIL != -999 and EPS != -999 and row >= REP_CNT_FAIL:
							#print 'make test 8'
							try:
								for i in range(REP_CNT_FAIL,data_np.shape[0]):
									if abs(max(data_np[row-REP_CNT_FAIL:row,col_ind]) - min(data_np[row-REP_CNT_FAIL:row,col_ind])) < EPS:
										QC=4
							except:
								Log.error('Error make QC-test 8', exc_info=True)
								
						#Log.debug('QC test8: ' + str(QC))
			
			else:	
				QC=4  # Bad position
				Log.debug('Bad position: ' + str(QC))
				
			if data_np[row,col_ind]==-999:
				QC=9
													
			data_np[row,col_ind+1]=QC					
	#except:
	#	if LLogging==1:
	#		Log.critical('Unexpected error: ', exc_info=True)
	#	else:
	#		print 'Unexpected error in IOCFTP_QC '

	if dim_corr==1:
		data_np=numpy.delete(data_np,1, axis=0)
		Log.debug('Remove 1-row')
	return data_np


def QC_CHECK_SHIP(STATION,STATION_NR,SMHI_WISKI_ID,DATA,HEADER_NR,LOGGER,PARAMETERS):
	global cfg_vst_corrections_dict

	# Logger
	Log = logging.getLogger(LOGGER)
	Log.info('')
	Log.info('QC_CHECK: ' + STATION + ' ' + STATION_NR)
	LLogging=1
	
	if len(PARAMETERS)==2:
		pass

	# Check if header has correct dimension
	if HEADER_NR.ndim==2:
		header_np=HEADER_NR[0]
	else:
		header_np=HEADER_NR
	
	# If one row duplicate row
	dim_corr=0
	if DATA.ndim==1:
		dim_corr=1
		DATA=numpy.vstack([DATA,DATA])
		if LLogging==1:
			Log.debug('only one observation make data-matrix 2-dimensional for proper work')
		else:
			print('only one observation make data-matrix 2-dimensional for proper work')

	# Create a dictionery with range mm 
	Log.debug('Get CMEMS_QC_dict_constant')
	CMEMS_QC_dict_constant=get_cfg_data(SMHI_WISKI_ID,header_np,QC_FILE_PATH,'QC_setup_cfg.txt',LOGGER)
	
	# Load QC_setup_cfg.txt 
	#load_QC_SETUP_FILE(CFG_FILE_PATH + 'QC_setup_cfg.txt',LOGGER)
	
	# Get station_status
	Log.debug('load_STATION_STATUS')
	load_STATION_STATUS(CFG_FILE_PATH + 'STATION_STATUS.txt',SMHI_WISKI_ID,LOGGER)
	
	# Loop rows
	key_prev=''
	for row in range(DATA.shape[0]):	
					
		# Read date and time with the datetime-function
		dt=datetime.datetime.strptime('%.0f' % DATA[row,0], '%Y%m%d%H%M')
					
		try:
			month=int(dt.strftime('%m'))
		except:
			Log.error('Error get year/month from timestamp: ' + str(DATA[row,0]))
			month=13
				
		# Loop columns
		for col_ind in range(1,header_np.shape[0],2):
			QC_tot=1;QC1=0;QC2=0;QC3=0;QC4=0;QC5=0;QC6=0;QC7=0;QC8=0;
			if DATA[row,col_ind] == -999:
				QC_tot=9
			else:
			
				QC_default=float(DATA[row,col_ind+1])
				if QC_default != 0:
					QC_tot=QC_default
				
				# Check station status
				for line in cfg_STATION_STATUS:
					if len(line[1])==0:
						if line[2] <= dt <=  line[3]:
							Log.debug('Time_data: ' + str(line[2]) + ',' + str(DATA[row,0]) + ',' + str(line[3]))
							QC_tot=4
					elif str(int(header_np[col_ind])) in str(line[1]) and line[2] <= dt <=  line[3]:
						Log.debug('STATION_STATUS set QC_default=4')
						QC_tot=4
					else:
						Log.debug('STATION_STATUS do not match: ')
						Log.debug(line)
					
				# If QC_default=4, bad indata no quality-controll QC=4						
				# Get constants
				key3=str(SMHI_WISKI_ID) + str(int(header_np[col_ind]))
				#Log.debug('key3 ' + key3)
				res3=CMEMS_QC_SETUP_DEPTH_dict.get(key3,'-999')
				#Log.debug('res3 ' + res3)
				
				# Get depth of observation
				Depth='0.0'
					
				# Find row with qc-value in CMEMS Qc-files
				#key=str(STATION_NR) + str(int(header_np[col_ind])) + str(month)  + Depth
				key1=str(SMHI_WISKI_ID) + '8195' + str(month)  + Depth
				#Log.debug('Key:' + str(key1))
				res1=CMEMS_QC_dict_constant.get(key1,'-999')
				
				if res1!='-999':
					# Read only new limits if necessary
					if key1 != key_prev:
						key_prev=key1											
						# QC-values										
						RANGE_TEST_MIN=float(res1[6])
						RANGE_TEST_MAX=float(res1[7])							
						STD=float(res1[9])		
						THRSHLD_LOW=float(res1[10])
						THRSHLD_HIGH=float(res1[11])
						RCNTF=float(res1[12])
						RCNTS=float(res1[13])
						TEPS=float(res1[14])
						NDEV=float(res1[15])
						TIMDEV=float(res1[16])
															
					# Make QC-test
					if 1==2: # Only test 6
						# Test 5 Range test
						if QC_tot != 4:
							#QC_TEST5(VALUE,RANGE_TEST_MIN,RANGE_TEST_MAX,STD)
							QC5=QC_TEST5(DATA[row,col_ind],RANGE_TEST_MIN,RANGE_TEST_MAX,STD)
							if QC5 > QC_tot:
								QC_tot = QC5
						
							Log.debug('QC5: ' + str(QC5))
						
	
					# Test 6 Spike test
					if QC_tot != 4:
						if row >= 1 and row < DATA.shape[0]-1:
							if DATA[row-1,col_ind] > -999 and DATA[row,col_ind] > -999 and DATA[row+1,col_ind] > -999:
								# Check time between observation. Multiplay by minutes to limits defined per minute
								dt_1=datetime.datetime.strptime('%.0f' % DATA[row-1,0], '%Y%m%d%H%M')
								dt1=datetime.datetime.strptime('%.0f' % DATA[row+1,0], '%Y%m%d%H%M')
								diff=dt1-dt_1
								minutes=diff.seconds/(2*60.0)
								try:
									QC6=QC_TEST6(DATA[row-1:row+2,col_ind],THRSHLD_LOW*minutes,THRSHLD_HIGH*minutes)
								except:
									QC6=0
									Log.warning('Error make Spike test')
									Log.warning(DATA[row-1:row+1,col_ind])
							else:
								QC6=0
						else:
							QC6=0
					if QC6 > QC_tot:
						QC_tot = QC6
							
					if 1==2:# Only test 6									
						# Test 7 Rate of change
						if QC_tot != 4:
							START=dt-datetime.timedelta(minutes=TIMDEV)
							ind=numpy.nonzero((DATA[:,0] > float(START.strftime('%Y%m%d%H%M'))) & (DATA[:,col_ind] > -999))[0]
							if len(ind)>2:
								QC7=QC_TEST7(DATA[ind,col_ind],NDEV)
							else:
								QC7=0
						if QC7 > QC_tot:
							QC_tot = QC7
															
						# Test 8 Flat line test for QC=4
						if QC_tot != 4:
							STARTS=dt-datetime.timedelta(minutes=RCNTS)
							indS=numpy.nonzero((DATA[:,0] > float(STARTS.strftime('%Y%m%d%H%M'))) & (DATA[:,col_ind] > -999))[0]
							STARTF=dt-datetime.timedelta(minutes=RCNTF)
							indF=numpy.nonzero((DATA[:,0] > float(STARTF.strftime('%Y%m%d%H%M'))) & (DATA[:,col_ind] > -999))[0]
							
							if len(indS)>2 and len(indF)>2:
								QC8=QC_TEST8(DATA[indS,col_ind],DATA[indF,col_ind],RCNTS,RCNTF,TEPS)
							else:
								QC8=0
						if QC8 > QC_tot:
							QC_tot = QC8
														
					#if QC_tot == 0: QC_tot=1						
			#QC_str = '%.0f' % QC8 + '%.0f' % QC7 + '%.0f' % QC6 + '%.0f' % QC5 + '%.0f' % QC4 + '%.0f' % QC3 + '%.0f' % QC2 + '%.0f' % QC1 + '%.0f' % QC_tot
			QC_str=QC_tot
			
			### Change Wiski_Qc-flag to 0
			DATA[row,col_ind+1]=QC_str

		if dim_corr==1:
			DATA=numpy.delete(DATA,1, axis=0)
			Log.debug('Remove 1-row')
	return DATA
					
def QC_CHECK_FERRYBOX(STATION,STATION_NR,DATA,HEADER_NR,LOGGER,PARAMETERS):
	global cfg_FERRYBOX_Basin	
	global cfg_FERRYBOX_Harbour
	global cfg_flowMin
	global cfg_speedMin
	global cfg_tempDiffMax
	global cfg_tempDiffMaxCO2		
	global FERRYBOX_CMEMS_QC_dict_constant	
	global cfg_STATION_STATUS	
	global SST_NR
	global PSAL_NR
	global COX_NR	
	global BOX9_NR		
	LLogging=0
	if len(LOGGER)>0:
		# Logger
		Log = logging.getLogger(LOGGER)
		Log.info('')
		Log.info('QC_CHECK: ' + STATION + ' ' + STATION_NR)
		LLogging=1
	if len(PARAMETERS)==2:
		pass

	if HEADER_NR.ndim==2:
		header_np=HEADER_NR[0]
	else:
		header_np=HEADER_NR
			
	data_np=DATA
	
	dim_corr=0
	if data_np.ndim==1:
		dim_corr=1
		data_np=numpy.vstack([data_np,data_np])
		if LLogging==1:
			Log.debug('only one observation make data-matrix 2-dimensional for proper work')
		else:
			print('only one observation make data-matrix 2-dimensional for proper work')

	# Load Ferrybox_Cfg
	Log.debug('load_FERRYBOX_CFG')
	load_FERRYBOX_CFG(CFG_FILE_PATH + 'Ferrybox_cfg.txt', LOGGER)

	# Get station_status
	Log.debug('load_STATION_STATUS')
	load_STATION_STATUS(CFG_FILE_PATH + 'STATION_STATUS.txt',STATION_NR,LOGGER)

	# Get Ferrybox_Qc
	FERRYBOX_CMEMS_QC_dict_constant={}
	Log.debug('load_FERRYBOX_CMEMS_QC_CONSTANT')
	FERRYBOX_CMEMS_QC_dict_constant=get_cfg_data_FERRYBOX(STATION_NR,header_np,QC_FILE_PATH,'QC_setup_cfg.txt',LOGGER)
	
	# Check if some value exist in observations 	
	# Lat
	try: Lat_ind=int(numpy.nonzero(header_np==8002)[0])   
	except: Lat_ind=-1
	
	# Long
	try: Long_ind=int(numpy.nonzero(header_np==8003)[0])
	except: Long_ind=-1
	# Flow
	try: Flow_ind=int(numpy.nonzero(header_np==8172)[0])   
	except: Flow_ind=-1
	
	# Speed
	try: Speed_ind=int(numpy.nonzero(header_np==8171)[0])   
	except: Speed_ind=-1
	
	# SeaTemperature1
	try: SST1_ind=int(numpy.nonzero(header_np==8179)[0])   
	except: SST1_ind=-1
	
	# SeaTemperature2
	try: SST2_ind=int(numpy.nonzero(header_np==8180)[0])   
	except: SST2_ind=-1
	
	# SeaTemperature3
	try: SST3_ind=int(numpy.nonzero(header_np==18102)[0])   
	except: SST3_ind=-1	

	# Loop rows
	key_prev=''
	for row in range(data_np.shape[0]):
		QC_FERRYBOX=0;QC1=0;QC2=0;QC3=0;

		# 1 FB. Datetime check
		QC_Time=0
		try:
			dt=datetime.datetime.strptime('%.0f' % data_np[row,0], '%Y%m%d%H%M%S')
			QC_Time=1
		except:
			QC_FERRYBOX=4; QC1=4; QC_Time=4			
		
		# 2FB Position, 3FB Harbour check, get basin
		QC_Position=0
		QC_Harbour=0
		basin=-999
		if QC_FERRYBOX != 4 and Lat_ind > -1 and Long_ind > -1:
			Lat=data_np[row,Lat_ind]
			Long=data_np[row,Long_ind]
			if Lat > -999 and Long > -999:	
				QC_Position=1				
				# Get basin number
				#Log.debug('Get basin number, LAT= ' + '%2.2f LONG: ' % Lat + '%2.2f' % Long)
				for i in range(cfg_FERRYBOX_Basin.shape[0]):
					if cfg_FERRYBOX_Basin[i,0] <= Lat <= cfg_FERRYBOX_Basin[i,1] and  cfg_FERRYBOX_Basin[i,2] <= Long <= cfg_FERRYBOX_Basin[i,3]:
						basin=cfg_FERRYBOX_Basin[i,4]
						break	
				# Harbour check
				QC_Harbour=1
				for i in range(cfg_FERRYBOX_Harbour.shape[0]):					
					if  cfg_FERRYBOX_Harbour[i,0] <= Lat <=  cfg_FERRYBOX_Harbour[i,1] and   cfg_FERRYBOX_Harbour[i,2] <= Long <=  cfg_FERRYBOX_Harbour[i,3]:
						QC_Harbour=4; QC_FERRYBOX=4
						break				
			else:
				# No position value
				Log.debug('No position1 ')
				QC_FERRYBOX=4; QC_Position=4; QC_Harbour=0
		else:
			# No position column
			Log.debug('No position2 ')
			QC_FERRYBOX=4; QC_Position=4; QC_Harbour=0
			
		# 4FB Flow check
		QC_Flow=0
		if QC_FERRYBOX != 4 and Flow_ind > -1:
			if data_np[row,Flow_ind] < cfg_flowMin:
				QC_Flow=4; QC_FERRYBOX=4
			else:
				QC_Flow=1

		# 5FB Speed check
		QC_Speed=0
		if QC_FERRYBOX != 4 and Speed_ind > -1:
			if data_np[row,Speed_ind] < cfg_speedMin:
				QC_Speed=4; QC_FERRYBOX=4
			else:
				QC_Speed=1			

		# 6FB Temp check1
		QC_SST1_2=0
		if QC_FERRYBOX != 4 and SST1_ind > -1 and SST2_ind > -1:
			#Log.debug('Temp_diff ' + str(abs(data_np[row,SST2_ind] - data_np[row,SST1_ind] )))
			#Log.debug('cfg_tempDiffMax ' + str(cfg_tempDiffMax))
			if abs(data_np[row,SST2_ind] - data_np[row,SST1_ind] ) > cfg_tempDiffMax:
				QC_SST1_2=4; QC_FERRYBOX=4
			else:
				QC_SST1_2=1		
				
		# Temp check2, only for CO2
		QC_SST1_3=0
		if QC_FERRYBOX != 4 and SST1_ind > -1 and SST3_ind > -1:
			if abs(data_np[row,SST3_ind] - data_np[row,SST1_ind] ) > cfg_tempDiffMax:
				QC_SST1_3=4; 
			else:
				QC_SST1_3=1		
				
		# Loop columns
		for col_ind in range(1,header_np.shape[0],2):
			QC_tot=0;QC4=0;QC5=0;QC6=0;QC7=0;QC8=0;
	
#			Log.debug('QC_tot ' + str( QC_tot))
#			Log.debug('QC_Flow ' + str(QC_Flow ))
#			Log.debug(' QC_Speed ' + str(QC_Speed ))
#			Log.debug(' QC_SST1_2 ' + str( QC_SST1_2))
#			Log.debug(' QC_SST1_3 ' + str(QC_SST1_3 ))


			QC_default=float(data_np[row,col_ind+1])
			if QC_default != 0:
				QC_tot=QC_default
			
			if QC_FERRYBOX != 4:												
				# Check station status
				for line in cfg_STATION_STATUS:
					if len(line[1])==0:
						if line[2] <= dt <=  line[3]:
							Log.debug('Time_data: ' + str(line[2]) + ',' + str(data_np[row,0]) + ',' + str(line[3]))
							QC_tot=4
					elif str(int(header_np[col_ind])) in str(line[1]) and line[2] <= dt <=  line[3]:
						Log.debug('STATION_STATUS set QC_default=4')
						QC_tot=4
					else:
						Log.debug('STATION_STATUS do not match: ')
						Log.debug(line)

				# Parameter to match with other CMEMS-number	
				if '%.0f' % header_np[col_ind] in SST_NR[0]: 
					key1='%.0f' % basin + '8179' + dt.strftime('%m') + '3.0'
				elif '%.0f' % header_np[col_ind] in PSAL_NR[0]:
					key1='%.0f' % basin + '8181' + dt.strftime('%m') + '3.0'
				else:
					key1='%.0f' % basin + str(int(header_np[col_ind])) + dt.strftime('%m') + '3.0'
					
				Log.debug('key1 ' + str(key1))
				res1=FERRYBOX_CMEMS_QC_dict_constant.get(key1,'-999')
				Log.debug('res1 ' + str(res1))
				
				if res1 != '-999':
					# Read only new limits if necessary
					if key1 != key_prev:
						key_prev=key1											
						# QC-values															
						RANGE_TEST_MIN=float(res1[4])
						RANGE_TEST_MAX=float(res1[5])
						STD=float(res1[7])
						THRSHLD_LOW=float(res1[8])
						THRSHLD_HIGH=float(res1[9])
						RCNTF=float(res1[10])
						RCNTS=float(res1[11])
						TEPS=float(res1[12])
						NDEV=float(res1[13])
						TIMDEV=float(res1[14])
				
					# Make ordinary QC-test
					make_ordinary_QC=0
					if '%.0f' % header_np[col_ind] == 8002 or \
						'%.0f' % header_np[col_ind] == 8003 or \
						'%.0f' % header_np[col_ind] == 8172 or \
						'%.0f' % header_np[col_ind] == 8171:
						make_ordinary_QC=0					
					elif '%.0f' % header_np[col_ind] in COX_NR[0]: # If CoX
						if QC_FERRYBOX != 4 and QC_SST1_3 != 4:
							make_ordinary_QC=1
					elif '%.0f' % header_np[col_ind] in BOX9_NR[0]: # If Box9 parameter
						make_ordinary_QC=1
					elif QC_FERRYBOX != 4:
						make_ordinary_QC=1
					
					if make_ordinary_QC==1:
						# Test 5 Range test
						if QC_tot != 4:
							#QC_TEST5(VALUE,RANGE_TEST_MIN,RANGE_TEST_MAX,STD)
							QC5=QC_TEST5(data_np[row,col_ind],RANGE_TEST_MIN,RANGE_TEST_MAX,STD)
							if QC5 > QC_tot:
								QC_tot = QC5				
							Log.debug('QC5: ' + str(QC5))
		
									
						# Test 6 Spike test
						if QC_tot != 4:
							if res1 != '-999' and row >= 1 and row < data_np.shape[0]-1:
								if data_np[row-1,col_ind] > -999 and data_np[row,col_ind] > -999 and data_np[row+1,col_ind] > -999:
									# Check time between observation. Multiplay by minutes to limits defined per minute
									dt_1=datetime.datetime.strptime('%.0f' % data_np[row-1,0], '%Y%m%d%H%M%S')
									dt1=datetime.datetime.strptime('%.0f' % data_np[row+1,0], '%Y%m%d%H%M%S')
									diff=dt1-dt_1
									minutes=diff.seconds/(1*60.0)
									#a=data_np[row,col_ind]-(data_np[row-1,col_ind]+data_np[row+2,col_ind])/2.0
									try:
										QC6=QC_TEST6(data_np[row-1:row+2,col_ind],THRSHLD_LOW*minutes,THRSHLD_HIGH*minutes)
										#if QC6==4:
										#	print a/minutes,THRSHLD_LOW*minutes,THRSHLD_HIGH*minutes
									except:
										QC6=0
										Log.warning('Error make Spike test')
										Log.warning(data_np[row-1:row+1,col_ind])									
								else:
									QC6=0
							else:
									QC6=0
									
						if QC6 > QC_tot:
							QC_tot = QC6
							
						
						# Test 7 Rate of change
						if QC_tot != 4:
							START=dt-datetime.timedelta(minutes=TIMDEV)
							ind=numpy.nonzero((data_np[:,0] > float(START.strftime('%Y%m%d%H%M%S'))) & (data_np[:,col_ind] > -999))[0]
							if len(ind)>2:
								QC7=QC_TEST7(data_np[ind,col_ind],NDEV)
							else:
								QC7=0
								
						if QC7 > QC_tot:
							QC_tot = QC7
							
							
						# Test 8 Flat line test for QC=4
						if QC_tot != 4:
							STARTS=dt-datetime.timedelta(minutes=RCNTS)
							indS=numpy.nonzero(data_np[:,0] > float(STARTS.strftime('%Y%m%d%H%M%S')))
							STARTF=dt-datetime.timedelta(minutes=RCNTF)
							indF=numpy.nonzero(data_np[:,0] > float(STARTF.strftime('%Y%m%d%H%M%S')))
							
							if len(indS)>2 and len(indF)>2:
								QC8=QC_TEST8(data_np[indS[0],col_ind],data_np[indF[0],col_ind],RCNTS,RCNTF,TEPS)
							else:
								QC8=0
	
						if QC8 > QC_tot:
							QC_tot = QC8
							
						QC_tot=max(1,QC_tot)
							
			# No ordinary Qc-check due to previous error or some ch-nr
			elif '%.0f' % header_np[col_ind] == 8002 or \
				'%.0f' % header_np[col_ind] == 8002: 
				QC_tot=QC_Position	
			elif '%.0f' % header_np[col_ind] == 8172:
				QC_tot=QC_Flow
			elif '%.0f' % header_np[col_ind] == 8171:
				QC_tot=QC_Speed
			else:
				QC_tot=4
				
			if data_np[row,col_ind] == -999:
				QC_tot=9
				
			if numpy.isnan(data_np[row,col_ind]):
				data_np[row,col_ind]=-999
				QC_tot=9
			
			#QC_str = '6%.0f' % QC8 + '%.0f' % QC7 + '%.0f' % QC6 + '%.0f' % QC5 + '%.0f' % QC4 + '%.0f' % QC3 + '%.0f' % QC2 + '%.0f' % QC1 + '%.0f' % QC_Time +\
			#		'%.0f' % QC_Position + '%.0f' % QC_Harbour + '%.0f' % QC_Speed + '%.0f' % QC_SST1_2 + '%.0f' % QC_SST1_3 + '%.0f' % QC_tot
			#print QC_str
			QC_str=QC_tot
			data_np[row,col_ind+1]=QC_str
								
	#except:
	#	if LLogging==1:
	#		Log.critical('Unexpected error: ', exc_info=True)
	#	else:
	#		print 'Unexpected error in IOCFTP_QC '

	if dim_corr==1:
		data_np=numpy.delete(data_np,1, axis=0)
		Log.debug('Remove 1-row')
	return data_np


def QC_CHECK_V2(STATION,STATION_NR,DATA,HEADER_NR,LOGGER,PARAMETERS):
	global cfg_vst_corrections_dict

	# Logger
	Log = logging.getLogger(LOGGER)
	Log.info('')
	Log.info('QC_CHECK_V2: ' + STATION + ' ' + STATION_NR)
	Log.debug('Header')
	Log.debug(HEADER_NR)
	LLogging=1
	
	if len(PARAMETERS)==2:
		pass

	# Check if header has correct dimension
	if HEADER_NR.ndim==2:
		header_np=HEADER_NR[0]
	else:
		header_np=HEADER_NR
	
	# If one row duplicate row
	dim_corr=0
	if DATA.ndim==1:
		dim_corr=1
		DATA=numpy.vstack([DATA,DATA])
		if LLogging==1:
			Log.debug('only one observation make data-matrix 2-dimensional for proper work')
		else:
			print('only one observation make data-matrix 2-dimensional for proper work')

	# Create a dictionery with range mm 
	Log.debug('Get CMEMS_QC_dict_constant')
	CMEMS_QC_dict_constant=get_cfg_data(STATION_NR,header_np,QC_FILE_PATH,'QC_setup_cfg_V2.txt',LOGGER)
	
	# Load QC_setup_cfg.txt 
	#load_QC_SETUP_FILE(CFG_FILE_PATH + 'QC_setup_cfg_V2.txt',LOGGER)
	
	# Get station_status
	Log.debug('load_STATION_STATUS')
	load_STATION_STATUS(CFG_FILE_PATH + 'STATION_STATUS.txt',STATION_NR,LOGGER)


	# Get default position from QC-files
	try: LAT= float(CMEMS_QC_dict_constant.get(CMEMS_QC_dict_constant.keys()[0],'-999')[1])
	except: LAT=-999
	Log.debug('LAT ' + STATION + ': ' + str(LAT))
	
	try: LONG=float(CMEMS_QC_dict_constant.get(CMEMS_QC_dict_constant.keys()[0],'-999')[2])
	except: LONG=-999
	Log.debug('LONG ' + STATION + ': ' + str(LONG))
	
	# Loop rows
	key_prev=''
	for row in range(DATA.shape[0]):	
					
		# Read date and time with the datetime-function
		dt=datetime.datetime.strptime('%.0f' % DATA[row,0], '%Y%m%d%H%M')
					
		try:
			month=int(dt.strftime('%m'))
		except:
			Log.error('Error get year/month from timestamp: ' + str(DATA[row,0]))
			month=13
				
		# Loop columns
		for col_ind in range(1,header_np.shape[0],2):
			QC_tot=1;QC1=0;QC2=0;QC3=0;QC4=0;QC5=0;QC6=0;QC7=0;QC8=0;
			if DATA[row,col_ind] == -999:
				QC_tot=9
			else:
			
				QC_default=float(DATA[row,col_ind+1])
				if QC_default != 0:
					QC_tot=QC_default
				
				# Check station status
				for line in cfg_STATION_STATUS:
					if len(line[1])==0:
						if line[2] <= dt <=  line[3]:
							Log.debug('Time_data: ' + str(line[2]) + ',' + str(DATA[row,0]) + ',' + str(line[3]))
							QC_tot=4
					elif str(int(header_np[col_ind])) in str(line[1]) and line[2] <= dt <=  line[3]:
						Log.debug('STATION_STATUS set QC_default=4')
						QC_tot=4
					else:
						Log.debug('STATION_STATUS do not match: ')
						Log.debug(line)
					
				# If QC_default=4, bad indata no quality-controll QC=4						
				# Get constants
				key3=str(STATION_NR) + str(int(header_np[col_ind]))
				#Log.debug('key3 ' + key3)
				res3=CMEMS_QC_SETUP_DEPTH_dict.get(key3,'-999')
				#Log.debug('res3 ' + res3)
				
				# Get depth of observation
				Depth='0.0'
					
				# Find row with qc-value in CMEMS Qc-files
				#key=str(STATION_NR) + str(int(header_np[col_ind])) + str(month)  + Depth
				key1=str(STATION_NR) + '8195' + str(month)  + Depth
				#Log.debug('Key:' + str(key1))
				res1=CMEMS_QC_dict_constant.get(key1,'-999')
				
				if res1!='-999':
					# Read only new limits if necessary
					if key1 != key_prev:
						key_prev=key1											
						# QC-values										
						RANGE_TEST_MIN=float(res1[6])
						RANGE_TEST_MAX=float(res1[7])							
						STD=float(res1[9])		
						THRSHLD_LOW=float(res1[10])
						THRSHLD_HIGH=float(res1[11])
						RCNTF=float(res1[12])
						RCNTS=float(res1[13])
						TEPS=float(res1[14])
						NDEV=float(res1[15])
						TIMDEV=float(res1[16])
															
					# Make QC-test
					# Test 5 Range test
					if QC_tot != 4:
						#QC_TEST5(VALUE,RANGE_TEST_MIN,RANGE_TEST_MAX,STD)
						QC5=QC_TEST5(DATA[row,col_ind],RANGE_TEST_MIN,RANGE_TEST_MAX,STD)
						if QC5 > QC_tot:
							QC_tot = QC5
					
						Log.debug('QC5: ' + str(QC5))
						
	
					# Test 6 Spike test
					if QC_tot != 4:
						if row >= 1 and row < DATA.shape[0]-1:
							if DATA[row-1,col_ind] > -999 and DATA[row,col_ind] > -999 and DATA[row+1,col_ind] > -999:
								# Check time between observation. Multiplay by minutes to limits defined per minute
								dt_1=datetime.datetime.strptime('%.0f' % DATA[row-1,0], '%Y%m%d%H%M')
								dt1=datetime.datetime.strptime('%.0f' % DATA[row+1,0], '%Y%m%d%H%M')
								diff=dt1-dt_1
								minutes=diff.seconds/(2*60.0)
								try:
									QC6=QC_TEST6(DATA[row-1:row+2,col_ind],THRSHLD_LOW*minutes,THRSHLD_HIGH*minutes)
								except:
									QC6=0
									Log.warning('Error make Spike test')
									Log.warning(DATA[row-1:row+1,col_ind])
							else:
								QC6=0
						else:
							QC6=0
					if QC6 > QC_tot:
						QC_tot = QC6
															
					# Test 7 Rate of change
					if QC_tot != 4:
						START=dt-datetime.timedelta(minutes=TIMDEV)
						ind=numpy.nonzero((DATA[:,0] > float(START.strftime('%Y%m%d%H%M'))) & (DATA[:,col_ind] > -999))[0]
						if len(ind)>2:
							QC7=QC_TEST7(DATA[ind,col_ind],NDEV)
						else:
							QC7=0
					if QC7 > QC_tot:
						QC_tot = QC7
														
					# Test 8 Flat line test for QC=4
					if QC_tot != 4:
						STARTS=dt-datetime.timedelta(minutes=RCNTS)
						indS=numpy.nonzero((DATA[:,0] > float(STARTS.strftime('%Y%m%d%H%M'))) & (DATA[:,col_ind] > -999))[0]
						STARTF=dt-datetime.timedelta(minutes=RCNTF)
						indF=numpy.nonzero((DATA[:,0] > float(STARTF.strftime('%Y%m%d%H%M'))) & (DATA[:,col_ind] > -999))[0]
						
						if len(indS)>2 and len(indF)>2:
							QC8=QC_TEST8(DATA[indS,col_ind],DATA[indF,col_ind],RCNTS,RCNTF,TEPS)
						else:
							QC8=0
					if QC8 > QC_tot:
						QC_tot = QC8
				else: #No qc-value
					QC_tot=0 
									
					#if QC_tot == 0: QC_tot=1						
			#QC_str = '%.0f' % QC8 + '%.0f' % QC7 + '%.0f' % QC6 + '%.0f' % QC5 + '%.0f' % QC4 + '%.0f' % QC3 + '%.0f' % QC2 + '%.0f' % QC1 + '%.0f' % QC_tot
			QC_str=QC_tot
			
			### Change Wiski_Qc-flag to 0
			DATA[row,col_ind+1]=QC_str

		if dim_corr==1:
			DATA=numpy.delete(DATA,1, axis=0)
			Log.debug('Remove 1-row')
			
	Log.debug('Finish IOCFTP_QC')
	Log.debug('')
	return DATA