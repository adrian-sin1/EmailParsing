import csv



with open('Export_for_Logs.CSV', 'r', encoding='ISO-8859-1') as infile:

    reader = csv.reader(infile)



    # Skip the header row if your file has one

    next(reader)



    rows = []



    for row in reader:

        if len(row) >= 2:

            name = row[0].strip(" '\"")   # First cell

            email = row[1].strip(" '\"")  # Second cell

            rows.append([name, email])



# Write the result to a new CSV file

with open('output.csv', 'w', newline='', encoding='utf-8') as outfile:

    writer = csv.writer(outfile)

    writer.writerow(['Name', 'Email'])  # Optional header

    writer.writerows(rows)



print("✅ Done! Check 'output.csv'")
