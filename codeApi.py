import csv
import os
import re
import requests

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

rows = []

with open('record127.csv', 'r', encoding='utf-8') as infile:
    reader = csv.reader(infile)
    for row in reader:
        if len(row) >= 5:
            raw_names = row[0].strip(" '\"")
            email = row[1].strip(" '\"")
            body = row[4]

            names = [n.strip() for n in raw_names.split(';')]
            replies = extract_replies_with_senders(body, email)

            for name in names:
                for sender, reply_text in replies:
                    rows.append([name, email, reply_text])

# Simulate pushing to another system
API_URL = "http://localhost:5000/upload"
for row in rows:
    if isinstance(row, list) and len(row) == 3:
        name, email, reply = row
        payload = {
            "name": name,
            "email": email,
            "message": reply
        }
        try:
            response = requests.post(API_URL, json=payload)
            print(f"✅ Sent: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error: {e}")
