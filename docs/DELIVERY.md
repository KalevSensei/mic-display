# Board delivery watch (Pi Hut order #[order no. removed])

Living record for the scheduled task `mic-board-delivery-watch` (Claude app, twice a day, 10:00 and 16:00 Finland time). The task writes a dated line under "Log" on every run that finds something new, and turns itself off once the board has arrived and been checked.

## Order
- The Pi Hut order #[order no. removed], placed Sat 14 Nov 2026 about 19:30 Finland time (17:30 UTC).
- ESP32-S3 1.75" AMOLED Round Touch Display Dev Board (466x466), option "Standard + Case", × 1.
- Paid £68.28: board £38.28, DHL Express £30.00. Finnish VAT (ALV) £13.88 is included in that total, so VAT is already paid.
- Confirmation and dispatch emails go to the Gmail account [email removed] (sender contact@thepihut.com).
- Order page: the "View your order" link in the confirmation email "Order #[order no. removed] confirmed" (14 Nov 17:30 UTC). Help: support.thepihut.com (Pi Hut support portal).

## Express timeline (from The Pi Hut's delivery page, read 14 Nov)
- Pi Hut ships orders placed before 14:00 UK time, Mon–Fri, the same day. It does not ship at weekends: weekend orders go out on **Mon 16 Nov**.
- DHL Express to the EU takes **1–2 working days** from dispatch, according to Pi Hut's delivery page. The checkout said "2–3 days".
- Expected: dispatch email **Mon 16 Nov**, delivery **Tue 17 Nov to Wed 18 Nov**, **Thu 19 Nov at the latest**.
- Checkpoints the task reacts to:

| When (Finland time) | Expected by then | If not |
|---|---|---|
| Tue 17 Nov 10:00 | Dispatch email with a DHL tracking number (sent Mon 16 Nov) | Reminder to Kalev: ask Pi Hut why order #[order no. removed] has not been dispatched |
| Any run after dispatch | A new DHL scan at least every working day | No scan for one full working day, or status "held", "exception", "address issue" or "returned": reminder to contact DHL with the tracking number, and Pi Hut if DHL can't fix it |
| Customs or duty notice | Possible: see "Duty" below | Reminder to pay only through DHL's own link on the official tracking page, after checking the amount |
| Fri 20 Nov 10:00 | Delivered | Reminder to Kalev: open a delivery-delay ticket with Pi Hut for order #[order no. removed] (the seller bears the parcel until it is delivered) |
| Delivered | Board unboxed and checked the same day | If damaged, missing parts or dead: photos of the box, label and board, then a Pi Hut ticket the same day |

## Duty (corrects the 14 Nov note)
Pi Hut's delivery page now says: "the duty-free exemption for imports under €150 has been eliminated. All shipments now require a mandatory flat-rate customs duty." Since 1 July 2026 the EU charges a flat €3 customs duty per item on parcels under €150. The order total has a VAT line but no duty line. So DHL may ask for about €3 duty, possibly plus a DHL processing fee, before delivery. VAT is already paid. Pay only through a link on dhl.com's own tracking page for this tracking number, never through a link in an SMS. The task reports the exact amount if DHL asks for one.

## Ready-to-paste messages (Kalev sends these himself through support.thepihut.com or DHL's page)
- **Not dispatched (Tue 17 Nov):** "Hi, order #[order no. removed] (DHL Express to Finland) was placed Sat 14 Nov and I have no dispatch email yet. Could you confirm it has shipped and send the DHL tracking number? Thanks, Kalev"
- **Late (Fri 20 Nov):** "Hi, order #[order no. removed] shipped by DHL Express on <dispatch date>, tracking <number>, and has not arrived. The last DHL scan was <status, date>. Could you open a trace with DHL and tell me the next step? Thanks, Kalev"
- **Damaged, missing or dead on arrival:** "Hi, order #[order no. removed] arrived on <date> with <damage / missing item / board not powering on>. Photos of the box, the label and the item are attached. Could you send a replacement? Thanks, Kalev"
- **To DHL (stuck scan or address issue):** use the tracking page's "Contact" or "Change delivery" option with the tracking number, and give the delivery address exactly as on the order.

## Log
- 14 Nov 2026: order confirmed (email 17:30 UTC). Not dispatched yet (weekend). Watch task created.
- 15 Nov 2026 (Sun, run): Gmail checked (account verified). Only the 14 Nov confirmation and two login-code emails from Pi Hut; no dispatch email, no DHL tracking number, no DHL mail. Status: awaiting dispatch Mon 16 Nov. No checkpoint due, nothing sent.
- 15 Nov 2026 (Sun, 18:15 run): Gmail checked (account verified). Still only the 14 Nov confirmation and two login-code emails from Pi Hut; no dispatch email, no DHL tracking number, no DHL mail. Status: awaiting dispatch Mon 16 Nov. No checkpoint due, nothing sent.
- 16 Nov 2026 (Mon, 10:30 run): Gmail checked (account verified). Dispatch email "A shipment from order #[order no. removed] is on the way" received 09:36 Finland time (07:36 UTC): shipped Mon 16 Nov, DHL Express tracking number [tracking no. removed], item ESP32-S3 1.75" AMOLED board Standard + Case × 1. DHL tracking: direct fetch blocked by DHL's bot page; opened in Kalev's Chrome (own tab, closed after): dhl.com/fi-en and MyDHL+ both show no data yet ("tracking attempt was not successful"), normal before the UK pickup scan. No DHL email, no duty request. Checkpoint (a) Dispatched met: email sent to Kalev, subject "Mic board shipped – DHL delivery Tue 17 or Wed 18 Nov". Next: 16:00 run should find the first DHL scan; if still none by Tue 17 Nov 16:00 run, treat as stuck (e).
