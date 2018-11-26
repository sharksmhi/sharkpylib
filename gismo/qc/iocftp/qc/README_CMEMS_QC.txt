Swedish Meteorological and Hydrological Institute (SMHI)
Oceanographic data 

Monthly characteristic values



FILENAMES:

CMEMS_QC_ <platform_type> _ <parameter_code> .txt



PLATFORM TYPES:

MO	Moorings (tide gauges, buoys and fixed platforms)
CT	CTD-measurements (monitoring cruises)
FB	Ferryboxes (moving vessels)
SF	Lightships (fixed vessels)



PARAMETER CODES:

channel_number	parameter_code	units		standard_name							long_name
8028		WFOR->WBFO	Beaufort	wind_force							WIND_FORCE
8029		GSPD		m/s		gust								GUST_WIND_SPEED
8030		WDIR		deg		wind_direction							WIND_DIRECTION_REL._TRUE_NORTH
8031		WSPD		m/s		wind_speed							HORIZONTAL_WIND_SPEED
8032		ATMP		hPa		airpressure							ATMOSPHERIC_PRESSURE
8033		ATEM->DRYT	degC		airtemperature							AIR_TEMPERATURE
8034		RELH		%		humidity							RELATIVE_HUMIDITY
8043		VHM0		m		sea_surface_wave_significant_height				SPECTRAL_SIGNIFICANT_WAVE_HEIGHT_(HM0)
8044		VTZA		s		sea_surface_zerocrossing_period					AVERAGE_ZERO_CROSSING_WAVE_PERIOD_(TZ)
8045		VDIR->VMDR	deg		sea_surface_wave_from_mean_direction				MEAN_WAVE_DIRECTION_FROM_(MDIR)
8046		VZMX		m		sea_surface_wave_maximum_height					MAXIMUM_ZERO_CROSSING_WAVE_HEIGHT_(HMAX)
8063		FLU2		mg/m3		chlorophyll_a_fluorescence					CHLOROPHYLL_A_FLUORESCENCE
8174		TURB->TUR4	NTU		turbidity							TURBIDITY
8179/86XX	TEMP		degC		sea_water_temperature						SEA_TEMPERATURE
8181/87XX	PSAL		PSU		sea_water_salinity						PRACTICAL_SALINITY
8183/88XX	HCDT		deg		current_direction						DIRECTION_REL._TRUE_NORTH
8184/89XX	HCSP		cm/s		current_speed							HORIZONTAL_CURRENT_SPEED
8187		SVEL		m/s		sound_velocity							SOUND_VELOCITY
8191		DOX1		ml/l		oxygen								DISSOLVED_OXYGEN
8195		SLEV		m		sea_surface_height_above_sea_level				OBSERVED_SEA_LEVEL
8515		VTPK		s		sea_surface_wave_period_at_variance_spectral_density_maximum	WAVE_PERIOD_AT_SPECTRAL_PEAK_(TP)
8523		VPED		deg		sea_surface_wave_from_direction_at_spectral_peak		WAVE_DIRECTION_AT_SPECTRAL_PEAK_(PRINCIPAL_DIRECTION)
8525		VPSP		deg		directional_spread_peak						DIR_SPREAD_WAVE_PEAK

where XX is the depth in meters



DATASTRUCTURE BY COLUMN:	

COLUMN	
01	STNR	station number according to CMEMS_STATIONS_BOOS.xlsx
02	LATX	nominal latitude (decimal degrees)
03	LONX	nominal longitude (decimal degrees)
04	CHAN	channel number SMHI
05	DEPH	measurement depth (m)
06	MONTH	month (number)
07	MIN	monthly minimum value
08	MAX	monthly maximum value
09	MEAN	monthly mean value
10	STD	monthly standard deviation
11	THRH	threshold high value for the spike test, THRSHLD_HIGH<abs[y(n-1)-(y(n-2)+y(0))/2] => bad
12	RCNT	repeated observations (X hours) for the flat line test, REP_CNT=X
13	TEPS	tolerance value for the flat line test to allow for a numerical round-off error, EPS
14	NOBS	number of observations
15	CELL	grid cell number (used only for station type FB=Ferrybox)



QUALITY CONTROL FLAGS:

CODE	MEANING						COMMENT
0	No QC was performed				-
1	Good data					All real-time QC tests passed.
2	Probably good data				-
3	Bad data that are potentially correctable	These data are not to be used without scientific correction.
4	Bad data					Data have failed one or more of the tests.
5	Value changed					Data may be recovered after transmission error.
6	Not used					-
7	Nominal value 					Data were not observed but reported. Example: an instrument target depth.
8	Interpolated value				Missing data may be interpolated from neighbouring data in space or time.
9	Missing value					-
