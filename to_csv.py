import csv
import os


def csv_new(filename):
    FIELDS = [
        ['reference', 'application_validated', 'address', 'proposal', 'status', 'applicant_name', 'applicant_address',
         'agent_name', 'agent_company_name', 'agent_address', 'agent_phone_number', 'agent_email']
    ]

    with open(filename, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for line in FIELDS:
            writer.writerow(line)


def csv_writer(data, filename):
    if not os.path.isfile(filename) or os.stat(filename).st_size == 0:
        csv_new(filename)

    with open(filename, 'a') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        for line in data:
            writer.writerow(line)
