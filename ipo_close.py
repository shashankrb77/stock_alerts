import os
import pandas as pd
from io import StringIO
from selenium_utils import fetch_single_table
from telegram_utils import send_telegram_message


def filter_ipo_close_within_days(df, cutoff_days):
    today = pd.Timestamp.today()
    in_days = today + pd.Timedelta(days=cutoff_days)
    ipo_date_col = None
    for col in df.columns:
        if 'close' in col.lower():
            ipo_date_col = col
            break
    if ipo_date_col:
        filtered_df = df[df[ipo_date_col].notnull() & (df[ipo_date_col] >= today) & (df[ipo_date_col] <= in_days)]
        return filtered_df
    else:
        return pd.DataFrame()


def format_ipo_message(df):
    if df.empty:
        return '🔔 Upcoming IPO Closures\nNone'
    else:
        companies = '\n'.join(str(company).strip() for company in df['Name'].tolist())
        return f'🔔 Upcoming IPO Closures\n{companies}'


def ipo_close():
    try:
        url = os.getenv("IPO_URL")
        company_table = fetch_single_table(url, wait_time=10, keyword="Name")
        df = pd.read_html(StringIO(str(company_table)))[0]

        # Clean column headers to remove ▲▼ and other non-ASCII chars
        df.columns = [col.encode('ascii', 'ignore').decode('ascii') for col in df.columns]

        # If column header contains 'close', convert that column to datetime
        for col in df.columns:
            if 'close' in col.lower():
                # Parse as dd-mon format, let pandas infer year as 1900
                df[col] = pd.to_datetime(df[col], format='%d-%b', errors='coerce')
                # Set year to current year for all non-null dates
                current_year = pd.Timestamp.today().year
                df[col] = df[col].apply(lambda x: x.replace(year=current_year) if pd.notnull(x) else x)

        # Filter for ipo closures within the next N days
        ipo_alert_cutoff_days = int(os.getenv("IPO_ALERT_CUT_OFF_DAYS"))

        df = filter_ipo_close_within_days(df, ipo_alert_cutoff_days)

        # Filter for required columns only
        required_columns = ['Name']
        df = df[required_columns]

        # Remove last 2 words from 'Name' column -- the word IPO and U or O or CT
        df['Name'] = df['Name'].apply(lambda x: ' '.join(str(x).split(' ')[:-2]) if pd.notnull(x) else x)

        print(df.to_string(index=False))

        # Send the message to Telegram
        message = format_ipo_message(df)
        response = send_telegram_message(message)
        print(response)

    except Exception as e:
        error_message = f"Error occured while fetching anchor lock-in data: {str(e)}"
        send_telegram_message(error_message)
        print(error_message)
