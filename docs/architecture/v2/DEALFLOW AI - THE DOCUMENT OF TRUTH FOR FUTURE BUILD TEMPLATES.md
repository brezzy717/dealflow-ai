**THE BUILD FOR DEALFLOW AI \- PHASE ONE AND TWO**  
**DATA INGESTION PIPELINE, DATABASE, 3-ENSEMBLE MACHINE LEARNING INTELLIGENCE SCORING MODULE AND ASSIGNMENT TO USER FACING DASHBOARD WITH OUTREACH FLOW**

**COMPONENT STRUCTURE:**

* PYTHON AND PYTORCH  
* NEON POSTGRES  
* VERCEL  
* CHRONJOB  
* API ENDPOINTS TO DATA SOURCES  
* (THINKING ACTUALLY THESE WILL BE THE 3 WE USE FOR ENSEMBLE- XG BOOST, RANDOM FOREST AND NEURAL NET)  
* WEBHOOKS

**DATA SOURCES (API INGEST)**:  
DEWEY DATA  
YELP BUSINESS DATA  
[DATA.GOV](http://DATA.GOV)  
NASDAQ  
SEC/EDGAR

## **What We're Building**

### **1\. Database (Neon Postgres)**

**Core Tables:**

* `raw_leads` \- Complete business/owner data from all sources  
* `ensemble_predictions` \- ML scores, tiers, explanations  
* `model_versions` \- Track active ML models  
* `ensemble_weights` \- Adaptive model weights  
* `lead_assignments` \- Territory-protected lead ownership  
* `tenants` \- Subscriber accounts  
* `broker_calendars` \- GHL calendar integration data  
* `lead_email_outreach` \- Email tracking  
* `ai_call_queue` \- Scheduled AI calls  
* `ai_call_outcomes` \- Call results  
* `appointments` \- Calendar bookings  
* `deal_outcomes` \- Closed/lost deals  
* `document_vault` \- Subscriber documents  
* `data_source_enrichment` \- Track enrichment sources  
* `admin_notifications` \- System alerts  
* `whatsapp_conversations` \- Support chat history

### **2\. Data Enrichment Pipeline (Python)**

**Multi-Source Data Ingestion:**

* **Dewey Data API** (primary): Business profiles, owner info, financials  
* **Data.com**: Owner personal financial data (liens, bankruptcy, credit)  
* **NASDAQ API**: Public company data, industry benchmarks  
* **Yelp API**: Business sentiment, reviews, ratings, trends

**Enrichment Workflow:**

1. Pull business list from Dewey (filtered by state: Arizona)  
2. For each business, enrich from Data.com (owner financials)  
3. Enrich from NASDAQ (market data)  
4. Enrich from Yelp (sentiment analysis)  
5. Save complete `raw_leads` record  
6. Trigger ML scoring

**Data Quality:**

* Deduplication (business name \+ address matching)  
* Missing data handling (default values)  
* Type validation

### **3\. ML Scoring Engine (ENSEMBLE- XG BOOST, RANDOM FOREST, NEURAL NET)**

**Feature Extraction (52 features):**

**Financial/Business (14):** revenue\_millions, revenue\_per\_employee, employee\_count, years\_in\_business, maturity\_score, owner\_age\_normalized, has\_successor, succession\_risk, pre\_foreclosure, tax\_delinquent, lease\_urgency, lease\_critical, balloon\_urgency, permit\_recency

**Owner Life Events (6):** recent\_divorce, recent\_spouse\_death, recent\_health\_event, life\_event\_recency, life\_event\_critical, has\_major\_life\_event

**Personal Financial Distress (6):** owner\_personal\_bankruptcy, owner\_lien\_count, owner\_lien\_amount\_normalized, owner\_recent\_lien\_count, bankruptcy\_recency, owner\_credit\_risk

**Online Sentiment (10):** yelp\_rating\_normalized, yelp\_trend\_risk, yelp\_rating\_drop, yelp\_rating\_drop\_severe, google\_rating\_normalized, google\_trend\_risk, avg\_online\_rating, avg\_sentiment\_risk, review\_velocity\_declining, negative\_review\_spike

**Market Dynamics (6):** new\_competitors\_risk, recent\_competitors\_count, nearby\_competitors\_count, recent\_zoning\_change, zoning\_change\_recency, property\_value\_risk

**Social Media (5):** social\_inactivity\_score, social\_abandoned, social\_frequency\_drop, social\_frequency\_drop\_severe, social\_engagement\_risk

**Composite Scores (4):** distress\_intensity, owner\_distress\_score, business\_decline\_score, urgency\_score

**Additional (1):** search\_intent\_score

**Ensemble Model:**

* 3 models: XGBoost, Random Forest, Neural Net  
* Weighted average prediction  
* Confidence score (model agreement)  
* Tier assignment: Green (75-100), Yellow (60-74), Red (40-59), Black (\<40)  
* Feature attribution (top 5 positive, top 5 negative)  
* Plain-English explanation

**Output:**

* Save to `ensemble_predictions` table  
* Trigger territory assignment

### **4\. Territory Assignment Engine**

**Logic:**

* Match scored leads to subscriber parameters (industries, revenue, employee count, years in business)  
* Admin Lead ClawBack Functionality from Admin Dashboard  
* **Permanent assignment** \- once assigned, lead belongs to that broker forever  
* No reassignments, no double-dipping  
* Create `lead_assignments` record as “Prospect” and lodged under “Prospect” tab on user dashboard

### **5\. Warm Outreach Auto-Flow**

* 

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**DATA SOURCES WITHIN DEWEY DATA THAT WE HAVE ACCESS TO:**

* ✅ ATTOM Pre-Foreclosure History (27M records)  
* ✅ ATTOM Tax Assessor data (158M properties)  
* ✅ Builty Building Permits (178M records, 20K+ jurisdictions)  
* ✅ People Data Labs (72M companies, workforce trends, employee churn, exec departures)  
* ✅ SafeGraph \+ Advan Foot Traffic (billions of data points)  
* ✅ Verisk Property \+ Consumer data (84M+ properties)  
* ✅ REsimplifi Commercial Listings (brokers, suites, listing data)  
* ✅ BrightQuery (public company employment, SBA loans, financials)  
* ✅ WageScape (423M job postings with salary data)  
* ✅ RentHub (rental listing data)  
* ✅ ConsumerEdge (credit/debit transaction data by geography/brand)  
* ✅ Property ownership details  
* ✅ Owner contact information (name, email, phone)  
* ✅ Property characteristics  
* ✅ Sales comparables  
* ✅ Market data  
* SENTIMENT ANALYSIS  
* Payment Trends by Region, NAICS, Industry and More  
* Business Owner Characteristics i.e. over the age of 65 \= higher score, divorce, widower, partnership dissolution, no beneficiary on record for transfer of assets, cross reference against owner internet search history or osint run to check for social media posting or group activity ect. Does the owner have more than one business and are they under the same umbrella? Status?

**FEATURE\_KEYS \= \[**

    **\# Financial/Business (existing) \- 14 features**

    'revenue\_millions', 'revenue\_per\_employee', 'employee\_count', 'years\_in\_business', 'maturity\_score',

    'owner\_age\_normalized', 'has\_successor', 'succession\_risk',

    'pre\_foreclosure', 'tax\_delinquent',

    'lease\_urgency', 'lease\_critical', 'balloon\_urgency', 'balloon\_critical',

    'permit\_recency',

    

    **\# Owner Life Events (NEW) \- 6 features**

    'recent\_divorce', 'recent\_spouse\_death', 'recent\_health\_event',

    'life\_event\_recency', 'life\_event\_critical', 'has\_major\_life\_event',

    

    **\# Personal Financial Distress (NEW) \- 6 features**

    'owner\_personal\_bankruptcy', 'owner\_lien\_count', 'owner\_lien\_amount\_normalized',

    'owner\_recent\_lien\_count', 'bankruptcy\_recency', 'owner\_credit\_risk',

    

    **\# Online Sentiment (NEW) \- 10 features**

    'yelp\_rating\_normalized', 'yelp\_trend\_risk', 'yelp\_rating\_drop', 'yelp\_rating\_drop\_severe',

    'google\_rating\_normalized', 'google

The personal financial distress section is expanding the model's risk assessment capabilities. These features dive deep into the owner's financial health, capturing bankruptcy history, liens, and credit risk. The six new metrics provide a comprehensive view of potential financial vulnerabilities that could impact business stability. The online sentiment section introduces nuanced rating and trend analysis. By tracking normalized ratings, trend risks, and rating drops across platforms like Yelp and Google, the model can detect early warning signs of reputational decline. The market dynamics features explore competitive landscape and property-related risks. Tracking new competitors, zoning changes, and property value shifts offers insights into potential business disruption and environmental challenges. Social media metrics add another layer of behavioral analysis. Measuring inactivity, engagement frequency, and overall social interaction risks provides a digital footprint of potential business distress. The composite scores synthesize these diverse signals into holistic distress and urgency indicators. The final search intent score likely serves as a predictive signal of potential business transformation or exit strategies. By leveraging all these data points with the major indicator of business owner age of 65+ accounting for a large portion of the score/weight will hopefully provide enough insight to be able to accurately predict intent to sell. 

These 52 features represent a comprehensive multi-dimensional risk assessment framework, integrating quantitative and qualitative signals to predict business health and transition potential.

**52 distinct scoring features**

* 14 financial/business metrics (revenue, employees, maturity, succession risk, distress signals, permit activity)  
* 6 owner life events \+ Age of Owner (We are targeting 65+ (scores higher), 55-64 is given a lower score (most businesses we place in the data base are preferential to the 55-65 yr old crowd of business owners (i.e. retirement age), then we factor in divorce, spouse death, health events, recency scoring and offspring/beneficiaries for passing on the business and/or does the business owner have a partner on record.  
* 6 personal financial distress (bankruptcy, liens, credit risk)  
* 10 online sentiment (Yelp/Google ratings, trends, review velocity, negative spikes)  
* 6 market dynamics (competitors, zoning changes, property value trends)  
* 5 social media (inactivity, posting frequency drops, engagement trends)  
* 4 composite scores (distress intensity, owner distress, business decline, urgency)  
* 1 search intent score

**\#\# COMPLETELY REVISED LEAD SCORING (Based on Available Data)**

**\#\#\# \*\*SCORING METHODOLOGY: 100 POINTS TOTAL\*\***

**\---**

**\#\#\# 1\. PRE-FORECLOSURE & TAX DISTRESS (30 points) 🔴 \*\*HIGHEST PRIORITY\*\***

**| Criterion | Points | Data Source | Exact Field/Dataset |**

**|-----------|--------|-------------|-------------------|**

**| \*\*Active Pre-Foreclosure\*\* | 20 | Crexi Intelligence | Pre-foreclosure status flag |**

**| \*\*Active Pre-Foreclosure (Historical)\*\* | 20 | Dewey: ATTOM Pre-Foreclosure History | Match property APN, check status \= "active" |**

**| \*\*Tax Delinquency\*\* | 10 | Dewey: ATTOM Tax Assessor | Delinquent tax records |**

**| \*\*Property Tax Increase \>20% YoY\*\* | 5 | Dewey: ATTOM Assessor History | Compare year-over-year assessed values |**

**\*\*Data Pull Process:\*\***

**1\. Export property from Crexi (get APN/address)**

**2\. Query Dewey: \`ATTOM Pre-Foreclosure History\` by APN**

**3\. Query Dewey: \`ATTOM Tax Assessor\` for tax delinquency**

**4\. Query Dewey: \`ATTOM Assessor History\` for YoY tax changes**

**\---**

**\#\#\# 2\. FINANCIAL DISTRESS INDICATORS (25 points) 💰**

**| Criterion | Points | Data Source | Exact Field/Dataset |**

**|-----------|--------|-------------|-------------------|**

**| \*\*D\&B PAYDEX Score \<50\*\* | 15 | D\&B Direct+ API | PAYDEX score field |**

**| \*\*D\&B Failure Score \>1,800\*\* | 10 | D\&B Direct+ API | Failure risk score |**

**| \*\*Payment Trends Declining\*\* | 5 | D\&B Direct+ API | Days Beyond Terms (DBT) trend |**

**| \*\*Workforce Decline \>15% (12mo)\*\* | 10 | Dewey: People Data Labs | \`Employee Count by Month\` table |**

**| \*\*Recent Executive Departure\*\* | 5 | Dewey: People Data Labs | \`Recent Exec Departure\` table |**

**\*\*Data Pull Process:\*\***

**1\. Get owner entity name from Crexi export**

**2\. Query D\&B API by business name \+ address**

**3\. Query Dewey: \`People Data Labs \- Employee Count by Month\`** 

**4\. Query Dewey: \`People Data Labs \- Recent Exec Departure\`**

**5\. Calculate 12-month employee trend**

**\---**

**\#\#\# 3\. PROPERTY NEGLECT & DEFERRED MAINTENANCE (20 points) 🏚️**

**| Criterion | Points | Data Source | Exact Field/Dataset |**

**|-----------|--------|-------------|-------------------|**

**| \*\*No Permits Filed in 5+ Years\*\* | 10 | Dewey: Builty Building Permits | Query by address, check date of last permit |**

**| \*\*Property Age \>30 Years \+ No Recent Permits\*\* | 5 | Crexi (Year Built) \+ Dewey (Builty) | Combine \`year\_built\` from Crexi with Builty permit history |**

**| \*\*Declining Foot Traffic YoY \>20%\*\* | 10 | Dewey: SafeGraph or Advan Foot Traffic | \`Weekly Patterns\` or \`Monthly Patterns\` \- compare YoY visits |**

**| \*\*Below-Market Sale Price\*\* | 5 | Crexi Intelligence | Sale price vs. comparable sales (Crexi comps) |**

**\*\*Data Pull Process:\*\***

**1\. Get property address from Crexi**

**2\. Query Dewey: \`Builty Building Permits \- United States\` by address**

**3\. Get Year Built from Crexi export**

**4\. For retail/restaurant: Query Dewey: \`SafeGraph Weekly Patterns\` or \`Advan Monthly Patterns\`**

**5\. Compare foot traffic YoY**

**\---**

**\#\#\# 4\. OWNERSHIP DISTRESS SIGNALS (15 points) 👤**

**| Criterion | Points | Data Source | Exact Field/Dataset |**

**|-----------|--------|-------------|-------------------|**

**| \*\*Out-of-State/Absentee Owner\*\* | 8 | Crexi Export | Mailing Address ≠ Property Address (distance \>100 miles) |**

**| \*\*Owner Entity Age \>25 Years\*\* | 5 | Dewey: BrightQuery \`Corporate Status\` | Entity formation date |**

**| \*\*Multiple Properties (Portfolio 10+)\*\* | 4 | Crexi Intelligence | Owner name matching across database |**

**| \*\*Recent Ownership Transfer (\<2 years)\*\* | 3 | Dewey: ATTOM Recorder | Deed recording date |**

**\*\*Data Pull Process:\*\***

**1\. Get owner mailing address from Crexi export**

**2\. Calculate distance between property address and mailing address**

**3\. Query Dewey: \`BrightQuery \- Corporate Status\` by entity name**

**4\. Query Dewey: \`ATTOM Recorder\` for recent deed transfers**

**5\. Search Crexi by owner name for portfolio size**

**\---**

**\#\#\# 5\. MARKET & TENANT RISK (10 points) 📉**

**| Criterion | Points | Data Source | Exact Field/Dataset |**

**|-----------|--------|-------------|-------------------|**

**| \*\*High Submarket Vacancy (\>15%)\*\* | 5 | Crexi Intelligence | MSA vacancy rate data |**

**| \*\*Tenant Job Postings Down \>30%\*\* | 5 | Dewey: WageScape \`Job Postings with Salary\` | Query by tenant company, compare posting volume |**

**| \*\*Active Comparable Listings Nearby (3+)\*\* | 3 | Crexi Intelligence | Filter by property type \+ 1-mile radius |**

**\*\*Data Pull Process:\*\***

**1\. Get MSA vacancy data from Crexi market reports**

**2\. Identify tenant from Crexi listing/description**

**3\. Query Dewey: \`WageScape \- Job Postings with Salary\` by company name**

**4\. Search Crexi for comparable properties within 1 mile**

**\---**

**\#\# LEAD TIER CLASSIFICATION**

**\#\#\# 🔥 \*\*RED HOT (75-100 points)\*\***

**\*\*Triggers:\*\* Pre-foreclosure OR (PAYDEX \<50 \+ 2 other distress signals)**

**\- Immediate broker assignment**

**\- 24-hour contact SLA**

**\- Priority outreach sequence**

**\#\#\# 🟡 \*\*WARM (50-74 points)\*\***

**\*\*Triggers:\*\* Moderate financial indicators (PAYDEX 50-70) \+ ownership distress**

**\- 72-hour contact SLA**

**\- Weekly drip campaign**

**\- Educational content nurture**

**\#\#\# 🟢 \*\*DEVELOPING (25-49 points)\*\***

**\*\*Triggers:\*\* Early indicators but not urgent**

**\- Monthly check-in**

**\- Market updates**

**\- Long-term relationship building**

**\#\#\# ⚪ \*\*MONITOR (\<25 points)\*\***

**\*\*Triggers:\*\* Minimal signals**

**\- Quarterly automated outreach**

**\- Track for changes**

**\---**

**\#\# DATA INTEGRATION WORKFLOW**

**\#\#\# \*\*STEP 1: Crexi Property Export\*\***

**\`\`\`**

**Fields to Export:**

**\- Property Address (Street, City, State, ZIP)**

**\- APN (Assessor Parcel Number)**

**\- Owner Name**

**\- Owner Entity**

**\- Owner Mailing Address**

**\- Owner Phone**

**\- Owner Email**

**\- Year Built**

**\- Property Type**

**\- Square Footage**

**\- Sale Price (if applicable)**

**\- Pre-Foreclosure Status**

**\`\`\`**

**\#\#\# \*\*STEP 2: Dewey Data Enrichment\*\***

**\*\*A. Pre-Foreclosure & Tax Data\*\***

**\`\`\`sql**

**\-- ATTOM Pre-Foreclosure History**

**SELECT \* FROM attom\_pre\_foreclosure\_history** 

**WHERE apn \= '\[Crexi APN\]'** 

**AND status \= 'active'**

**\-- ATTOM Tax Assessor**

**SELECT \* FROM attom\_tax\_assessor**

**WHERE apn \= '\[Crexi APN\]'**

**AND (delinquent\_status \= TRUE OR tax\_lien \= TRUE)**

**\-- ATTOM Assessor History**  

**SELECT year, assessed\_value FROM attom\_assessor\_history**

**WHERE apn \= '\[Crexi APN\]'**

**ORDER BY year DESC**

**LIMIT 2**

**\`\`\`**

**\*\*B. Building Permits\*\***

**\`\`\`sql**

**\-- Builty Building Permits**

**SELECT MAX(issue\_date) as last\_permit\_date**

**FROM builty\_building\_permits**

**WHERE address \= '\[Crexi Property Address\]'**

**\`\`\`**

**\*\*C. Workforce & Company Data\*\***

**\`\`\`sql**

**\-- People Data Labs \- Employee Count by Month**

**SELECT month, employee\_count FROM pdl\_employee\_count\_by\_month**

**WHERE company\_id \= (**

  **SELECT company\_id FROM pdl\_company\_insights** 

  **WHERE name \= '\[Owner Entity Name\]'**

**)**

**ORDER BY month DESC**

**LIMIT 12**

**\-- People Data Labs \- Recent Exec Departure**

**SELECT \* FROM pdl\_recent\_exec\_departure**

**WHERE company\_id \= (**

  **SELECT company\_id FROM pdl\_company\_insights** 

  **WHERE name \= '\[Owner Entity Name\]'**

**)**

**AND departure\_date \> DATE\_SUB(CURRENT\_DATE, INTERVAL 12 MONTH)**

**\`\`\`**

**\*\*D. Foot Traffic (If Retail/Restaurant)\*\***

**\`\`\`sql**

**\-- SafeGraph Weekly Patterns OR Advan Monthly Patterns**

**SELECT date\_range\_start, raw\_visit\_counts**

**FROM safegraph\_weekly\_patterns**

**WHERE placekey \= '\[Property Placekey\]'**

**ORDER BY date\_range\_start DESC**

**LIMIT 52  \-- Last 12 months of weekly data**

**\`\`\`**

**\*\*E. Entity & Ownership Data\*\***

**\`\`\`sql**

**\-- BrightQuery \- Corporate Status**

**SELECT formation\_date, entity\_status**

**FROM brightquery\_corporate\_status**

**WHERE legal\_name \= '\[Owner Entity\]'**

**\-- ATTOM Recorder (Recent Ownership Transfer)**

**SELECT recording\_date, grantor, grantee**

**FROM attom\_recorder**

**WHERE apn \= '\[Crexi APN\]'**

**ORDER BY recording\_date DESC**

**LIMIT 1**

**\`\`\`**

**\*\*F. Job Posting Trends (Tenant Risk)\*\***

**\`\`\`sql**

**\-- WageScape \- Job Postings**

**SELECT DATE\_TRUNC('month', post\_date) as month, COUNT(\*) as posting\_count**

**FROM wagescape\_job\_postings**

**WHERE company\_name \= '\[Tenant Company Name\]'**

**AND post\_date \> DATE\_SUB(CURRENT\_DATE, INTERVAL 12 MONTH)**

**GROUP BY month**

**ORDER BY month DESC**

**\`\`\`**

**\#\#\# \*\*STEP 3: D\&B Financial Scoring (When Added)\*\***

**\`\`\`javascript**

**// D\&B Direct+ API Call**

**const dnbResponse \= await fetch("https://api.dnb.com/v1/data/duns/{DUNS}", {**

  **headers: {**

    **"Authorization": "Bearer {API\_KEY}",**

    **"Content-Type": "application/json"**

  **}**

**});**

**const creditData \= await dnbResponse.json();**

**const paydexScore \= creditData.financialStrength.paydexScore;**

**const failureScore \= creditData.riskIndicators.failureScore;**

**const dbt \= creditData.paymentTrends.daysBeyondTerms;**

**\`\`\`**

**\#\#\# \*\*STEP 4: Scoring Calculation\*\***

**\`\`\`javascript**

**let totalScore \= 0;**

**// Pre-Foreclosure & Tax Distress (30 points)**

**if (attomPreForeclosure.status \=== 'active') totalScore \+= 20;**

**if (attomTaxAssessor.delinquent) totalScore \+= 10;**

**if (taxIncreaseYoY \> 0.20) totalScore \+= 5;**

**// Financial Distress (25 points)**  

**if (dnb.paydex \< 50\) totalScore \+= 15;**

**if (dnb.failureScore \> 1800\) totalScore \+= 10;**

**if (dnb.dbtTrend \=== 'increasing') totalScore \+= 5;**

**if (workforceDecline \> 0.15) totalScore \+= 10;**

**if (pdl.recentExecDeparture) totalScore \+= 5;**

**// Property Neglect (20 points)**

**const yearsSinceLastPermit \= (new Date() \- new Date(builty.lastPermitDate)) / (365 \* 24 \* 60 \* 60 \* 1000);**

**if (yearsSinceLastPermit \> 5\) totalScore \+= 10;**

**if (propertyAge \> 30 && yearsSinceLastPermit \> 5\) totalScore \+= 5;**

**if (footTrafficDecline \> 0.20) totalScore \+= 10;**

**if (belowMarketPrice) totalScore \+= 5;**

**// Ownership Distress (15 points)**

**if (absenteeOwner) totalScore \+= 8;**

**if (entityAge \> 25\) totalScore \+= 5;**

**if (portfolioSize \>= 10\) totalScore \+= 4;**

**if (recentTransfer) totalScore \+= 3;**

**// Market & Tenant Risk (10 points)**

**if (submarketVacancy \> 0.15) totalScore \+= 5;**

**if (tenantJobPostingsDecline \> 0.30) totalScore \+= 5;**

**if (comparableListingsNearby \>= 3\) totalScore \+= 3;**

**IMPLEMENTATION CHECKLIST**

* Build data pipeline: DEWEYi → NASDAQ → DATA.GOV → YELP and SEC/EDGAR= DATA INGESTION INTO SCORING ENGINE  
* Create database schema for enriched property records  
* Develop scoring algorithm (weighted calculation, ensemble metrics and training, numerical value into color block green, yellow or red)  
* Build broker dashboards to display scores \+ underlying data  
* Build Admin dashboard to watch real time modules, error handling and lead clawback  
* Set up 2x weekly data refresh automation  
* Create audit trail for score changes over time  
* Build Feedback Loop for conversion data on how many leads \= booked & how many booked \= closed  
* Build Automation for Outreach Flow (initial email then calling sequence by Hume Ai or the Broker/User)  
* Round Robin Assignment Engine (Slow drip 30 leads per week to each broker, 10g/10y/10r- assigned to one user permanently unless user departs prior to making contact then back into pool for next round of assignments if not enough from color then pull from the next block down)

**WHAT WE ARE TRYING TO ACCOMPLISH, THE PROBLEM WERE SOLVING AND THE SPECS OF THE BUILD FOR OUR PHASE ONE:**

Deal Flow AI, which can be found under the domain dealflowtech.io, is a proprietary data parsing, ingesting, aggregating, sorting, scoring, matching platform aimed at using proprietary data from several sources (Dewey Data, Data.gov, Yelp Business Data as well as Nasdaq and SecEdgar) ingested into our machine learning module via API endpoints to build a database of small and medium size businesses throughout the United States first, focusing on the markets in Arizona, Utah, and Texas and expanding outward building little by little. The entire goal is to identify businesses, potentially looking to sell based off of the measurement of over 52 data points each of those data points is a weighted measurement, which then returns a numerical value and placed on a color-coded point system (green, yellow, and red \- green are the highest scored businesses when measured against the data points that were found to be potential new off market leads identifying businesses looking to sell yellow is moderate red is lower, but still in the game). Right now is an incredible wealth transfer event happening many of the baby boomer. Businesses are looking to transfer cell and exit their businesses that ended up being very successful over the years yet they have nobody to pass the baton too. Maybe they didn’t have children or so on so forth But they’re looking to retire, wanting to exit and need qualified buyers. However, after speaking with several business brokers, it looks to be that the issue is not that there is a lack of sellers, but there’s a lack of finding them before the deals are all picked over traditionally, business, brokers, or old school. They still do everything by spreadsheet and cold calling and that’s just not the way of things anymore, especially with the technology in advance as we make every day . Utilizing something like machine, learning software proprietary data sets and an excellent scoring model we should be able to put these pieces together in such a way that we’re able to identify potential sellers, off market, before they have sourced out their own brokers, etc. By doing things like targeting owners over the age of 65 with no beneficiaries, maybe the properties and financial distress maybe the owners personal finances are in distress maybe they just got divorced or perhaps there was Delinquent tax filings pre-foreclosure notices filed. The list goes on and on as we have access to all of this data when we build out our list in the database for these businesses all throughout the US we are checking for those very data points as soon as enough of those weighted attributes can be pinned down to a specific business and scored high enough to fall into one of our green yellow or red categories It is then tagged as an off market potential it is attached green, yellow, or red with the reasoning for the score in plain English and will be then distributed to our brokers platforms on a round robin slow drip feed process of 30 leads per week 10 of each color for a total of 120 leads per month that will be labeled as prospects in the user facing dashboard.

The machine learning model will be a combination of three separate ML‘s. It is an AI powered scoring system that learns from feedback, the scoring gets smarter overtime based on which leads actually convert into bookings and essentially into deals closed. It needs to understand patterns in the data, not just assign static points. there’s a feedback loop. That will be training the model in an ongoing manner. We’re not looking for just interested it will be which of those leads that were assigned to the brokers were then able to be booked and then from the ones that were booked were the brokers able to then close all of those data points get placed back in the feedback loop sent back to the model to be ingested making it better with time and more on point. The machine learning approach feature engineering that continuously learns and grows and evolves from actions initiated by either our user or the ai employee (Hume ai calling agent) who will be validating the leads from the dashboard (2 pronged approach- first action is if the lead resulted in a booked appointment and second action is if the booked appointment turned into a signed deal) and that data that can be sent back to the ensemble to be retrained each time new feedback comes in- pattern recognition that identifies which combinations of signals predict success not just something as arbitrary as pre-foreclosure equals 20 points, but something that understands complex interactions. The model which is a three prong model features vectors from the lead data with regular retraining on feedback AND data confidence scores not just static point assignments. The schema also needs to support model versioning and drift, error Logging with real time feeds to an admin dashboard which can be monitored for error messages. Will also be integrating lead clawback feature features in case of misassignment by the models where the admin can override any assigned leads to correct the action.

I feel that only using one model is hugely limiting the approach- the model then loses comparative performance insights, it creates aversion, lock-in risk and limits AB testing capabilities. If we combine predictions, using weighted averages, it would mitigate risk by maintaining fallback models for concept, drift detection, emergency rollback scenarios and compliance audits. Therefore, we will be utilizing three models and averaging out to score data. The ensemble approach with multiple active models will look to be as follows: XGBoost\_v1, random\_forest\_v1, neural\_net\_v1. Performance metrics, Model ensemble weights, which will be adaptive based on recent performance.

 • Prediction drift score (how much predictions diverge from other models)  
 • Ensemble predictions (combined output)  
 • Individual model predictions  
 • Model predictions and model weights

The ensemble output will be a weighted average score and prediction confidence, along with prediction variance across models.

 • Feature-level scoring breakdown (detailed attribution per feature)  
 • Tier assignments (our green, yellow, and red)

We will then need, as I stated above, explainability features driving the score up or down in plain text. All predictions must be time and date stamped for record keeping purposes and data compliance. We'll need model performance tracking for weight adjustment as well as lead assignments. It will track the predicted score, the actual outcome, actual quality score, prediction error, and a logging of the time and date stamp will also be default.

Enhanced feature engineering will include robust feature extraction, such as:

* Financial Health Indicators:  
* Annual revenue degradation  
* Salary and revenue per employee  
* employee count  
* years in business

The business maturity score is a composite. It features:

*  Number of years in business  
*  Business maturity score  
*  Years in business (we're capping it at 25 years)  
* Owner life events, data points for divorce, death of a spouse, or other significant life events which are strong catalysts for selling.   
* Personal financial distress, inclusion of personal liens or bankruptcies tied to the owner, as this can directly impact the business.   
* Online business sentiment, a trend score based on recent Google Yelp reviews. A steady decline can indicate owner burnout or operational problems.   
* Local market dynamics, data on new competitors opening in the immediate vicinity or local zoning changes that could affect property value.   
* Social media posting frequency, this can lead… Or lend… Significant insight into signaling owner disengagement. 

This also includes owner demographics:  
If the owner's age is over 60, the score is higher than if they're between 40 and 59  
If the owner has a successor and succession risk

* Personal and professional distress signals:  
* pre-foreclosure  
* tax delinquency  
* Divorce  
* Death of spouse or biz partner

Then there is time urgency features- we measure today's date and then look at:

* If there is a lease in place the Number of days till the lease ends \= lease urgency.   
* We factor in mortgage information, such as if a balloon payment is due on the building IF the building is owned by biz owner. 

* We also track any other businesses, sister, corporations, child companies, underneath the same owners umbrella in a corporate sense to measure as well the health of those businesses seeking out any indicators of distress if they start selling off other properties or businesses, then we know this one may be next

Business activity indicators:

* money being spent at this business   
* $ spending trends in the region, in the industry and in the zip code

* We factor in foot traffic. 

* climate information and ratings for the area for fire, flood, tornado and hurricane or earthquakes along with regular doplar data

* manufacturing and distribution trends in the industry  
* Raw lead web, search activity if available from the data sources  
* Industry risks  
* Location features  
* Business size

\*These are not all-inclusive. We actually have several more that we would need to add in here.

When scoring against all the data points, the outcome is a weighted combination of all of the features indicated from the ensemble models, this gives a timing prediction of potential sale for the business. The business is then given a numerical score and categorized into green yellow or red based off of the numerical value. All historical predictions with score and the reasoning for said score is date and time stamped, and then saved for data quality, training, and for historical look back. What was once a cold lead can go piping hot with the filing of a court notice owner bankruptcy or even a steep increase in competition coupled with a huge dip in sales for the third month in a row putting the owner in distress. That is why it’s hugely important that we put heavy emphasis on feedback loop plus the continuous API data pulls from our sources at least 2 to 3 times a week and checking the new data against what we have in our base.

**The ensemble training and prediction.** We'll have to build a pipeline through Python. Our database will be through Neon Postgres. We'll have to import XGBoost. We'll have to import Random Forest Regressor and import the Standard Scaler as well as MLP Regressor. We will also have to import NumPy as well as Joblib.

We will then import our initial training set of data into the model simultaneously to begin building our tables, our database, and to then begin weighted scoring of analyzed data, predicting lead quality and using the output of the ensemble to then produce those potential off-market leads which will then be assigned to our users/brokers. 

On a rolling ongoing basis data ingestion via API for all the data sets/sources will be happening on MondayWed/Fri mornings at 10 AM- then Tuesday mornings at 6 AM all leads will be dispersed to each user/broker dashboard: 30 per week total- 10 green 10 yellow 10 red. For 120 total leads per month. Vercel chron job will be manning the automation portion here which covers the consistent weekly pulling of new data points/ingestion from the sources outlined above. ONLY The initial ingestion will be kicked off manually, Everything else runs on the automation outlined- even the feedback loop is going to be automated, as well as lead assignment (as stated above) lead assignment occurs every Tuesday morning at 6 AM no exceptions

At onboarding, the user/broker will be asked a series of questions that will then create parameters for lead assignment. Once leads are ready to be assigned, they will be matched against the parameters for each individual user/broker and if it matches the parameters it will be dispersed. If not, it goes back in the lead pool for the next broker. This occurs until all required leads are dispensed. Any left over will be assigned the following week. If for some reason we run out of a certain color lead under that user/brokers parameters than we go ahead and pull from the next color block we are two green short for example, then we go ahead and pull two from the yellow if we’re too yellow short, we pull two red And so on so forth.

Once a lead is assigned to a broker/user, it stays with that broker for the lifetime duration in our database the only exception is if the broker leaves our platform prior to initiating contact with this lead, at that point, we claw back and re-integrate the lead back into the data pool.

**User/broker specific parameters for assignment:**  
Number of years in business  
Number of employees  
Annual revenue in millions  
Any industries to be omitted  
Any cities/ZIP Codes to be omitted in your licensing state

\*These parameters can be changed at any time by the client/broker from their settings tab on their dashboard.

The feedback loop will run based off of two actions which are initiated by either the user/broker or the AI calling concierge agent that will be doing the outreach for each of the leads. There will be two instances where they will be requested to action the lead. We will be tracking how many leads were then converted into a booked appointment And how many booked appointments were then converted into a signed deal. As those actions are occurring, they are immediately sent through the feedback loop back to our ensemble for retrain and we do all this in the hopes that it will make our module stronger better faster at predicting Analyzing and scoring better quality leads overtime as the model gets more confident and grows more intelligent the quality of the leads will also get better.

The leads are sent down through the pipeline to the user facing dashboards lodged under the “prospects” tab.

**OUTREACH AUTOMATION & AI CALLING CONCIERGE**  
Immediately upon being assigned to a user dashboard the outreach automation starts. During onboarding, the user has the opportunity to either approve or decline the calling concierge/outreach feature. If they choose to do the outreach themselves, then they are responsible 100% for providing an action/outcome for each of the perspectives on their dashboard that will flow into our feedback loop for the machine learning module. If they choose to allow us to do the automation sequence for outreach then the calling concierge will be responsible for providing an action/outcome on the prospects. This feature can be toggled on her off at a later time under the settings in the users dashboard if they change their mind.

The outreach sequence: An immediate email goes out as soon as prospects hit the dashboard. It includes two value add documents in PDF form attached to the email and the email body includes a self service booking link for our self hosted cal.com instance which gives the business owner, the opportunity to book an appointment at their leisure for their discovery call.

Seven days later on the following Tuesday between 11 and 1 PM, the calling sequence begins where our calling concierge powered by Hume Ai scans the inbox for any responses to our initial email. Check the calendar to see if anybody has booked an appointment and for any of the emails that went out that do not have a response or an appointment booked then receive a follow up phone call with the whole initiative being to book that 30 minute discovery call on the brokers calendar between the broker and the business owner/prospect. The calling concierge will then provide an action for each attempt at calling they will be able to choose booked or not booked, and if they call did not result in a booking, they must then choose the reason why their choices will be, DNC if the business owner requested us to not contact them again at that point, they’ll be deactivated in our database and taken off our calling list. The next reason is going to be interested, but future, and at that point, the concierge will attempt to get a timeframe they would like to have a call back if no timeframe is obtained we schedule out about 60 days for a call back and put them on our callback list. If they didn’t make contact with the business owner, then they will say and see for no contact and they will be put on the list to be called back in three days. All of the actions and reasons will then be fed to the feedback loop and filtered back into our machine learning platform for ingestion. Whether it is the common concierge or the broker making the phone calls or outreach, they must action exactly the same way.

Friday around the same time between let’s say 11 AM and 1 PM the second outreach telephone call will be placed by either the broker or the calling concierge following the same sequence with the same initiative and providing actions and outcomes for each prospect the exact same way as above. For any prospect where no contact was made. They will be placed on the list to call back in 90 days and the same sequence from above will initiate: email will go out first and then two phone calls. 

Each call is going to be recorded and transcribed and then attached to the prospect/client (they are still a “prospect” If no contact was made and they’re considered a “client” if they were booked on the brokers calendar).

All prospects, clients calls, transcripts appointments tasks you name it. Everything can be exported via CSV or Excel spreadsheet or it can be exported via API to their preferred CRM if they don’t choose to use ours. And if they are choosing to use ours, then they’re able to have the upload feature where they can bulk ingest or upload via API from another service or a Google spreadsheet if they want to go ahead in bulk and just clients contacts customers appointments that kind of thing in into our dashboard/CRM.

 as soon as a prospect has been booked on the brokers calendar after the broker has the discovery call, he must then provide another action which is closed/signed or not closed if it was not closed then he provides the reason which are not multiple-choice that will be an open text box where he will then in plain English, write the reason. This thing gets filtered back through our pipeline to our machine, learning platform for ingestion the broker than at this point has the option to go ahead and utilize our CRM for tracking his new client there’s going to be a toggle button on that client that takes it from a prospect to client and as soon as the prospect is now a client then enters the deal pipeline tab if they don’t ever toggle this switch then the prospect never hits the pipeline and they are responsible for tracking their deal after that point.

* All prospects must have an action associated with an outcome for each prospect on a users dashboard. Otherwise, the user will not receive their upcoming trip of new leads the following week.

\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**PHASE TWO: THE USER AND ADMIN DASHBOARD STRUCTURE USING THE PROVIDED UX/UI AND THEN MODIFIED FOR OUR ACTUAL LINKED SECTIONS AND DESIRED COMPONENTS OUTLINED BELOW**  
   
**COMPONENT STRUCTURE(S):**  
PYTHON DATA PIPELINE NEEDS API ENDPOINTS TO ATTACH TO OUR NEON POSTGRES DATABASE AS WELL AS OUR FEEDBACK LOOP HOOKUP POINTS

**VERCEL** IS FRONT END HOSTING

**CHRONJOB** FOR AUTOMATIONS

**API HOOKS FOR HOSTING OUR OWN INSTANCE OF [CAL.](http://CAL.com)COM BOOKING**

**API/HOOKS FOR HUME AI VOICE AGENT/TWILIO (FALLBACK IS RE-TELL)**

**BRAVE BROWSER API** FOR SEARCH BAR

**GOOGLE MAPS API** 

**CLERK USER AUTH:** ONBOARDING/USER FACING AND ADMIN ACCOUNT SET UP

**STRIPE PAYMENT**

**DEALROOM TAB/SECTION** NEEDS DOCUSIGN OR ADOBE ECT FOR CONTRACT SIGNING, GROUP TWO WAY CHAT FUNCTIONALITY, SECURE DOCUMENT UPLOAD AND ATTACH TO MESSAGE/ CHAT AND SEND TO CLIENTS \- BUYER AND SELLER, ONE CLICK SAVE AND ATTACH DOC TO PROSPECT OR CLIENT FILE, INSTANT PUSH NOTIFICATION FOR MESSAGES RECEIVED 

**ADDITIONAL INFO FOR THE REQUIRED FEATURES AND TABS OF THE USER FACING DASHBOARD**

**HOMEPAGE: UNIVERSAL NAVIGATION ON LEFT SIDE (VERTICAL): ALL BOLD UNDERLINED ITEMS ARE THE NAVIGATION LINKS TO BE DISPLAYED ON THE HOMEPAGE, I HAVE INCLUDED A DESCRIPTION FOR EACH OF THE LINKED PAGES FOR EXTRA CLARIFICATION:**

**HOME PAGE W/ DEAL ASSIST-** DEAL ASSIST AS A FLOATING ICON WIDGET NAMED ARIA- STAYS STATIONARY IN THE BOTTOM LEFT OF THE SCREEN UNIVERSALLY- The dashboard across the top is going to have a row of graphs, charts, and features with metrics personal to the user/broker. It'll have:

* Year-to-date commissions  
* Monitor their closing rates  
* How many prospects had been converted into an appointment and then converted into a close

That way they can see the value they're receiving from the platform right then and there.

Obviously up in the top left corner we're going to have our logo. We're going to do a vertical navigation along the left hand side of the screen. The tabs will follow underneath here in the bold, underlined sections.

Underneath the graphs and charting with the metrics, I would like to see perhaps something cool like:

* A quick view of their upcoming appointments for the week  
* Tasks that need to be done  
* A quick list of their prospects ingested for that week

Maybe like a quick action to go ahead and initiate a walkthrough of the platform if they need to go ahead and have help or whatever. Just like a widget-style coming together dashboard, an overview of their life inside of our application.

**PROSPECTS (LEADS)-** This is where the scored leads fall after assignment has been made to each user/broker. All leads are now labeled as prospects and placed here for further working. The user is able to upload any of their previous clients by CSV, Excel, Google Spreadsheet, and they can also ingest prior historical clients or prospects via Webhook API and linking into their previously/favorite CRM. Along with the upload feature, they're also able to download and export any of their perspectives or clients inside our system/database. We need to make sure we accurately map the fields required for each of our perspectives, which ones are going to be mandatory and which ones can be left blank and still accepted into the system?

So, obviously, like business name and address, phone number, email address, owner information, name, phone number, email. If we have an address, if not, no biggie. Industry, number of employees, annual recurring revenue, years in business, reason for selling. If it was a buyer client, what business did they acquire? If it was a seller client, who acquired it? Prospect won't have that information yet if it's still a perspective. But once they turn into a client, all of those fields will be mapped. For a prospect, we will just need the business name, industry, address, phone number, email, owner's information, number of employees, years in business, annual recurring revenue, and the scoring logic from the machine learning module. We want the user/broker to know why it scored the way it was scored. What we gave weight to and why. \*Side note, the Prospects tab is where the Brave Browser feature is going to live. There's going to be a search bar embedded via API to the Brave Browser. The way the Prospects tab I envision it looking is going to be a listing of all of the scored leads which are now prospects. That list view will have the name of the business, the pertinent information like the number of employees, ARR, years in business, the industry, etc. When you hover over the business or click into it, it will expand and give you the detail of why it scored the way it did and all the nitty-gritty stuff. On the right-hand side of the list, there's going to be a heat map with overlays with color-coded pins. The color of the pin is going to match the heat of the lead (green, yellow, or red). When they hover over the pin or click on the pin, it will expand the info to the business as well. When it expands the info to the business, it'll be able to be swiped left or right and around Robin-style carousel for a quick view. This will be powered by Google Maps API. Underneath that map feature, I would like to see that Brave browser search bar embedded where if they see a business they're not sure about, they can pop the name into the search feature and they can search the wide web and get pictures, reviews, things of that nature without having to leave the app.

**APPOINTMENTS-** The Appointments tab is going to house all of the broker's booked appointments:

* Either made by them  
* Or the calling concierge  
* Or via the self-service link included in the email outreach

They can also import appointments from their own calendars. We're going to be utilizing Cal.com. We're going to host our own instance of this. Upon onboarding the broker/user, we're going to request credentials for their preferred email client. If they're not comfortable giving that, then we'll go ahead and set them up with our instance of Cal.com which can be imported or exported to a calendar of their choosing. We'll go ahead and try to reaffirm to them that this isn't the best way to do it because we're not going to have real-time access to their actual appointments, and things may get double-booked. So their best bet is to allow us to have credentialed access via OAuth to their email client. Assure them that privacy is of the utmost concern. All of their data will be purged from our system should they ever cancel or leave our platform. And during their stay, the only things we keep are actions or outcomes for our machine learning module. Other than that, everything is under them; they own it and they can choose what to do with it (export, delete, etc.)

So under the Appointments tab feature, I would like to see:

* A week view of their current upcoming appointments by day (obviously for the upcoming week)  
* Next to that, somewhere have a 30-day calendar  
* Under that, a listing of their appointments where they can then expand them and read the detail of the business broker seller buyer whatever

**MY CLIENTS-** The user/broker can import their list of past or current clients via API or webhook from their current CRM, or they can bulk upload a list as a CSV, Excel, or Google spreadsheet, map the features according to my specifications which I've included above, and everything is housed here. All notes made for each client or prospect as the prospects are turned into clients. They're going to live here. Literally everything attaches as an asset to their client and is stored here for archive use. It can be exported any time by the user/broker, and we will use the actions and outcomes for our machine learning module to make it better and better. It will be a list style where they can then click into a specific name and it will open up that client and show all the pertinent information they could ever want to see.

**DEAL ROOM-** The Deal Room spins up an action every single time they close on a prospect and the prospect becomes a client after one of their discovery calls. As soon as they hit the deal pipe pipeline, they're able to be spun up into a Deal Room.

The Deal Room is going to be a two-way chat function feature, almost like a chat room, for the broker, the buyer, and then the seller can also be invited in or vice versa for any document exchange, notarization, deal signings of any kind, updates, questions, concerns, things of that nature. It will be pushed notifications for real-time notifying of messages received or documents received or a request by the broker to the seller for documents etc etc. Documents can be attached and sent via The Deal Room. They can be one-click attached to that client as an asset. It will follow the actual necessary stipulations and requirements to be considered a valid electronic signature HIPAA SOC 2 compliant. We can invite a notary in if necessary. If we need another party to come in like the underwriter or doing due diligence of some kind, an accountant for financials, you can invite others in to The Deal Room to go ahead and make your deals. If they want to attach a document from their own document vault which is on their dashboard, they'll have a one-click attach feature where they can choose to upload from their own vault, 

**PIPEDEAL**\- THIS IS THE DEAL PIPELINE FOLLOWING THE DEAL FROM THE SIGNATURE OF THE PROSPECT NOW TURNED INTO A CLIENT THROUGH THE ENTIRE PROCESS OF MATCHING WITH A POTENTIAL BUYER FOR THEIR BUSINESS THROUGH THE LETTER OF INTENT AND DUE DILIGENCE PHASES, ALL THE WAY UP TO THE SIGNING OF THE BUY-SELL AGREEMENT UNDERWRITING AND FINAL CLOSING DOCS ACCOMPANIED BY THE EXCHANGE OF PAYMENT. IT IS A KANBAN STYLE DRAG AND DROP WHERE THE CLIENT IS MOVED THROUGH THE VARIOUS STAGES OF DEAL DEVELOPMENT AND AT THE END THE BROKER/USER IS PROMPTED TO “ACTION” THE CLIENT AS CLOSED/COMPLETE, AT WHICH POINT THE SYSTEM MOVES THE CLIENT FROM THE ACTIVE PIPEDEAL TO THE “CLIENTS” TAB OF THE APPLICATION MAKING THEM A HISTORIC OR PAST CLIENT AND ALL DOCUMENTATION, NOTES, AND DEAL ASSETS WILL BE SAVED TO THE CLIENT AND WILL BE STORED IN THE DATABASE UNTIL THE BROKER/USER CHOOSES TO EXPORT THE INFO VIA WEBHOOK OR API TO A CHOSEN CRM OR DOWNLOAD TO THEIR HARD DRIVE ECT AND/OR IF THE USER/BROKER LEAVES OUR PLATFORM THEN THEY CAN SELECT TO HAVE ALL THEIR PERSONAL INFORMATION PURGED AND WE ONLY KEEP INFO/DATA RELATED TO THE DEAL WHICH FEEDS OUR ML MODULE. 

**PHASE ONE:** BUYER MATCHING  
**PHASE TWO:** LOI, NDA SIGNED  
**PHASE THREE:** DEEP DIVE, DUE DILIGENCE (FINANCIALS, ONSITE VISIT ECT)  
**PHASE FOUR:** NEGOTIATIONS   
**PHASE FIVE:** DOCS SIGNED, SENT TO UNDERWRITER  
**PHASE SIX:** FUNDED, DEAL COMPLETE\!  
**NEXT STEPS FOR SYSTEM:** MOVE TO “CLIENT” TAB OF THE DASHBOARD AND ATTACH ALL ASSETS, NOTES, DOCS, ECT AND ARCHIVE (CAN BE EXPORTED BY THE USER AT ANY TIME)

**AI CALLING CONCIERGE-** The AI Calling Concierge is essentially our warm outreach feature to our application. This feature can be toggled on or off at the user's preference. This happens under the settings tab of their home page of the application. When they first initialize the app, and get walked through onboarding steps, they'll be asked to define their parameters for the assignment of the leads, they'll be generated a user name and password as well as asked if they want to participate in the warm outreach feature. Then we'll give them a rundown of how it works. I.e. as soon as the client prospect hits their dashboard, an initial email goes out with a booking link and a couple of PDFs attached to the email as a value with some really great tips and tricks features for the seller. There will also be a self-service booking link for the broker's calendar, and the email will be very tactfully written but very to the point expressing our interest in a 30-minute discovery call so they can get their free valuation for their business, potentially get matched with a buyer, etc. At the very least, here are a couple of really great PDFs for you to have. And should you ever have any questions, go ahead and give us a call. That kind of thing.

The Calling Concierge runs automatically to send out their initial message on a Tuesday at 6am. It then waits 7 days and then reaches out via telephone as a follow-up to the email. The call is initiated on the following Tuesday between 11am and 1pm. The AI calling concierge scans the inbox for returned responses as well as the calendar for made appointments, and anybody who has not made contact is who gets a phone call. The entire goal of the phone call is to book a 30-minute consult/discovery call with the broker. The calling concierge is then responsible for providing a res- with the details of the appointment. If no contact was made, the calling concierge must action- the outcome as- no contact or no answer and sets it for callback in three days, which will occur on a Friday again between 11am and 1pm. If no contact is made during this second telephone call, it is marked as no contact and set for callback in 60 days.The entire outreach cycle is as follows:

Leads are dispersed at 6 a.m. on Tuesday mornings to the dashboards for the brokers. These leads are then labeled as prospects and they fall on the prospects tab. Immediately, an email is sent out with the attachments outlined above.

After 7 days, a phone call is made on Friday between 11 a.m. and 1 p.m. as a follow-up to the email, attempting to book an appointment on the brokers' calendar. If no appointment is booked on that phone call, a second phone call is made 3 days later on Friday between 11 a.m. and 1 p.m. Again hoping for the same outcome.

If no outreach has been successful, we set it for contact back in 60 days. Every time an outreach is made, the action is logged and sent back to our feedback loop to the machine learning module ensemble.

The only time the lead or prospect is deactivated from our system is if the seller explicitly states they would like to be removed from our calling list. Then we mark them as DNC and deactivate them.

**DAY ZERO- TUESDAY @6AM:** SCORED LEADS ARE DELIVERED TO THE USER DASHBOARD UNDER “PROSPECTS” AND AN EMAIL OUTREACH IS AUTOMATICALLY INTITIATED (INCLUDES BOOKING LINK, PDF’S)  
**DAY 7- TUESDAY @11AM-1PM**: FIRST FOLLOW UP PHONE CALL- AI SCANS THE INBOX FOR REPLY EMAILS AND THE CALENDAR FOR BOOKED APPOINTMENTS CROSS REFERENCE AGAINST THE LIST OF PROSPECTS TO BE CALLED AND OMITS ANY THAT HAVE ALREADY MADE CONTACT SO AS TO NOT DUPLICATE THEN PROCEEDS TO CALL THE PROSPECTS ON THEIR LIST FROM THE BROKER/USER DASHBOARD (ACTION/OUTCOME LOGGED BY EITHER THE CALLING CONCIERGE OR THE BROKER DEPENDING ON IF THE USER HAS OPTED IN TO THE WARM OUTREACH FLOW)   
**DAY 10- FRIDAY @11AM-1PM:** SECOND FOLLOW UP CALL IS PLACED IF NO CONTACT IS MADE THEN THE PROSPECT IS MARKED AS “NO CONTACT” AND PLACED ON THE LIST FOR ANOTHER FOLLOW UP SEQUENCE IN 60 DAYS. (ACTION/OUTCOME LOGGED BY EITHER THE CALLING CONCIERGE OR THE BROKER DEPENDING ON IF THE USER HAS OPTED IN TO THE WARM OUTREACH FLOW) 

**TASK MANAGER-** The task manager. If there are any prospects or clients that need to be actioned/outcome logged, and they are still outstanding on the user's dashboard, they will be logged here. They'll be given a list of clients to gently remind them that they need to go ahead and provide an action or outcome on these prospects or clients. They will have a week after the due date to go ahead and action or outcome the prospect or client. Otherwise, they will not receive the following weeks' leads applied to their dashboard. They want their leads for the following week, they're going to action our current ones.

Okay. I would like to see a to-do list where they can go ahead and add their to-dos here. I would like to see a notebook where they can voice record their thoughts, notes, reminders for themselves, things of that nature where they can set alarms etc. Aria, their assistant, will have access to this page among many others where they will be able to have her retrieve information. She'll have read-write capabilities, web search capabilities. She'll be able to draft and send emails, SMS, enter the deal room, send documents, retrieve documents, read them, their schedule, add new appointments, reschedule appointments. You name it. So, this will be the coming together of that area where they will be able to if they don't use the floating widget, where they can come under here and they can set up their tasks and to-dos and all that good stuff right from this tab for Aria. As I stated, she has many features and functionalities as I just listed here and much more. Underneath the floating Deal Assist widget, which is ARIA, in the bottom right corner universally located on every single page, there's also going to be a Tiny Microphone floating widget which is going to be voice record. Those voice recordings will go into the notebook located here under this tab. They're also able to after they hit stop on the record button, they can attach it to a client, a prospect, or their private notebook, or one of their tasks or calendar appointments.

**VAULT-** The Document Vault. It will start out with customized templates for an NDA, a representation agreement, letter of intent for their people that they can utilize. Basically customized with the brokers logo or website or phone number, all of their personalized information will be set to these documents. They can also edit them at any time before sending them out. They can upload their own to keep everything in one place. They can also download or export these and use them however they'd like. It will also house the PDFs attached to the Warm Outreach going to the prospect. The PDFs will be like, "20 Things a Seller Should Do Before Listing Their Business for a Smooth Transition," "How to Get the Most Valuation for Your Business," or maybe even a seller checklist, before listing and then before closing that deal.

**REPORTS-** There will be many reports located here. The reports will also feedback into our feedback loop for the machine learning module, and it will also power the charts, graphs, and metrics that will be highlighted and shown on the home page of this application. However, they'll be able to get super granular and really drill down into certain categories, functionalities, and features. Maybe they can go ahead and they want to see, "Man, I'm getting a ton of businesses in the cannabis sector," and they're able to really drill down and see, "Man, I've closed this percentage of businesses this year and this many of them are cannabis or this many of them or this or I usually close you know in the summer rather than winter why is that? What am I doing? Or is it just me or is it something else I can help with?" And they can change up. Give them real insight into their practices.As I stated above, things like year-to-date commissions, conversion rates, and the things I've listed above are all hugely necessary and incredibly telling for a broker and anybody else along that trajectory.

**SETTINGS-** Under the Settings tab, they're going to be able to toggle on or off the Automatic Outreach so that the deal, or calling concierge, I mean. They're able to change their parameters that they set during onboarding for assignment of leads/prospects to their dashboard. Here is where they can close their account. They can export all their data. They can import whatever they need to do here. They're also going to be able to watch how-to videos that I've recorded and I'll embed here. They will also have a WhatsApp 24/7 help desk bot, then they will also have direct access to ping me for questions or concerns. They'll be able to toggle back and forth between light and dark mode.

**WHAT WE ARE TRYING TO ACCOMPLISH, THE PROBLEM WERE SOLVING AND THE SPECS OF THE BUILD:**

Deal Flow AI, which can be found under the domain dealflowtech.io, is a proprietary off market deal sourcing platform leveraging proprietary data sources and using ensemble machine learning custom built modules to quickly ingest, analyze, aggregate, match, parse and score the data sets into forward looking predictive pattern recognition software able to accurately identify potential sellers BEFORE they hit the market. There is an unprecedented transfer of wealth happening right now and an incredible amount of baby boomers looking to sell their businesses and unfortunately majority of them typically don’t have a beneficiary or even a buyer willing to take over and/or purchase the business thus hundreds of businesses a day are being lost through the cracks Simply due to not being able to make the connection necessary by the time it’s needed- whether it’s retirement, divorce, or financial distress, many times an owner is looking for an exit and if they don’t find it in time, they simply let a profitable business go. After speaking with some testers, we have found that the issue is not a lack of buyers or even a lack of sellers for that matter there’s an influx of both at the moment yet by the time they hit the mainstream, they are less than ideal. In this day and age the best deals go to those with the deep networks or deep pockets. Our whole goal is to make a new group of potential buyers and potential sellers come together through an easily accessible platform, where once a lead is assigned to a user/broker in this case, it stays with them for life, there is no cross assignment. There are no takebacks and no oversaturation for certain areas of the market. We even go one step further and do the hard reach out first. As soon as a lead is assigned to a users dashboard which typically happens once a week, Tuesdays at 6 AM a total of 30 leads will hit the dashboard (120 per month) color-coded for heat intensity with a given numerical score and a plain text reason for the score from the machine learning platform. Each lead contains all the necessary, contact/business information for the user to disseminate at their leisure. Upon hitting the dashboard an automatic warm up email goes out to the business owner, introducing the broker with a customizable script and a self service booking link for the brokers calendar along with some value added documents automatically attached to give the business seller/owner tips and tricks on how to valuate their business & best practices for selling. We do this rather than cold call on the first run for two reasons one we’re planting the seed, if the owner had been tossing the idea around, but hadn’t really had the time to reach out to a broker or find a potential buyer. Here’s their chance. Plus, we provided information on the potential broker done the introduction and given them some value documents so the chances of them using that self service booking link are quite high. Second reason is because on the off chance they don’t respond to the email when we reach out for the second time via telephone as a follow up call on the first contact we’ve given the seller time to sit with the idea  maybe do some research and if they weren’t really open to the idea before they’re probably open to the idea of evaluation and talking with a broker now, especially after our strategic value add documents and the incredible framing we have done. Trust us, they’re pretty great however, you definitely have the option to edit these as you see fit. Every document and every script on this platform is edible. All information is exportable CVS Excel spreadsheet or even if you have a favorite CRM that isn’t ours we’re happy to hook up via API and export it for you. The email is automatically generated and will happen no matter what however the next outreach is performed by our AI calling concierge powered by Hume Ai with a customizable script and Voice cloning, this feature can be toggled on or off as stated above, and if the user chooses to be the one to reach out they’re more than welcome to do so however, if they would like to have the concierge do it for them it’s an incredible feature\! The Calling Concierge’s whole mission is to book a 30 minute discovery call on the brokers calendar with the potential seller. Once booked a confirmation email goes out to the potential seller and the broker with the details of the call/appointment. The prospect is then moved under the appointments tab on the dashboard, and the AI agent will then action the prospect with the outcome that gets fed back into the loop which makes our machine learning algorithms even smarter and more accurate as time goes on. The appointments tab will include a historical list of all appointments along with a look at the upcoming weeks schedule and a 30 day outlook for a wider picture of the month. When we couple Using a continuous data scanning process for new hits on data points for business’ in our growing database with the custom feedback loops mentioned above continuously sending info back to the ML Module on outcomes of assigned prospects is what will make our platform incredibly accurate as time goes on. We predict that the first 0-6 months our platform will be able to predict perspective sellers with a 90 to 94% accuracy rate and within 6-9 months of continuous use our platform will be somewhere in the range of 99% accurate with prediction rates making what we can offer incredibly valuable for certain factions/industries serving the same target customer sets i.e Business Brokers (our beta testers), Insurance Agents, Estate and Trust Attorney, Tax Professionals and CPA’s, Residential and Commercial Real Estate Agents and even Investors. As an added source of value, a robust feature set akin to custom CRM platforms will house delegated leads we call “Prospects” to each User while in parallel, providing a rich, focused way to move their active deals through the pipeline, keep track or past and present Client data/details, utilize a customized DealRoom for secure messaging and document signing/transmission, chart metrics and generate reports specific to them and their individual numbers, create and manage to do lists, action important tasks and even create custom voice notes on the fly that can be attached to a client, prospect or private notebook. There is also a dedicated place to see booked appointments generated from our Ai Calling Concierge or the User (this ai calling concierge feature can be toggled on or off depending on users need \- housed in the “Settings” tab), user can even set the parameters for the leads being distributed to their dashboard.