# Dash imports

import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import dash_table
from dash.dependencies import Input, Output, State
import dash_daq as daq
import dash_uploader as du

# Plotly Imports
import plotly.express as px
import plotly.graph_objects as go

EXAMPLE_DASHBOARD = [
    dbc.CardHeader(html.H5("Example Exploration Dashboards")),
    dbc.CardBody(
        [
            html.H5("Basic Examples - LC/MS Metabolomics"),
            html.Hr(),

            html.A("LCMS Multiple m/z XIC for QC Files", style={"text-decoration": "none"}, href='/?xic_mz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=No&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=Off&feature_finding_ppm=10&feature_finding_noise=10000&feature_finding_min_peak_rt=0.05&feature_finding_max_peak_rt=1.5&feature_finding_rt_tolerance=0.3&sychronization_session_id=fc02496b0307452d928ba8231c6886d6&chromatogram_options=%5B%5D&comment=&map_plot_color_scale=Hot_r&map_plot_quantization_level=Medium#%7B"usi"%3A%20"mzspec%3AMSV000085852%3AQC_0"%2C%20"usi2"%3A%20""%7D'),
            html.Br(),
            html.A("LCMS Side By Side Visualization", style={"text-decoration": "none"}, href='/?usi=mzspec%3AMSV000085852%3AQC_0&usi2=mzspec%3AMSV000085852%3AQC_1&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381%3B833.062397505189&xic_tolerance=0.5&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&show_ms2_markers=True&ms2_identifier=MS2%3A2277&show_lcms_2nd_map=True&map_plot_zoom=%7B"xaxis.range%5B0%5D"%3A+3.2846848333333334%2C+"xaxis.range%5B1%5D"%3A+3.5981121270270275%2C+"yaxis.range%5B0%5D"%3A+815.4334319736646%2C+"yaxis.range%5B1%5D"%3A+853.5983309206755%7D'),
            html.Br(),
            html.A("LCMS XIC by Formula - QC Amitryptiline", style={"text-decoration": "none"}, href='/?usi=mzspec%3AMSV000085852%3AQC_0&usi2=&xicmz=&xic_formula=C20H23N&xic_tolerance=0.01&xic_ppm_tolerance=20&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B"autosize"%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC'),
            html.Br(),
            html.A("LCMS auto zoomed by URL", style={"text-decoration": "none"}, href='/?xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B"xaxis.range%5B0%5D"%3A+3.225196497160058%2C+"xaxis.range%5B1%5D"%3A+3.4834247492797554%2C+"yaxis.range%5B0%5D"%3A+521.8432333663449%2C+"yaxis.range%5B1%5D"%3A+615.6041749343235%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&feature_finding_type=Off#{"usi":%20"mzspec:MSV000085852:QC_0",%20"usi2":%20""}'),
            html.Br(),
            html.A("LCMS auto zoomed by scan in USI", style={"text-decoration": "none"}, href="/?usi=mzspec:MSV000085852:QC_0:scan:2277"),
            html.Br(),
            html.Br(),

            html.H5("Various Vendor Examples - LC/MS Metabolomics"),
            html.Hr(),
            
            html.A("Thermo Q Exactive LCMS mzML", style={"text-decoration": "none"}, href="/?usi=mzspec%3AMSV000084951%3AAH22&xicmz=870.9543493652343&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Thermo Q Exactive LCMS RAW", style={"text-decoration": "none"}, href="/?usi=mzspec%3AMSV000086206%3Araw/raw/S_N1.raw&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Thermo Orbitrap Elite LCMS with MS3", style={"text-decoration": "none"}, href='/#%7B"usi"%3A%20"mzspec%3AMSV000084754%3Accms_peak/raw/Toronamide_MS3_DDA_2.mzML"%2C%20"usi2"%3A%20""%7D'),
            html.Br(),
            html.A("Thermo Lumos LCMS RAW", style={"text-decoration": "none"}, href="/?usi=mzspec:MSV000086729:raw/raw/Identification/UP_Fusion_AcX_SAT_ob_pool_1_NOlist.raw"),
            html.Br(),
            html.A("Sciex LCMS", style={"text-decoration": "none"}, href="/?usi=mzspec%3AMSV000085042%3AQC1_pos-QC1&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Bruker LCMS", style={"text-decoration": "none"}, href="/?usi=mzspec%3AMSV000086015%3AStdMix_02__GA2_01_55623&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Bruker LCMS - PA14 rhlR", style={"text-decoration": "none"}, href="/?usi=mzspec:MSV000083500:ccms_peak/9177.mzML"),
            html.Br(),
            html.A("Waters LCMS", style={"text-decoration": "none"}, href="/?usi=mzspec%3AMSV000084977%3AOEPKS7_B_1_neg&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Agilent LCMS", style={"text-decoration": "none"}, href="/?usi=mzspec:MSV000084060:KM0001"),
            html.Br(),
            html.A("Agilent LCMS CDF", style={"text-decoration": "none"}, href="/?usi=mzspec:MSV000086521:raw/ORSL13CM.CDF"),
            html.Br(),
            html.A("Shimadzu LCMS", style={"text-decoration": "none"}, href="/?usi=mzspec%3AMSV000081501%3Accms_peak%2FAA+BPM+D7+1_Seg1Ev1.mzML"),
            html.Br(),
            html.Br(),

            html.H5("Basic Examples - LC/MS Proteomics"),
            html.Hr(),

            html.A("Thermo LCMS - Orbitrap Elite - Proteomics - Pandey Draft Proteome - mzML from MassIVE", style={"text-decoration": "none"}, href="/?usi=mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01"),
            html.Br(),
            html.A("Thermo LCMS - Orbitrap Velos - Proteomics - Pandey Draft Proteome - RAW from PRIDE via PX", style={"text-decoration": "none"}, href="/?usi=mzspec:PXD000561:Adult_Adrenalgland_bRP_Velos_1_f07.raw"),
            html.Br(),
            html.A("Thermo LCMS - Q Exactive HF - Proteomics - TMT10Plex - RAW from MassIVE via PX", style={"text-decoration": "none"}, href="/?usi=mzspec:PXD022935:21720-TMT-Fra-1-1.raw"),
            html.Br(),
            html.A("Thermo LCMS - Q Exactive - Proteomics - Deep Proteome - mzML from MassIVE", style={"text-decoration": "none"}, href='/?xicmz=&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B"autosize"%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=mzspec%3AGNPS%3ATASK-5ecfcf81cb3c471698995b194d8246a0-f.benpullman%2F_cluster%2Ffeatures%2F29_tissues_colon_01308_H02_P013387_B00_N16_R1.tsv&overlay_mz=m%2Fz&overlay_rt=Retention+time&overlay_color=&overlay_size=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=Off#%7B"usi":%20"mzspec:MSV000083508:01308_H02_P013387_B00_N16_R1%5Cn",%20"usi2":%20""%7D'),
            html.Br(),
            html.A("Thermo LCMS - Q Exactive - Proteomics - mzXML from MassIVE, imported from PRIDE", style={"text-decoration": "none"}, href='/?usi=mzspec:PXD002854:20150414_QEp1_LC7_GaPI_SA_Serum_DT_03_150416181741.mzXML:scan:2308:[+314.188]-QQKPGQAPR/2'),
            html.Br(),
            html.A("Sciex SWATH - Proteomics - mzML from MassIVE", style={"text-decoration": "none"}, href='/?usi=mzspec:MSV000085570:170425_01_Edith_120417_CCF_01'),
            html.Br(),
            html.A("LC/MS without MS1 data - from PRIDE", style={"text-decoration": "none"}, href='/?xic_mz=&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=MZ&xic_integration_type=AUC&show_ms2_markers=True&ms2marker_color=blue&ms2marker_size=5&ms2_identifier=&show_lcms_2nd_map=False&map_plot_zoom=%7B%22xaxis.autorange%22%3A+true%2C+%22yaxis.autorange%22%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=Off&feature_finding_ppm=10&feature_finding_noise=10000&feature_finding_min_peak_rt=0.05&feature_finding_max_peak_rt=1.5&feature_finding_rt_tolerance=0.3&sychronization_session_id=060c1de5066e49788d8d4ad33201b797&chromatogram_options=%5B%5D&comment=&map_plot_color_scale=Hot_r&map_plot_quantization_level=Medium&plot_theme=plotly_white#%7B%22usi%22%3A%20%22mzspec%3APXD023659%3AV200409_13.mzML%22%2C%20%22usi2%22%3A%20%22%22%7D'),
            html.Br(),
            html.Br(),

            html.H5("Different Data Sources Examples - LC/MS Metabolomics"),
            html.Hr(),

            html.A("LCMS from Metabolights", style={"text-decoration": "none"}, href="/?usi=mzspec:MTBLS1124:QC07.mzML"),
            html.Br(),
            html.A("LCMS from Metabolomics Workbench Native", style={"text-decoration": "none"}, href="/?usi=mzspec:ST001709:Sample_01___neg.mzXML"),
            html.Br(),
            html.A("LCMS from Metabolomics Workbench Imported into GNPS", style={"text-decoration": "none"}, href="/?usi=mzspec:ST000763:20160411_MB_CS00000074-1_P.mzXML"),
            html.Br(),
            html.A("Thermo LCMS from GNPS Analysis Classical Molecular Networking Task", style={"text-decoration": "none"}, href="/?usi=mzspec:GNPS:TASK-5ecfcf81cb3c471698995b194d8246a0-f.MSV000085444/ccms_peak/peak/Hui_N1_fe.mzML#%7B%7D"),
            html.Br(),
            html.A("LCMS from Glycopost", style={"text-decoration": "none"}, href="/?usi=mzspec:GPST000082:VV_PGM_200204.raw"),
            html.Br(),
            html.Br(),

            html.H5("Basic Examples - GC/MS Metabolomics"),
            html.Hr(),

            html.A("Thermo GCMS", style={"text-decoration": "none"}, href="/?usi=mzspec:MSV000086150:BA1.mzML"),
            html.Br(),
            html.A("GCMS in CDF Format", style={"text-decoration": "none"}, href="/?usi=mzspec:MSV000084169:raw/FractA1/0205045.CDF"),
            html.Br(),
            html.Br(),

            html.H5("Advanced Examples - LC/MS Metabolomics"),
            html.Hr(),

            html.A("Multiple Files to show comparison", style={"text-decoration": "none"}, href="/?usi=mzspec%3AMSV000085618%3Accms_peak%2FBLANK_P2-F-1_01_13263.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED103_P1-D-8_01_3762.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED104_P1-D-9_01_3763.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED105_P1-A-1_01_3781.mzML%3Ascan%3A1%0A&usi2=mzspec%3AMSV000085618%3Accms_peak%2FED24_P1-B-2_01_2171.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED25_P1-B-3_01_2172.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED26_P1-B-4_01_2173.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED36_P1-C-3_01_2181.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED37_P1-C-4_01_2182.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED38_P1-C-5_01_2183.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FSJ-123_P1-A-6_01_13658.mzML%3Ascan%3A1&xicmz=799.437&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=ppm&xic_rt_window=2.5&xic_norm=False&xic_file_grouping=MZ&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B%22autosize%22%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC"),
            html.Br(),
            html.A("Combined Pos/Neg Filtered Side by Side", style={"text-decoration": "none"}, href='/?xic_mz=&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=MZ&xic_integration_type=AUC&show_ms2_markers=True&ms2marker_color=blue&ms2marker_size=5&ms2_identifier=None&show_lcms_2nd_map=True&map_plot_zoom=%7B%7D&polarity_filtering=Positive&polarity_filtering2=Negative&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=Off&feature_finding_ppm=10&feature_finding_noise=10000&feature_finding_min_peak_rt=0.05&feature_finding_max_peak_rt=1.5&feature_finding_rt_tolerance=0.3&sychronization_session_id=2f255123ee444ec7b85385a79b15b7bf&chromatogram_options=%5B%5D&comment=&map_plot_color_scale=Hot_r&map_plot_quantization_level=Medium#%7B"usi"%3A%20"mzspec%3AMSV000087127%3Apeak/peak/20170728_KBL_PZ-KM_Root_SMs__QE139-UV_C18_102_FPS-MS1_0_Mid______ITSD-Lipid-ABMBA_Run66.mzML"%2C%20"usi2"%3A%20"mzspec%3AMSV000087127%3Apeak/peak/20170728_KBL_PZ-KM_Root_SMs__QE139-UV_C18_102_FPS-MS1_0_Mid______ITSD-Lipid-ABMBA_Run66.mzML"%7D'),
            html.Br(),
            html.A("LCMS with Feature Finding Overlay from FBMN", style={"text-decoration": "none"}, href="/?usi=mzspec:GNPS:TASK-ddd650381cef4bcfad4b068e9400c8d7-f.MSV000085444/ccms_peak/peak/Hui_N1_fe.mzML&overlay_usi=mzspec:GNPS:TASK-ddd650381cef4bcfad4b068e9400c8d7-quantification_table_reformatted/"),
            html.Br(),
            html.A("LCMS with Feature Finding Overlay from FBMN with Sizing of highlight", style={"text-decoration": "none"}, href="/?usi=mzspec:GNPS:TASK-bc7e7e3d61714464a6b47d247933040e-f.MSV000085444/ccms_peak/peak/Hui_N1.mzML&overlay_usi=mzspec:GNPS:TASK-bc7e7e3d61714464a6b47d247933040e-quantification_table_reformatted/&overlay_size=Hui_N1.mzML%20Peak%20area#%7B%7D"),
            html.Br(),
            html.A("LCMS with MZMine2 Feature Finding Active", style={"text-decoration": "none"}, href='/?usi=mzspec%3AMSV000085852%3AQC_0&usi2=&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B"autosize"%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&feature_finding_type=MZmine2'),
            html.Br(),
            html.A("LCMS with MZMine2 Feature Finding Parameters Set", style={"text-decoration": "none"}, href='/?xicmz=482.123497282169&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=ppm&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=MS2%3A3065&show_lcms_2nd_map=True&map_plot_zoom=%7B"autosize"%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=MZmine2&feature_finding_ppm=10&feature_finding_noise=100000&feature_finding_min_peak_rt=0.02&feature_finding_max_peak_rt=2&feature_finding_rt_tolerance=0.1#%7B"usi":%20"mzspec:GNPS:TASK-5844c6bea85442b0a998f4d558caa310-f.daniel/Exampel_FBMN_Nissel/mzml/S_N1.mzML%5Cnmzspec:GNPS:TASK-5844c6bea85442b0a998f4d558caa310-f.daniel/Exampel_FBMN_Nissel/mzml/S_N2.mzML%5Cnmzspec:GNPS:TASK-5844c6bea85442b0a998f4d558caa310-f.daniel/Exampel_FBMN_Nissel/mzml/S_N3.mzML",%20"usi2":%20"mzspec:GNPS:TASK-5844c6bea85442b0a998f4d558caa310-f.daniel/Exampel_FBMN_Nissel/mzml/S_P1.mzML%5Cnmzspec:GNPS:TASK-5844c6bea85442b0a998f4d558caa310-f.daniel/Exampel_FBMN_Nissel/mzml/S_P2.mzML%5Cnmzspec:GNPS:TASK-5844c6bea85442b0a998f4d558caa310-f.daniel/Exampel_FBMN_Nissel/mzml/S_P3.mzML"%7D'),
            html.Br(),
            html.A("LCMS with SRM Targeted Analysis", style={"text-decoration": "none"}, href='/?xic_mz=&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=Off&feature_finding_ppm=10&feature_finding_noise=10000&feature_finding_min_peak_rt=0.05&feature_finding_max_peak_rt=1.5&feature_finding_rt_tolerance=0.3&sychronization_session_id=ca12499c5aa54d2cbd98551634fd62b0&chromatogram_options=%5B"SRM+SIC+152%2C111"%5D&comment=&map_plot_color_scale=Hot_r&map_plot_quantization_level=Medium#%7B"usi"%3A%20"mzspec%3AMSV000087058%3Apeak/peak/std1_022721.mzML%5Cnmzspec%3AMSV000087058%3Apeak/peak/std2_022721.mzML%5Cnmzspec%3AMSV000087058%3Apeak/peak/std3_022721.mzML%5Cnmzspec%3AMSV000087058%3Apeak/peak/std4_022721.mzML"%2C%20"usi2"%3A%20""%7D'),
            html.Br(),
            html.Br(),

            html.H5("Advanced Examples - MassQL Queries"),
            html.Hr(),

            html.A("LCMS with MassQL MS2 Highlights", style={"text-decoration": "none"}, href='/?xic_mz=415.2111&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=MZ&xic_integration_type=AUC&show_ms2_markers=True&ms2marker_color=blue&ms2marker_size=5&ms2_identifier=MS2%3A83&show_lcms_2nd_map=False&map_plot_zoom=%7B"xaxis.autorange"%3A+true%2C+"yaxis.autorange"%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=MassQL&feature_finding_ppm=10&feature_finding_noise=10000&feature_finding_min_peak_rt=0.05&feature_finding_max_peak_rt=1.5&feature_finding_rt_tolerance=0.3&massql_statement=QUERY+scaninfo%28MS2DATA%29+WHERE+MS2PROD%3D119&sychronization_session_id=c03656e8a448477a9144705754c4d438&chromatogram_options=%5B%5D&comment=&map_plot_color_scale=Hot_r&map_plot_quantization_level=Medium&plot_theme=plotly_white#%7B"usi"%3A%20"mzspec%3AMSV000084494%3AGNPS00002_A3_p"%2C%20"usi2"%3A%20""%7D'),
            html.Br(),
            html.A("LCMS with MassQL MS1 Highlights", style={"text-decoration": "none"}, href='/?xic_mz=415.2111&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=MZ&xic_integration_type=AUC&show_ms2_markers=True&ms2marker_color=blue&ms2marker_size=5&ms2_identifier=MS2%3A83&show_lcms_2nd_map=False&map_plot_zoom=%7B%22xaxis.autorange%22%3A+true%2C+%22yaxis.autorange%22%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=MassQL&feature_finding_ppm=10&feature_finding_noise=10000&feature_finding_min_peak_rt=0.05&feature_finding_max_peak_rt=1.5&feature_finding_rt_tolerance=0.3&massql_statement=QUERY+scaninfo%28MS1DATA%29+WHERE+MS1MZ%3DX+AND+X%3Drange%28min%3D119%2C+max%3D120%29&sychronization_session_id=c03656e8a448477a9144705754c4d438&chromatogram_options=%5B%5D&comment=&map_plot_color_scale=Hot_r&map_plot_quantization_level=Medium&plot_theme=plotly_white#%7B%22usi%22%3A%20%22mzspec%3AMSV000084494%3AGNPS00002_A3_p%22%2C%20%22usi2%22%3A%20%22%22%7D'),
            html.Br(),
            html.A("LCMS with MassQL Siderophore", style={"text-decoration": "none"}, href='/?xic_mz=415.2111&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=MZ&xic_integration_type=AUC&show_ms2_markers=True&ms2marker_color=blue&ms2marker_size=5&ms2_identifier=MS2%3A83&show_lcms_2nd_map=False&map_plot_zoom=%7B"xaxis.range%5B0%5D"%3A+1.7583140445641567%2C+"xaxis.range%5B1%5D"%3A+2.1218645847384137%2C+"yaxis.range%5B0%5D"%3A+457.9858263464266%2C+"yaxis.range%5B1%5D"%3A+564.9069290802073%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=MassQL&feature_finding_ppm=10&feature_finding_noise=10000&feature_finding_min_peak_rt=0.05&feature_finding_max_peak_rt=1.5&feature_finding_rt_tolerance=0.3&massql_statement=QUERY+scaninfo%28MS2DATA%29+WHERE+MS1MZ%3DX-1.993%3AINTENSITYMATCH%3DY%2A0.063%3AINTENSITYMATCHPERCENT%3D25%3ATOLERANCEPPM%3D10+AND+MS1MZ%3DX%3AINTENSITYMATCH%3DY%3AINTENSITYMATCHREFERENCE%3AINTENSITYPERCENT%3D10+AND+MS1MZ%3DX%2B1%3AINTENSITYMATCH%3DY%2A0.3%3AINTENSITYMATCHPERCENT%3D60+AND+MS1MZ%3DX-52.91%3ATOLERANCEPPM%3D10+AND+X%3Drange%28min%3D500%2C+max%3D600%29+AND+MS2PREC%3D%28X+OR+X-52.91%29+AND+RTMIN%3D1.8+AND+RTMAX%3D2.0&sychronization_session_id=c03656e8a448477a9144705754c4d438&chromatogram_options=%5B%5D&comment=&map_plot_color_scale=Hot_r&map_plot_quantization_level=Medium&plot_theme=plotly_white#%7B"usi"%3A%20"mzspec%3AMSV000084030%3Accms_peak/isa_9_fe.mzML"%2C%20"usi2"%3A%20""%7D'),
            html.Br(),
            html.A("LCMS with MassQL Bromination", style={"text-decoration": "none"}, href='/?xic_mz=572.7534&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=MZ&xic_integration_type=AUC&show_ms2_markers=True&ms2marker_color=blue&ms2marker_size=5&ms2_identifier=MS2%3A83&show_lcms_2nd_map=False&map_plot_zoom=%7B%22xaxis.range%5B0%5D%22%3A+9.494785264800566%2C+%22xaxis.range%5B1%5D%22%3A+14.449900194801941%2C+%22yaxis.range%5B0%5D%22%3A+458.4555016131659%2C+%22yaxis.range%5B1%5D%22%3A+672.33768016986%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&overlay_hover=&overlay_filter_column=&overlay_filter_value=&feature_finding_type=MassQL&feature_finding_ppm=10&feature_finding_noise=10000&feature_finding_min_peak_rt=0.05&feature_finding_max_peak_rt=1.5&feature_finding_rt_tolerance=0.3&massql_statement=QUERY+scaninfo%28MS1DATA%29+WHERE+MS1MZ%3DX%3ATOLERANCEMZ%3D0.1%3AINTENSITYPERCENT%3D25%3AINTENSITYMATCH%3DY%3AINTENSITYMATCHREFERENCE+AND+%0AMS1MZ%3DX%2B2%3ATOLERANCEMZ%3D0.2%3AINTENSITYMATCH%3DY%2A0.66%3AINTENSITYMATCHPERCENT%3D30+AND+%0AMS1MZ%3DX-2%3ATOLERANCEMZ%3D0.2%3AINTENSITYMATCH%3DY%2A0.66%3AINTENSITYMATCHPERCENT%3D30+AND+MS1MZ%3DX%2B4%3ATOLERANCEMZ%3D0.2%3AINTENSITYMATCH%3DY%2A0.17%3AINTENSITYMATCHPERCENT%3D40+AND+%0AMS1MZ%3DX-4%3ATOLERANCEMZ%3D0.2%3AINTENSITYMATCH%3DY%2A0.17%3AINTENSITYMATCHPERCENT%3D40+AND+%0AMS2PREC%3DX+AND%0AX%3Drange%28min%3D500%2Cmax%3D1000%29+AND%0ARTMIN%3D10+AND+RTMAX%3D12&sychronization_session_id=c03656e8a448477a9144705754c4d438&chromatogram_options=%5B%5D&comment=&map_plot_color_scale=Hot_r&map_plot_quantization_level=Medium&plot_theme=plotly_white#%7B%22usi%22%3A%20%22mzspec%3AMSV000084691%3Accms_peak/1810E-II.mzML%22%2C%20%22usi_select%22%3A%20%22mzspec%3AMSV000084691%3Accms_peak/1810E-II.mzML%22%2C%20%22usi2%22%3A%20%22%22%7D'),
        ]
    )
]





SPECTRUM_DETAILS_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Spectrum Details as XML"),
            dbc.ModalBody([
                dcc.Loading(
                    id="spectrum_details_area",
                    children=[html.Div([html.Div(id="loading-output-1035")])],
                    type="default",
                ),
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="spectrum_details_modal_close", className="ml-auto")
            ),
        ],
        id="spectrum_details_modal",
        size="xl",
    ),
]


ADVANCED_VISUALIZATION_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Advanced Visualization Modal"),
            dbc.ModalBody([
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Row(
                                [
                                    dbc.Label("Heatmap Color", width=4.8, style={"width":"150px"}),
                                    dcc.Dropdown(
                                        id='map_plot_color_scale',
                                        options=[
                                            {'label': 'Hot', 'value': 'Hot'},
                                            {'label': 'Hot_r', 'value': 'Hot_r'},
                                            {'label': 'Blues', 'value': 'Blues'},
                                            {'label': 'Blues_r', 'value': 'Blues_r'},
                                            {'label': 'Sunsetdark', 'value': 'Sunsetdark'},
                                            {'label': 'Sunsetdark_r', 'value': 'Sunsetdark_r'},
                                            {'label': 'Viridis', 'value': 'Viridis'},
                                            {'label': 'Viridis_r', 'value': 'Viridis_r'},
                                            {'label': 'Greys', 'value': 'Greys'},
                                            {'label': 'Greys_r', 'value': 'Greys_r'},
                                            {'label': 'Plotly3', 'value': 'Plotly3'},
                                            {'label': 'Plotly3_r', 'value': 'Plotly3_r'},
                                            {'label': 'Aggrnyl', 'value': 'Aggrnyl'},
                                            {'label': 'Aggrnyl_r', 'value': 'Aggrnyl_r'},
                                            {'label': 'Jet', 'value': 'Jet'},
                                            {'label': 'Jet_r', 'value': 'Jet_r'},
                                            {'label': 'Turbo', 'value': 'Turbo'},
                                            {'label': 'Turbo_r', 'value': 'Turbo_r'},
                                        ],
                                        searchable=True,
                                        clearable=False,
                                        value="Hot_r",
                                        style={
                                            "width":"60%"
                                        }
                                    )
                                ],
                                className="mb-3",
                                style={"margin-left": "4px"}
                        )),
                        dbc.Col()
                    ]
                ),
                html.Hr(),

                dbc.Row([
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Label("LCMS Quantization Map Level", width=4.8, style={"width":"250px"}),
                                dcc.Dropdown(
                                    id='map_plot_quantization_level',
                                    options=[
                                        {'label': 'Low', 'value': 'Low'},
                                        {'label': 'Medium', 'value': 'Medium'},
                                        {'label': 'High', 'value': 'High'},
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value="Medium",
                                    style={
                                        "width":"60%"
                                    }
                                )  
                            ],
                            className="mb-3",
                            style={"margin-left": "4px"}
                    )),
                ]),
                html.Hr(),
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupText("RT Range"),
                                dbc.Input(id='map_plot_rt_min', placeholder="Enter Min RT", value=""),
                                dbc.Input(id='map_plot_rt_max', placeholder="Enter Max RT", value=""),
                            ],
                            className="mb-3",
                            style={"margin-left": "4px"}
                    )),
                ]),
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroup(
                            [
                                dbc.InputGroupText("m/z Range"),
                                dbc.Input(id='map_plot_mz_min', placeholder="Enter Min m/z", value=""),
                                dbc.Input(id='map_plot_mz_max', placeholder="Enter Max m/z", value=""),
                            ],
                            className="mb-3",
                            style={"margin-left": "4px"}
                    )),
                ]),
                dbc.Button("Update Map Plot Ranges", id="map_plot_update_range_button"),
                html.Br(),
                html.Hr(),
                html.H5("MS2 Markers"),
                dbc.Row([
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Label("MS2 Marker Color", width=4.8, style={"width":"250px"}),
                                dcc.Dropdown(
                                    id='ms2marker_color',
                                    options=[
                                        {'label': 'blue', 'value': 'blue'},
                                        {'label': 'white', 'value': 'white'},
                                        {'label': 'red', 'value': 'red'},
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value="blue",
                                    style={
                                        "width":"60%"
                                    }
                                )  
                            ],
                            className="mb-3",
                            style={"margin-left": "4px"}
                    )),
                ]),
                dbc.Row([
                    dbc.Col(
                        dbc.Row(
                            [
                                dbc.Label("MS2 Marker Size", width=4.8, style={"width":"250px"}),
                                dcc.Dropdown(
                                    id='ms2marker_size',
                                    options=[
                                        {'label': '5', 'value': 5},
                                        {'label': '10', 'value': 10},
                                        {'label': '15', 'value': 15},
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value=5,
                                    style={
                                        "width":"60%"
                                    }
                                )  
                            ],
                            className="mb-3",
                            style={"margin-left": "4px"}
                    )),
                ]),
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_visualization_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_visualization_modal",
        size="lg",
    ),
]


ADVANCED_IMPORT_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("GNPS Dashboard Settings as JSON"),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.H5("Current Settings"),
                        dbc.Textarea(id="setting_json_area", className="mb-3", placeholder="JSON Settings", rows="20"),
                        dcc.Upload(
                            id='upload-settings-json',
                            children=html.Div([
                                'Paste settings or Drag and Drop file with existing settings',
                                html.A(' or Select Files')
                            ]),
                            style={
                                'width': '95%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                            multiple=False
                        ),
                        html.Br(),
                        html.Div([dbc.Button("Import These JSON Settings", id="advanced_import_update_button")], className="d-grid gap-2"),
                        html.Br(),
                        html.A(
                            html.Div([dbc.Button("Download Settings as File")], className="d-grid gap-2"),
                            id="advanced_import_download_button",
                            target="_blank",
                            href="/settingsdownload"
                        ),
                    ]),
                    dbc.Col([
                        html.H5("Settings History"),
                        dbc.Textarea(id="setting_json_area_history", className="mb-3", placeholder="JSON History Settings", rows="20"),
                        html.Br(),
                        html.A(
                            html.Div([dbc.Button("Link to Analysis History Replay")], className="d-grid gap-2"),
                            id="advanced_import_history_link",
                            target="_blank",
                            href="/"
                        ),
                    ])
                ]),
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_import_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_import_modal",
        size="xl",
    ),
]

ADVANCED_REPLAY_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("GNPS Dashboard Replay"),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        html.H5("Previous Replay JSON"),
                        dbc.Textarea(id="replay_json_area_previous", className="mb-3", placeholder="Replay JSON Settings", rows="20"),
                        html.Div(id="replay_summary")
                    ]),
                    dbc.Col([
                        html.H5("Next Replay JSON"),
                        dbc.Textarea(id="replay_json_area", className="mb-3", placeholder="Replay JSON Settings", rows="20"),
                        html.A(
                            dbc.Button("Link to this Replay"),
                            id="advanced_import_replay_link",
                            target="_blank",
                            href="/"
                        ),
                    ])
                ])
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_replay_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_replay_modal",
        size="xl",
    ),
]

ADVANCED_USI_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("GNPS Metabolomics USI Modal"),
            dbc.ModalBody([
                html.Iframe(
                    id="usi_frame",
                    style={
                        "width" : "100%",
                        "height" : "800px",
                        "border" : "0"
                    }
                )
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_usi_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_usi_modal",
        size="xl",
        style={
            "max-width": "1920px"
        }
    ),
]



UPLOAD_MODAL = [
    dbc.Modal(
        [
            dbc.ModalHeader("Upload Files"),
            dbc.ModalBody([
                html.Div("Upload your files here, we have two options, upload many small files at once (up to 120MB), or one big file at one time (up to 2GB). \
                    Files are deleted after 30 days so if you would it more permanent, \
                    please make a public dataset at MassIVE. We currently support the upload of mzML, mzXML, CDF, and Thermo RAW files."),
                html.Br(),
                dbc.Alert("Note: If you are uploading a 2GB file, please do so on an internet connection with at least a 100 mbps upload speed!", color="primary"),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.H3("Upload Several Small Files"),
                        html.Hr(),
                        html.Div(
                            dcc.Upload(
                                id='upload-data1',
                                children=html.Div([
                                    'Drag and Drop your own files',
                                    html.A('(120MB Max and multiple at a time)')
                                ]),
                                style={
                                    'width': '95%',
                                    'height': '120px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '7px',
                                    'textAlign': 'center',
                                    'margin': '10px',
                                    'margin-top': '27px'
                                },
                                multiple=True,
                                max_size=150000000 # 150MB
                            ),
                        )
                    ]),
                    dbc.Col([
                        html.H3("Upload One Big File"),
                        html.Hr(),
                        html.Div(
                            du.Upload(
                                id="upload-data2",
                                max_file_size=2048, 
                                filetypes=['mzML', 'mzml', 'mzXML', 'mzxml', 'cdf', 'CDF', 'RAW', 'raw'],
                                max_files=1,
                                pause_button=True,
                                text="Drag and Drop your own files (up to 2GB)",
                            ),
                            style={
                                'width': '95%',
                                'height': '100px',
                                'lineHeight': '100px',
                                'borderWidth': '1px',
                                'display': 'inline-block',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                        )
                    ]),
                ]),
                html.Hr(),
                html.H3("Upload Status"),
                html.Hr(),
                dcc.Loading(
                    id="upload_status",
                    children=[html.Div([html.Div(id="loading-output-3423")])],
                    type="default",
                ),
            ]),
            dbc.ModalFooter(
                dbc.Button("Close", id="advanced_upload_modal_close", className="ml-auto")
            ),
        ],
        id="advanced_upload_modal",
        size="xl",
    ),
]
