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


# Read and process the exported CSV
input_file = "Export_for_Logs.csv"
output_file = "output.csv"
rows = []

with open(input_file, 'r', encoding='ISO-8859-1') as infile:
    reader = csv.DictReader(infile)

    for row in reader:
        name = row.get("To: (Name)", "").strip(" '\"")
        email = row.get("To: (Address)", "").strip(" '\"")
        subject = row.get("Subject", "").strip(" '\"")
        body = row.get("Body", "")

        replies = extract_replies_with_senders(body, email)

        for sender, reply_text in replies:
            rows.append({
                "Name": name,
                "Email": email,
                "Subject": subject,
                "Sender": sender,
                "Reply": reply_text
            })

# Write to output.csv
with open(output_file, 'w', newline='', encoding='utf-8') as out:
    fieldnames = ["Name", "Email", "Subject", "Sender", "Reply"]
    writer = csv.DictWriter(out, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print(f"✅ Done! Created {len(rows)} rows in {output_file}")
