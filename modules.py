import pytz
import time
from time import gmtime, strftime
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import numpy as np
import pandas as pd
import xlsxwriter
import datetime
import re

from sklearn.linear_model import LinearRegression 

from statkraft.ssa.wrappers import ReadWrapper



def main_read_excel(sheet: str, file: str) -> [[str], [str], [str], [str], [str]]:
    """This function reads the excel file for this program (must be in the main folder)."""
    
    Sheet = pd.read_excel(file,sheet) 
    keys = Sheet['Område:'].values
    vhhQ_OBSE_list = Sheet['VHH tilsig:'].values
    comments_list = Sheet['Kommentar:']
    exluded_list = Sheet['Ikke analyserbar:']
    start_list = Sheet['Start:']
    end_list = Sheet['Slutt:']
    
    return keys, vhhQ_OBSE_list, comments_list, exluded_list, start_list, end_list

def saved_runs_excel(file: str) -> [[str], [str]]:
    """This function reads the excel file for this program (must be in the main folder)."""
    
    Sheet = pd.read_excel(file,'saved abat runs') 
    models = Sheet['Saved models:'].values
    dates = Sheet['Started from:'].values
    
    print('Time saved models were started from:')
    for model, date in zip(models, dates):
        print('{}: {}'.format(model,date))



def read_timeseries(names: list, vhhQ_OBSE_list: list, sheet: str) -> [[pd.DataFrame], [pd.DataFrame]]:
    """This function reads presaved spring_temp time series from the TEMP folder, presaved ref time series from the REF folder, and temp, ltm and normal series from SMG."""
    
    
    #Internal functions
    def get_catchment_keys(catchment: str, ltm: str) -> [[str], [str]]:
        """This function lists all catchment keys that should be read from SMG."""

        #inflow
        #ref1Q_N_FB = '/HBV/{}-{}/REF/UPDAT/Q_N_FB'.format(ltm,catchment)
        ltmQ_N_FB = '/HBV/{}-{}/LTM/UPDAT/Q_N_FB'.format(ltm,catchment)
        #temp2Q_N_FB = '/HBV/{}-{}/TEMP/UPDAT/Q_N_FB'.format(ltm,catchment)
        ltmQ_OBSE = '/HBV/{}-{}/LTM/UPDAT/Q_OBSE'.format(ltm,catchment)
        normQ_N_FB = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/Q_N_FB'.format(ltm,catchment)
        #SWE
        #ref1SNOW_S = '/HBV/{}-{}/REF/UPDAT/SNOW_S'.format(ltm,catchment)
        ltmSNOW_S = '/HBV/{}-{}/LTM/UPDAT/SNOW_S'.format(ltm,catchment)
        #temp2SNOW_S = '/HBV/{}-{}/TEMP/UPDAT/SNOW_S'.format(ltm,catchment)
        normSNOW_S = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/SNOW_S'.format(ltm,catchment)

        #keys = [ref1Q_N_FB, ltmQ_N_FB, temp2Q_N_FB, ltmQ_OBSE, normQ_N_FB, ref1SNOW_S, ltmSNOW_S, temp2SNOW_S, normSNOW_S]
        #cols = ['ref1Q_N_FB', 'ltmQ_N_FB', 'temp2Q_N_FB', 'ltmQ_OBSE', 'normQ_N_FB', 'ref1SNOW_S', 'ltmSNOW_S', 'temp2SNOW_S', 'normSNOW_S']
        keys = [ltmQ_N_FB, ltmQ_OBSE, normQ_N_FB, ltmSNOW_S, normSNOW_S]
        cols = ['ltmQ_N_FB', 'ltmQ_OBSE', 'normQ_N_FB', 'ltmSNOW_S', 'normSNOW_S']
        #keys = [ltmQ_N_FB, temp2Q_N_FB, ltmQ_OBSE, normQ_N_FB, ltmSNOW_S, temp2SNOW_S, normSNOW_S]
        #cols = ['ltmQ_N_FB', 'temp2Q_N_FB', 'ltmQ_OBSE', 'normQ_N_FB', 'ltmSNOW_S', 'temp2SNOW_S', 'normSNOW_S']

        return keys, cols
    
    
    def get_region_keys(region: str, country:str) -> [[str], [str]]:
        """This function lists all region keys that should be read from SMG."""
        
        dotsQ = '......'
        dotsSnow = '..........'
        if region == 'Norge':
            dotsQ = '.....'
            dotsSnow = '.........'
        if region == 'Sverige':
            dotsQ = '...'
            dotsSnow = '.......'
        
        #inflow
        #ref1Q_N_FB = '/REF/{}-{}.NFB{}-D1050A5R-0105'.format(country,region,dotsQ)
        ltmQ_N_FB = '/{}-{}.NFB{}-D1050A5R-0105'.format(country,region,dotsQ)
        #temp2Q_N_FB = '/TEMP/{}-{}.NFB{}-D1050A5R-0105'.format(country,region,dotsQ)
        ltmQ_OBSE = '/{}-{}{}-D1050A5R-0105'.format(country,region,dotsSnow)
        normQ_N_FB = '/Mean/198009-201009/{}-{}.NFB{}-D1050A5R-0105'.format(country,region,dotsQ)
        #SWE
        #ref1SNOW_S = '/REF/{}-{}{}-D2003A5R-0105'.format(country,region,dotsSnow)
        ltmSNOW_S = '/{}-{}{}-D2003A5R-0105'.format(country,region,dotsSnow)
        #temp2SNOW_S = '/TEMP/{}-{}{}-D2003A5R-0105'.format(country,region,dotsSnow)
        normSNOW_S = '/Mean/198009-201009/{}-{}{}-D2003A5R-0105'.format(country,region,dotsSnow)
        
        #keys = [ref1Q_N_FB, ltmQ_N_FB, temp2Q_N_FB, ltmQ_OBSE, normQ_N_FB, ref1SNOW_S, ltmSNOW_S, temp2SNOW_S, normSNOW_S]
        #cols = ['ref1Q_N_FB', 'ltmQ_N_FB', 'temp2Q_N_FB', 'ltmQ_OBSE', 'normQ_N_FB',  'ref1SNOW_S', 'ltmSNOW_S', 'temp2SNOW_S', 'normSNOW_S']
        #keys = [ltmQ_N_FB, temp2Q_N_FB, ltmQ_OBSE, normQ_N_FB, ltmSNOW_S, temp2SNOW_S, normSNOW_S]
        #cols = ['ltmQ_N_FB', 'temp2Q_N_FB', 'ltmQ_OBSE', 'normQ_N_FB', 'ltmSNOW_S', 'temp2SNOW_S', 'normSNOW_S']
        keys = [ltmQ_N_FB, ltmQ_OBSE, normQ_N_FB, ltmSNOW_S, normSNOW_S]
        cols = ['ltmQ_N_FB', 'ltmQ_OBSE', 'normQ_N_FB', 'ltmSNOW_S', 'normSNOW_S']
        
        return keys, cols
       
    
    def get_resources_keys(key:str, sheet:str) -> [[str], [str]]:
        """This function lists all resources keys that should be read from SMG."""
        
        if sheet[0:3] == 'LTM':
            ltm = sheet
            catchment = key
            evapor = '/HBV/{}-{}/LTM/UPDAT/EVAPOR'.format(ltm,catchment)
            gr_wat = '/HBV/{}-{}/LTM/UPDAT/GR_WAT'.format(ltm,catchment)
            soil_m = '/HBV/{}-{}/LTM/UPDAT/SOIL_M'.format(ltm,catchment)
            name, ref = catchment.split('-')
            dots = (14-len(name))*'.'
            adj_temp = '/{}-{}{}-D0017F3A-HBV-{}'.format(ltm,name,dots,ref)
            snow_s = '/HBV/{}-{}/LTM/UPDAT/SNOW_S'.format(ltm,catchment)
            precip = '/HBV/{}-{}/LTM/UPDAT/PRECIP'.format(ltm,catchment)
            norm_evapor = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/EVAPOR'.format(ltm,catchment)
            norm_gr_wat = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/GR_WAT'.format(ltm,catchment)
            norm_soil_m = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/SOIL_M'.format(ltm,catchment)
            orig_temp = '/{}-{}{}-D0017G3A-HBV-{}'.format(ltm,name,dots,ref)
            norm_snow_s = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/SNOW_S'.format(ltm,catchment)
            norm_precip = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/PRECIP'.format(ltm,catchment)
            
            keys = [evapor, gr_wat, soil_m, orig_temp, snow_s, precip, norm_evapor, norm_gr_wat, norm_soil_m, adj_temp, norm_snow_s, norm_precip]
            cols = ['evapor', 'gr_wat', 'soil_m', 'orig_temp', 'snow_s', 'precip', 'norm_evapor', 'norm_gr_wat', 'norm_soil_m', 'adj_temp', 'norm_snow_s', 'norm_precip']
        
        else:
            country = sheet
            region = key
            if key[0:3] == 'Reg':
                dots = '...'
            elif key == 'Norge':
                dots = '..'
            else:
                dots = ''
            evapor = '/{}-{}.......{}-D0001A5B-0105'.format(country,region,dots)
            gr_wat = '/{}-{}.......{}-D2000A5B-0105'.format(country,region,dots)
            soil_m = '/{}-{}.......{}-D2001A5B-0105'.format(country,region,dots)
            temper = '/{}-{}.GWh...{}-D0017A3R-0114'.format(country,region,dots)
            snow_s = '/{}-{}.......{}-D2003A5R-0105'.format(country,region,dots)
            precip = '/{}-{}.......{}-D0000A5R-0105'.format(country,region,dots)
            norm_evapor = '/Mean/198009-201009/{}-{}.......{}-D0001A5B-0105'.format(country,region,dots)
            norm_gr_wat = '/Mean/198009-201009/{}-{}.......{}-D2000A5B-0105'.format(country,region,dots)
            norm_soil_m = '/Mean/198009-201009/{}-{}.......{}-D2001A5B-0105'.format(country,region,dots)
            norm_temper = '/Mean/198009-201009/{}-{}.GWh...{}-D0017A3R-0114'.format(country,region,dots)
            norm_snow_s = '/Mean/198009-201009/{}-{}.......{}-D2003A5R-0105'.format(country,region,dots)
            norm_precip = '/Mean/198009-201009/{}-{}.......{}-D0000A5R-0105'.format(country,region,dots)
        
            keys = [evapor, gr_wat, soil_m, temper, snow_s, precip, norm_evapor, norm_gr_wat, norm_soil_m, norm_temper, norm_snow_s, norm_precip]
            cols = ['evapor', 'gr_wat', 'soil_m', 'temper', 'snow_s', 'precip', 'norm_evapor', 'norm_gr_wat', 'norm_soil_m', 'norm_temper', 'norm_snow_s', 'norm_precip']
        
        return keys, cols
    
    
    #Specifying timezone
    tz = pytz.timezone('Etc/GMT-1')
    year = datetime.date.today().year
    read_start = tz.localize(dt.datetime(year-1, 9, 1))
    today = pd.to_datetime(time.strftime("%Y.%m.%d %H:%M"), format="%Y.%m.%d %H:%M", errors='ignore')  # now
    read_end = tz.localize(today - pd.Timedelta(days=2))

    #Making a wrapper to read in the series with
    wrapper = ReadWrapper(start_time=read_start, end_time=read_end, tz=tz, read_from='SMG_PROD')

    
    # Reading timeseries for each catchment/region and combining all into one list for inflow and snow magazine
    df_list = list()
    for key, vhh in zip(names,vhhQ_OBSE_list):
        
        #getting keys to read and col names for final df
        if sheet[:3] == 'LTM':
            keys, cols = get_catchment_keys(key, sheet)
        else:
            keys, cols = get_region_keys(key, sheet)
            
        #Adding vhh_Q_OBSE if it exist to keys and cols
        if str(vhh) != 'nan':
            vhhQ_OBSE = '/{}'.format(vhh)
            keys.append(vhhQ_OBSE)
            cols.append('vhhQ_OBSE')
        
        #Reading series from SMG_PROD
        df = wrapper.read(keys)
        df.columns = cols
        
        #Adding spring_temp, read from local csv files
        temp_df = pd.read_csv(r'TEMP1\TEMP_{}_{}.csv'.format(sheet,key), index_col=0, parse_dates=True) 
        df['temp1Q_N_FB'] = temp_df['q'].astype(float)
        df['temp1SNOW_S'] = temp_df['s'].astype(float)
        
        
        #Adding spring_temp, read from local csv files
        temp_df = pd.read_csv(r'TEMP2\TEMP_{}_{}.csv'.format(sheet,key), index_col=0, parse_dates=True) 
        df['temp2Q_N_FB'] = temp_df['q'].astype(float)
        df['temp2SNOW_S'] = temp_df['s'].astype(float)
        
        #Adding ref1, read from local csv files
        ref_df = pd.read_csv(r'REF\REF_{}_{}.csv'.format(sheet,key), index_col=0, parse_dates=True) 
        df['ref1Q_N_FB'] = ref_df['q'].astype(float)
        df['ref1SNOW_S'] = ref_df['s'].astype(float)
        
        
        #Add final df to list of dataframes
        df_list.append(df)
        
        
    # Reading resources
    df_list_resources = list()
    for key in names:
        #getting keys to read
        keys, cols = get_resources_keys(key, sheet)
        #Reading series from SMG_PROD
        df_resources = wrapper.read(keys)
        df_resources.columns = cols
        df_list_resources.append(df_resources)
        
    return df_list, df_list_resources

 
    
    

def exclude_keys(df_list: [pd.DataFrame], keys: [str], excluded_list:[str]) -> [[pd.DataFrame], [str]]:
    """This functin takes in the whole list of dataframes for each region/catchment and then exlude dataframes for regions/catchments that for some reason is not okay to use in the analysis. The list of excluded regions/catchments is read from the excel document."""
    
    #Analysis
    df_for_analysis = df_list.copy()
    keys_for_analysis = list(keys)
    #remove excluded catchments
    dont_print = False
    for i, x, key in zip(range(len(keys)),excluded_list, keys):
        if x == 'X':
            if not dont_print:
                print('\nExcluded in this analysis:')
            print(key)
            del df_for_analysis[i]
            del keys_for_analysis[i]
            dont_print=True
    print('')
    
    return df_for_analysis, keys_for_analysis


def df_analysis_periods(df_list: [pd.DataFrame], all_resources: [pd.DataFrame], start_list: [str], end_list: [str], sheet: str) -> [[pd.DataFrame], [pd.DataFrame], [str], [str]]:
    """This function chooses the analysis period for each region/catchment and returns the dataframes for that period."""
    
    # Finding analysis period
    spring_flod_list = []
    resources_spring_flod = []
    spring_flod_info_start = []
    spring_flod_info_end = []
    analysis1_list =[]
    analysis1_info_start = []
    analysis2_list = []
    analysis2_info_start = []
    
    
    for df, resource_df, start_excel, end_excel in zip(df_list, all_resources, start_list, end_list):

        #FINDING START OF ANALYSIS
        if len(str(start_excel)) >= 5:
            #sp for spring_flod
            sp_start = pd.to_datetime(start_excel, format="%Y.%m.%d %H:%M", errors='ignore') 
            start_info = 'Analysis start ({}): read from excel.'.format(str(sp_start)[:-9])
        else:
            # Start of analysis is for date of maximum SWE
            sp_start = df['ref1SNOW_S'].idxmax()
            start_info = 'Analysis start ({}): Peak of snow magasine for ref inndatasett.'.format(str(sp_start)[:-15])

        #FINDING END OF ANALYSIS
        year = datetime.date.today().year
        last_possible_end = dt.datetime(year, 9, 1)
        
        if sheet[0:3] == "LTM":
            df_from_start = df[sp_start:]
            min_snow = 10
            maxQ_part = 0.025
        else:
            df_from_start = df[sp_start:last_possible_end]
            min_snow = df_from_start['ref1SNOW_S'].max()*0.08
            maxQ_part = 0.05

        if len(str(end_excel)) >= 5:
            end = pd.to_datetime(end_excel, format="%Y.%m.%d %H:%M", errors='ignore')
            end_info = 'Analysis end ({}): read from excel.'.format(str(end)[:-9])
        else:
            # End of analysis is when the SWE has reached a treshold minimum + 7 days for the runoff
            check_snow = (df_from_start['ref1SNOW_S'] + df_from_start['ltmSNOW_S'])/2
            end = df_from_start[check_snow.gt(min_snow)].index[-1] + dt.timedelta(days=7)
            error = False

            #checking if the end date is set outside the last time of the timeseries
            if end > df.index[-1]:
                # The chosen date is outside the range of the time series
                #end = df.index[-1]
                end = df_from_start['ref1SNOW_S'].idxmin()
                end_info = 'WARNING, end after last day! Analysis end ({}): this script did not find a sufficient estimation of the end of the spring flod, used here date for the ref snow magasine minimum.'.format(str(end)[:-15])
              
            else:
                #finding the first value where the diff in Q between observed and modelled is less or equal (le) than 10
                df_from_end = df[end:]
                check_q = (abs(df_from_end['ltmQ_OBSE']-df_from_end['ref1Q_N_FB']) + abs(df_from_end['ltmQ_OBSE']-df_from_end['ltmQ_N_FB']))/2
                min_val = df_from_end['ltmQ_OBSE'].max()*maxQ_part

                if len(df_from_end[check_q.le(min_val)].index) >= 1:
                    end = df_from_end[check_q.le(min_val)].index[0]
                    end_info = 'Analysis end ({}): First day when the inflow models are close to Q_OBSE, one week after the snow magasine goes under 20 GWh SWE.'.format(str(end)[:-15])
                else:
                    end = df_from_start['ref1SNOW_S'].idxmin()
                    #year = datetime.date.today().year
                    #end = dt.datetime(year, 9, 1)
                    end_info = 'WARNING! Analysis end ({}): this script did not find a sufficient estimation of the end of the spring flod, used here date for the ref snow magasine minimum.'.format(str(end)[:-15])

        spring_flod_list.append(df_from_start[:end])
        resources_spring_flod.append(resource_df[sp_start:end])
        spring_flod_info_start.append(start_info)
        spring_flod_info_end.append(end_info)
        
        
        def find_period_snow_adjusted(df: pd.DataFrame, end, orig: str, adj: str, adjustment: bool) -> [pd.DataFrame, pd.DataFrame]:
            # Finding analysis period a snow adjustment
            found_diff = False
            for df_orig, df_adj in zip(df[orig],df[adj]):
                if abs(df_orig-df_adj) >= 5:
                    if adjustment == 'first':
                        start = df[df[orig].gt(df_orig)][:'04.04.2019'].index[0] - pd.Timedelta(days=2)
                    else:
                        start = df[df[orig].gt(df_orig)].index[-1]
                    start_info = 'First analysis start ({}): Day befor {} snow adjustment.'.format(str(start)[:-15], adjustment)
                    analysis_df = df[start:end]
                    analysis_info = start_info
                    found_diff = True
                    break
            if not found_diff:
                analysis_df = ''
                analysis_info = ''
            return analysis_df, analysis_info
        
        # Finding analysis period for first snow adjustment (same end as above)
        analysis1_df, analysis1_info = find_period_snow_adjusted(df, end, orig='ref1SNOW_S', adj='temp1SNOW_S', adjustment='first')
        analysis1_list.append(analysis1_df)
        analysis1_info_start.append(analysis1_info)
        # Finding analysis period for second snow adjustment (same end as above)
        analysis2_df, analysis2_info = find_period_snow_adjusted(df[sp_start:], end, orig='temp1SNOW_S', adj='temp2SNOW_S', adjustment='second')
        analysis2_list.append(analysis2_df)
        analysis2_info_start.append(analysis2_info)

    return spring_flod_list, resources_spring_flod, spring_flod_info_start, spring_flod_info_end, analysis1_list, analysis1_info_start, analysis2_list, analysis2_info_start
        
        

        

def calc_performance(df_analysis_list: [pd.DataFrame], models: [str]) -> [pd.DataFrame, pd.DataFrame]:
    """This function is a head funcition for calculations of the performance of the models in the analysis period. See the functions for each calculation for more information: acc_performance, R2_performance."""
    
    # Initializing result dataframes for each model
    acc_perf_df = pd.DataFrame(columns = ['ref1','temp1', 'temp2','ltm'])
    R2_perf_df = pd.DataFrame(columns = ['ref1', 'temp1', 'temp2', 'ltm'])
    
    for df, model in zip(df_analysis_list, models):

        # Picking out the columns of the dataframe to shorten code
        obse = df['ltmQ_OBSE']
        ref1 = df['ref1Q_N_FB']
        temp1 = df['temp1Q_N_FB']
        #ref2 = df['ref2Q_N_FB']
        temp2 = df['temp2Q_N_FB']
        ltm = df['ltmQ_N_FB']
        
        # calculating performance and adding to 
        acc_perf = acc_performance(obse, [ref1, temp1, temp2, ltm])
        R2_perf = R2_performance(obse, [ref1, temp1, temp2, ltm])
    
        #Add performance results to dataframe
        acc_perf_df.loc[model] = acc_perf
        R2_perf_df.loc[model] = R2_perf
        
    
    return acc_perf_df, R2_perf_df

    

    
def acc_performance(fasit: pd.DataFrame, models: [pd.DataFrame]) -> [float]:
    """This function calculates the accumulated performance. The way it is calculated is that we find the accumulated value at the last time of the time series, and then calculates the percentage difference."""
    
    performance = []
    for model in models:
        performance.append((model.cumsum()[-1] - fasit.cumsum()[-1])/fasit.cumsum()[-1]*100)
        
    return performance


    
    
def R2_performance(fasit: pd.DataFrame, models: [pd.DataFrame]) -> [float]:
    """This function calculates the correlation coefficient between models and a fasit.
    Args:
        Fasit: A timeseries
        Models: modelled timesries

    Returns:
        R2: the correlation coefficient bewteen the two series."""
    
    # Calculating
    performance = []
    for model in models:
        performance.append(1 - sum(np.power(fasit - model, 2)) / (sum(np.power(fasit - np.mean(fasit), 2)) + 0.00001))
        
    return performance


    

def summary_table(df_analysis_list: [pd.DataFrame], models: [str], sheet: str) -> pd.DataFrame:
    """This function makes a styled pd.dataframe to be printed as a table of the main results."""
    
    # transform m^3/s to Mm^3 if neccesary
    if sheet[0:3] == 'LTM':
        #ax1b.set_ylabel('accumulated inflow Q [Mm3]')
        transform = (24*3600)/1000000 # m^3/s accumulated to Mm^3
    else:
        #ax1b.set_ylabel('accumulated inflow Q [GWh]')
        transform = 1
        
        
    # Initializing result dataframes for each model
    acc_inf = pd.DataFrame(columns = ['OBSE', 'REF', 'TEMP1', 'TEMP2','LTM', 'NORMAL'])

    for df, model in zip(df_analysis_list, models):

        # Picking out the columns of the dataframe and calculating the accumulated inflow over the analysis period
        obse = df['ltmQ_OBSE'].cumsum()[-1]*transform
        ref1 = df['ref1Q_N_FB'].cumsum()[-1]*transform - obse
        temp1 = df['temp1Q_N_FB'].cumsum()[-1]*transform - obse
        temp2 = df['temp2Q_N_FB'].cumsum()[-1]*transform - obse
        ltm = df['ltmQ_N_FB'].cumsum()[-1]*transform - obse
        norm = df['normQ_N_FB'].cumsum()[-1]*transform - obse
        
        #Add accumulated results to dataframe
        acc_inf.loc[model] = [obse,ref1,temp1,temp2,ltm,norm]
        
    if sheet[0:3] == 'LTM':
        unit = 'Mm^3'
        transform = 1
    else:
        unit ='TWh'
        trnasform = 1000
        
    df = (acc_inf/transform).round(1)  
    
    df_styled = df.style.set_caption('Accumulated inflow ({}) deviation from Q_OBSE for the spring flod period.'.format(unit))\
    .bar(subset=['OBSE', 'REF', 'TEMP1', 'TEMP2','LTM', 'NORMAL'], align='zero', color=['#23c6c8', '#f8ac59'])
       
    return df_styled

     
    
    
    
def box_plot(acc_perf_df: pd.DataFrame) -> None:
    """Box and whiskers plot of the performance dataframe for each model."""
    
    # Create a figure instance
    fig = plt.figure(1, figsize=(9, 6))
    
    # Create an axes instance
    ax = fig.add_subplot(111)

    ## add patch_artist=True option to ax.boxplot() 
    ## to get fill color
    bp = ax.boxplot(acc_perf_df.transpose(), patch_artist=True, meanline=True, showmeans=True, whis=100)
    linecolor = 'black'
    linestyles=['-.','-.',':',':',':',':','-','-']
    colors=['green', 'green', 'deepskyblue', 'deepskyblue', 'red', 'red','plum', 'plum']

    ## change outline color, fill color and linewidth of the boxes
    for box,color,linestyle in zip(bp['boxes'],colors[::2],linestyles[::2]):
        # change outline color
        box.set(color=color, linewidth=3, linestyle=linestyle)
        # change fill color
        box.set( facecolor = 'white', alpha=1)

    ## change color and linewidth of the whiskers
    for whisker,color,linestyle in zip(bp['whiskers'],colors,linestyles):
        whisker.set(color=color, linewidth=3, linestyle=linestyle)

    ## change color and linewidth of the caps
    for cap,color,linestyle in zip(bp['caps'],colors,linestyles):
        cap.set(color=color, linewidth=3, linestyle=linestyle)

    ## change color and linewidth of the medians
    for median in bp['medians']:
        median.set(color='black', linewidth=2)

    for mean in bp["means"]:
        mean.set(color='black', linewidth=2)
        
    ## change the style of fliers and their fill
    for flier in bp['fliers']:
        flier.set(marker='o', markersize='5', markerfacecolor='black',markeredgewidth='0', markeredgecolor='black')

    ## Custom x-axis labels and ylabel
    ax.set_xticklabels(['ref1', 'temp1', 'temp2', 'ltm'])
    plt.ylabel('Accumulated deviation from Q_OBSE [%]')

    ## Remove top axes and right axes ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    
    plt.title('box and whiskers plot: spring flod period')
    explintaiotion = 'Make a box and whisker plot for each column of x or each vector in sequence x. The box extends from the lower to upper quartile values of the data, with a line at the median. The whiskers extend from the box to show the range of the data. Flier points are those past the end of the whiskers.'
    # you can set whisker maximum and minimum, so that outliers are "fliers"
    
    
        
############# LOOP OVER ALL REGIONS/CATCHMENTS ####################################    


def make_all(df_analysis_period: [pd.DataFrame], all_df: [pd.DataFrame], resources_analysis_period: [pd.DataFrame], all_resources: [pd.DataFrame], all_keys: [str], start_info_list: [str], end_info_list: [str], sheet: str, vhhQ_OBSE_list: [str], comments_list: [str], excluded_list: [str], file: str, df_analysis1_list: list, start_analysis1_list: list , df_analysis2_list: list, start_analysis2_list: list) -> None:
    """This is the head function for showing the output for each region/catchment."""
    
    #Calculates here for all catchments, also those who were excluded
    acc_perf_df, R2_perf_df = calc_performance(df_analysis_period, all_keys)
    
    if type(comments_list) == bool:
        comments_list = ['nan']*len(end_info_list)
    if type(excluded_list) == bool:
        excluded_list = ['nan']*len(end_info_list)
        
    
    #Read from excel the color of each week with snow adjustmets
    Sheet = pd.read_excel(file,'Snow updates') 
    adjusted_weeks = Sheet['Registrated Week:'].values
    adjusted_weeks_colors = Sheet['Color:'].values
    colors_adj = dict(zip(adjusted_weeks, adjusted_weeks_colors))

    
    for df, df_long, df_r, df_r_long, key, start_info, end_info, vhh, comment, excluded, df1, start_info1, df2, start_info2 in zip(df_analysis_period, all_df, resources_analysis_period, all_resources, all_keys, start_info_list, end_info_list, vhhQ_OBSE_list, comments_list, excluded_list, df_analysis1_list, start_analysis1_list, df_analysis2_list, start_analysis2_list):
        
        print('\n\n')
        print('------------------------------------------------------------------------------------------------------------------------')
        print('                                                        {}'.format(key))
        print('------------------------------------------------------------------------------------------------------------------------')
        print(start_info)
        print(end_info)
        if len(str(comment)) >= 4:
            print('\nComment from Excel file: "{}"\n'.format(comment))
        if excluded == 'X':
            print('WARNING: THIS CATCHMENT IS EXCLUDED FROM THE ANALYSIS!')
       
        if str(vhh) == 'nan':
            vhh = False
        else:
            vhh = True
        
        acc_perf = acc_perf_df.loc[[key]]
        R2_perf = R2_perf_df.loc[[key]]

        
        # PROGNOSIS PLOT
        if key[0:3] == 'Reg':
            plot_prognosis(file, df, key, sheet, colors_adj)
            
        # PLOTS: ANALYSIS PERIOD
        plot_resources(df_r, df, key, sheet)
        subplot_acc_R2(df, key, sheet, vhh)
        # printout
        print('\nAccumulated performance [percentage deviation]: ref1: {:.2f}, temp1: {:.2f}, temp2: {:.2f}, ltm: {:.2f}'.format(acc_perf['ref1'][0], acc_perf['temp1'][0], acc_perf['temp2'][0], acc_perf['ltm'][0]))
        print('Profile correlation performance [R2 value]: ]: ref1: {:.2f}, temp1: {:.2f}, temp2: {:.2f}, ltm: {:.2f}\n\n'.format(R2_perf['ref1'][0], R2_perf['temp1'][0], R2_perf['temp2'][0], R2_perf['ltm'][0]))
        
        if sheet[0:3] == 'LTM':
            if type(df1) == pd.DataFrame:
                subplot_acc_R2(df1, key, sheet, vhh, adjustment='first')
            if type(df2) == pd.DataFrame:
                subplot_acc_R2(df2, key, sheet, vhh, adjustment='second')
           
        
        #PLOTS: WHOLE PERIOD
        plot_resources(df_r_long, df_long, key, sheet, long=True)
        subplot_acc_R2(df_long, key, sheet, vhh, long=True)
        
        print('\n\n\n')
        
            
        
        
        
        




def subplot_acc_R2(df: pd.DataFrame, key: str, sheet: str, vhh: bool = False, long: bool = False, adjustment: str = False) -> None:
    """This function makes a plot of the accumulated inflow and snow magazine and also the raw inflow, for each model."""

    #Change font
    font = {'weight' : 'normal',
        'size'   : 14}

    mpl.rc('font', **font)
    
    fig, (ax1, ax2) = plt.subplots(2,1, figsize=(16,14), sharex=True)
    plt.gca().xaxis.set_tick_params(which='major', pad=20)

    
    # ACC PLOT
    #Set scale for accumulated plot for regions so that its the same for snow and inflow [GWh]
    y_max = max(df['normQ_N_FB'].cumsum().max(), df['ltmQ_OBSE'].cumsum().max(), df['ltmQ_N_FB'].cumsum().max(), df['temp2Q_N_FB'].cumsum().max(), df['ref1Q_N_FB'].cumsum().max())*1.03
    color = 'k'
    if sheet[0:3] == 'LTM':
        ax1.set_ylabel('snow magasine SNOW_S [mm]', color=color)
    else:
        ax1.set_ylabel('snow magasine SNOW_S [GWh]', color=color)
        ax1.set_ylim(0, y_max)
    ax1.plot(df['normSNOW_S'],'-', color='moccasin', linewidth=5.0, label = 'SNOW_S_1980-2010')
    ax1.plot(df['ltmSNOW_S'],'-', color='plum', linewidth=4.0, label = 'ltmSNOW_S')
    ax1.plot(df['temp2SNOW_S'],':', color='red', linewidth=3.0, label = 'temp2SNOW_S')
    ax1.plot(df['temp1SNOW_S'],':', color='deepskyblue', linewidth=2.0, label = 'temp1SNOW_S')
    ax1.plot(df['ref1SNOW_S'],'-.', color='green', linewidth=3.0, label = 'ref1SNOW_S')
    ax1.tick_params(axis='y', labelcolor=color)
    #plt.gcf().autofmt_xdate()
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles[::-1], labels[::-1], loc='center left')
    
    # second y-axis for acc plot
    ax1b = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    color = 'k'
    if sheet[0:3] == 'LTM':
        ax1b.set_ylabel('accumulated inflow Q [Mm3]', color=color)
        transform = (24*3600)/1000000 # m^3/s accumulated to Mm^3
    else:
        ax1b.set_ylabel('accumulated inflow Q [GWh]', color=color)
        transform = 1
        ax1b.set_ylim(0,y_max)
    ax1b.plot(df['normQ_N_FB'].cumsum()*transform,'-', color='moccasin', linewidth=5.0, label = 'Q_N_FB_1980-2010')
    if vhh:
        ax1b.plot(df['vhhQ_OBSE'].cumsum()*transform,'-', color='grey', linewidth=4.0, label = 'vhhQ_OBSE')
    ax1b.plot(df['ltmQ_OBSE'].cumsum()*transform,'-k', linewidth=4.0, label = 'ltmQ_OBSE')
    ax1b.plot(df['ltmQ_N_FB'].cumsum()*transform,'-', color='plum', linewidth=4.0, label='ltmQ_N_FB')
    ax1b.plot(df['temp2Q_N_FB'].cumsum()*transform,':', color='red', linewidth=3.0, label = 'temp2Q_N_FB')
    ax1b.plot(df['temp1Q_N_FB'].cumsum()*transform,':', color='deepskyblue', linewidth=2.0, label = 'temp1Q_N_FB')
    ax1b.plot(df['ref1Q_N_FB'].cumsum()*transform,'-.', color='green', linewidth=3.0, label = 'ref1Q_N_FB')
    ax1b.tick_params(axis='y', labelcolor=color)
    handles, labels = ax1b.get_legend_handles_labels()
    ax1b.legend(handles[::-1], labels[::-1], loc='center right')
  
    #max_list=[df['normQ_N_FB'].cumsum()*transform,df['ltmQ_OBSE'].cumsum()*transform]
    #ax1.set_ylim(0, max(max_list)+max(max_list)*0.1)
   
    
    # R2 PLOT
    color = 'k'
    if sheet[0:3] == 'LTM':
        ax2.set_ylabel('inflow [m3/s]', color=color)
    else:
        ax2.set_ylabel('inflow [GWh]', color=color)
    ax2.plot(df['normQ_N_FB'],'-', color='moccasin', linewidth=5.0, label = 'Q_N_FB_1980-2010')
    if vhh:
        ax2.plot(df['vhhQ_OBSE'],'-', color='grey', linewidth=4.0, label = 'vhhQ_OBSE')
    ax2.plot(df['ltmQ_OBSE'],'-k', linewidth=4.0, label = 'ltmQ_OBSE')
    ax2.plot(df['ltmQ_N_FB'],'-', color='plum', linewidth=4.0, label = 'ltmQ_N_FB')
    ax2.plot(df['temp2Q_N_FB'],':', color='red', linewidth=3.0, label = 'temp2Q_N_FB')
    ax2.plot(df['temp1Q_N_FB'],':', color='deepskyblue', linewidth=2.0, label = 'temp1Q_N_FB')
    ax2.plot(df['ref1Q_N_FB'],'-.', color='green', linewidth=3.0, label = 'ref1Q_N_FB')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.yaxis.tick_right()
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(handles[::-1], labels[::-1], loc='upper right')
    ax2.yaxis.set_label_position("right")
   
    #General
    if long:
        fig.suptitle('{}: whole period'.format(key))
        plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
        plt.gca().xaxis.set_minor_locator(mdates.MonthLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    else:
        plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter('u%V'))
        plt.gca().xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=(0), interval=1))
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        if adjustment:
            fig.suptitle('{}: {} analysis period'.format(key, adjustment))
        else:
            fig.suptitle('{}: spring flod period'.format(key))
    fig.tight_layout()
    fig.subplots_adjust(top=0.95)
    plt.show()
    

    
    
   
  
    
    
def plot_prognosis(file: str, df: pd.DataFrame, key: str, sheet: str, colors_adj: [str]) -> None:

    
    def sort_adjustments(keys : [str], snowjust: list) -> [dict, [str]]:
        
        ########## for sorting the week numbers ##################
        def atoi(text):
            return int(text) if text.isdigit() else text

        def natural_keys(text):
            '''
            alist.sort(key=natural_keys) sorts in human order
            http://nedbatchelder.com/blog/200712/human_sorting.html
            (See Toothy's implementation in the comments)
            '''
            return [ atoi(c) for c in re.split(r'(\d+)', text) ]

        ##########################################################
    
        #Make a dict with the catchments as keys and the week they are updates as values.
        snowjust_dict = {}
        for i in range(len(keys)):
            if (type(snowjust[i]) != float) and (snowjust[i] not in snowjust_dict.keys()) and (str(snowjust[i]) != 'nan'):
                snowjust_dict[snowjust[i]] = [key for key,date in zip(keys,snowjust) if date == snowjust[i]]
        #Getting the list of the updated weeks and sorted using the above functions
        weeks_aft = list(snowjust_dict.keys())
        weeks_aft.sort(key=natural_keys)
        
        return snowjust_dict, weeks_aft
        
    
    if key[0:3] == 'Reg':
        reg = '{}-{}'.format(sheet,key)
        Sheet = pd.read_excel(file,reg) 
        keys = Sheet['Nedslagsfelt:'].values
        snowjust1 = Sheet['Snøjustert dato 1:'].values
        snowjust2 = Sheet['Snøjustert dato 2:'].values

        snowjust1_dict, weeks_aft1 = sort_adjustments(keys,snowjust1)
        snowjust2_dict, weeks_aft2 = sort_adjustments(keys,snowjust2)
        snowjust_dict = dict(snowjust1_dict)
        snowjust_dict.update(snowjust2_dict)
        weeks_aft = weeks_aft1+ weeks_aft2
        
        #Specifying timezone
        tz = pytz.timezone('Etc/GMT-1')
        year = datetime.date.today().year
        #read_start = df.index[0]
        read_start = dt.datetime(year, 1, 1)
        read_end = df.index[-1] + pd.Timedelta(days=1)

        #Making a wrapper to read in the series with
        wrapper = ReadWrapper(start_time=read_start, end_time=read_end, tz=tz, read_from='SMG_PROD')

        dotsQ = '......'
        dotsSnow = '..........'

        smg_text_q = '.NFB{}-D1050A5S-0105'.format(dotsQ)
        smg_text_s = '{}-D2003A5S-0105'.format(dotsSnow)

        if weeks_aft:
            weeks_bf = ['u{:02d}'.format(int(week[1:])-1) for week in weeks_aft]
            q_keys_aft = ['/{}/{}-{}{}'.format(week,sheet,key,smg_text_q) for week in weeks_aft]
            q_keys_bf = ['/{}/{}-{}{}'.format(week,sheet,key,smg_text_q) for week in weeks_bf]
            s_keys_aft = ['/{}/{}-{}{}'.format(week,sheet,key,smg_text_s) for week in weeks_aft]
            s_keys_bf = ['/{}/{}-{}{}'.format(week,sheet,key,smg_text_s) for week in weeks_bf]
            
            
            #Reading series from SMG_PROD
            q_aft = wrapper.read(q_keys_aft)
            q_aft.columns = [weeks_aft]
            q_bf = wrapper.read(q_keys_bf)
            q_bf.columns = [weeks_bf]
            s_aft = wrapper.read(s_keys_aft)
            s_aft.columns = [weeks_aft]
            s_bf = wrapper.read(s_keys_bf)
            s_bf.columns = [weeks_bf]


                
            fig, ax1 = plt.subplots(figsize=(16,16))
            plt.gca().xaxis.set_tick_params(which='major', pad=20)
            
            
            ax1.plot(df['ltmSNOW_S'], ':', color='plum', linewidth=3.0, label = 'ltmSNOW_S')
            ax1.set_ylabel('snow magazine [GWh]')
            
            ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
            ax2.plot(df['ltmQ_OBSE'].cumsum(),'-k', linewidth=4.0, label = 'ltmQ_OBSE')
            ax2.plot(df['ltmQ_N_FB'].cumsum(),':', color='plum', linewidth=3.0, label='ltmQ_N_FB')
            ax2.set_ylabel('accumulated inflow [GWh]')
            
            plt.title('{}: Prognosis week before and after snow updates (p.50)'.format(key))
            
            
            print('\nModels updated in explicit weeek:')
            for i in range(len(weeks_bf)):
                print("{}: {}".format(weeks_aft[i],snowjust_dict[weeks_aft[i]]))
                
                
                #ax1 Snow magazine:
                #Plots here the observed using the start and end of the first prognosis
                #Plotting the prognosis accumulated started from the ltmQ_N_FB
                ax1.plot(s_bf[weeks_bf[i]], '-.', color=colors_adj[weeks_aft[i]], linewidth=3.0, label=weeks_bf[i])
                ax1.plot(s_aft[weeks_aft[i]], color=colors_adj[weeks_aft[i]], linewidth=3.0, label=weeks_aft[i])
                
                #ax2 accumulated inflow:
                #Plots here the observed using the start and end of the first prognosis
                #Plotting the prognosis accumulated started from the ltmQ_N_FB
                acc_q_bf = q_bf[weeks_bf[i]].cumsum()+df['ltmQ_N_FB'].cumsum()[q_bf[weeks_bf[i]].dropna().index[0]]
                acc_q_aft = q_aft[weeks_aft[i]].cumsum()+df['ltmQ_N_FB'].cumsum()[q_aft[weeks_aft[i]].dropna().index[0]]
                ax2.plot(acc_q_bf, '-.', color=colors_adj[weeks_aft[i]], linewidth=3.0, label=weeks_bf[i])
                ax2.plot(acc_q_aft, color=colors_adj[weeks_aft[i]], linewidth=3.0, label=weeks_aft[i])
                
                
                #Set scale for accumulated plot for regions so that its the same for snow and inflow [GWh]
                y_max = max(df['normQ_N_FB'].cumsum().max(), df['ltmQ_OBSE'].cumsum().max(), acc_q_bf.max().max(), acc_q_aft.max().max())*1.03
                ax1.set_ylim(0,y_max)
                ax2.set_ylim(0,y_max)
                
             
            ax1.yaxis.tick_right()
            handles, labels = ax1.get_legend_handles_labels()
            ax1.legend(handles[::], labels[::], loc='upper left')
            ax1.yaxis.set_label_position("left")
                
            ax2.yaxis.tick_right()
            handles, labels = ax2.get_legend_handles_labels()
            ax2.legend(handles[::], labels[::], loc='center right')
            ax2.yaxis.set_label_position("right")
            
            #general
            plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter('u%V'))
            plt.gca().xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=(0), interval=1))
            plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
            plt.show()

                
                

                
                       
    
def plot_perf_models(df: pd.DataFrame, sheet: str, perfType: str) -> None:
    """Plot the performance dataframes for the chosen type of performance check (perfType)."""
    
    fig = plt.figure(figsize=(16,8))
    ax = fig.add_subplot(1, 1, 1)
    plt.gca().xaxis.set_tick_params(which='major', pad=20)
    
    if sheet[0:3] == 'LTM':
        ax.plot(df['ltm'],'-', color='plum', linewidth=3.0, label = 'ltm {:.2f} +/- {:.2f}'.format(df['ltm'].mean(),df['ltm'].std()))
        ax.plot(df['temp2'],':', color='red', linewidth=3.0, label = 'temp2 {:.2f} +/- {:.2f}'.format(df['temp2'].mean(),df['temp2'].std()))
        ax.plot(df['temp1'],':', color='deepskyblue', linewidth=3.0, label = 'temp1 {:.2f} +/- {:.2f}'.format(df['temp1'].mean(),df['temp1'].std()))
        ax.plot(df['ref1'],'-.', color='green', alpha=0.8, linewidth=3.0, label = 'ref1 {:.2f} +/- {:.2f}'.format(df['ref1'].mean(),df['ref1'].std()))
    else:
        if sheet == 'Sver':
            land = 'Sverige'
        else:
            land = 'Norge'
        ax.plot(df['ltm'],'-', color='plum', linewidth=3.0, label = 'ltm {:.2f} +/- {:.2f}'.format(df.drop(land)['ltm'].mean(),df.drop(land)['ltm'].std()))
        ax.plot(df['temp2'],':', color='red', linewidth=3.0, label = 'temp2 {:.2f} +/- {:.2f}'.format(df.drop(land)['temp2'].mean(),df.drop(land)['temp2'].std()))
        ax.plot(df['temp1'],':', color='deepskyblue', linewidth=3.0, label = 'temp1 {:.2f} +/- {:.2f}'.format(df.drop(land)['temp1'].mean(),df.drop(land)['temp1'].std()))
        ax.plot(df['ref1'],'-.', color='green', alpha=0.8, linewidth=3.0, label = 'ref1 {:.2f} +/- {:.2f}'.format(df.drop(land)['ref1'].mean(),df.drop(land)['ref1'].std()))
    
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc='best')
    
    plt.plot(df['ltm']*0, 'k', linewidth=3.0)
    if max(abs(df['ltm'])) <= 1:
        plt.plot(df['ltm']/df['ltm']*1, 'k', linewidth=3.0)
    plt.gcf().autofmt_xdate()
    ax = plt.gca()
    ax.grid(True)
    if perfType == 'R2':
        plt.ylabel('Correlation with Q_OBSE (R2)')
    else:
        plt.ylabel('Accumulated deviation from Q_OBSE [%]')
    plt.title('{} Performance'.format(perfType))
    plt.show()
    
    
    
    
    
    
def plot_resources(df_r: pd.DataFrame, df_q_s: pd.DataFrame, key: str, sheet: str, long: bool = False) -> None:
    """This function plots the resources for each reagion/catchment."""

    fig, (ax1, ax2) = plt.subplots(2,1, figsize=(16,14), sharex=True)
    plt.gca().xaxis.set_tick_params(which='major', pad=20)

    #FIGURE1: dev from normal
    #ax1.set_title('{}: Resource development for melting/analysis period'.format(key))
    ax1.set_ylabel('deviation from normal [GWh]')
    #precipitation
    ax1.fill_between(df_r.index[:],df_r['precip'].cumsum()-df_r['norm_precip'].cumsum(),color='grey',alpha=0.5, label='accumulated precipitation')

    #Evaporation
    ax1.fill_between(df_r.index[:],df_r['evapor'].cumsum()-df_r['norm_evapor'].cumsum(),color='gold',alpha=0.5, label='accumulated evaporation')

    #Bounded water = snow + groundwater + soil moisture
    bounded_water = df_r['snow_s'] + df_r['gr_wat'] + df_r['soil_m']
    norm_bounded_water = df_r['norm_snow_s'] + df_r['norm_gr_wat'] + df_r['norm_soil_m']
    ax1.plot(df_r['snow_s']-df_r['norm_snow_s'], 'purple', linewidth=3, label='bounded water = snow + ground water + soil moisture')

    #Inflow
    ax1.plot(df_q_s['ltmQ_N_FB'].cumsum() - df_q_s['normQ_N_FB'].cumsum(), 'b', linewidth=3, label = 'accumulated simulated inflow')

    #general ax1
    ax1.legend()

    #FIGURE 2

    # Precipitation
    ax2.fill_between(df_r.index[:],df_r['precip'].cumsum(),color='grey',alpha=0.5, label='accumulated precipitation')
    ax2.plot(df_r['norm_precip'].cumsum(), ':k', linewidth=3, label='accumulated normal precipitation')
    ax2.set_ylabel('precipitation [GWh]')
    ax2.legend(loc='lower right')

    #temperature
    ax2b = ax2.twinx()
    if sheet[0:3] == 'LTM':
        ax2b.plot(df_r['orig_temp'], '--g', linewidth=3, label='original temperature')
        ax2b.plot(df_r['adj_temp']*0, '-k', linewidth=1.5, alpha=0.5, label='zero degrees')
        ax2b.plot(df_r['adj_temp'], '-r', linewidth=3, label='temperature with adjustments')
    else:
        ax2b.plot(df_r['temper'], '-r', linewidth=3, label='temperature')
        ax2b.plot(df_r['temper']*0, '--k', linewidth=1.5, alpha=0.5, label='zero degrees')
        ax2b.plot(df_r['norm_temper'], ':r', linewidth=3, label=' normal temperature')
    ax2b.set_ylabel('temperature [deg]')
    ax2b.legend(loc='upper left')

    #General
    fig.tight_layout()
    fig.subplots_adjust(top=0.95)
    if long:
        fig.suptitle('{}: Whole period'.format(key))
        plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
        plt.gca().xaxis.set_minor_locator(mdates.MonthLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        plt.gca().xaxis.set_major_locator(mdates.YearLocator())
    else:
        fig.suptitle('{}: Melting/Analysis period'.format(key))
        plt.gca().xaxis.set_minor_formatter(mdates.DateFormatter('u%V'))
        plt.gca().xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=(0), interval=1))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
        #plt.gcf().autofmt_xdate()
          
    plt.show()  
        
    
    
    
    
    
def pie_subplot_perf(acc_perf_df: pd.DataFrame, sheet: str, ref_model: str, model: str) -> None:
    """This function plots pieplots."""
    
    ref_perf = acc_perf_df[ref_model]
    mod_perf = acc_perf_df[model]

    if sheet in ['Norg', 'Sver']:
        what = 'R'
    else:
        what = 'M'
    
    def pie(ax, values, **kwargs):
        total = sum(values)
        def formatter(pct):
            if pct*total == 0:
                return ''
            else:
                return '${:0.0f}'.format(pct*total/100, what)
            #return '${:0.0f}M\n({:0.1f}%)'.format(pct*total/100, pct)
        wedges, _, labels = ax.pie(values, autopct=formatter, **kwargs)
        return wedges


    width = 0.35 
    kwargs_outside = dict(colors=['#66FF66','#FF9999', '#FF9999', '#66FF66'], startangle=90)
    kwargs_inside = dict(colors=['#FF9955','#9999FF'], startangle=90)
    
    
    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(16,8))

    for ax,lim in zip([ax1, ax2],[0.5, 5]):
        
        #Calculating number of models adjusted up/down and better/worse results to plot
        #Initializing
        no_edit = 0
        up_better = 0
        up_worse = 0
        down_better = 0
        down_worse = 0
        #Calculationg
        for ref, mod in zip(ref_perf, mod_perf):
            listed = [abs(mod),abs(ref)]
            if ref+lim >= mod >= ref-lim:
                no_edit += 1
            elif mod >= ref:
                #checking if ltm was better than ref (1) or not (-1)
                if listed.index(min(listed)) == 0:
                    up_better += 1
                else:
                    up_worse += 1
            else:
                #checking if ltm was better than ref (1) or not (-1)
                if listed.index(min(listed)) == 0:
                    down_better += 1
                else:
                    down_worse += 1
        
        ax.axis('equal')

        outside = pie(ax, [up_better, up_worse, down_worse, down_better], radius=1, pctdistance=1-width/2, **kwargs_outside)
        inside = pie(ax, [up_better+up_worse, down_better+down_worse], radius=1-width, 
                     pctdistance=1 - (width/2) / (1-width), **kwargs_inside)
        plt.setp(inside + outside, width=width, edgecolor='white')

        ax.legend(inside[::-1] + outside[::-1], ['adjusted down', 'adjusted up', 'better', 'worse'], frameon=False, loc = 'upper left')
        #ax.legend(outside[::-1], ['better', 'worse'], frameon=False)

        kwargs = dict(size=13, color='white', va='center', fontweight='bold')
        
        ax.text(0, 0, 'Out of:\n${}{}'.format(up_better+up_worse+down_better+down_worse+no_edit, what), ha='center', 
            bbox=dict(boxstyle='round', facecolor='blue', edgecolor='none'),
            **kwargs)
        ax.annotate('Year {}'.format(datetime.date.today().year), (0, 0), xytext=(np.radians(-45), 1.1), 
                    bbox=dict(boxstyle='round', facecolor='green', edgecolor='none'),
                    textcoords='polar', ha='left', **kwargs)
        ax.set_title('Q diff > {}%'.format(lim))
        
    if model == 'temp1':
        plt.suptitle('Early Spring Snow Adjustments ({} vs. {})\n'.format(model, ref_model), size=20)
    elif model == 'temp2':
        plt.suptitle('Lat Spring/Summer Snow Adjustments ({} vs. {})\n'.format(model, ref_model), size=20)
    elif model == 'ltm':
        plt.suptitle('Added Temperature Adjustments ({} vs. {})\n'.format(model, ref_model), size=20)


    plt.show()
 











    
################# COPY TEMP FROM SMG ###########################

def copy_from_SMG(to_save: str, file: str) -> None:
    """This function copies certain series from SMG to csv files saved in the folders TEMP and REF, chosen from the excel file."""
    
    #Internal function
    def read_excel(sheet: str, file: str) -> [str]:

        Sheet = pd.read_excel(file,sheet) 
        keys = Sheet['Område:'].values
        return keys

    if to_save[0:3] == 'REF':
        model = 'REF'
    if to_save[0:4] == 'TEMP':
        model = 'TEMP'
    
    #Specifying timezone
    tz = pytz.timezone('Etc/GMT-1')
    year = datetime.date.today().year
    read_start = tz.localize(dt.datetime(year-1, 9, 1))
    today = pd.to_datetime(time.strftime("%Y.%m.%d %H:%M"), format="%Y.%m.%d %H:%M", errors='ignore')  #now
    read_end = tz.localize(today - pd.Timedelta(days=2))

    #Making a wrapper to read in the series with
    wrapper = ReadWrapper(start_time=read_start, end_time=read_end, tz=tz, read_from='SMG_PROD')
    
    # Getting time series info from sheets in the excel file
    all_sheets = ['LTM1','LTM2','LTM3','LTM4','LTM5','LTM6','LTM7','LTM8','LTMS','Norg', 'Sver'] 
    
    for sheet in all_sheets:
        
        ids_list = read_excel(sheet, file)
        
        for ids in ids_list:

            if sheet in all_sheets[-2:]:
                q = '/{}/'.format(model) + '{}-{}.NFB......'.format(sheet,ids)[0:19] + '-D1050A5R-0105' #inflow
                s = '/{}/'.format(model) + '{}-{}..........'.format(sheet,ids)[0:19] + '-D2003A5R-0105' #snow water eqvialent (SWE)
            else:
                q = '/HBV/{}-{}/{}/UPDAT/Q_N_FB'.format(sheet,ids,model) #inflow
                s = '/HBV/{}-{}/{}/UPDAT/SNOW_S'.format(sheet,ids,model) #snow water eqvialent (SWE)

            keys = [q,s]
            #Reading series from SMG_PROD
            df = wrapper.read(keys)
            df.columns = ['q','s']
            df.to_csv(r'{}\{}_{}_{}.csv'.format(to_save,model,sheet,ids))
    
    print('Done saving to {}'.format(to_save))
