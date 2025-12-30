from selenium_utils import fetch_single_table, download_csv_with_year_filter
import os
from telegram_utils import send_telegram_message
import pandas as pd

def filter_lockin_within_days(df, lockin_period, days):
    today = pd.Timestamp.today()
    in_days = today + pd.Timedelta(days=days)
    lockin_col = None
    for col in df.columns:
        if str(lockin_period) in col and 'date' in col.lower():
            lockin_col = col
            break
    if lockin_col:
        filtered_df = df[df[lockin_col].notnull() & (df[lockin_col] >= today - pd.Timedelta(days=1)) & (df[lockin_col] <= in_days)]
        return filtered_df
    else:
        return pd.DataFrame()

def format_lockin_message(df_30, df_90):
    msg_parts = []
    msg_parts.append(f'🔔 Upcoming 30-Day Lock-ins Expiry\n' + (
        '\n'.join(str(company).strip() for company in df_30['Company'].tolist()) if not df_30.empty else 'None'
    ))
    msg_parts.append('\n')
    msg_parts.append(f'🔔 Upcoming 90-Day Lock-ins Expiry\n' + (
        '\n'.join(str(company).strip() for company in df_90['Company'].tolist()) if not df_90.empty else 'None'
    ))
    return '\n'.join(msg_parts)

def anchor_lockin():

    try:
        url = os.getenv("ANCHOR_URL")

        # Get current year and previous year
        current_year = pd.Timestamp.today().year
        prev_year = current_year - 1

        # Download CSV for current year
        print(f"\nDownloading data for {current_year}...")
        csv_file_path_current = download_csv_with_year_filter(url, current_year)
        df_current = pd.read_csv(csv_file_path_current)

        # print(f"\nCSV Content for {current_year}:")
        # print(df_current.to_string())

        # Download CSV for previous year
        print(f"\nDownloading data for {prev_year}...")
        csv_file_path_prev = download_csv_with_year_filter(url, prev_year)
        df_prev = pd.read_csv(csv_file_path_prev)

        # print(f"\nCSV Content for {prev_year}:")
        # print(df_prev.to_string())

        # Combine both DataFrames
        df = pd.concat([df_current, df_prev], ignore_index=True)

        # print(f"\nCombined CSV Content ({current_year} + {prev_year}):")
        # print(df.to_string())

        # Clean column headers to remove ▲▼ and other non-ASCII chars
        df.columns = [col.encode('ascii', 'ignore').decode('ascii') for col in df.columns]

        # If column header contains 'date', convert that column to datetime
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Filter for 30-day and 90-day lock-ins within the next N days
        anchor_alert_cutoff_days = int(os.getenv("ANCHOR_ALERT_CUT_OFF_DAYS"))
        df_30 = filter_lockin_within_days(df, 30, anchor_alert_cutoff_days)
        df_90 = filter_lockin_within_days(df, 90, anchor_alert_cutoff_days)

        # Filter for required columns only
        required_columns = ['Company']
        df_30 = df_30[required_columns]
        df_90 = df_90[required_columns]

        print(df_30.to_string(index=False))
        print(df_90.to_string(index=False))

        # Send both DataFrames as one aesthetic message to Telegram
        message = format_lockin_message(df_30, df_90)
        response = send_telegram_message(message)
        print(response)
    except Exception as e:
        error_message = f"Error occured while fetching anchor lock-in data: {str(e)}"
        send_telegram_message(error_message)
        print(error_message)
