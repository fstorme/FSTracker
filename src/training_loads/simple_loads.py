import pandas as pd
import numpy as np


def redi_df(wl_series, N=28, lambda_const=None, col_workload='sRPE'):
    """
    Function to compute the REDI from aggregated workloads
    :param wl_series: pandas series containing the workloads
    :param N: number of days for equivalent workload
    :param lambda_const: lambda constant for the REDI
    :param col_workload: column to use for the REDI
    :return: REDI time series
    """
    if not lambda_const:
        lambda_const = 2 / (N + 1)

    if lambda_const > 0 and N:
        print("Both N and lambda_const have been given. lambda_const will be used")

    # date index correction
    wl_series = wl_series.sort_values('date', ascending=False)
    idx = pd.date_range(wl_series['date'].min(), wl_series['date'].max())
    wl_series = wl_series.set_index('date')
    wl_series = wl_series.reindex(idx)
    wl_series = wl_series.reset_index().rename(columns={"index": 'date'})
    wl_series = wl_series.sort_values('date', ascending=False)

    # Work Load Matrix
    wl_series['mat_load'] = wl_series.apply(
        lambda row: wl_series.loc[(wl_series['date'] <= row['date']), col_workload].values,
        axis=1
    )

    # Weights
    weights = np.exp(-lambda_const * np.arange(0, wl_series.shape[0]))
    num = wl_series['mat_load'].apply(lambda x: np.nansum(x * weights[:len(x)]))
    denum = wl_series['mat_load'].apply(lambda x: np.sum((1 * (np.isnan(x) == False)) * weights[:len(x)]))
    wl_series['REDI {}'.format(lambda_const)] = num / denum

    r_series = wl_series[['date', 'REDI {}'.format(lambda_const)]]

    return r_series

def filter_and_aggregate_wl(df, sports=['Run', 'Ride'], load_type='sRPE'):
    """
    Function that filters over activity types and compute aggregated work load
    :param df: Raw dataframe extracted form strava
    :param sports: Activity types to be kept
    :param load_type: type of work load to compute
    :return: dataframe with aggregate work loads per day
    """
    acceptable_loads =["sRPE", 'log_sRPE']
    if load_type not in acceptable_loads:
        raise Exception('Invalid load_type')
    df_processed = df[['date', 'distance', 'type', 'time', 'rpe']]
    df_processed = df_processed[df_processed['type'].isin(sports)]
    if load_type == 'sRPE':
        df_processed[load_type] = df_processed['time']*df_processed['rpe']
    if load_type == 'log_sRPE':
        df_processed[load_type] = np.log(df_processed['time'])*df_processed['rpe']

    df_processed['date'] = df_processed['date'].dt.date
    df_agg = df_processed[['date', load_type]].groupby('date')[['sRPE']].sum().reset_index()
    df_agg['date'] = pd.to_datetime(df_agg['date'])
    return df_agg


def rolling_acwr(df, acute_n=7, chronic_n=28, load_type='sRPE'):
    """
    rolling ACWR function
    :param df: workload dataframe
    :param acute_n: number of days for the acute load
    :param chronic_n: number of days for the chronic load
    :param load_type: type of load of interest
    :return: dataframe with the date and the associated ACWR
    """
    tmp_df = df.set_index('date')
    zero_filled_load = tmp_df[load_type].fillna(0).reset_index()
    zero_filled_load = zero_filled_load.sort_values(by='date', ascending=True)
    zero_filled_load['rolling ACWR'] = (zero_filled_load[load_type].rolling(acute_n).mean()/
                                        zero_filled_load[load_type].rolling(chronic_n).mean()
                                        )
    return zero_filled_load[['date', 'rolling ACWR']]


if __name__ == '__main__':
    df = pd.read_excel("../../data/strava.xlsx",
                       index_col=0,
                       parse_dates=["date"]
                       )
    df_wl = filter_and_aggregate_wl(df, sports=['Run', 'Ride'], load_type='sRPE')
    redi_series_007 = redi_df(df_wl, lambda_const=0.07, N=None, col_workload='sRPE')
    redi_series_028 = redi_df(df_wl, lambda_const=0.28, N=None, col_workload='sRPE')
    rolling_acwr_df = rolling_acwr(df_wl, acute_n=7, chronic_n=28, load_type='sRPE')
    df_proc = redi_series_007.merge(redi_series_028, on='date')
    df_proc = df_proc.merge(df_wl, on='date', how='left')
    df_proc = df_proc.merge(rolling_acwr_df, on='date', how='left')
    df_proc.to_excel("../../data/wl_processed.xlsx")
