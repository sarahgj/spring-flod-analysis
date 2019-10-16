import pytz
import time
from time import gmtime, strftime
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib as mpl
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import numpy as np
import pandas as pd
import xlsxwriter
import datetime
import re

from sklearn.linear_model import LinearRegression 

from statkraft.ssa.wrappers import ReadWrapper



def read_excel(sheet, file):
    
    Sheet = pd.read_excel(file,sheet) 
    keys = Sheet['Område:'].values
    vhhQ_OBSE_list = Sheet['VHH tilsig:'].values
    comments_list = Sheet['Kommentar:']
    exluded_list = Sheet['Ikke analyserbar:']
    start_list = Sheet['Start:']
    end_list = Sheet['Slutt:']
    
    return keys, vhhQ_OBSE_list, comments_list, exluded_list, start_list, end_list



def read_from_SMG(names, vhhQ_OBSE_list, sheet):
    
    #Internal functions
    def get_catchment_keys(catchment, ltm):

        #inflow
        refQ_N_FB = '/HBV/{}-{}/REF/UPDAT/Q_N_FB'.format(ltm,catchment)
        ltmQ_N_FB = '/HBV/{}-{}/LTM/UPDAT/Q_N_FB'.format(ltm,catchment)
        tempQ_N_FB = '/HBV/{}-{}/TEMP/UPDAT/Q_N_FB'.format(ltm,catchment)
        ltmQ_OBSE = '/HBV/{}-{}/LTM/UPDAT/Q_OBSE'.format(ltm,catchment)
        meanQ_N_FB = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/Q_N_FB'.format(ltm,catchment)
        #SWE
        refSNOW_S = '/HBV/{}-{}/REF/UPDAT/SNOW_S'.format(ltm,catchment)
        ltmSNOW_S = '/HBV/{}-{}/LTM/UPDAT/SNOW_S'.format(ltm,catchment)
        tempSNOW_S = '/HBV/{}-{}/TEMP/UPDAT/SNOW_S'.format(ltm,catchment)
        meanSNOW_S = '/HBV/{}-{}/LTM/UPDAT/Mean/198009-201009/SNOW_S'.format(ltm,catchment)

        keys = [refQ_N_FB, ltmQ_N_FB, tempQ_N_FB, ltmQ_OBSE, meanQ_N_FB, refSNOW_S, ltmSNOW_S, tempSNOW_S, meanSNOW_S]
        cols = ['refQ_N_FB', 'ltmQ_N_FB', 'tempQ_N_FB', 'ltmQ_OBSE', 'meanQ_N_FB', 'refSNOW_S', 'ltmSNOW_S', 'tempSNOW_S', 'meanSNOW_S']

        return keys, cols
    
    def get_region_keys(region, country):
        
        dotsQ = '......'
        dotsSnow = '..........'
        if region == 'Norge':
            dotsQ = '.....'
            dotsSnow = '.........'
        if region == 'Sverige':
            dotsQ = '...'
            dotsSnow = '.......'
        
        #inflow
        refQ_N_FB = '/REF/{}-{}.NFB{}-D1050A5R-0105'.format(country,region,dotsQ)
        ltmQ_N_FB = '/{}-{}.NFB{}-D1050A5R-0105'.format(country,region,dotsQ)
        tempQ_N_FB = '/TEMP/{}-{}.NFB{}-D1050A5R-0105'.format(country,region,dotsQ)
        ltmQ_OBSE = '/{}-{}{}-D1050A5R-0105'.format(country,region,dotsSnow)
        meanQ_N_FB = '/Mean/198009-201009/{}-{}.NFB{}-D1050A5R-0105'.format(country,region,dotsQ)
        #SWE
        refSNOW_S = '/REF/{}-{}{}-D2003A5R-0105'.format(country,region,dotsSnow)
        ltmSNOW_S = '/{}-{}{}-D2003A5R-0105'.format(country,region,dotsSnow)
        tempSNOW_S = '/TEMP/{}-{}{}-D2003A5R-0105'.format(country,region,dotsSnow)
        meanSNOW_S = '/Mean/198009-201009/{}-{}{}-D2003A5R-0105'.format(country,region,dotsSnow)
        
        keys = [refQ_N_FB, ltmQ_N_FB, tempQ_N_FB, ltmQ_OBSE, meanQ_N_FB, refSNOW_S, ltmSNOW_S, tempSNOW_S, meanSNOW_S]
        cols = ['refQ_N_FB', 'ltmQ_N_FB', 'tempQ_N_FB', 'ltmQ_OBSE', 'meanQ_N_FB',  'refSNOW_S', 'ltmSNOW_S', 'tempSNOW_S', 'meanSNOW_S']
        
        return keys, cols
    
    
    #Specifying timezone
    tz = pytz.timezone('Etc/GMT-1')
    year = datetime.date.today().year
    read_start = tz.localize(dt.datetime(year-1, 9, 1))
    today = pd.to_datetime(time.strftime("%Y.%m.%d %H:%M"), format="%Y.%m.%d %H:%M", errors='ignore')  # now
    read_end = tz.localize(today - pd.Timedelta(days=2))

    #Making a wrapper to read in the series with
    wrapper = ReadWrapper(start_time=read_start, end_time=read_end, tz=tz, read_from='SMG_PROD')

    
    # Reading timeseries for each catchment and combining all into one list
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
        temp_df = pd.read_csv(r'TEMP\TEMP_{}_{}.csv'.format(sheet,key), index_col=0, parse_dates=True) 
        df['spring_tempQ_N_FB'] = temp_df['q'].astype(float)
        df['spring_tempSNOW_S'] = temp_df['s'].astype(float)
        
        #Adding ref, read from local csv files
        ref_df = pd.read_csv(r'REF\REF_{}_{}.csv'.format(sheet,key), index_col=0, parse_dates=True) 
        df['refQ_N_FB'] = ref_df['q'].astype(float)
        df['refSNOW_S'] = ref_df['s'].astype(float)
        
        #Add final df to list of dataframes
        df_list.append(df)
        
    return df_list

 
    
    

def exclude_keys(df_list,keys,excluded_list):
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


def df_analysis_period(df_list, start_list, end_list, sheet):
    # Finding analysis period
    
    df_analysis_list = []
    start_info_list = []
    end_info_list = []
    
    for df, start_excel, end_excel in zip(df_list, start_list, end_list):

        #FINDING START OF ANALYSIS
        if len(str(start_excel)) >= 5:
            start = pd.to_datetime(start_excel, format="%Y.%m.%d %H:%M", errors='ignore')
            start_info = 'Analysis start ({}): read from excel.'.format(str(start)[:-9])
        else:
            # Start of analysis is for date of maximum SWE
            snow_start = df['refSNOW_S'].idxmax()
            snow_start_info = 'Analysis start ({}): Peak of snow magasine for ref inndatasett.'.format(str(snow_start)[:-15])
            for ref,temp in zip(df['refSNOW_S'],df['spring_tempSNOW_S']):
                if abs(ref-temp) >= 5:
                    diff_start = df[df['refSNOW_S'].gt(ref)].index[0] - pd.Timedelta(days=2)
                    if diff_start <= snow_start:
                        start = diff_start
                        start_info = 'Analysis start ({}): Day befor spring snow adjustment.'.format(str(start)[:-15])
                    else:
                        start = snow_start
                        start_info = snow_start_info
                    break
                else:
                    start = snow_start
                    start_info = snow_start_info

        #FINDING END OF ANALYSIS
        year = datetime.date.today().year
        last_possible_end = dt.datetime(year, 9, 1)
        
        if sheet[0:3] == "LTM":
            df_from_start = df[start:]
            min_snow = 10
            maxQ_part = 0.025
        else:
            df_from_start = df[start:last_possible_end]
            min_snow = df_from_start['refSNOW_S'].max()*0.08
            maxQ_part = 0.05

        if len(str(end_excel)) >= 5:
            end = pd.to_datetime(end_excel, format="%Y.%m.%d %H:%M", errors='ignore')
            end_info = 'Analysis end ({}): read from excel.'.format(str(end)[:-9])
        else:
            # End of analysis is when the SWE has reached a treshold minimum + 7 days for the runoff
            check_snow = (df_from_start['refSNOW_S'] + df_from_start['ltmSNOW_S'])/2
            end = df_from_start[check_snow.gt(min_snow)].index[-1] + dt.timedelta(days=7)
            error = False

            #checking if the end date is set outside the last time of the timeseries
            if end > df.index[-1]:
                # The chosen date is outside the range of the time series
                #end = df.index[-1]
                end = df_from_start['refSNOW_S'].idxmin()
                end_info = 'WARNING, end after last day! Analysis end ({}): this script did not find a sufficient estimation of the end of the spring flod, used here date for the ref snow magasine minimum.'.format(str(end)[:-15])
              
            else:
                #finding the first value where the diff in Q between observed and modelled is less or equal (le) than 10
                df_from_end = df[end:]
                check_q = (abs(df_from_end['ltmQ_OBSE']-df_from_end['refQ_N_FB']) + abs(df_from_end['ltmQ_OBSE']-df_from_end['ltmQ_N_FB']))/2
                min_val = df_from_end['ltmQ_OBSE'].max()*maxQ_part

                if len(df_from_end[check_q.le(min_val)].index) >= 1:
                    end = df_from_end[check_q.le(min_val)].index[0]
                    end_info = 'Analysis end ({}): First day when the inflow models are close to Q_OBSE, one week after the snow magasine goes under 20 GWh SWE.'.format(str(end)[:-15])
                else:
                    end = df_from_start['refSNOW_S'].idxmin()
                    #year = datetime.date.today().year
                    #end = dt.datetime(year, 9, 1)
                    end_info = 'WARNING! Analysis end ({}): this script did not find a sufficient estimation of the end of the spring flod, used here date for the ref snow magasine minimum.'.format(str(end)[:-15])

        df_analysis_list.append(df_from_start[:end])
        start_info_list.append(start_info)
        end_info_list.append(end_info)
        
    return df_analysis_list, start_info_list, end_info_list
        
        

        

def calc_performance(df_analysis_list, models):
    
    # Initializing result dataframes for each model
    acc_perf_df = pd.DataFrame(columns = ['ref', 'spring_temp', 'temp','ltm'])
    R2_perf_df = pd.DataFrame(columns = ['ref', 'spring_temp', 'temp', 'ltm'])
    
    for df, model in zip(df_analysis_list, models):

        # Picking out the columns of the dataframe to shorten code
        obse = df['ltmQ_OBSE']
        ref = df['refQ_N_FB']
        temp = df['tempQ_N_FB']
        spring_temp = df['spring_tempQ_N_FB']
        ltm = df['ltmQ_N_FB']
        
        # calculating performance and adding to 
        acc_perf = acc_performance(obse, [ref, spring_temp, temp, ltm])
        R2_perf = R2_performance(obse, [ref, spring_temp, temp, ltm])
    
        #Add performance results to dataframe
        acc_perf_df.loc[model] = acc_perf
        R2_perf_df.loc[model] = R2_perf

    return acc_perf_df, R2_perf_df



    
def acc_performance(fasit, models):
    performance = []
    for model in models:
        performance.append((model.cumsum()[-1] - fasit.cumsum()[-1])/fasit.cumsum()[-1]*100)
    return performance


    
    
def R2_performance(fasit, models):
    """This function calculates the correlation coefficient between models and a fasit.
    Args:
        Fasit: A timeseries
        Models: modelled timesries

    Returns:
        R2: the correlation coefficient bewteen the two series."""
    # Calculating
    performance = []
    for model in models:
        performance.append(1 - sum(np.power(fasit - model, 2)) / sum(np.power(fasit - np.mean(fasit), 2)))
    return performance




def make_all(df_analysis, all_df, all_keys, start_info_list, end_info_list, sheet, vhhQ_OBSE_list, comments_list, excluded_list, file):
    
    #Calculates here for all catchments, also those who were excluded
    acc_perf_df, R2_perf_df = calc_performance(df_analysis, all_keys)
    
    if type(comments_list) == bool:
        comments_list = ['nan']*len(end_info_list)
    if type(excluded_list) == bool:
        excluded_list = ['nan']*len(end_info_list)
        
    
    #Read from excel the color of each week with snow adjustmets
    Sheet = pd.read_excel(file,'Snow updates') 
    adjusted_weeks = Sheet['Registrated Week:'].values
    adjusted_weeks_colors = Sheet['Color:'].values
    colors_adj = dict(zip(adjusted_weeks, adjusted_weeks_colors))
    print(colors_adj)

    for df, df_long, key, start_info, end_info, vhh, comment, excluded in zip(df_analysis, all_df, all_keys, start_info_list, end_info_list, vhhQ_OBSE_list, comments_list, excluded_list):
        
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

        if key[0:3] == 'Reg':
            plot_prognosis(file, df, key, sheet, colors_adj)

        
        #PRINTOUT
        print('\nAccumulated performance [percentage deviation]: ref: {:.2f}, spring_temp: {:.2f}, temp: {:.2f}, ltm: {:.2f}'.format(acc_perf['ref'][0], acc_perf['spring_temp'][0], acc_perf['temp'][0], acc_perf['ltm'][0]))
        print('Profile correlation performance [R2 value]: ref: {:.2f}, spring_temp: {:.2f}, temp: {:.2f}, ltm: {:.2f}'.format(R2_perf['ref'][0], R2_perf['spring_temp'][0], R2_perf['temp'][0], R2_perf['ltm'][0]))
        
        # ANALYSIS PLOT
        subplot_acc_R2(df, key, sheet, vhh)
        subplot_acc_R2(df_long, key, sheet, vhh, long=True)
        #plot_R2(df, catchment, vhh)
        #plot_accumulate(df, catchment, vhh)

        # LONG PLOT
        #plot_R2(df_long,catchment,vhh,long=True)
        #plot_accumulate(df_long,catchment,vhh,long=True)




def subplot_acc_R2(df, key, sheet, vhh=False, long=False):

    #Change font
    font = {'weight' : 'normal',
        'size'   : 14}

    mpl.rc('font', **font)
    
    fig, (ax1, ax2) = plt.subplots(2,1, figsize=(16,14))
    
    # ACC PLOT
    #Set scale for accumulated plot for regions so that its the same for snow and inflow [GWh]
    y_max = max(df['meanQ_N_FB'].cumsum().max(), df['ltmQ_OBSE'].cumsum().max(), df['ltmQ_N_FB'].cumsum().max(), df['tempQ_N_FB'].cumsum().max(), df['refQ_N_FB'].cumsum().max())*1.03
    color = 'k'
    if sheet[0:3] == 'LTM':
        ax1.set_ylabel('snow magasine SNOW_S [mm]', color=color)
    else:
        ax1.set_ylabel('snow magasine SNOW_S [GWh]', color=color)
        ax1.set_ylim(0, y_max)
    ax1.plot(df['meanSNOW_S'],'-', color='moccasin', linewidth=5.0, label = 'SNOW_S_1980-2010')
    ax1.plot(df['ltmSNOW_S'],'-', color='plum', linewidth=4.0, label = 'ltmSNOW_S')
    ax1.plot(df['tempSNOW_S'],':', color='red', linewidth=3.0, label = 'tempSNOW_S')
    ax1.plot(df['spring_tempSNOW_S'],':', color='deepskyblue', linewidth=2.0, label = 'spring_tempSNOW_S')
    ax1.plot(df['refSNOW_S'],'-.', color='green', linewidth=3.0, label = 'refSNOW_S')
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
    ax1b.plot(df['meanQ_N_FB'].cumsum()*transform,'-', color='moccasin', linewidth=5.0, label = 'Q_N_FB_1980-2010')
    if vhh:
        ax1b.plot(df['vhhQ_OBSE'].cumsum()*transform,'-', color='grey', linewidth=4.0, label = 'vhhQ_OBSE')
    ax1b.plot(df['ltmQ_OBSE'].cumsum()*transform,'-k', linewidth=4.0, label = 'ltmQ_OBSE')
    ax1b.plot(df['ltmQ_N_FB'].cumsum()*transform,'-', color='plum', linewidth=4.0, label='ltmQ_N_FB')
    ax1b.plot(df['tempQ_N_FB'].cumsum()*transform,':', color='red', linewidth=3.0, label = 'tempQ_N_FB')
    ax1b.plot(df['spring_tempQ_N_FB'].cumsum()*transform,':', color='deepskyblue', linewidth=2.0, label = 'spring_tempQ_N_FB')
    ax1b.plot(df['refQ_N_FB'].cumsum()*transform,'-.', color='green', linewidth=3.0, label = 'refQ_N_FB')
    ax1b.tick_params(axis='y', labelcolor=color)
    handles, labels = ax1b.get_legend_handles_labels()
    ax1b.legend(handles[::-1], labels[::-1], loc='center right')
  
    #max_list=[df['meanQ_N_FB'].cumsum()*transform,df['ltmQ_OBSE'].cumsum()*transform]
    #ax1.set_ylim(0, max(max_list)+max(max_list)*0.1)
   
    
    # R2 PLOT
    color = 'k'
    if sheet[0:3] == 'LTM':
        ax2.set_ylabel('inflow [m3/s]', color=color)
    else:
        ax2.set_ylabel('inflow [GWh]', color=color)
    ax2.plot(df['meanQ_N_FB'],'-', color='moccasin', linewidth=5.0, label = 'Q_N_FB_1980-2010')
    if vhh:
        ax2.plot(df['vhhQ_OBSE'],'-', color='grey', linewidth=4.0, label = 'vhhQ_OBSE')
    ax2.plot(df['ltmQ_OBSE'],'-k', linewidth=4.0, label = 'ltmQ_OBSE')
    ax2.plot(df['ltmQ_N_FB'],'-', color='plum', linewidth=4.0, label = 'ltmQ_N_FB')
    ax2.plot(df['tempQ_N_FB'],':', color='red', linewidth=3.0, label = 'tempQ_N_FB')
    ax2.plot(df['spring_tempQ_N_FB'],':', color='deepskyblue', linewidth=2.0, label = 'spring_tempQ_N_FB')
    ax2.plot(df['refQ_N_FB'],'-.', color='green', linewidth=3.0, label = 'refQ_N_FB')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.yaxis.tick_right()
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(handles[::-1], labels[::-1], loc='upper right')
    ax2.yaxis.set_label_position("right")
    
    #General
    plt.gcf().autofmt_xdate()
    fig.tight_layout()
    if long:
        plt.title('{}: Whole Period'.format(key))
    else:
        plt.title('{}: Melting/Analysis Period'.format(key))
          
    plt.show()

  
    
    
def plot_prognosis(file, df, key, sheet, colors_adj):

    
    def sort_adjustments(keys,snowjust):
        
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
            
            
            ax1.plot(df['ltmSNOW_S'], ':', color='plum', linewidth=3.0, label = 'ltmSNOW_S')
            ax1.set_ylabel('snow magazine [GWh]')
            
            ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
            ax2.plot(df['ltmQ_OBSE'].cumsum(),'-k', linewidth=4.0, label = 'ltmQ_OBSE')
            ax2.plot(df['ltmQ_N_FB'].cumsum(),':', color='plum', linewidth=3.0, label='ltmQ_N_FB')
            ax2.set_ylabel('accumulated inflow [GWh]')
            
            plt.title('Prognosis week before and after snow updates (p.50)')

            #Fix dates for x-axis
            plt.gcf().autofmt_xdate()
            
            #Set scale for accumulated plot for regions so that its the same for snow and inflow [GWh]
            y_max = max(df['meanQ_N_FB'].cumsum().max(), df['ltmQ_OBSE'].cumsum().max(), df['ltmQ_N_FB'].cumsum().max(), df['tempQ_N_FB'].cumsum().max(), df['refQ_N_FB'].cumsum().max())*1.03
            ax1.set_ylim(0,y_max)
            ax2.set_ylim(0,y_max)
            
            print('\nModels updated in explicit weeek:')
            for i in range(len(weeks_bf)):
                print("{}: {}".format(weeks_aft[i],snowjust_dict[weeks_aft[i]]))
                
                #ax1 Snow magazine:
                #Plots here the observed using the start and end of the first prognosis
                #Plotting the prognosis accumulated started from the ltmQ_N_FB
                ax1.plot(s_bf[weeks_bf[i]], '-.', color=colors_adj[weeks_aft[i]], linewidth=3.0)
                ax1.plot(s_aft[weeks_aft[i]], color=colors_adj[weeks_aft[i]], linewidth=3.0, label=weeks_aft[i])
                
                #ax2 accumulated inflow:
                #Plots here the observed using the start and end of the first prognosis
                #Plotting the prognosis accumulated started from the ltmQ_N_FB
                ax2.plot(q_bf[weeks_bf[i]].cumsum()+df['ltmQ_N_FB'].cumsum()[q_bf[weeks_bf[i]].dropna().index[0]], '-.', color=colors_adj[weeks_aft[i]], linewidth=3.0)
                ax2.plot(q_aft[weeks_aft[i]].cumsum()+df['ltmQ_N_FB'].cumsum()[q_aft[weeks_aft[i]].dropna().index[0]], color=colors_adj[weeks_aft[i]], linewidth=3.0, label=weeks_aft[i])
                
             
            ax1.yaxis.tick_right()
            handles, labels = ax1.get_legend_handles_labels()
            ax1.legend(handles[::], labels[::], loc='center left')
            ax1.yaxis.set_label_position("left")
                
            ax2.yaxis.tick_right()
            handles, labels = ax2.get_legend_handles_labels()
            ax2.legend(handles[::], labels[::], loc='center right')
            ax2.yaxis.set_label_position("right")
                
                

                
                
    
def plot_perf_models(df, sheet, perfType):
    fig = plt.figure(figsize=(16,8))
    ax = fig.add_subplot(1, 1, 1)
    
    if sheet[0:3] == 'LTM':
        ax.plot(df['ltm'],'-', color='plum', linewidth=3.0, label = 'ltm {:.2f} +/- {:.2f}'.format(df['ltm'].mean(),df['ltm'].std()))
        ax.plot(df['temp'],':', color='red', linewidth=3.0, label = 'temp {:.2f} +/- {:.2f}'.format(df['temp'].mean(),df['temp'].std()))
        ax.plot(df['spring_temp'],':', color='deepskyblue', linewidth=3.0, label = 'spring_temp {:.2f} +/- {:.2f}'.format(df['spring_temp'].mean(),df['spring_temp'].std()))
        ax.plot(df['ref'],'-.', color='green', alpha=0.8, linewidth=3.0, label = 'ref {:.2f} +/- {:.2f}'.format(df['ref'].mean(),df['ref'].std()))
    else:
        if sheet == 'Sver':
            land = 'Sverige'
        else:
            land = 'Norge'
        ax.plot(df['ltm'],'-', color='plum', linewidth=3.0, label = 'ltm {:.2f} +/- {:.2f}'.format(df.drop(land)['ltm'].mean(),df.drop(land)['ltm'].std()))
        ax.plot(df['temp'],':', color='red', linewidth=3.0, label = 'temp {:.2f} +/- {:.2f}'.format(df.drop(land)['temp'].mean(),df.drop(land)['temp'].std()))
        ax.plot(df['spring_temp'],':', color='deepskyblue', linewidth=3.0, label = 'spring_temp {:.2f} +/- {:.2f}'.format(df.drop(land)['spring_temp'].mean(),df.drop(land)['spring_temp'].std()))
        ax.plot(df['ref'],'-.', color='green', alpha=0.8, linewidth=3.0, label = 'ref {:.2f} +/- {:.2f}'.format(df.drop(land)['ref'].mean(),df.drop(land)['ref'].std()))
    
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
    
    
    
    
    
    
def pie_subplot_perf(acc_perf_df, sheet, ref_model, model):
    
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
        
    if model == 'spring_temp':
        plt.suptitle('Snow Adjustments Before 01.04 ({} vs. {})\n'.format(model, ref_model), size=20)
    elif model == 'temp':
        plt.suptitle('Further Snow Adjustments ({} vs. {})\n'.format(model, ref_model), size=20)
    elif model == 'ltm':
        plt.suptitle('Added Temperature Adjustments ({} vs. {})\n'.format(model, ref_model), size=20)


    plt.show()
    


    
def pie_all(acc_perf_df, what, model='ltm'):
    #what = region or catchment
    
    ref_perf = acc_perf_df['ref']
    mod_perf = acc_perf_df[model]

    def pie(ax, values, **kwargs):
        total = sum(values)
        def formatter(pct):
            if pct*total == 0:
                return ''
            else:
                if what == 'region':
                    return '${:0.0f}R'.format(pct*total/100)
                else:
                    return '${:0.0f}M'.format(pct*total/100)
            #return '${:0.0f}M\n({:0.1f}%)'.format(pct*total/100, pct)
        wedges, _, labels = ax.pie(values, autopct=formatter, **kwargs)
        return wedges

    width = 0.35 
    kwargs_inside = dict(colors=['#3CB371','#FF6347', '#FF6347', '#3CB371'], startangle=90)
    kwargs_middle = dict(colors=['#FF9955','#9999FF'], startangle=90)
    kwargs_outside = dict(colors=['#66FF66','#FF9999', '#FF9999', '#66FF66'], startangle=90)
    
    
    fig, (ax1, ax2) = plt.subplots(1,2, figsize=(17,7.5))
    
    if what == 'region':
        lim_list = [10,5]
    else:
        lim_list = [20,10]
    
    for ax,lim in zip([ax1, ax2],lim_list):
        
        #Calculating number of models adjusted up/down and better/worse results to plot
        #Initializing
        no_edit_good = 0
        no_edit_bad = 0
        edit_good = 0
        edit_bad = 0
        ref_no_edit_good = 0
        ref_no_edit_bad = 0
        ref_edit_good = 0
        ref_edit_bad = 0
        #Calculationg
        for ref, mod in zip(ref_perf, mod_perf):
            
            if mod == ref:
                #checking if ltm was less or equal to lim % deviation from Q_OBSE
                if abs(mod) <= lim:
                    no_edit_good += 1
                else:
                    no_edit_bad += 1
                
                #checking if ref was less or equal to lim % deviation from Q_OBSE
                if abs(ref) <= lim:
                    ref_no_edit_good += 1
                else:
                    ref_no_edit_bad += 1
            else:
                #checking if ltm was less or equal to lim % deviation from Q_OBSE
                if abs(mod) <= lim:
                    edit_good += 1
                else:
                    edit_bad += 1
                    
                #checking if ref was less or equal to lim % deviation from Q_OBSE
                if abs(ref) <= lim:
                    ref_edit_good += 1
                else:
                    ref_edit_bad += 1
        
        ax.axis('equal')
        r = 0.9
        outside = pie(ax, [no_edit_good, no_edit_bad, edit_bad, edit_good], radius=r+width, pctdistance=1-width/2.2, **kwargs_outside)
        middle = pie(ax, [no_edit_good+no_edit_bad, edit_bad+edit_good], radius=r, pctdistance=1-width/2, **kwargs_middle)
        inside = pie(ax, [ref_no_edit_good, ref_no_edit_bad, ref_edit_bad, ref_edit_good], radius=r-width, pctdistance=1 - width*1.2, **kwargs_inside)
        plt.setp(inside + middle + outside, width=width, edgecolor='white')
        #ax.legend( inside[::-2] + middle[::-1] + outside[::-2] , ['ref good', 'ref bad', 'adjusted', 'not adjusted', '{} good'.format(model), '{} bad'.format(model)], frameon=False, loc='best')
        #ax.legend(outside[::-1], ['better', 'worse'], frameon=False)

        kwargs = dict(size=13, color='white', va='center', fontweight='bold')
        ax.text(0, 0, 'Out of:\n${}M'.format(no_edit_good+no_edit_bad+edit_bad+edit_good), ha='center', 
                bbox=dict(boxstyle='round', facecolor='blue', edgecolor='none'),
                **kwargs)
        #ax.annotate('Year {}'.format(datetime.date.today().year), (0, 0), xytext=(np.radians(-45), 1.1), 
        #            bbox=dict(boxstyle='round', facecolor='green', edgecolor='none'),
        #            textcoords='polar', ha='left', **kwargs)
        ax.set_title('Good models if <= +/-{}'.format(lim))
    
    fig.legend( inside[::-2] + middle[::-1] + outside[::-2] , ['good ref', 'bad ref', 'adjusted', 'not adjusted', 'good {}'.format(model), 'bad {}'.format(model)], frameon=False, loc='upper right')    
    if model == 'temp':
        plt.suptitle('Snow Adjustments ({} vs. ref)\n'.format(model), size=30)
    elif model == 'ltm':
        plt.suptitle('All Adjustments ({} vs. ref)\n'.format(model), size=30)
    else:
        plt.suptitle('{} vs. ref\n'.format(model), size=30)


    plt.show()
    
    

    
def box_plot(acc_perf_df):

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

    ## Custom x-axis labels
    ax.set_xticklabels(['ref', 'spring_temp', 'temp', 'ltm'])

    ## Remove top axes and right axes ticks
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    
    plt.title('box and whiskers plot of accumulative deviation')
    explintaiotion = 'Make a box and whisker plot for each column of x or each vector in sequence x. The box extends from the lower to upper quartile values of the data, with a line at the median. The whiskers extend from the box to show the range of the data. Flier points are those past the end of the whiskers.'
    # you can set whisker maximum and minimum, so that outliers are "fliers"
    
    
    
    
################# COPY TEMP FROM SMG ###########################

def copy_from_SMG(file):
    
    #Internal function
    def read_excel(sheet, file):

        Sheet = pd.read_excel(file,sheet) 
        keys = Sheet['Område:'].values
        return keys

    
    #Specifying timezone
    tz = pytz.timezone('Etc/GMT-1')
    year = datetime.date.today().year
    read_start = tz.localize(dt.datetime(year-1, 9, 1))
    today = pd.to_datetime(time.strftime("%Y.%m.%d %H:%M"), format="%Y.%m.%d %H:%M", errors='ignore')  # now
    read_end = tz.localize(today - pd.Timedelta(days=2))

    #Making a wrapper to read in the series with
    wrapper = ReadWrapper(start_time=read_start, end_time=read_end, tz=tz, read_from='SMG_PROD')
    
    # Getting time series info from sheets in the excel file
    all_sheets = ['LTM1','LTM2','LTM3','LTM4','LTM5','LTM6','LTM7','LTM8','LTMS','Norg', 'Sver'] 
    for sheet in all_sheets:
        
        ids_list = read_excel(sheet, file)
        
        for model in ['TEMP','REF']:
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
                df.to_csv(r'{}\{}_{}_{}.csv'.format(model,model,sheet,ids))
