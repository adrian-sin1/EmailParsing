import csv
import os
import re

def extract_replies_with_senders(body, csv_email):
    pattern = re.compile(
        r'(?=^From:|^On .+? wrote:|^-----Original Message-----)', 
        re.IGNORECASE | re.MULTILINE
    )
    chunks = pattern.split(body.strip())
    results = []
    last_sender = csv_email

    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk or len(chunk.splitlines()) < 2:
            continue

        sender = None

        # First chunk is from CSV sender
        if i == 0:
            sender = csv_email
        else:
            match_from = re.search(r'^From:\s*(.*)', chunk, re.IGNORECASE | re.MULTILINE)
            if match_from:
                sender = match_from.group(1).strip()
            else:
                match_wrote = re.search(r'On .+? (.+?) <(.+?)> wrote:', chunk, re.IGNORECASE)
                if match_wrote:
                    name = match_wrote.group(1).strip()
                    email_addr = match_wrote.group(2).strip()
                    sender = f"{name} <{email_addr}>"

        if not sender:
            sender = last_sender
        else:
            last_sender = sender

        results.append((sender, chunk))

    return results


rows = []

# 🔽 NEW: Input file name
input_file = 'Export_for_Logs.CSV'

# 🔽 NEW: Output file name
output_file = 'output.csv'

with open(input_file, 'r', encoding='ISO-8859-1') as infile:
    reader = csv.reader(infile)
    # next(reader)  # Uncomment if your CSV has a header

    for row in reader:
        if len(row) >= 5:
            raw_names = row[0].strip(" '\"")
            email = row[1].strip(" '\"")
            body = row[4]

            names = [n.strip() for n in raw_names.split(';')]
            replies = extract_replies_with_senders(body, email)

            for name in names:
                for sender, reply_text in replies:
                    rows.append([name, email, sender, reply_text])

# ✅ Write clean output with no separators
with open(output_file, 'w', newline='', encoding='utf-8') as out:
    writer = csv.writer(out, quoting=csv.QUOTE_ALL, doublequote=True, lineterminator=os.linesep)
    writer.writerow(['Name', 'Email', 'Sender', 'Reply'])

    for row in rows:
        writer.writerow(row)

print(f"✅ Done! Created {len(rows)} rows in {output_file}")
