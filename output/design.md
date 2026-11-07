# Dashboard design notes

These notes paraphrase the choices for the Campus Customs desk. Later prompts and edits will be added here.

## How the desk should feel

The board is a working desk for a real person, not a demo screen. It uses the Yale colors from the earlier homeworks: Yale blue `#00356b`, the darker blue `#002147`, and intensity blue `#286dc0`, with a serif heading face and a plain sans-serif for the reading text. The page stays light, with wide cards and a calm header, so someone can sit with it open while tickets are running.

## What the board shows

The front end lives in `frontend/` and is React, Vite, and TypeScript. It talks only to the Problem 7 routes at `http://localhost:8000`. Vite serves the page at `http://localhost:5173`, and the backend allows that origin so the browser can call the routes. `npm run dev` opens the desk in the browser.

Across the top are the three tickets. Each card shows who asked, the subject, and whether the ticket is open or resolved. The person picks one card and starts the agent team on that ticket.

While the run is going, the five agents stay on a shared floor. Each one has a speech bubble with a short line about what they are doing or what they just found, and the same lines collect in a conversation column. That is so the desk reads like people talking, not like a raw log. A bubble, a transcript line, and a summary belong to the agent who did that step. The boss calls someone over, and that person's own result stays under their name. A finished tool check stays a short line. The raw record, including database hashes, stays in the audit file.

A finished agent run leaves the ticket open. The ticket is marked resolved only after a person approves a payment or records a pricing decision that does not move cash. When one ticket has both a restock and a price list, it stays open until the person has decided both. The resolved state is stored, so a refresh still shows it. Resolving the ticket means the person has acted. It does not mean the team may move cash on its own.

Under the conversation, each agent gets a short summary of what they did on that ticket. The boss summary is the team's closing decision. The other summaries come from what each agent reported back. The unsent email, the conversation, and those summaries stay with the ticket. Choosing another ticket shows that ticket's own email, conversation, and summaries.

## Cash and approval

Checking sits in the header, large enough to read at a glance, with the shop date beside it. Agents can prepare a payment or a purchase, and the desk shows that request only after they ask. The human types their name and approves it. That approval is the click that changes cash. Once the click is accepted, the button turns grey and stays unavailable. The header then shows the lower balance and a line saying what the old and new amounts were. On a bulk-price ticket, the discount section appears after the team has assessed that ticket. The person then types a per-unit discount in Human approval. The desk refuses a discount greater than the stored current margin, and a discount equal to that margin is still accepted. The card shows a table with the stored current margin, that discount, and the margin after the discount in dollars and percent per unit. The desk adds the resulting quote and order total to the unsent customer email. A restock for the shortfall can still be prepared. If the team finishes a bulk-price ticket without that purchase, the desk adds it from the stored shortfall and unit cost when one vendor has no open invoice. Approving the restock is the click that changes cash. Recording or declining the quote does not. Both stay on the card until each has a decision.

## Characters, motion, and sound

The desk should feel like a paper shop ledger: warm paper, square edges, and Yale blue used as a rule rather than a glow. Human approval sits above the conversation, because the payment decision should be seen before the transcript.

The five workers are Halloween figures from Tiny Creatures by Clint Bellanger, released CC0. They share one pixel-art drawing style. The witch is the boss. Inventory is a zombie, accounting is a vampire, facilities is a Frankenstein monster, and customer service is a ghost. The labels on the desk use the job, not the costume: Boss, Inventory, Accounting, Facilities, and Customer Service. The boss label sits above the witch. The other labels sit below. Each sprite bobs on the same beat, with clear space above the drawing so the top is not cut off. Credits are in `frontend/public/characters/CREDITS.txt`.

The floor behind the team is a dusk Halloween scene: a moon, a few stars, a cobweb, and two small pumpkins. Those decorations stay still, inside the floor, so they do not cover the balance, the tickets, or the approval. Each role name has a small still mark drawn for this desk: a gavel for the boss, a cardboard box for inventory, a calculator for accounting, a wrench for facilities, and a smiley face for customer service. Motion of the figures and the treats can be turned off from the header, and it also stays off when the system asks for less motion. The job names sit directly on the floor, with no beige chip behind them. The boss name is light so it stays readable on the dark sky. The other names stay dark on the lighter ground. When customer service writes a note, that unsent email is its own section under the agent window, with the recipient, subject, and body. It is not drawn on the floor. The quiet curves from the boss to each specialist remain. When two agents actually talk, a new line draws between them, bowed farther out than the standing chart, and a pumpkin and a piece of candy travel that line in both directions. After the exchange the line stays, without the treats.

While a ticket is running, the desk names who is working and how many of the five have reported. A speech bubble shows three bouncing dots while that person is thinking, then the short summary. A ticket that has a payment or a price list waiting is marked Needs you. After the person has decided every item on that ticket, that mark becomes a green Human Review Complete label. The approval button states the prepared amount and the checking balance after that payment. Decline leaves checking unchanged. A ticket with one decision closes on that click. A ticket with a restock and a price list closes on the last of the two. The full conversation stays closed until the person opens the transcript. The floor still shows the latest speech bubble.

Sound is there so the same handoff can be heard as well as seen. Each character has a short original tone. A single tone plays when that agent starts or finishes, and two tones play when one agent calls another. Tool checks stay visual, so the desk does not chirp on every database lookup. Sound can be turned off from the header, because a real desk is sometimes in a shared room.

## Why this is comfortable to use

The three ticket cards share one width, the same width as the human-approval column, and sit in an even row across the top. Notices and errors appear in a box between the blue header and those ticket cards, with dark text on a pale ground. An X on that box dismisses it. The person can see the whole shop at once: which ticket they picked, who is speaking, who is talking to whom, whether the work is finished, and whether the checking account changed. The characters and sounds make the handoffs obvious without making the person read a transcript first. The approval step stays separate from the talking, so it is clear that the team can prepare a bill and only the human can pay it.
