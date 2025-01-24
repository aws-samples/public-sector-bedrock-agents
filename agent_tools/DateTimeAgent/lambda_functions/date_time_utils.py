# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from datetime import date, datetime, timedelta, timezone

from typing import Tuple

import ssl
import socket

class DateTimeUtils:
    
    def get_date_time(self) -> dict:
        """
        Returns a dictionary containing the current date, time, day of the week, and timezone.

        Returns:
            dict: A dictionary with the following keys:
                - 'date' (str): The current date in 'mm/dd/YYYY' format.
                - 'time' (str): The current time in 'HH:MM:SS' 24-hour format.
                - 'day' (Optional[str]): The current day of the week, or None if an error occurs.
                - 'timezone' (str): The current timezone.
        """
        utc_now = datetime.now(tz=timezone.utc)
        local_now = utc_now.astimezone()
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        try:
            current_day = days[utc_now.weekday()]
        except IndexError:
            current_day = None

        return {
            'date': utc_now.strftime("%m/%d/%Y"),
            'time': utc_now.strftime("%H:%M:%S"),
            'day': current_day,
            'timezone': local_now.tzname()
        }

    def calculate_age(self, birth_date: date) -> int:
        """
        Calculates the age based on the given birth date.

        Args:
            birth_date (date): The birth date of the person.

        Returns:
            int: The calculated age in years.
        """
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age

    def date_diff(self, start_date: datetime, end_date: datetime) -> int:
        """
        Calculates the difference between two dates in days.

        Args:
            start_date (datetime): The start date.
            end_date (datetime): The end date.

        Returns:
            int: The number of days between the start and end dates.
        """
        diff = end_date - start_date
        return diff.days

class BusinessDateTimeUtils:
    def is_business_day(self, date_obj: date) -> bool:
        """
        Checks if the given date is a business day (Monday to Friday).

        Args:
            date_obj (date): The date to check.

        Returns:
            bool: True if the date is a business day, False otherwise.
        """
        weekday = date_obj.weekday()
        return weekday >= 0 and weekday <= 4

    def calculate_business_days(self, start_date: datetime, end_date: datetime) -> int:
        """
        Calculates the number of business days between two dates.

        Args:
            start_date (datetime): The start date.
            end_date (datetime): The end date.

        Returns:
            int: The number of business days between the start and end dates.
        """
        business_days = 0
        current_date = start_date
        while current_date < end_date:
            if self.is_business_day(current_date.date()):
                business_days += 1
            current_date += timedelta(days=1)
        return business_days

    def get_fiscal_year(self, date_obj: date, fiscal_year_start_month: int = 10) -> int:
        """
        Calculates the fiscal year for a given date based on a specified fiscal year start month.

        Args:
            date_obj (date): The date for which to calculate the fiscal year.
            fiscal_year_start_month (int, optional): The month in which the fiscal year starts (default is 10 for October).

        Returns:
            int: The fiscal year corresponding to the given date.
        """
        year = date_obj.year
        if date_obj.month < fiscal_year_start_month:
            year -= 1
        return year

    def get_fiscal_year_range(self, date_obj: date, fiscal_year_start_month: int = 10) -> Tuple[date, date]:
        """
        Calculates the start and end dates of the fiscal year for a given date based on a specified fiscal year start month.

        Args:
            date_obj (date): The date for which to calculate the fiscal year range.
            fiscal_year_start_month (int, optional): The month in which the fiscal year starts (default is 10 for October).

        Returns:
            tuple: A tuple containing the start and end dates of the fiscal year.
        """
        fiscal_year = self.get_fiscal_year(date_obj, fiscal_year_start_month)
        start_date = date(fiscal_year, fiscal_year_start_month, 1)
        end_date = date(fiscal_year + 1, fiscal_year_start_month, 1) - timedelta(days=1)
        return start_date, end_date

    # def is_holiday(self, date_obj: date) -> bool:
    #     """
    #     Checks if the given date is a holiday.

    #     Args:
    #         date_obj (date): The date to check.

    #     Returns:
    #         bool: True if the date is a holiday, False otherwise.
    #     """
    #     # Define a list of holidays
    #     holidays = [
    #         (1, 1),   # New Year's Day
    #         (7, 4),   # Independence Day
    #         (12, 25)  # Christmas Day
    #     ]
    #     month, day = date_obj.month, date_obj.day
    #     return (month, day) in holidays

    def get_next_business_day(self, date_obj: date) -> date:
        """
        Calculates the next business day after the given date.

        Args:
            date_obj (date): The date for which to find the next business day.

        Returns:
            date: The next business day after the given date.
        """
        next_day = date_obj + timedelta(days=1)
        while next_day.weekday() > 4 or self.is_holiday(next_day):
            next_day += timedelta(days=1)
        return next_day

class SSLCertificateUtils:
    def get_ssl_cert_expiry(self, hostname, port=443):
        """
        Retrieves the expiration date of the SSL/TLS certificate for a given hostname.

        Args:
            hostname (str): The hostname for which to retrieve the SSL/TLS certificate expiration date.
            port (int, optional): The port number for the SSL/TLS connection (default is 443 for HTTPS).

        Returns:
            str: The expiration date of the SSL/TLS certificate in 'YYYY-MM-DD HH:MM:SS' format.

        Raises:
            ValueError: If an error occurs while retrieving the SSL/TLS certificate expiration date.
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=20) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as conn:
                    ssl_info = conn.getpeercert()
                    expiry_date = ssl_info['notAfter']
                    expiry_datetime = datetime.strptime(expiry_date, "%b %d %H:%M:%S %Y %Z")
                    return expiry_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            raise ValueError(f"Error retrieving SSL/TLS certificate expiration date: {e}")