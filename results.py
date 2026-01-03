import os
import pandas as pd
from telegram_utils import send_telegram_message
from selenium_utils import download_csv_with_year_filter

def filter_results_within_days(df, cutoff_days):
    today = pd.Timestamp.today().normalize()
    in_days = today + pd.Timedelta(days=cutoff_days)
    result_date_col = None
    for col in df.columns:
        if 'result' in col.lower() and 'date' in col.lower():
            result_date_col = col
            break
    if result_date_col:
        filtered_df = df[df[result_date_col].notnull() & (df[result_date_col] >= today) & (df[result_date_col] <= in_days)]
        return filtered_df
    else:
        return pd.DataFrame()

def format_results_message(df):
    if df.empty:
        return '🔔 Upcoming Results\nNone'
    else:
        companies = '\n'.join(str(company).strip() for company in df['Company Name'].tolist())
        return f'🔔 Upcoming Results\n{companies}'

def results():
    try:
        base_url = os.getenv("RESULTS_URL")

        # Get current year and previous year
        current_year = pd.Timestamp.today().year

        # Download CSV for current year
        print(f"\nDownloading data for {current_year}...")
        csv_file_path_current = download_csv_with_year_filter(base_url, current_year)
        df_current = pd.read_csv(csv_file_path_current)

        print(f"\nCSV Content for {current_year}:")
        print(df_current.to_string())

        # Clean column headers to remove ▲▼ and other non-ASCII chars
        df_current.columns = [col.encode('ascii', 'ignore').decode('ascii') for col in df_current.columns]

        # If column header contains 'date', convert that column to datetime
        for col in df_current.columns:
            if 'result' in col.lower() and 'date' in col.lower():
                df_current[col] = pd.to_datetime(df_current[col], format='%b %d, %Y', errors='coerce')

        # Filter for results within the next N days
        results_alert_cutoff_days = int(os.getenv("RESULT_ALERT_CUT_OFF_DAYS"))
        df = filter_results_within_days(df_current, results_alert_cutoff_days)
        required_columns = ['Company Name']
        df = df[required_columns]
        print(df.to_string(index=False))
        message = format_results_message(df)
        response = send_telegram_message(message)
        print(response)

    except Exception as e:
        error_message = f"Error occured while fetching results data: {str(e)}"
        send_telegram_message(error_message)
        print(error_message)
