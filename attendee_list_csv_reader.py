#  -*- coding: utf-8 -*-
"""
Sample script to return current date/time in required formats.
Copyright (c) 2016-2019 Cisco and/or its affiliates.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import csv

def read_list(emails_list):
	emails = []
	with open(emails_list, 'r') as attendees:
		"""Import Email Addresses from file"""
		for line in attendees:
			currentPlace = line[:-1]
			emails.append(currentPlace)
	return emails

def read_csv(csv_file, column):
	emails = []
	with open(csv_file, 'r') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				line_count += 1
			else:
				emails.append(row[column - 1])
				line_count += 1
	return emails

def compare_csv_2(csv_file, column1, column2):
	value_col1 = []
	value_col2 = []
	with open(csv_file, 'r') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				line_count += 1
			else:
				value_col1.append(row[column1 - 1])
				value_col2.append(row[column2 - 1])
				line_count += 1
	return (value_col1, value_col2)

def compare_csv_3(csv_file, column1, column2, column3):
	value_col1 = []
	value_col2 = []
	value_col3 = []
	with open(csv_file, 'r') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				line_count += 1
			else:
				value_col1.append(row[column1 - 1])
				value_col2.append(row[column2 - 1])
				value_col3.append(row[column3 - 1])
				line_count += 1
	return (value_col1, value_col2, value_col3)

def compare_csv_4(csv_file, column1, column2, column3, column4):
	value_col1 = []
	value_col2 = []
	value_col3 = []
	value_col4 = []
	with open(csv_file, 'r') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				line_count += 1
			else:
				value_col1.append(row[column1 - 1])
				value_col2.append(row[column2 - 1])
				value_col3.append(row[column3 - 1])
				value_col4.append(row[column4 - 1])
				line_count += 1
	return (value_col1, value_col2, value_col3, value_col4)

def compare_csv_3(csv_file, column1, column2, column3):
	value_col1 = []
	value_col2 = []
	value_col3 = []
	with open(csv_file, 'r') as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				line_count += 1
			else:
				value_col1.append(row[column1 - 1])
				value_col2.append(row[column2 - 1])
				value_col3.append(row[column3 - 1])
				line_count += 1
	return (value_col1, value_col2, value_col3)


def main():
	csv_emails = read_csv('attendee_data.csv', 4)
	print(csv_emails)
	txt_emails = read_list('attendee_emails.txt')
	print(txt_emails)
	return()

if __name__ == "__main__":
    main()
