## GNPS LCMS Visualization Dashboard

### URL Parameters

1. usi
1. xicmz

### Heroku Deployment

We are also trying to support a heroku deployment. This is why we have a Procfile. 

### Example Sources of Data

1. GNPS Analysis Tasks - [mzspec:GNPS:TASK-d93bdbb5cdda40e48975e6e18a45c3ce-f.mwang87/data/Yao_Streptomyces/roseosporus/0518_s_BuOH.mzXML:scan:171](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AGNPS%3ATASK-d93bdbb5cdda40e48975e6e18a45c3ce-f.mwang87%2Fdata%2FYao_Streptomyces%2Froseosporus%2F0518_s_BuOH.mzXML%3Ascan%3A171&xicmz=841.3170166%3B842.3170166&xic_tolerance=0.5&xic_norm=No&show_ms2_markers=1&ms2_identifier=MS2%3A1176)
1. GNPS/MassIVE public datasets - [mzspec:MSV000084951:AH22](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AMSV000084951%3AAH22&xicmz=870.9543493652343&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. MassiVE Proteomics datasets - mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01
1. MassiVE Proteomics dataset large - mzspec:MSV000083508:ccms_peak_centroided/pituitary_hypophysis/Trypsin_HCD_QExactiveplus/01697_A01_P018020_S00_N01_R2.mzML:scan:62886
1. Metabolights public datasets - [mzspec:MTBLS1124:QC07.mzML](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AMTBLS1124%3AQC07.mzML&xicmz=&xic_tolerance=0.5&xic_norm=No&show_ms2_markers=1&ms2_identifier=)

### Instrument Vendors for Metabolomics

1. Thermo - [mzspec:MSV000084951:AH22](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AMSV000084951%3AAH22&xicmz=870.9543493652343&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. Thermo MS3 - [mzspec:MSV000084765:Leptocheline_MS3_DDA_IT_5](https://gnps-lcms.ucsd.edu/?usi=mzspec:MSV000084765:Leptocheline_MS3_DDA_IT_5)
1. Sciex - [mzspec:MSV000085042:QC1_pos-QC1](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AMSV000085042%3AQC1_pos-QC1&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. Bruker - [mzspec:MSV000086015:StdMix_02__GA2_01_55623](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AMSV000086015%3AStdMix_02__GA2_01_55623&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. Waters - [mzspec:MSV000084977:OEPKS7_B_1_neg](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AMSV000084977%3AOEPKS7_B_1_neg&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None)
1. Agilent - [mzspec:MSV000084060:KM0001](https://gnps-lcms.ucsd.edu/?usi=mzspec:MSV000084060:KM0001)

### Data Types for Proteomics

1. Sciex - SWATH - [mzspec:MSV000085570:170425_01_Edith_120417_CCF_01](https://gnps-lcms.ucsd.edu/?usi=mzspec:MSV000085570:170425_01_Edith_120417_CCF_01)

### Example Use Cases

**Quick analysis of QC data**

Here is the USI for a QC run

mzspec:MSV000085852:QC_0

What we can easily do is paste in the QC molecules and pull them out in one fell swoop:

271.0315;278.1902;279.0909;285.0205;311.0805;314.1381

You can try it out at this [URL](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AMSV000085852%3AQC_0&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_tolerance=0.5&xic_norm=No&show_ms2_markers=1&ms2_identifier=) 

**Quickly Compare Multiple files**

mzspec:MSV000085852:QC_0
mzspec:MSV000085852:QC_1
mzspec:MSV000085852:QC_2

271.0315;278.1902;279.0909;285.0205;311.0805;314.1381

[Test Link](https://gnps-lcms.ucsd.edu/?usi=mzspec%3AMSV000085852%3AQC_DOM_2%0Amzspec%3AMSV000085852%3AQC_DOM_3%3Ascan%3A62886%0Amzspec%3AMSV000085852%3AQC_DOM_4%3Ascan%3A62886%0Amzspec%3AMSV000085852%3AQC_DOM_5%3Ascan%3A62886%0A&usi2=mzspec%3AMSV000085852%3AQC_DOM_0%3Ascan%3A62886%0Amzspec%3AMSV000085852%3AQC_DOM_1%3Ascan%3A62886%0A%0A&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_tolerance=0.5&xic_norm=False&xic_file_grouping=FILE&show_ms2_markers=True&ms2_identifier=None)

## API

We aim to provide several APIs to programmatically get data.


### Image Preview of MS run
```
/mspreview?usi=<usi>
```

## Development

There are several ways to get GNPS Dashboard working locally, our preferred and recommended way is using docker/docker-compose as it provides a more consistent experience. 

The initial steps are identical:

1. Fork the GNPS Dashboard repository
2. Clone down to your system

### Docker 

To get everything up and running, we've created a make target for you to get docker up and running:

```
make server-compose-interactive
```

The requirements on your locally system are:

1. Docker
2. Docker Compose

This will bring the server up on http://localhost:6548. 

### Conda

1. Install Python3 within conda
3. Install all packages from the requirements.txt
4. Install packages via conda
5. Start the dashboard locally (defaults to http://localhost:5000)

**Example shell**

```
# make sure to have Python3 installed via conda (preferably 3.8)
conda install -c conda-forge datashader
conda install -c conda-forge openjdk

# install requirements
pip install -r requirements.txt

# run or debug the GNPS Dashboard with Python 3 on http://localhost:5000
python ./app.py

# on problem, maybe install the following (tested on Windows 10 with WSL2 Ubuntu) 
sudo apt-get install libffi-dev
```

### Supporting new data sources

Since we utilize a USI to find datasets, there are a limited number of locations we can grab data from. If you want to provide a new data source, you'll have to implement the following

1. USI Specification that denotes what the resource is and how to get data
1. Update the code in ```download.py```, specifically in ```_resolve_usi_remotelink``` to implement how to get the remote URL for your new USI. 


### Useful links for developers
**Dash and plotly documentations**

- Components: https://dash.plotly.com/dash-core-components 
- Callbacks: https://dash.plotly.com/basic-callbacks 
- Plotly express: https://plotly.com/python/plotly-express/ 
- Plotly: https://plotly.com/python/ 
