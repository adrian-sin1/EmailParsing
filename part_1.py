import csv
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


def main():
    input_file = "Export_for_Logs-New.csv"
    output_file = "output.csv"
    rows = []

    with open(input_file, 'r', encoding='ISO-8859-1') as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            name = row.get("To: (Name)", "").strip(" '\"")
            email = row.get("To: (Address)", "").strip(" '\"")
            subject = row.get("Subject", "").strip(" '\"")
            body = row.get("Body", "")

            # Handle Exchange internal address — look for any external email in the body
            if email.lower().startswith("/o=nycc/ou=exchange"):
                match_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', body)
                if match_emails:
                    email = match_emails[0]
                else:
                    email = "/o=NYCC/ou=Exchange Administrative"

            replies = extract_replies_with_senders(body, email)

            for sender, reply_text in replies:
                rows.append({
                    "Name": name,
                    "Email": email,
                    "Subject": subject,
                    "Sender": sender,
                    "Reply": reply_text
                })

    with open(output_file, 'w', newline='', encoding='utf-8') as out:
        fieldnames = ["Name", "Email", "Subject", "Sender", "Reply"]
        writer = csv.DictWriter(out, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"✅ Done! Created {len(rows)} rows in {output_file}")


if __name__ == "__main__":
    main()
