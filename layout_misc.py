# Dash imports

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import dash_daq as daq

# Plotly Imports

import plotly.express as px
import plotly.graph_objects as go 

EXAMPLE_DASHBOARD = [
    dbc.CardHeader(html.H5("Example Exploration Dashboards")),
    dbc.CardBody(
        [
            html.H5("Basic Examples - LC/MS Metabolomics"),
            html.Hr(),

            html.A("LCMS Multiple m/z XIC for QC Files", href="/?usi=mzspec%3AMSV000085852%3AQC_0&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_tolerance=0.5&xic_norm=No&show_ms2_markers=1&ms2_identifier="),
            html.Br(),
            html.A("LCMS Side By Side Visualization", href='/?usi=mzspec%3AMSV000085852%3AQC_0&usi2=mzspec%3AMSV000085852%3AQC_1&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381%3B833.062397505189&xic_tolerance=0.5&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&show_ms2_markers=True&ms2_identifier=MS2%3A2277&show_lcms_2nd_map=True&map_plot_zoom=%7B"xaxis.range%5B0%5D"%3A+3.2846848333333334%2C+"xaxis.range%5B1%5D"%3A+3.5981121270270275%2C+"yaxis.range%5B0%5D"%3A+815.4334319736646%2C+"yaxis.range%5B1%5D"%3A+853.5983309206755%7D'),
            html.Br(),
            html.A("LCMS XIC by Formula - QC Amitryptiline", href='/?usi=mzspec%3AMSV000085852%3AQC_0&usi2=&xicmz=&xic_formula=C20H23N&xic_tolerance=0.01&xic_ppm_tolerance=20&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B"autosize"%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC'),
            html.Br(),
            html.A("LCMS auto zoomed by URL", href='/?xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B"xaxis.range%5B0%5D"%3A+3.225196497160058%2C+"xaxis.range%5B1%5D"%3A+3.4834247492797554%2C+"yaxis.range%5B0%5D"%3A+521.8432333663449%2C+"yaxis.range%5B1%5D"%3A+615.6041749343235%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&feature_finding_type=Off#{"usi":%20"mzspec:MSV000085852:QC_0",%20"usi2":%20""}'),
            html.Br(),
            html.A("LCMS auto zoomed by scan in USI", href="/?usi=mzspec:MSV000085852:QC_0:scan:2277"),
            html.Br(),
            html.Br(),

            html.H5("Various Vendor Examples - LC/MS Metabolomics"),
            html.Hr(),
            
            html.A("Thermo Q Exactive LCMS mzML", href="/?usi=mzspec%3AMSV000084951%3AAH22&xicmz=870.9543493652343&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Thermo Q Exactive LCMS RAW", href="/?usi=mzspec%3AMSV000086206%3Araw/raw/S_N1.raw&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Sciex LCMS", href="/?usi=mzspec%3AMSV000085042%3AQC1_pos-QC1&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Bruker LCMS", href="/?usi=mzspec%3AMSV000086015%3AStdMix_02__GA2_01_55623&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Bruker LCMS - PA14 rhlR", href="/?usi=mzspec:MSV000083500:ccms_peak/9177.mzML"),
            html.Br(),
            html.A("Waters LCMS", href="/?usi=mzspec%3AMSV000084977%3AOEPKS7_B_1_neg&xicmz=&xic_tolerance=0.5&xic_norm=False&show_ms2_markers=True&ms2_identifier=None"),
            html.Br(),
            html.A("Agilent LCMS", href="/?usi=mzspec:MSV000084060:KM0001"),
            html.Br(),
            html.A("Agilent LCMS CDF", href="/?usi=mzspec:MSV000086521:raw/ORSL13CM.CDF"),
            html.Br(),
            html.Br(),

            html.H5("Basic Examples - LC/MS Proteomics"),
            html.Hr(),

            html.A("Thermo LCMS - Orbitrap Elite - Proteomics - Pandey Draft Proteome", href="/?usi=mzspec:MSV000079514:Adult_CD4Tcells_bRP_Elite_28_f01"),
            html.Br(),
            html.Br(),

            html.H5("Different Data Sources Examples - LC/MS Metabolomics"),
            html.Hr(),

            html.A("LCMS from Metabolights", href="/?usi=mzspec:MTBLS1124:QC07.mzML"),
            html.Br(),
            html.A("LCMS from Metabolomics Workbench that include MS/MS", href="/?usi=mzspec:ST000763:20160411_MB_CS00000074-1_P.mzXML"),
            html.Br(),
            html.A("Thermo LCMS from GNPS Analysis Classical Molecular Networking Task", href="/?usi=mzspec:GNPS:TASK-5ecfcf81cb3c471698995b194d8246a0-f.MSV000085444/ccms_peak/peak/Hui_N1_fe.mzML#%7B%7D"),
            html.Br(),
            html.Br(),

            html.H5("Basic Examples - GC/MS Metabolomics"),
            html.Hr(),

            html.A("Thermo GCMS", href="/?usi=mzspec:MSV000086150:BA1.mzML"),
            html.Br(),
            html.A("GCMS in CDF Format", href="/?usi=mzspec:GNPS:TASK-ce31b7fdd01244dbb31478147889de1e-f.aaksenov/GC_data/Sterols_data/Samples/0104006.cdf"),
            html.Br(),
            html.Br(),

            html.H5("Advanced Examples - LC/MS Metabolomics"),
            html.Hr(),

            html.A("Multiple Files to show comparison", href="/?usi=mzspec%3AMSV000085618%3Accms_peak%2FBLANK_P2-F-1_01_13263.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED103_P1-D-8_01_3762.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED104_P1-D-9_01_3763.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED105_P1-A-1_01_3781.mzML%3Ascan%3A1%0A&usi2=mzspec%3AMSV000085618%3Accms_peak%2FED24_P1-B-2_01_2171.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED25_P1-B-3_01_2172.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED26_P1-B-4_01_2173.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED36_P1-C-3_01_2181.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED37_P1-C-4_01_2182.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FED38_P1-C-5_01_2183.mzML%3Ascan%3A1%0Amzspec%3AMSV000085618%3Accms_peak%2FSJ-123_P1-A-6_01_13658.mzML%3Ascan%3A1&xicmz=799.437&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=ppm&xic_rt_window=2.5&xic_norm=False&xic_file_grouping=MZ&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B%22autosize%22%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC"),
            html.Br(),
            html.A("LCMS with Feature Finding Overlay from FBMN", href="/?usi=mzspec:GNPS:TASK-ddd650381cef4bcfad4b068e9400c8d7-f.MSV000085444/ccms_peak/peak/Hui_N1_fe.mzML&overlay_usi=mzspec:GNPS:TASK-ddd650381cef4bcfad4b068e9400c8d7-quantification_table_reformatted/"),
            html.Br(),
            html.A("LCMS with Feature Finding Overlay from FBMN with Sizing of highlight", href="/?usi=mzspec:GNPS:TASK-bc7e7e3d61714464a6b47d247933040e-f.MSV000085444/ccms_peak/peak/Hui_N1.mzML&overlay_usi=mzspec:GNPS:TASK-bc7e7e3d61714464a6b47d247933040e-quantification_table_reformatted/&overlay_size=Hui_N1.mzML%20Peak%20area#%7B%7D"),
            html.Br(),
            html.A("LCMS with MZMine2 Feature Finding Active", href='/?usi=mzspec%3AMSV000085852%3AQC_0&usi2=&xicmz=271.0315%3B278.1902%3B279.0909%3B285.0205%3B311.0805%3B314.1381&xic_formula=&xic_peptide=&xic_tolerance=0.5&xic_ppm_tolerance=10&xic_tolerance_unit=Da&xic_rt_window=&xic_norm=False&xic_file_grouping=FILE&xic_integration_type=AUC&show_ms2_markers=True&ms2_identifier=None&show_lcms_2nd_map=False&map_plot_zoom=%7B"autosize"%3A+true%7D&polarity_filtering=None&polarity_filtering2=None&tic_option=TIC&overlay_usi=None&overlay_mz=row+m%2Fz&overlay_rt=row+retention+time&overlay_color=&overlay_size=&feature_finding_type=MZmine2'),
        ]
    )
]