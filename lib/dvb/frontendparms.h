#ifndef __lib_dvb_frontendparms_h
#define __lib_dvb_frontendparms_h

#include <lib/python/swig.h>

#include <dvbsi++/satellite_delivery_system_descriptor.h>
#include <dvbsi++/cable_delivery_system_descriptor.h>
#include <dvbsi++/terrestrial_delivery_system_descriptor.h>
#include <dvbsi++/t2_delivery_system_descriptor.h>

struct eDVBFrontendParametersSatellite
{
#ifndef SWIG
	void set(const SatelliteDeliverySystemDescriptor  &);
#endif
	enum {
		Polarisation_Horizontal, Polarisation_Vertical, Polarisation_CircularLeft, Polarisation_CircularRight
	};

	enum {
		Inversion_Off, Inversion_On, Inversion_Unknown
	};

	enum {
		FEC_Auto=0, FEC_1_2=1, FEC_2_3=2, FEC_3_4=3, FEC_5_6=4, FEC_7_8=5, FEC_8_9=6, FEC_3_5=7, FEC_4_5=8, FEC_9_10=9, FEC_None=15,
		FEC_13_45=16, FEC_9_20=17, FEC_11_20=18, FEC_23_36=19, FEC_25_36=20,
		FEC_13_18=21, FEC_26_45=22, FEC_28_45=23, FEC_7_9=24, FEC_77_90=25,
		FEC_32_45=26, FEC_11_15=27, FEC_1_2_L=28, FEC_8_15_L=29, FEC_3_5_L=30,
		FEC_2_3_L=31, FEC_5_9_L=32, FEC_26_45_L=33
	};

	enum {
		System_DVB_S, System_DVB_S2, System_DVB_S2X
	};

	enum {
		Modulation_Auto, Modulation_QPSK, Modulation_8PSK, Modulation_QAM16, Modulation_16APSK, Modulation_32APSK, Modulation_8APSK
	};

	// dvb-s2
	enum {
		RollOff_alpha_0_35, RollOff_alpha_0_25, RollOff_alpha_0_20
	};

	enum {
		Pilot_Off, Pilot_On, Pilot_Unknown
	};

	enum {
		PLS_Root, PLS_Gold, PLS_Combo, PLS_Unknown
	};

	bool no_rotor_command_on_tune;
	unsigned int frequency, symbol_rate;
	int polarisation, fec, inversion, orbital_position, system, modulation, rolloff, pilot, is_id, pls_mode, pls_code;
};
SWIG_ALLOW_OUTPUT_SIMPLE(eDVBFrontendParametersSatellite);

struct eDVBFrontendParametersCable
{
#ifndef SWIG
	void set(const CableDeliverySystemDescriptor  &);
#endif
	enum {
		Inversion_Off, Inversion_On, Inversion_Unknown
	};

	enum {
		FEC_Auto, FEC_1_2, FEC_2_3, FEC_3_4, FEC_5_6, FEC_7_8, FEC_8_9, FEC_None=15
	};

	enum {
		Modulation_Auto, Modulation_QAM16, Modulation_QAM32, Modulation_QAM64, Modulation_QAM128, Modulation_QAM256
	};

	unsigned int frequency, symbol_rate;
	int modulation, inversion, fec_inner;
};
SWIG_ALLOW_OUTPUT_SIMPLE(eDVBFrontendParametersCable);

struct eDVBFrontendParametersTerrestrial
{
#ifndef SWIG
	void set(const TerrestrialDeliverySystemDescriptor  &);
	void set(const T2DeliverySystemDescriptor &);
#endif

	enum {
		Bandwidth_8MHz, Bandwidth_7MHz, Bandwidth_6MHz, Bandwidth_Auto, Bandwidth_5MHz, Bandwidth_10MHz, Bandwidth_1_712MHz
	};

	enum {
		FEC_1_2, FEC_2_3, FEC_3_4, FEC_4_5, FEC_5_6, FEC_7_8, FEC_Auto, FEC_6_7, FEC_8_9
	};

	enum {
		TransmissionMode_2k, TransmissionMode_8k, TransmissionMode_Auto, TransmissionMode_4k, TransmissionMode_1k, TransmissionMode_16k, TransmissionMode_32k
	};

	enum {
		GuardInterval_1_32, GuardInterval_1_16, GuardInterval_1_8, GuardInterval_1_4, GuardInterval_Auto, GuardInterval_1_128, GuardInterval_19_128, GuardInterval_19_256
	};

	enum {
		Hierarchy_None, Hierarchy_1, Hierarchy_2, Hierarchy_4, Hierarchy_Auto
	};

	enum {
		Modulation_QPSK, Modulation_QAM16, Modulation_QAM64, Modulation_Auto, Modulation_QAM256
	};

	enum {
		Inversion_Off, Inversion_On, Inversion_Unknown
	};

	enum {
		System_DVB_T, System_DVB_T2
	};

	unsigned int frequency;
	int bandwidth;
	int code_rate_HP, code_rate_LP;
	int modulation;
	int transmission_mode;
	int guard_interval;
	int hierarchy;
	int inversion;
	int system;
	int plpid;
};
SWIG_ALLOW_OUTPUT_SIMPLE(eDVBFrontendParametersTerrestrial);

#endif /* __lib_dvb_frontendparms_h */
