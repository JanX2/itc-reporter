#!/usr/bin/python
# -*- coding: utf-8 -*-

# Reporting tool for querying Sales- and Financial Reports from iTunes Connect
#
# This script mimics the official iTunes Connect Reporter by Apple which is used
# to automatically retrieve Sales- and Financial Reports for your App Store sales.
# It is written in pure Python and doesn’t need a Java runtime installation.
# Opposed to Apple’s tool, it can fetch iTunes Connect login credentials from the
# macOS Keychain in order to tighten security a bit. Also, it goes the extra mile
# and unzips the downloaded reports if possible.
#
# Copyright (c) 2016 fedoco <fedoco@users.noreply.github.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import reporter, sys, argparse, calendar, datetime

from datetime import timedelta


# calendar units

# Originally based on
# http://stackoverflow.com/questions/702834/whats-the-common-practice-for-enums-in-python?noredirect=1&lq=1
# Could be improved upon by using Python enums
# http://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python#1695250
class CalendarUnit:
    Day, Week, Month, Year = range(4)

    def __init__(self, Type):
        self.value = Type

    def __str__(self):
        return self.name_string_for(self.value)

    @staticmethod
    def name_string_for(value):
        if value == CalendarUnit.Day:
            return 'Day'
        if value == CalendarUnit.Week:
            return 'Week'
        if value == CalendarUnit.Month:
            return 'Month'
        if value == CalendarUnit.Year:
            return 'Year'

    def adverbial_representation(self):
        return self.adverbial_string_for(self.value)

    @classmethod
    def from_adverbial_representation(string):
        return self(self.for_adverbial_representation(string))

    @staticmethod
    def adverbial_string_for(value):
        if value == CalendarUnit.Day:
            return 'Daily'
        if value == CalendarUnit.Week:
            return 'Weekly'
        if value == CalendarUnit.Month:
            return 'Monthly'
        if value == CalendarUnit.Year:
            return 'Yearly'

    @staticmethod
    def for_adverbial_representation(string):
        if string == 'Daily':
            return CalendarUnit.Day
        elif string == 'Weekly':
            return CalendarUnit.Week
        elif string == 'Monthly':
            return CalendarUnit.Month
        elif string == 'Yearly':
            return CalendarUnit.Year
        else:
            raise ValueError("Error: invalid calendar unit.")

    @staticmethod
    def date_parser_format_for(value):
        if value == CalendarUnit.Day or value == CalendarUnit.Week:
            return '%Y%m%d'
        if value == CalendarUnit.Month:
            return '%Y%m'
        if value == CalendarUnit.Year:
            return '%Y'

    def __eq__(self, y):
       return self.value == y.value


# queries

def itc_get_sales_reports_for_calendar_unit(args, calendar_unit, start_date, end_date):
    if calendar_unit == CalendarUnit.Week:
        start_date = closest_future_sunday(start_date)

    if calendar_unit == CalendarUnit.Week:
        end_date = closest_past_sunday(end_date)

    args.datetype = CalendarUnit.adverbial_string_for(calendar_unit)

    for date_string in date_strings_for_range(start=start_date, end=end_date, step=calendar_unit):
        args.date = date_string
        try:
            reporter.itc_get_sales_report(args)
        except ValueError, e:
            print(e)

def itc_get_sales_reports(args):
    calendar_unit = CalendarUnit.for_adverbial_representation(args.datetype)
    format = CalendarUnit.date_parser_format_for(calendar_unit)

    startdate_string = args.date
    start_date = datetime.datetime.strptime(startdate_string, format)

    # FIXME: “Report is not available yet. Daily reports for the Americas are available by 5 am Pacific Time; Japan, Australia, and New Zealand by 5 am Japan Standard Time; and 5 am Central European Time for all other territories.”
    end_date = datetime.datetime.now()

    itc_get_sales_reports_for_calendar_unit(args, calendar_unit, start_date, end_date)

def itc_get_sales_reports_for_all_calendar_units(args):
    calendar_units = [CalendarUnit.Day, CalendarUnit.Week, CalendarUnit.Month, CalendarUnit.Year]

    startdate_string = args.date

    format = CalendarUnit.date_parser_format_for(CalendarUnit.Day)
    start_date = datetime.datetime.strptime(startdate_string, format)

    end_date = datetime.datetime.now()

    for calendar_unit in calendar_units:
        itc_get_sales_reports_for_calendar_unit(args, calendar_unit, start_date, end_date)


# helpers

# I really don’t like all those magic numbers in the date calculations.
# You never want to do date calculations yourself and should always use a library!

# Originally from
# http://stackoverflow.com/a/25166764/152827
def date_range(start=None, end=None, delta_days=1):
    span = end - start
    for i in xrange(0, span.days + 1, delta_days):
        yield start + timedelta(days=i)

def date_strings_for_range(start=None, end=None, step=CalendarUnit.Day):
    format = CalendarUnit.date_parser_format_for(step)

    if step == CalendarUnit.Day or step == CalendarUnit.Week:
        if step == CalendarUnit.Day:
            delta_days = 1
        elif step == CalendarUnit.Week:
            delta_days = 7

        for date in date_range(start=start, end=end, delta_days=delta_days):
            date_string = date.strftime(format)
            yield date_string
    elif step == CalendarUnit.Month:
        for date in months_range(start=start, end=end):
            date_string = date.strftime(format)
            yield date_string
    elif step == CalendarUnit.Year:
        for date in years_range(start=start, end=end):
            date_string = date.strftime(format)
            yield date_string

# Originally from
# http://stackoverflow.com/a/6558571/152827
def closest_weekday(d, weekday=0, future=True):
    # weekday: 0 = Monday, 1=Tuesday, 2=Wednesday...
    days_ahead = weekday - d.weekday()
    if future and days_ahead < 0: # Target day already happened this week and is not today.
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

def closest_future_sunday(d):
    return closest_weekday(d, weekday=6, future=True)

def closest_past_sunday(d):
    return closest_weekday(d, weekday=6, future=False)

# Originally from
# http://stackoverflow.com/a/5735013/152827
def months_range(start=None, end=None):
    date = start
    while date <= end:
        yield date
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        date += datetime.timedelta(days_in_month)

def years_range(start=None, end=None):
    date = start
    while date <= end:
        yield date
        if (calendar.isleap(date.year)):
            days_in_year = 366
        else:
            days_in_year = 365 
        date += datetime.timedelta(days_in_year)


# additional commands    

def get_subparser(parser, dest):
    if parser._subparsers:
        actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction) and action.dest == dest
        ]
        assert len(actions) == 1
        return actions[0]

def setup_arguments_parser_additional_commands(parser_main):
    subparsers = get_subparser(parser_main, 'command')

    if subparsers is None:
        return

    parser_auth_token = reporter.setup_arguments_parser_auth_token_template()

    parser_cmd = subparsers.add_parser('getSalesReports', help="download sales report summary files for a specific date range", parents=[parser_auth_token])
    parser_cmd.add_argument('vendor', type=int, help="vendor number of the report to download (for a list of your vendor numbers, use the 'getVendors' command)")
    parser_cmd.add_argument('datetype', choices=['Daily', 'Weekly', 'Monthly', 'Yearly'], help="calendar unit covered by the report")
    parser_cmd.add_argument('date', help="specific time covered by the report (weekly reports use YYYYMMDD, where the day used is the Sunday that week ends; monthly reports use YYYYMM; yearly reports use YYYY)")
    parser_cmd.set_defaults(func=itc_get_sales_reports)

    parser_cmd = subparsers.add_parser('getSalesReportsForAllCalendarUnits', help="download sales report summary files for a specific date range", parents=[parser_auth_token])
    parser_cmd.add_argument('vendor', type=int, help="vendor number of the report to download (for a list of your vendor numbers, use the 'getVendors' command)")
    parser_cmd.add_argument('date', help="specific time covered by the report (weekly reports use YYYYMMDD, where the day used is the Sunday that week ends; monthly reports use YYYYMM; yearly reports use YYYY)")
    parser_cmd.set_defaults(func=itc_get_sales_reports_for_all_calendar_units)

def parse_arguments():
    """Build and parse the command line arguments"""
    parser_main = reporter.prepare_arguments_parser()
    
    reporter.setup_arguments_parser(parser_main)
    setup_arguments_parser_additional_commands(parser_main)
    
    args = parser_main.parse_args()

    try:
        reporter.validate_arguments(args)
    except ValueError, e:
        parser_main.error(e)

    return args


# main

if __name__ == '__main__':
    args = parse_arguments()

    try:
        args.func(args)
    except ValueError, e:
        print e
        exit(-1)

    exit(0)
