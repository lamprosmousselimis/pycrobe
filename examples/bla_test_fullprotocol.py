import numpy
import pandas

from pycrobe.standard import *
from pycrobe.betalactamase import *


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


incubator = Incubator(set_temp=37.0, temp_std_batch=0.5, temp_std_location=0.25, temp_std_transient=0.0)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


VMAX_B 		= [0.0, 200.0, 400.0, 600.0, 800.0, 1000.0]
K_B 		= [10.0 for i in range(len(VMAX_B))]
strainNames = ["TEM-"+str(int(Vmax)) for Vmax in VMAX_B]

strains 	= {}
for i, strainName in enumerate(strainNames):
	strains[strainName] = BlaStrain(name = strainName, 					
									max_growth_rate 					= 2, 
									max_lysis_rate 						= 1, 				
									halfmax_lysis_drug_conc 			= 0.125,			# ug/mL <- scMIC for Bla-free strain
									lysis_hill_coefficient 				= 5,				# ?
									betalactamase = 
										BetaLactamase(
											name = "Bla-"+strainName, 
											decay_rate_intracellular 	= 0, 
											decay_rate_extracellular 	= 0, 
											max_hydrolysis_rate 		= VMAX_B[i], 		# ug/mL/t
											halfmax_hydrolysis_drug_conc= K_B[i], 			# ug/mL
											is_intracellular 			= True
											),
									bla_production_rate 				= 1, 				# ?
									bla_saturation_conc 				= 1,				# ?
									halfmax_bla_production_conc 		= 0.01,
									bla_leak_rate 						= 0, 		
									bla_debris_sink_fraction 			= 0,	   
									drug_diffusion_rate 				= 50, 				# ? 				
									drug_debris_sink_fraction 			= 0,
									periplasm_volume 					= 0.16*1.3e-12, 	# periplasm estimated to be 16% of total E coli volume, which is approximately 1.3 um^3 = 1.3 fL = 1.3 fL*(1e-12 mL/ 1 fL):: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0035205#pone-0035205-g001, http://book.bionumbers.org/how-big-is-an-e-coli-cell-and-what-is-its-mass/
									optimal_temp						= 37.0,	
									mean_lag_exit_time					= 1.5,
									stdev_lag_exit_time					= 0.125,
									halfmax_growth_nutrient_conc		= 7e9, 
									nutrient_consumption_rate			= 1,
									marker								= '',
									plasmids							= []
								)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


freezedowns = {}
for strainName, strain in strains.items():
    freezedowns[strainName] = Culture(media=Media(volume=1.0), inoculums=[BlaInoculum(strain=strain, cell_count=1.0e9)], name="Freezedown_"+strainName)
    freezedowns[strainName].info()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LB_carryingCapacity = 2e9

LBStock = Culture(media=Media(volume=1000, nutrient=Nutrient(concentration=LB_carryingCapacity)), name="LB Stock")
LBStock.info()

CTXStock= Culture(media=Media(volume=1.0, drugs=[BetaLactam(name="CTX", concentration=10e3)]), name="CTX Stock") # 10 mg/mL stock conc = 10,000 ug/mL
CTXStock.info()

LBCTXMedia = Culture(name="LB+CTX Media")
LBCTXMedia.add(LBStock.sample(25.0))
LBCTXMedia.add(CTXStock.sample(0.025))
LBCTXMedia.info()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


overnights = {}
for strainName, strain in strains.items():
    overnight = Culture(name="Overnight_"+strainName, dynamics=BetaLactamaseDynamics())
    overnight.add(LBStock.sample(5.0))
    overnight.add(freezedowns[strain.name].sample(0.001))
    overnights[strainName] = overnight
    overnight.info()    

incubator.incubate(cultures=overnights.values(), time=24, dt=0.01)

for overnight in overnights.values():
    overnight.info()
    # overnight.dynamics.figure()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dilutedBackDensity = LB_carryingCapacity / 1e2

dilutedBacks = {}
for strainName, strain in strains.items():
	dilutedBack = Culture(name="Diluted-back_"+strainName, dynamics=BetaLactamaseDynamics())
	dilutedBack.add(LBStock.sample(5.0))
	dilutedBack.add(overnights[strainName].sample(0.050))
	dilutedBacks[strainName] = dilutedBack
	dilutedBack.info()  


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 


competitionVolume 	= 25.0
initDensity_total 	= LB_carryingCapacity / 1e4
initDensity_strain	= initDensity_total / len(strains)
inoculationVolume 	= competitionVolume * initDensity_strain/dilutedBackDensity

competition = Culture(name="competition", dynamics=BetaLactamaseDynamics())
competition.add(LBStock.sample(25.0))
competition.add(LBCTXMedia.sample(0.5))

for strainName, strain in strains.items():
	competition.add(dilutedBacks[strainName].sample(inoculationVolume))
competition.info()

incubator.incubate(cultures=[competition], time=24, dt=0.01)

competition.info()
competition.dynamics.figure()


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    
