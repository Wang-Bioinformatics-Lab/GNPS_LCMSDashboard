## GNPS LCMS Visualization Dashboard

We typitcally will deploy this locally. To bring everything up

```server-compose```

### URL Parameters

1. usi
1. xicmz

### Heroku Deployment

We are also trying to support a heroku deployment. This is why we have a Procfile. 


### Example Sources of Data

1. GNPS Analysis Tasks - [mzspec:GNPS:TASK-d93bdbb5cdda40e48975e6e18a45c3ce-f.mwang87/data/Yao_Streptomyces/roseosporus/0518_s_BuOH.mzXML:scan:171](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec%3AGNPS%3ATASK-d93bdbb5cdda40e48975e6e18a45c3ce-f.mwang87%2Fdata%2FYao_Streptomyces%2Froseosporus%2F0518_s_BuOH.mzXML%3Ascan%3A171&xicmz=841.3170166%3B842.3170166&xic_tolerance=0.5&xic_norm=No&show_ms2_markers=1&ms2_identifier=MS2%3A1176)
1. GNPS/MassIVE public datasets - [mzspec:MSV000084951:AH22:scan:62886](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec%3AMSV000084951%3AAH22%3Ascan%3A62886&xicmz=870.9543493652343&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. MassiVE Proteomics datasets - mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01:scan:62886
1. MassiVE Proteomics dataset large - mzspec:MSV000083508:ccms_peak_centroided/pituitary_hypophysis/Trypsin_HCD_QExactiveplus/01697_A01_P018020_S00_N01_R2.mzML:scan:62886
1. Metabolights public datasets - [mzspec:MTBLS1124:QC07.mzML:scan:1](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec%3AMTBLS1124%3AQC07.mzML%3Ascan%3A1&xicmz=&xic_tolerance=0.5&xic_norm=No&show_ms2_markers=1&ms2_identifier=)

### Instrument Vendors for Metabolomics

1. Thermo - [mzspec:MSV000084951:AH22:scan:62886](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec%3AMSV000084951%3AAH22%3Ascan%3A62886&xicmz=870.9543493652343&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. Sciex - [mzspec:MSV000085042:QC1_pos-QC1:scan:1](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec%3AMSV000085042%3AQC1_pos-QC1%3Ascan%3A1&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. Bruker - [mzspec:MSV000086015:StdMix_02__GA2_01_55623:scan:1](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec%3AMSV000086015%3AStdMix_02__GA2_01_55623%3Ascan%3A1&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. Waters - [mzspec:MSV000084977:OEPKS7_B_1_neg:scan:1](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec%3AMSV000084977%3AOEPKS7_B_1_neg%3Ascan%3A1&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. Agilent - [mzspec:MSV000084060:KM0001:scan:1](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec:MSV000084060:KM0001:scan:1)

### Data Types for Proteomics

1. Sciex - SWATH - [mzspec:MSV000085570:170425_01_Edith_120417_CCF_01:scan:1](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec:MSV000085570:170425_01_Edith_120417_CCF_01:scan:1)

### Example Use Cases

**Quick analysis of QC data**

Here is the USI for a QC run

mzspec:MSV000085852:QC_0:scan:62886

What we can easily do is paste in the QC molecules and pull them out in one fell swoop:

271.0315;278.1902;279.0909;285.0205;311.0805;314.1381

You can try it out at this [URL](http://dorresteintesthub.ucsd.edu:6548/?usi=mzspec%3AMSV000085852%3AQC_0%3Ascan%3A62886&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_tolerance=0.5&xic_norm=No&show_ms2_markers=1&ms2_identifier=) 

