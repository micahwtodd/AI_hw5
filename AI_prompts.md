# AI Prompts

Prompts are logged verbatim, in the order they are entered in this chat. Each problem starts with a header for the problem number and title. Individual prompts are tagged Prompt 1a, Prompt 1b, and so on. Prompt subsections are indented under their problem.

## Problem 1: Vibe coder prompts

  ### Prompt 1a

  Please help me work on my 5th AI class homework assignment. Similar to prior homeworks, please start by creating a AI_prompts.md file and update it while i work, pasting in my verbatim prompts. This file is the documentation log of what i typed in my vibe coder. Please put one section for each problem (1, 2, 3), and a subsection for each prompt (a, b, c). Each section will include the Problem number and title, then list the prompts i typed. please see prior homeworks for an example. This is the first prompt and should be logged under Problem 1: vibe coder prompts

  ### Prompt 1b

  Atta boy. Here is some context for the project. Do not do anything yet, just save this context. We will create a Campus Customs Multi Agent Operation, an agentic team that runs our campus customs shop. It will receive open tickets and must handle them. I'll build three pieces that talk to each other: an MCP server, a FAST backend API with multi agent team, and a REACT dashboard so i can watch the agents work and approve requests. some Rules: 
  1) the agent team has full connectivity, which means they can all delegate tasks to each other.
  2) keep my API key hidden at all times. When using portkey for AI calls, only use gpt-6-luna for all agents. i will lose points if i use any other model!
  3) the field desk.date_today is "today" for the shops perspective, so the shop can determine what is overdue. 
  4) vendor lead times come from the vendors table
  5) a human's approval is required for all payments. i will lose points if agents can approve payments - they cannot! humans only!
  6) the pay tool must refuse if there is not enough cash. no negative balances are allowed.
  7) cash only goes out in this homework because we are not modeling revenue or money coming in
  8) before doing a full run to resolve the tickets, we should reset the database to its original values. 
  9) do not email customers or call real vendors. drafts stay on the board
  10) do not make up values or hallucinate things
  11) if you are ever unsure of something, just ask me.

  Later in this homework we will create five agents:
  1) boss, who reads tickets, assigns it to workers, and makes final decisions
  2) inventory, who checks stock by SKU and size, identifies shortfalls, and determines which vendors can restock
  3) accounting, who observes cash and invoices, checks margins, and prpares payments or purcahse orders for human approval
  4) facilities, who handles leases, rent, and anything else related to the shop space
  5) customer service, who drafts responses to customers.

  my final submission will be a public GitHub path, similar to homework 4. 

  Please confrim you understand, then we will move onto problem 2

## Problem 2: Study the campus customs database

  ### Prompt 2a

  We are now moving onto Problem 2: Study the campus customs database. Please open the database file in the data/ folder so i can review every table and its fields. In this chat window, please list every table, all fields by columns, and the first five rows for each table so i can review them and learn more about the dataset. then, make a copy of the database in the same directory called data/campus_customs_new.db

  ### Prompt 2b

  thanks. while i review, please remove unused sections from the @AI_prompts.md  file. then, create output/harness.md that lists each table and the fields within them, leaving space for a short line where i can manually type in why that table matters for the agents. we will expand the harness file as we progress through the homework

  ### Prompt 2c

  Thanks. please review the summaries i added. You may add up to one clariying sentence in your own words after mine, but please preserve mine verbatim

## Problem 3: Build the MCP server

  ### Prompt 3a

  Thanks. we are now moving onto Problem 3: Build the MCP server. plese write an MCP server in mcp_server/ using FastMCP. it should talk to data/campus_customs_new.db but we do not need to connect or run it in this problem. Every agent in this homework will use the tools in the MCP server. I will add more tools to it later, but for now we need to write three tools i know i will need for the tickets in the database. the names should be clear, you should never invent any data, and use only the information in the database. in output/harness.md, list each of the three MCP tools and include which table it reads, which ticket it helps unlock (101, 102, or 103 in the tickets database), and one sentence or two on why that tool is the right one for the ticket. We shouldn't be vague, we must be specific. Then, please create a short mcp_server/README.md file that explains what the MCP server is for, which databse file it uses, and the three tools it has. Before we continue, here are the three tools i think we should make, can you please review and recommend changes? Dont want to miss anything here:
  1) write_customer_email, which drafts emails for customers
  2) draft_billpay_for_human, which identifies outstanding bills for human review
  3) check_inventory_status, which checks sizes and quantities available in inventory

  ### Prompt 3b

  Thanks, let's try this from your feedback:
  Keep check_inventory_status—read tickets and inventory; return exact stock and shortfall for tickets 101 and 103. Rename draft_billpay_for_human to draft_payment_for_human_review—read tickets, invoices, leases, cash_accounts, and desk; return a proposal and projected balance, but never approve or execute payment. Replace write_customer_email with check_pricing_and_margin—read tickets and pricing; provide the facts needed for ticket 103.

  ### Prompt 3c

  also, if you were designing this from the ground up, what three tools would you include?

  ### Prompt 3d

  please use mine and save these for later, we'll add more tools in later problems. but you should remember these for future use

## Problem 4: Add the MCP server to the vibe coder and test each tool

  ### Prompt 4a

  thanks, we are now moving onto Problem 4: Add the MCP server to the vibe coder and test each tool. I am someone uncertain on this one so please explain what you will do before you do it, and ill approve next steps. You should add an MCP server to this project so the vibe coder can call the tools. Pleas save the connection JSON text in .mcp.json at the project root, or however you typically save local MCP server lists. we will then test each of the three MCP tools - i will provide prompts below. Please save the evidence in output/mcp_smoke.json. for each tool we test, you should include (1) the prompt i ask the vibe coder, (2) the tool name, and (3) the tool output, which must match the values in data/campus_customs_new.db. 

  You should use these prompts for the tools, and please also repeat their output here:
  (1) check_inventory_status - how many CC-TEE-WHITE shirts in size S do we have in stock?
  (2) check_pricing_and_margin - what are the costs, retail price, and margins for CC-HOOD-NAVY size M
  (3) draft_payment_for_human_review - when is my next rent payment due, and how much is it?

  ### Prompt 4b

  thanks. the tools should be structured so they can flexibly handle prompts and inputs, your comment in #1 makes them seem fragile. What would you recommend changing to make them more robust, if anything?

  ### Prompt 4c

  approve, thanks

  ### Prompt 4d

  please move mcp.json up to the root directory and delete the .cursor folder. these results look great! but please double check and validate your work. also, i am not clear why we need cursor smoke testing and have to restart cursor?

  ### Prompt 4e

  might be a little late for this, but are there any relevant cursor extensions that i should install for this project?

## Problem 5: Build the agent team and grow the MCP tools

  ### Prompt 5a

  thanks, added python but will save the rest for later. we are now moving onto Problem 5: build the agent team and grow the MCP tools. we will build the agentic team for campus customs using PyDantic AI: Boss, Inventory, Accounting, Faciltiies, and Customer Services. We will include prompts, models, and agent loops so they can delegate work to each other with full connectivity. please put the agent prompts in backend/prompts/ with one file per agent. i will provide prompts. data types should go in backend/models.py, and teh agent files under backend/. please use my portkey API key for agent model calls and only use gpt-6-luna for all agent like we discussed. based on my prompts, please also add any additional tools the agents need to MCP server so they can work on the open tickets. Shop facts some from the MCP server over data/campus_customs_new.db. Please do not invent a second shop-tools layer that bypasses the MCP, and do not make up facts. 

  Please write the agents so they append to output/audit_trail.json as they run. for each agent-loop step. record enough fields to audit later. Please recommend audit fields or advise if you are unsure. You sould append the audit file, do not wipe it with each run. 

  In output/harness.md, please list each agent and add any new MCP tools we created in this section and update changes to existing tools along with the table the tool uses. Please also add a short safety section that i will provide details on shortly. it should contain guardrails a real business would place on agents if the agents interacted with real customers and real money, plus limits that keep token usage costs in check. 

  Please also update mcp_server/README.md so the tool lists matches these updates. Please confirm you understand, and i'll give youprompts for the five agents before you proceed building code

  ### Prompt 5b

  thanks, audit list and strcuture looks good. please also keep my API key secret and safe. 

  Here are the prompts. Please save them verbatim, then provide feedback on anything missing or that could be improved.

  Boss: you are the Campus Customs Boss. You are decisive, fair, and equitable. You read each ticket, decide who should work on it, and make final calls. If there are conflicting opinions or information, you will ask the user for help and clarification. You should optimally and efficiently delegate tasks in a way that minimizes token spend, but maximizes speed. You are responsible for everyone else’s actions and should review their work for accuracy and ensure they are following the shop rules. Before a full run to resolve tickets, you should ensure the database was reset to its original values. You should not make up information or invent facts. You may delegate tasks that are outside your scope to other agents. You must follow the shop rules.
  Inventory: you are the Campus Customs Inventory Manager. You are detailed and well-organized. You check stock by SKU and size, identify inventory shortfalls, and determine which vendors can restock. You should prioritize vendors who can restock more quickly, and balance fast deliveries with costs. Inventory cannot be negative, and you should not allow orders for more than the quantity in stock. A vendor will not ship new product while they have open unpaid invoices; the invoices must be paid first. You should also not overstock. You should not make up information or invent facts. You may delegate tasks that are outside your scope to other agents. You must follow the shop rules.
  Accounting: you are the Campus Customs Accountant. You are precise and meticulous, and conservatively monitor our financials. You manage and monitor cash and invoices, check profit margins, and prepare payments or purchase orders for human approval. A human must approve your recommendations, and you cannot take action yourself – only a human can. The bank account balancess should not fall negative – if they do, you should warn the other agents and refuse payment. Remember, all payments require human approval! There are no revenues, only cash outflows. Money does not come in. You should not make up information or invent facts. You may delegate tasks that are outside your scope to other agents. You must follow the shop rules.
  Facilities: you are the Campus Customs Facilities Manager. You are reliable and diligent and take accountability for ensuring a well-run facility. You manage the shop space and handle leases and rent. You should not make up information or invent facts. You may delegate tasks that are outside your scope to other agents. You must follow the shop rules.
  Customer Service: you are the Campus Customs Customer Service Representative. You are friendly and collaborative, and speak with a warm tone. You draft messages to customers. Do not email customers or call real vendors. Drafts must stay on the board. You should not make up information or invent facts. You may delegate tasks that are outside your scope to other agents. You must follow the shop rules.

  Shop rules: please summarize the shop rules from my earlier prompt. All agents must follow these rules. 

  ### Prompt 5c

  Thanks. Let's make some enhancements. First, in each agent prompt file, put a header section called "Micah's verbatim agent prompt" and keep my verbatim text under it. Then, in a second section, add the shop rules under a new section called "Micah's shop rules from homework assignment", then, delete the shop_rules file.

  ### Prompt 5d

  Thanks. This is great feedback but I want to protect my original wording as the homework requires,  and add some of the safeguards you suggested. in the prompt files, can you please add a seperate "Additional enhancements recommended by AI" section, that incorporates your feedback in an actionable way for the relevant agents?

  ### Prompt 5e

  thanks. Please double check these prompts again and review for safety, reasonableness, and accuracy

  ### Prompt 5f

  Thanks. go ahead and build the agentic team

  ### Prompt 5g

  the backend contains many files, see this screencap. any opportunity to consolidate some of them without adverse consequences?

## Problem 6: Plan the three tickets

  ### Prompt 6a

  ok that's fine, we'll keep as is. We are now moving onto Problem 6: Plan the three tickets. before we wire the backend, i need to write down what i expect the team will do for each ticket. Please build output/desk_tickets.html, a webpage i can double click with one tab per ticket (101, 102, 103). Please also add empty Cash and Reflection tabs for later problems, but leave them blank for now and add a "Coming later" note. On each ticket tab, create an Expected section and an Actual section. Do not fill them out for me, i will give you language that you can copy in verbatim for the Expected section, and you'll fill in actual later once we run the agent team. please use html formatting consistent with prior homeworks - use the nice layout, Yale colors, etc. please let me know if you have any questions.

  ### Prompt 6b

  Thanks. can you please pull up the ticket table from earlier? Row for each ticket, and each field as a column?

  ### Prompt 6c

  for ticket 101, can you please remind me how many CC-TEE-WHITE size S are in stock?

  ### Prompt 6d

  can you please briefly list all the MCP tools we created, with a sentence or two about what they do?

  ### Prompt 6e

  please remind me, how many CC-HOOD-NAVY size M are in stock, the hoody referenced in ticket 103?

  ### Prompt 6f

  Thanks. here are my expected descriptions for the html file: 

  Ticket 101 expected agent actions: This ticket requests a t-shirt that is unfortunately not in stock. First, I expect the Boss agent will use list_open_tickets to view the ticket queue then delegate the ticket to the Inventory agent, which will use check_inventory_status to determine the requested size is out of stock. The Inventory agent will need to restock. It will use list_invoices and check_vendor_status to ensure there are no payables due. Then it will call the Accounting agent to check the restock invoices and setup a payment for human approval using get_cash_status and draft_payment_for_human_review. The Inventory agent will simultaneously call the Customer Service Agent and tell them to draft a customer email noting the shirt they requested in on backorder, and will provide an estimated restock  date based on inventory lead times. Finally, the Customer Service Agent’s draft email and Accounting agent’s draft payment will go back to the Boss for review, and the Boss will check their work before sending for final human approval. The Facilities Agent should not be called at all for this ticket. 
  Ticket 102 expected agent actions: this ticket says rent is due in two days. I expect the Boss Agent will use list_open_tickets to assign and delegate the ticket to the Facilities agent, who will use get_lease_status to evaluate the lease due date. The Facilities agent will determine rent is due and ask the Accounting agent to draft a payment, using draft_payment_for_human_review for the lease shop. The Accounting agent will also use get_cash_status to evaluate the checking account value and ensure the shop has enough money for payment. Then, the Accounting agent will send their final summary back to the Boss for review before a human does a final review and approval. The Customer Service and Inventory agents should not be called.
  Ticket 103 expected agent actions: this ticket shows a student request for a bulk discount on 20 hoodies, however there are only 8 in stock. I expect the Boss Agent will use list_open_tickets to assign this to the Inventory agent first, who will use check_inventory_status to identify the shortfall, then call check_vendor_status to order more, and call the Accounting agent to draft the payment via draft_payment_for_human_review. The Accounting agent will also use get_cash_status to ensure there is enough money in the bank account for the restock order and report back to the Inventory agent. The Accounting agent will also use check_pricing_and_margin to assess profitability and a range of bulk discount options. Then, both the Inventory and Accounting Agents will communicate with the Customer Service agent who will draft an email to the customer noting the backorder timing restrictions and range of bulk discounts offered for the 20-hoodie order. Then, the Boss will review the Accounting payment and Customer Service email before sending for human approval. The Facilities agent should not be called for this ticket.

  ### Prompt 6g

  thanks i will make some slight manual tweaks here. Also i notice cursor keeps changing my chosen AI model, why is that?

  ### Prompt 6h

  how cna i view my current usage and token spend?

  ### Prompt 6i

  what is the token usage difference between Grok 4.6 and 4.7?

## Problem 7: Backend routes

  ### Prompt 7a

  ok i'm good, not sure what happened there. We are now moving onto Problem 7: Backend routes. Problem 8 will ask for  React front-end dashboard, and this problem sets up the backend for it. in backend/main.py, please use Fast API and add routes to do the following: 
  1) return the three tickets and whether each is open or resolved
  2) take a ticket id and run my agent team on that particular ticket
  3) return recent agent events (like what each agent said and what tools they used) so the board can refresh
  4) approve a payment or purchase after a human clicks approve. Remember, agents only prepare the pay, this route is what actually changes cash.
  5) Return the current checking balance from cash_accounts
  6) reset the databse to its original values when i want to try a fresh run. 

  from the backend/ folder, the server should start with uvicorn main:app --reload --port 8000

  This turns on the backend at http://localhost:8000 so the frontend dashboard can call the routes. 

  Finally, in output/harness.md, create a new section at the end that lists each route in one line - what URL, and what it does. 

  Please let me know if anything is unclear here and i will advise

  ### Prompt 7b

  Ticket 103 should be able to get the vendor cost from the database, right?

  ### Prompt 7c

  doesn't bulldog handle the apparel reprints?

  ### Prompt 7d

  what do you mean "the approve route should not create one", can you provide a simple numerical exmaple?

  ### Prompt 7e

  yes that is correct, unless a human approves the restock order. agree?

## Problem 8: Agent dashboard

  ### Prompt 8a

  Thanks. we are now moving onto Problem 8: Agent dashboard. please build the frontend dashboard in frontend/ with React + Vite + TypeScript. The page should call the routes we built in Problem 7. THe board should:
  1) list all three tickets
  2) let me, the human user, pick one ticket and start the agent team on it
  3) show each agent and what they are doing and saying while the ticket runs. Use speach bubbles with brief insights so it looks like they are talking.
  4) mark a ticket "resolved" when the run finishes.
  5) show a short summary of what each agent did on that ticket
  6) let a human approve a pay or purchase when asked
  7) show the checking balance, which should drop after an approved pay

  The dashboard should look good. use professional formatting and yale color formats we used in previous homeworks. Real people will use this dashboard as a desk so it should feel comfortable. Please give each of the agents a Super Mario brothers character that fits with their job description. This picture should be animated and bounce up and down when they are being called or interacting with each other. please also add connections and dynamic sounds that trigger when they are in use, so the human user can visualize who is talking to each other. I'll add more formatting in a follow up prompt once you set up the initial view.

  please make the front end talk to the back end at http://localhost:8000. the backend should allow the Vite page origin (please state this if you are unclear) so the browser is allowed to call the routes. the board should start with "npm run dev", which should open the React desk in my browser  so i can pick tickets and watch agents. Plesae write a file called output/design.md that paraphrases my design notes shared here and in future prompts. It will contain what i chose for the dashboard look, like the layout, how agents read differently, and how the resolved tickets and cash show up, and why, including my creative choices and why humans would enjoy using it. We'll keep adding to this as i edit your work. Please let me know if anything is unclear. when you are finished, please double check your work.

  ### Prompt 8b

  please shut everything down

  ### Prompt 8c

  Please perform a full end-to-end review of all the code in this workspace for consistency with the homework requirements and purpose. Identify any potential issues we should address before moving onto the ticket testing stage. Review your work, challenge your assumptions, and ensure the API key is safe. i still dont see an .env file. Make sure everything is set up so we can eventually push this to Github at the end of the assignment. Please let me know where anything is unclear. also, the mario characters are awful! please redraw using publicly available resources

  ### Prompt 8d

  please restart the back end and share the link to the front end so i can review again

  ### Prompt 8e

  Are the agents running right now?

  ### Prompt 8f

  thanks. in the frontend dash board, please make the following changes:
  1) Move the human approval box above the conversation box
  2) make it prettier. keep it professional and with Yale color theme, but clean it up because it looks far too stale and AI-generated. when the agents are talking to each other, add more dynamic curve lines with animations that show the flow of communication. 
  3) These characters aren't great. Instead replace them with South Park characters - have Cartman be the boss, then add Kyle, Stan, Kenny, and Towlie as the workers. 

  also 4) while an agent is working and typing an update for the speech bubble, just show "..." with the ... bouncing while the bot is thinking then replace it with the actual text summary

  ### Prompt 8g

  please remove knock off south park and mario characters and references, and update the design.md file. can you instead make the 5 workers look like these characters?

  ### Prompt 8h

  man these reallllly don't look good. let's switch to something else - halloween characters. Use a whimsical animated zombie, ghost, witch, frankenstein, and vampire. Make the witch the boss. Use consistent animation / drawing styles from the public domain or creative commons.

  ### Prompt 8i

  thanks. please remove the lines from the agent background. the two curved lines connecting the two right agents should curve the other way so they are symmetrical. please make it so when the characters bounce, the top of them does not get cut off. please synchronize their bouncing - the ghost is offbeat. please put the witch's label above her head. please also change the labels to describe the agents role, not what halloween character they are.

  ### Prompt 8j

  can we make the agent background more festive and halloween or spooky themed? when the agents talk to each other, please make it so little pumpkins and pieces of candy travel up and down the connection lines. If agents talk to each other, please also draw new lines that appear and show them communicating with each other. Then, using objective sources from credible experts, please recommend 5 enhancements that would make this dashboard more user friendly, and another three that would accentuate the halloween theme without reducing usability.

  ### Prompt 8k

  please implement all 5 usability changes, and all three halloween additions. then, restart the backend 

  ### Prompt 8l

  i jsut tested ticket 101. the boss shows this screenshot and doesnt proceed. please diagnose and review your code. Explain what you got wrong and how you'll fix it before proceeding. please also ensure you updated design.md with our prior changes.

  ### Prompt 8m

  here is more error information: status_code: 400, model_name: gpt-6-luna, body: {'message': "azure-openai error: Invalid 'input[1].id': 'portkey_cache_ca3d3d5e-6291-46db-a3ea-2b170410fc1f'. Expected an ID that begins with 'fc'.", 'type': 'invalid_request_error', 'param': 'input[1].id', 'code': 'invalid_value'}

  ### Prompt 8n

  i'm wokring through Ticket 101 and there are a few issues. the speach bubbles and summary only appear above the boss, but she isnt doing all the work - the bubbles should appear over the agent that is doing the task. the COnversation window only shows Boss and should include other agents. the "What each agent did" section also only shows the boss, but should include the other agents' activity. similarly, the "approve invoice payment" button lets me click it multiple times. one the human approves, it should grey out so it can't be clicked again. it seems for ticket 101 the agents restocked, but then stopped - they should have proceeded drafting an email to the customer about the backorder. Please review your work and recommend updates

  ### Prompt 8o

  yes, please make all these changes. the boss should be delegating tasks not doing everything itself. please ensure that is clear in the agent prompts. Then, reset the shop and restart the backend

  ### Prompt 8p

  thanks. the agents should be able to call each other, work efficiently, but not do actions outside their scope of defined responsibilities. Can you please confirm the agent prompts accurately reflect that? if not, recommend changes for me to review before implementing them

  ### Prompt 8q

  yes, please make these changes and restart everything so i can test again

  ### Prompt 8r

  The code stopped again with the following error, can you please diagnose?
  Exceeded the total_tokens_limit of 20000 (total_tokens=22753). Consider raising the limit, or see the docs on usage limits for budget-aware patterns: https://pydantic.dev/docs/ai/core-concepts/agent/#usage-limits

  ### Prompt 8s

  How can we adjust this to make it more effiient and use less tokens?

  ### Prompt 8t

  yes please make these changes and keep the current cap

  ### Prompt 8u

  Same error, but we got further. 20,000 tokens seems like a lot and i'm worried i'm missing the mark on this assignment. Please take a step back and holistically review our work so far within the goals of the assignment. Does this outcome make sense? challenge your thinking and consider whether there is a more efficient way to structure this from the ground up. also please help me estimate the cost of 20k tokens. Do not make any changes until i approve, just recommend updates

  Exceeded the total_tokens_limit of 20000 (total_tokens=21412). Consider raising the limit, or see the docs on usage limits for budget-aware patterns: https://pydantic.dev/docs/ai/core-concepts/agent/#usage-limits

  ### Prompt 8v

  please implement 1, 2, 3, 4, and 5, and raise cap to 25,000

  ### Prompt 8w

  can you restart the backend?

  ### Prompt 8x

  Thanks. more formatting stuff: in the agent visual, please replace the icons next to each agents name with the following (can use public images):
  Boss = gavel
  Inventory = cardboard box
  Accounting  = calculator
  Faciltiies = wrench
  Customer service = smiley face

  and remove the beige backgrounds with their labels.

  ### Prompt 8y

  Thanks. Ticket 101 shows as resolved but it really isnt - the agents should have identified the empty inventory, outstanding invoice, drafted payment for human approval, but never did the latter. here are the transcript notes - please identify what broke down and how to fix it:

  What each agent did

  Boss
  The requested Bulldog tee (CC-TEE-WHITE, size S, quantity 1) cannot be fulfilled: stock is 0. The shortfall is 1. Restock cannot be confirmed because Bulldog Print Co has an open unpaid invoice ($840, due 2026-08-28), and vendor-to-SKU eligibility and product cost are unknown. No payment or purchase order was drafted.

  Inventory
  CC-TEE-WHITE size S has 0 in stock; requested 1, so the shortfall is 1. Apparel specialty vendor Bulldog Print Co has a 5-day lead time but cannot ship new product under the shop rule because it has open invoice 501 ($840, due 2026-08-28). Vendor-to-SKU eligibility and product cost are unknown; no restock can be confirmed.

  Accounting
  No summary yet.

  Facilities
  No summary yet.

  Customer Service
  Prepared an unsent customer note. It explains that the requested Bulldog tee in size S is currently unavailable, without promising a delivery date or claiming an order was placed.

  ### Prompt 8z

  ok this is much better but a few more design notes for the dashboard: 
  1) a ticket should not be marked as resolved until the human takes action. 
  2) Below the agent, please show the draft customer service email
  3) the error / notification section at the very bottom right of the screen is super hard to read. please move it up to the top as an overlay.
  4) please align the length of ticket 103 box with the length of the Human approval box, apply that same length to the 101 and 102 boxes, and evenly distribute them at the top of the page

  ### Prompt 8aa

  rather than making notices an overlay, can it be a box that appears above the three ticket boxes but below the blue banner, that closes out with an x?

  ### Prompt 8ab

  couple more things:
  1) in human approval section, please also add another button to decline. 
  2) in the ticket boxes, once human approval is given, please update the brown NEEDS YOU button to a green "Human Review Complete" button
  3) the customer service email should be a new section below  the agent window, not a bubble inside it. similar to "What each agent did" section

  ### Prompt 8ac

  ok thanks. l'm testing ticket 103 now, why didn't the agents propose bulk discount prices? are they waiting for a human?

  What each agent did

  Boss
  Only 8 of 20 requested CC-HOOD-NAVY size M hoodies are in stock; 12 are short. Bulldog Print Co's SKU eligibility is unknown, so no restock is confirmed. Accounting reports list pricing of $58 each ($1,160 total), but no approved discount policy or discounted price is recorded. Human approval is needed to set a discount and confirm restock eligibility. No invoice was provided.

  Inventory
  CC-HOOD-NAVY size M: 8 available; requested 20, so the shortfall is 12. Apparel vendor Bulldog Print Co has a 5-day lead time and no open invoices, so it can ship under the open-invoice rule. Vendor eligibility for this specific SKU is unknown, so a restock is blocked pending confirmation. The requested 20 cannot be filled from stock alone.

  Accounting
  Stored pricing is $58 per hoodie ($1,160 for 20), with a $22 unit cost and 62.07% gross margin at list price. No approved discount or discount policy is recorded, so I cannot determine or authorize a discounted price. Human approval is required to set any override.

  Facilities
  No summary yet.

  Customer Service
  Prepared an unsent customer update. The requested discount requires human approval; no restock is confirmed.

  ### Prompt 8ad

  i'm not sure i follow, will you please elaborate?

  ### Prompt 8ae

  i see. how would you implement that change?

  ### Prompt 8af

  yes please make both changes - the pricing range and restock approval

  ### Prompt 8ag

  please shut down the backends

  ### Prompt 8ah

  yes please stop that too

  ### Prompt 8ai

  Please review the AI_prompts file - why are these latest prompts getting tagged under Problem 9?

  ### Prompt 8aj

  please update the names to continue past z, for example using aa, ab, ac so everything falls under Problem 8

## Problem 9: Resolve the tickets

  ### Prompt 9a

  thanks looks better. please restart the front end and backend. We are now moving onto Problem 9: Resolve the tickets. before testing the agents on a full run, please reset the campus_customs_new.db to its original values so we can start clean. please note the starting checking balance. Then, run all three tickets, in order, until each is resovled. If you run into issues, please pause and ask me for clarifications. diagnose the issues and propose resolutions for me to evaluate, but do not implement them yet. 

  in output/desk_tickets.html that we made earlier, please fill in the "Actual" section from each ticket tab with info from this run: which agents worked, what they delegated, and which tools they used. please do not modify my expected section in that file, because i need to compare the two. 

  on the cash tab of that same desk_tickets file, itemize the money. show the starting checking account balance after reset, for each ticket how cash changed when that ticket resolved and why (which pay / purchase, dollar amount),  and the ending checking balance, which should match cash_accounts in the working database. Please add an explicit reconciliation check for this piece. Wrong cash math will lose points even if the board shows tickets are resolved so ensure the project can reconcile the cash balances.  

  Please also save: 
  output/resolved_tickets.json - for each ticket, id, final status, short outcome, what each agent contributed, and any human approvals.
  output/resolved_board.html - a page i can double click with a screenshot of my React board for each resolved ticket (101, 102, and 103). If taking screenshots is hard for you, i can do it myself and paste them into our chat

  Please append real runs to output/audit_trail.json. Then, please update the @output/harness.md  file so it covers tables, MCP tools, the five agents, API routes, the dashboard, and safety rules. For safety rules, please cap agent calls at 10 each per ticket and recommend other safety features that are relevant from prior homeworks.   There is a lot here - please plan your next steps so i can review and approve

  ### Prompt 9b

  your decision for ticket 103 is correct. for #8, please ignore my new cap proposal, sorry forgot we already added it. go wild!

  ### Prompt 9c

  please implement option 2

  ### Prompt 9d

  thanks. to clarify, is the code approving as MIcah? remember, only a human can approve payments. please ensure that whatever you used to approve payments is not embedded in the code. i'm going to review your work

  ### Prompt 9e

  Thanks! please double check our work so far for potential issues. i'll now run the tickets manually

  ### Prompt 9f

  thanks. i'll reset the front end myself. did you make any back-end changes that require a restart? Also, did your rerun make it to the html files we created?

  ### Prompt 9g

  why didnt you create those files?

  ### Prompt 9h

  i see. please perform the full rerun yourself now that we've fixed the code for ticket 102

  ### Prompt 9i

  and make sure you reset the database first

  ### Prompt 9j

  please go with option 2

  ### Prompt 9k

  thanks, please shut down the back end

  ### Prompt 9l

  and any other remaining processes

  ### Prompt 9m

  Can you ensure the prior prompts made it into AI_prompts.md?

  ### Prompt 9n

  thanks for fixing. please restart both the back and front ends

  ### Prompt 9o

  i manually tried ticket 3 and recieved the following error i thought we increased the ticket cap to 40k?

  Exceeded the total_tokens_limit of 25000 (total_tokens=27104). Consider raising the limit, or see the docs on usage limits for budget-aware patterns: https://pydantic.dev/docs/ai/core-concepts/agent/#usage-limits

  ### Prompt 9p

  lets raise it to 40,000

  ### Prompt 9q

  Thanks. for the customer service agent, please make sure its email for ticket 103 is capable of providing the approved quote decision, and relevant numbers for the total order cost

  ### Prompt 9r

  For ticket 103, let's change the format a little. rather than suggesting discounts, lets make the discount a user input in the "Human approval" window. Please show a simple table with the product's current margin, the human input discount, and margin net of discount in both % and dollar terms per unit. Then, weave the final quote into the unsent customer email.

  ### Prompt 9s

  thanks. please make it so that additoinal dicscount section only appears after the agents have run and assessed the ticket

  ### Prompt 9t

  much better! can you please also make the Unsent customer email, Conversation, and What each agent did sections speciifc to each ticket? I.e. when i click on a ticket, those sections should show the relevant info for that specific ticket. currently, running a new ticket overwrites all those sections with the latest ticket

  ### Prompt 9u

  thanks. Regarding the code for ticket 103, please add protection that ensures the user cannot enter a discount greater than the current margin.

  ### Prompt 9v

  thanks. We've made quite a few changes, so let's do this: rerun everything we did  initially from my Prompt 9a. there are quite a few dependent files that must be updated when you rerun the tickets, included updated screenshots

  ### Prompt 9w

  what is your recommendation? I'm not sure i follow

  ### Prompt 9x

  yes lets do option #3 and an $8 discount

  ### Prompt 9y

  in the descriptions below the Ticket numbers on the resolved_board.html file, please add the cash balance after the ticket was resolved

## Problem 10: Reflection

  ### Prompt 10a

  Thanks. We are now moving onto Problem 10: Reflection. in output/desk_tickets.html, Reflection tab, please fill in my verbatim vibe below. I get more points specific to this App and the three tickets, and should connect them to the ticket and Cash tabs we saved as evidence. Once you've copied in my verbatim wording, please provide feedback on anything i can do to enhance my response. 

  #1 / #2 Ticket performance evaluation and Actual / Expected analysis:
  Ticket 101: The agents performed very well because they worked seamlessly as intended. As expected, the Boss agent called Inventory since the bulldog T is a clear stock request. Inventory correctly identified the CC-TEE-WHITE / S was out of stock using check_inventory_status and check_vendor_status, then called Accounting to check restock invoices. Accounting used draft_payment_for_human_review to prepare the $840 outstanding invoice for human approval, a human (me!) approved it, and the checking balance correctly went from $3,400 to 2,560. Customer service drafted a backorder note to the customer Tauhid. The facilities agent was not called, as expected. Overall actual results were very consistent with expectations. A future improvement would be to follow up on the sale once backordered inventory arrives, assuming the buyer is still interested. 
  Ticket 102: The agents also performed very well, and the Customer Service agent added some unexpected creative flair. Initially the agents’ actual behavior followed my expectations: the Boss agent called Facilities, who identified the upcoming due lease payment using get_lease_status, then called Accounting who drafted the $2,400 payment to Elm City Properties with draft_payment_for_human_review. The checking balance correctly fell from $2,560 to $160, which a human (me) approved. However, there was a disconnect with the Customer service agent – although I did not expect them to be called, the Customer service agent drafted an email to the landlord saying the payment was on its way. I hadn’t fully intended this but liked the feature and kept it. As expected, the inventory agent was not called. A future improvement would be to broaden this agent tool for other utilities (electric, heat, water, etc.)
  Ticket 103: This was the trickiest to engineer, and the agent performed weakly compared to the other two because it struggled to follow through with the quote given the potential for a negative checking account balance. The agents did ok but there is lots of room for improvement, I spent a lot of time troubleshooting this one got the code to compromise: it would refuse the order due to the negative checking account balance, but provide the quote to the customer anyway with a note about restock lag time. Initially, the Boss called Inventory to assess stock, then Accounting for margins. I made it so the human user could enter the exact bulk discount they wanted, floored at the total margin (won’t sell below cost). I expected to offer ranges but changed the code while troubleshooting issues. Facilities was not called, as expected. Cash remains at $160 because we never issued the order, and need to top off the checking account before ordering more for the quote. 
  #3 Agent consolidation opportunities: 
  The Inventory management, Facilities, and Accounting agents feel like they could be consolidated into a single Operations agent that uses separate tools for each of these aspects. Most of the agent back-and-forth communications were among these three, and the Boss just acted as a delegator and facilitator, especially when coordinating with the Customer Service agent. Integrating these three agents into tools under one functional role would streamline the code and reduce model calls, since the information they need is more readily accessible via database pulls. 
  #4 Three new problems Campus Customs might face that this agent team could solve with the tools I built:
  1)	The agent team should be able to handle different monthly bill payments, although this requires some testing. An electric, cable, or water bill should be able to be called with the same agentic processes as the lease payment in Ticket 102. 
  2)	Bank account depletion – the agents should be able to identify when the bank account will be depleted for a given order stock, i.e. the max a customer can order

  #5) Three new problems Campus Customs might face that this agent team could NOT solve:
  1)	Revenue generation – right now we only track money going out of the checking account, and not money coming in. I’d create a Sales agent with tools that track revenues, money moving into the checking account, and business cash flow. The Sales agent would complement the Inventory and Accounting agents nicely, and could rely on them to coordinate prices and proactive restocking.
  2)	Marketing / Advertising – If Campus Customs wants to expand their distribution, they’ll need a Marketing agent with tools that identify sales leads, track our most popular products, and internet scrapers that identify trends. The Marketing agent could also use tools that generate ads for social media, print, and local flyers. 
  3)	Warehouse Staffing / Fulfillment Manager – my agents don’t have any timekeeping or scheduling abilities, which Campus Customs needs to physically ship orders. I’d create an Operations agent that has tools to design work schedules for warehouse employees, manages employee callouts / sick time and leave, and coordinates order fulfillment behind the scenes. This would make the Campus Customs manual labor behind the scenes more efficient.

  ### Prompt 10b

  please propose explicit wording changes for the three tickets, be factual and concise. i will review and approve. 

  in the verbatim reflection, please add this to the end of #3 agent consolidation: " For context, ticket 101 was three separate boss calls, ticket 102 was facilities calling accounting, and ticket 103 called accounting again but was refused." please make sure my counts are accurate there. 

  in section 4, i forgot a third thing.

  ### Prompt 10c

  Thanks, Please replace Ticket 102 with this:

  Ticket 102: The agents also performed very well, and the Facilities agent added some unexpected creative flair. Initially the agents’ actual behavior followed my expectations: the Boss agent called Facilities, who identified the upcoming due lease payment using get_lease_status, then called Accounting who drafted the $2,400 payment to Elm City Properties with draft_payment_for_human_review. The checking balance correctly fell from $2,560 to $160, which a human (me) approved. The Facilities agent drafted an email to the landlord saying the payment was on its way. I hadn’t fully intended this but liked the feature and kept it. As expected, the inventory and customer service agents were not called.

  ### Prompt 10d

  you previosuly said "The cash math and the handoffs are the parts a grader can check against the Ticket and Cash tabs, and two of those sentences currently disagree with that evidence." which two sentences? I'll fix

  ### Prompt 10e

  please replace Ticket 101 with "Ticket 101: The agents performed very well because they worked seamlessly as intended. As expected, the Boss agent called Inventory since the bulldog T is a clear stock request. Inventory correctly identified the CC-TEE-WHITE / S was out of stock using check_inventory_status and check_vendor_status, then the Boss called Accounting to use draft_payment_for_human_review to prepare the $840 outstanding invoice for human approval, a human (me!) approved it, and the checking balance correctly went from $3,400 to 2,560. Customer service drafted a backorder note to the customer Tauhid. The facilities agent was not called, as expected. Overall actual results were very consistent with expectations. A future improvement would be to follow up on the sale once backordered inventory arrives, assuming the buyer is still interested."

  ### Prompt 10f

  thanks. any more potential inconsistencies?

  ### Prompt 10g

  How would you reocmmend improving tsection #4? I agree some of these are fairly weak

  ### Prompt 10h

  Let's just start over with section #4, here are some better ideas:

  1) A second rent payment for the same lease. Ticket 102 already paid lease 1, $2,400, and checking is $160 after all three tickets were processed. The agents won't let a bank account balance go negative so the human will refuse it until the bank account is topped off.

  2) The largest hoodie reorder that keeps checking accounts >=0. After the three tickets, checking is $160 and the hoodie unit cost is $22.00. get_cash_status and check_pricing_and_margin can divide those: 7 units × $22 = $154, leaving $6. An eighth unit is $176, and $160 − $176 = −$16, so the payment will not be allowed.

  3) Restock the sold-out tee now that invoice 501 is paid for ticket 101.  The same inventory, vendor, and restock tools can price a new size S order subject to the bank account constriants.

## Problem 11: Submit to GitHub

  ### Prompt 11a

  thanks, we are now moving onto Problem 11: Submit to GitHub. We will push this code to a public repo so graders can clone it. Please save the repo URL in output/github_url.txt. Before we do so, please perform and exhaustive review of all code and homework problems we've worked on so far and identify any potential issues. Ensure you keep the .env file out of the repo and protect my API key. you should include both database files under data. please create a readme file that explains to copy the database to the working copy when you need a clean run, start MCP server, start FASTAPI backend, start the react board, and reset the DB before a full three ticket run. Please set everything up, then i will give you the repo url. please also ensure we follow this file structure:

  ### Prompt 11b

  thanks,. the frontend and backend folders and other necessary scripts still get pushed, right? for example team.py is not gitignored

  ### Prompt 11c

  thanks. please push to this repo. but first, remember to update that url file:
  https://github.com/micahwtodd/AI_hw5
