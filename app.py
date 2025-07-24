from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
from datetime import datetime, timedelta
import uuid
import logging
import time

app = Flask(__name__)
app.secret_key = 'upsc_mock_exam_secret_key_2023'

# In-memory storage for exam results (in production, use Redis or database)
exam_results_storage = {}

# Clean up old results every hour
def cleanup_old_results():
    current_time = time.time()
    keys_to_remove = []
    for key, value in exam_results_storage.items():
        if current_time - value.get('timestamp', 0) > 3600:  # 1 hour
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del exam_results_storage[key]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html'), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return render_template('error.html'), 500

# Complete Questions and answers extracted from the PDFs
QUESTIONS_DATA = [
    {"id": 1, "question": "The difference between two numbers is 1165. When the larger number is divided by the smaller one, the quotient is 6 and the remainder is 15. What is the smaller number?", "options": ["240", "270", "295", "360"], "correct_answer": "B", "subject": "Mathematics"},
    {"id": 2, "question": "21 mango trees, 42 apple trees and 56 orange trees have to be planted in rows such that each row contains the same number of trees of one variety only. Minimum number of rows in which the trees may be planted is", "options": ["3", "15", "17", "20"], "correct_answer": "C", "subject": "Mathematics"},
    {"id": 3, "question": "A car company sold 150 cars in a special 6-day sale. Each day, the company sold 6 more than the previous day. How many cars were sold on the 6th day?", "options": ["35", "40", "50", "60"], "correct_answer": "B", "subject": "Mathematics"},
    {"id": 4, "question": "Three numbers are in the ratio 4 : 5 : 6 and their average is 25. The largest number is", "options": ["30", "32", "36", "42"], "correct_answer": "A", "subject": "Mathematics"},
    {"id": 5, "question": "The age of a mother today is three that of her daughter. After 12 years, the age of the mother will be twice that of her daughter. The present age of the daughter is:", "options": ["12 years", "14 years", "16 years", "18 years"], "correct_answer": "D", "subject": "Mathematics"},
    {"id": 6, "question": "Ten percent of twenty plus twenty percent of ten equals", "options": ["10 percent of 20", "20 percent of 10", "1 percent of 200", "2 percent of 200"], "correct_answer": "D", "subject": "Mathematics"},
    {"id": 7, "question": "The cost price of 20 articles is the same as the selling price of x articles. If the profit is 25%, then the value of x is", "options": ["15", "16", "18", "25"], "correct_answer": "B", "subject": "Mathematics"},
    {"id": 8, "question": "A, B, C and D have Rs40, Rs 50, Rs 60 and Rs 70 respectively when they go to visit a fair. A spends Rs 18, B spends Rs21, C spends Rs 24 and D spends Rs 27. Who has done the highest expenditure proportionate to his resources?", "options": ["A", "B", "C", "D"], "correct_answer": "A", "subject": "Mathematics"},
    {"id": 9, "question": "A and B started a business jointly. A's investment was thrice the investment of B and the period of his investment was two times the period of investment of B. If B received Rs 4000 as profit, then their total profit is:", "options": ["Rs 16000", "Rs 20000", "Rs 24000", "Rs28000"], "correct_answer": "D", "subject": "Mathematics"},
    {"id": 10, "question": "In a camp, there is a meal for 120 men or 200 children. If 150 children have taken the meal, how many men will be catered to with the remaining meal?", "options": ["20", "30", "40", "50"], "correct_answer": "B", "subject": "Mathematics"},
    {"id": 11, "question": "Two pipes A and B can fill a tank in 12 minutes and 15 minutes respectively. If both the pipes are opened simultaneously and pipe A is closed after 3 minutes, then how much more time will it take to fill the tank by pipe B?", "options": ["7 min 15 sec", "7 min 45 sec", "8 min 5 sec", "8 min 15 sec"], "correct_answer": "D", "subject": "Mathematics"},
    {"id": 12, "question": "A man and a boy together can do a certain amount of digging in 40 days. Their speeds in digging are in the ratio of 8 : 5. How many days will the boy take to complete the work if engaged alone?", "options": ["52 days", "68 days", "80 days", "104 days"], "correct_answer": "D", "subject": "Mathematics"},
    {"id": 13, "question": "An aeroplane flies twice as fast as a train which covers 60 miles in 80 minutes. What distance will the aeroplane cover in 20 minutes?", "options": ["30 miles", "35 miles", "40 miles", "50 miles"], "correct_answer": "A", "subject": "Mathematics"},
    {"id": 14, "question": "A man can row at 5 kmph in still water. If the velocity of current is 1 kmph and it takes him 1 hour to row to a place and come back, how far is the place?", "options": ["2.4 km", "2.5 km", "3 km", "3.6 km"], "correct_answer": "A", "subject": "Mathematics"},
    {"id": 15, "question": "A train of length 150 metres takes 40.5 seconds to cross a tunnel of length 300 metres. What is the speed of the train in km/hr?", "options": ["13.33", "26.67", "40", "66.67"], "correct_answer": "C", "subject": "Mathematics"},
    {"id": 16, "question": "Consider the following statements regarding the 'Zombie ice': 1. It is also referred to as dead or doomed ice. 2. Zombie ice is one that is not accumulating fresh snow even while continuing to be part of the parent ice sheet. Which of the following statements is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "A", "subject": "Geography"},
    {"id": 17, "question": "Which of the following are the possible outcomes of the La Nina event? 1. Wet and humid conditions in the Horn of Africa. 2. Above-average hurricane season for the Atlantic Ocean. 3. Drought conditions in southern South America. 4. No spring season for India. Select the correct answer using the code given below:", "options": ["1 and 2 only", "3 and 4 only", "2, 3 and 4 only", "1, 2 and 3 only"], "correct_answer": "C", "subject": "Geography"},
    {"id": 18, "question": "With reference to United Nations Framework Convention on Climate Change (UNFCCC), consider the following statements: 1. India has hosted the COP of all three Rio conventions on climate change. 2. It is the parent treaty of the 2015 Paris Agreement and the 1997 Kyoto Protocol. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "Environment"},
    {"id": 19, "question": "With reference to the International Monetary Fund (IMF), consider the following statements: 1. It was established in the aftermath of the Great Depression. 2. India is the founding member of the International Monetary Fund. 3. The World Economic Outlook report is compiled by the IMF. Which of the given above statements are correct?", "options": ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "Economics"},
    {"id": 20, "question": "Justice Amitava Roy Committee, which was recently in news, was constituted for which of the following?", "options": ["Jail reforms", "Political participation of women", "Higher education", "Police reforms"], "correct_answer": "A", "subject": "Current Affairs"},
    {"id": 21, "question": "Consider the following statements 1. Tax buoyancy refers to changes in tax revenue in response to changes in tax rate. 2. There is a strong connection between the government's tax revenue earnings and economic growth. Which of the following statements is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "B", "subject": "Economics"},
    {"id": 22, "question": "With reference to Green Bonds, consider the following statements: 1. The International Monetary Fund is a major issuer of green bonds in the international market. 2. Green Bonds are issued to exclusively fund projects having positive environmental impacts. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "B", "subject": "Economics"},
    {"id": 23, "question": "Which of the following are the potential benefits offered by 5G technology? 1. Low latency & greater download speeds. 2. Connecting multiple devices and exchanging data in real-time. 3. Improving road safety by allowing vehicles to communicate between themselves 4. Creating efficient sensor networks to track patients 5. Increased energy savings Select the correct answer using the code given below:", "options": ["1 and 2 only", "1, 2 and 5 only", "4 and 5 only", "1, 2, 3, 4 and 5"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 24, "question": "In which place India is planning to establish its First Dark Sky Reserve?", "options": ["Manali", "Hanle", "Spiti Valley", "Jaisalmer"], "correct_answer": "C", "subject": "Science & Technology"},
    {"id": 25, "question": "With reference to I-STEM, consider the following statements: 1. It is a dynamic and interactive national portal initiated by the Ministry of Science and Technology, Government of India. 2. The main objective is to provide support to needy researchers in different ways and strengthen the R&D ecosystem of the country. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "C", "subject": "Science & Technology"},
    {"id": 26, "question": "Consider the following statements regarding 'Progress on the Sustainable Development Goals (SDG): The Gender Snapshot 2022' report: 1. The report is annually released by NITI Aayog to track India's progress in achieving SDG 15. 2. According to the report, it will take close to 300 years to achieve full gender equality at the current rate of progress. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "B", "subject": "Current Affairs"},
    {"id": 27, "question": "Consider the following statements: 1. Slow moving continental plates may lead to frequent volcanic activities. 2. Volcanoes occur along both convergent (subduction) and divergent (rift) plate boundaries 3. The Ring of Fire is a string of volcanoes and sites of seismic activity around the edges of the Pacific Ocean. Which of the statements given above is/are correct?", "options": ["1 only", "1 and 2 only", "2 and 3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "Geography"},
    {"id": 28, "question": "With reference to Plastic, consider the following statements: 1. Plastic is a synthetic organic polymer made from petroleum. 2. Puneet Sagar Abhiyan launched only to clean sea shores of plastic material. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "A", "subject": "Environment"},
    {"id": 29, "question": "With reference to the Convention on International Trade in Endangered Species of Wild Fauna and Flora (CITES), consider the following statements: 1. It is legally binding on the member states. 2. India is a signatory to this convention. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "C", "subject": "Environment"},
    {"id": 30, "question": "With reference to Financial Inclusion Index, consider the following statements: 1. It is published annually by the State Bank of India (SBI). 2. It is responsive to ease of access, availability and usage of services, and quality of services. 3. It has been constructed without any base year and reflects cumulative efforts of all stakeholders over the years towards financial inclusion. Which of the statements given above is/are correct?", "options": ["1 and 2", "2 only", "1 and 3 only", "2 and 3 only"], "correct_answer": "D", "subject": "Economics"},
    {"id": 31, "question": "Consider the following statements regarding Anti-Tank Guided Missiles (ATGM): 1. It is a guided missile primarily designed to hit and destroy heavily armored military vehicles. 2. HELINA is Anti-tank Guided Missile (ATGM) system mounted on the Advanced Light Helicopter (ALH). Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "C", "subject": "Science & Technology"},
    {"id": 32, "question": "Consider the following statements regarding the International Atomic Energy Agency: 1. It is also known as the world's 'Atoms for Peace and Development' 2. It is an autonomous and independently established organisation. 3. It reports to both the UN General Assembly and the Security Council. Which of the statements given above are correct?", "options": ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "International Relations"},
    {"id": 33, "question": "Ocean Thermal Energy Conversion plant (OTEC) technology can be used for which of the following? 1. Air-conditioning systems. 2. Chilled-soil agriculture. 3. Seawater desalination. 4. Hydrogen extraction Select the correct answer using the code given below:", "options": ["1 and 2 only", "2, 3 and 4 only", "3 and 4 only", "1, 2, 3 and 4"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 34, "question": "Consider the following statements regarding India-ASEAN Relations: 1. Delhi Dialogue is a mechanism hosted by India annually with ASEAN. 2. India is a part of ASEAN's ADMM Plus, which is an annual meeting of Defence Ministers. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "International Relations"},
    {"id": 35, "question": "Which of the following are the key provisions of the Energy Conservation (Amendment) Bill, 2022? 1. Mandating the use of non-fossil sources. 2. Establishment of Carbon Markets 3. Bringing large residential buildings within the fold of the Energy Conservation regime 4. Increasing the members of the governing council of the Bureau of Energy Efficiency (BEE) Select the correct answer using the code given below:", "options": ["1 and 2 only", "3 and 4 only", "1, 2 and 3 only", "1, 2, 3 and 4"], "correct_answer": "C", "subject": "Environment"},
    {"id": 36, "question": "With reference to the Ancient India: 1. Cotton route refers to the maritime route in the Indian Ocean for export of textiles from India 2. India regularly exported large quantities of cotton cloth from Tagara in current Maharashtra state Which among the above is / are correct?", "options": ["Only 1", "Only 2", "Both 1 & 2", "Neither 1 nor 2"], "correct_answer": "C", "subject": "History"},
    {"id": 37, "question": "Consider the following statement: 1. Traces of ash have been found around Kurnool caves. 2. An inscribed stone was found in Rosetta, a town on the north coast of Egypt. 3. Tools made from limestone were found in caves of France. Select the correct answer using the codes given below:", "options": ["1 only", "1 and 3 only", "1 and 2 only", "1, 2 and 3"], "correct_answer": "C", "subject": "History"},
    {"id": 38, "question": "In the context of indus valley civilization, which of the following statement is correct about faience?", "options": ["Faience were an artificially produced material and were used to make beads, bangles, earrings, and tiny vessels", "Faience is a naturally found mineral used in making vessels.", "Faience was a kind of stone tool used in not making.", "Faience were stone weights found in Lothal"], "correct_answer": "A", "subject": "History"},
    {"id": 39, "question": "Match the following: Column A 1. GOLD 2. TIN 3. COPPER 4. PRECIOUS STONE Column B A. Rajasthan B. Afghanistan C. Karnataka D. Gujarat", "options": ["1.C 2.B 3.D 4.A", "1.B 2.C 3.D 4.A", "1.C 2.B 3.A 4.D", "1.A 2.B 3.D 4.C"], "correct_answer": "C", "subject": "History"},
    {"id": 40, "question": "Which of the following pairs are correctly matched? 1. Mrichchakatika – Shudraka 2. Buddhacharita – Vasubandhu 3. Mudrarakshasha – Vishakhadatt 4. Harshacharita – Banabhatta Select the correct answer using the codes given below:", "options": ["1,2,3 and 4", "1,3 and 4", "1 and 4", "2 and 3"], "correct_answer": "B", "subject": "History"},
    {"id": 41, "question": "Which of the following statements is/ are applicable Jain doctrine? 1. The surest way of annihilating Karma is to practice penance 2. Every object, even the smallest particle has a soul 3. Karma is the bane of the soul and must be ended Select the correct answer using the codes given below:", "options": ["1 Only", "2 and 3 Only", "1 and 3 Only", "1,2 and 3"], "correct_answer": "D", "subject": "History"},
    {"id": 42, "question": "With reference to the guilds (Shreni) of ancient India that played a very important role in the country's economy, which of the following statements is/are correct? 1. Every guild was registered with the central authority of the State and the king was the chief administrative authority on them. 2. The wages, rules of work, standards and prices were fixed by the guild. 3. The guild had judicial power over its own members. Select the correct answer using the codes given below:", "options": ["1 and 2 only", "3 Only", "2 and 3 only", "1, 2, and 3"], "correct_answer": "C", "subject": "History"},
    {"id": 43, "question": "Which of the following statements regarding Pala Dynasty is / are correct? 1. Pala rulers patronized Jainism and played an important role in establishing Jainism in different regions. 2. The first Bengali literary work Charyapada is attributed to the Pala Dynasty. 3. During the Pala Era, Vikaramsila and Nalanda were established as two significant centres of learning. Select the correct answer using the codes given below.", "options": ["1 and 2 Only", "2 Only", "3 Only", "1, 2 and 3"], "correct_answer": "C", "subject": "History"},
    {"id": 44, "question": "With reference to the political scenario during the 8th and 9th centuries, consider the following statements: 1. Kanauj was seen as a sign of status and authority. 2. During the time it represented the political domination over northern India. 3. Kanauj was connected to the silk road. 4. Kanauj was rich in resources and hence strategically and commercially significant. Which of the above was/were the possible cause(s) of Tripartite Struggle?", "options": ["1 and 3 only", "2 and 3 only", "1,3 and 4 only", "1,2,3 and 4"], "correct_answer": "D", "subject": "History"},
    {"id": 45, "question": "Consider the following statements regarding the administration of Cholas: 1. The Cholas maintained a regular standing army consisting of elephants, cavalry, infantry, and navy. 2. The naval achievements of the Tamils reached their climax under the Cholas. 3. Cholas had a well – developed naval fleet and had undertaken naval expeditions to foreign shores. Which of the statements given above is / are correct?", "options": ["3 only", "2 and 3 only", "1 and 3 only", "1,2 and 3"], "correct_answer": "D", "subject": "History"},
    {"id": 46, "question": "In what way did the policy of the Rashtrakutas differ from their predecessors in the Deccan?", "options": ["They tried to maintain good relations with the Southern kingdoms while waging wars in the North.", "They attempted to be the transmitters of good ideas from one part to the other.", "They tried to exploit their positions as a bridge to dominate both the North and the South.", "They tried to maintain the balance of power in the struggle between the North and the South"], "correct_answer": "C", "subject": "History"},
    {"id": 47, "question": "Which of the following was not a result of the Turkish conquest on India?", "options": ["It paved the way for the liquidation of multistate system in India.", "It broke the isolation of the Indian society.", "It led to an urban revolution and development of trade and commerce.", "It helped in the growth of liberal religious reform movement in Hinduism"], "correct_answer": "D", "subject": "History"},
    {"id": 48, "question": "Iqta in Medieval India meant", "options": ["Land assigned to religious personnel for spiritual purpose.", "Land revenue from different territorial units assigned to army officers.", "Charity for educational and cultural activities.", "The right of the zamindars."], "correct_answer": "B", "subject": "History"},
    {"id": 49, "question": "One consistent features found in the history of southern India was the growth of the small regional kingdoms rather than large empires because of", "options": ["The absence of minerals like iron.", "Too many divisions in the social structures.", "The absence of vast areas of fertile land.", "The scarcity of manpower."], "correct_answer": "C", "subject": "History"},
    {"id": 50, "question": "Which of the following is not correctly matched? Place of revolt of 1857 | Leader (A) Kanpur | Nana Saheb (B) Baghpat | Shahmal (C) Mathura | Kadam Singh (D) Faizabad | Maulawi Ahamadullah Choose the answer from below:", "options": ["A", "B", "C", "D"], "correct_answer": "C", "subject": "History"},
    {"id": 51, "question": "Consider the following statements regarding the early years of the East India Company establishment in India: 1. The colonial rule was first established in The Bengal. 2. In the beginning, the earliest attempts were made to reorder rural society and establish a new regime of land rights and a new revenue system. 3. The Permanent Settlement had come into operation in 1793. The East India Company had fixed the revenue that each zamindar had to pay. Which of the following statement(s) is are correct?", "options": ["Only 1", "1 and 2 only", "1 and 3", "All of the above"], "correct_answer": "D", "subject": "History"},
    {"id": 52, "question": "After the Santhal Uprising subsided, what was were the measure measures taken by the colonial government? 1. The territories called 'Santhal Paraganas' were created. 2. It became illegal for a Santhal to transfer land to a non-Santhal. Choose from following options:", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "C", "subject": "History"},
    {"id": 53, "question": "Consider the following statements: 1. Governor General Lord Dalhousie described the kingdom of Poona as \"a cherry that will drop into our mouth one day 2. Satara was first princely state to be annexed under Doctrine of lapse. Which of the following is are correct?", "options": ["1 only", "2 only", "All of the above", "None of the above"], "correct_answer": "B", "subject": "History"},
    {"id": 54, "question": "Which one of the following was a very significant aspect of the Champaran Satyagraha?", "options": ["Active all-India participation of lawyers, students and women in the National Movement", "Active involvement of Dalit and Tribal communities of India in the National Movement", "Joining of peasant unrest to India's National Movement.", "Drastic decrease in the cultivation of plantation crops and commercial crops"], "correct_answer": "C", "subject": "History"},
    {"id": 55, "question": "Match the following: Match List I with List II and select the correct answer from the codes given below: List I A.Vinoba Bhave B. B.G. Tilak C. Aruna Asaf Ali D.Sarojini Naidu List II (i) Home Rule Movement (ii) Individual Satyagraha (iii) Dharsana Raid (iv) Quit India Movement Codes : A B C D", "options": ["(ii) (i) (iv) (iii)", "(i) (ii) (iii) (iv)", "(iv) (iii) (ii) (i)", "(i) (ii) (iv) (iii)"], "correct_answer": "A", "subject": "History"},
    {"id": 56, "question": "Who wrote – \"So far as Bengal is concerned, Vivekananda may be regarded as the spiritual father of Modern Nationalist Movement\"", "options": ["Keshab Chandra", "Mahatma Gandhi", "S.C. Bose", "Raja Ram Mohan Roy"], "correct_answer": "B", "subject": "History"},
    {"id": 57, "question": "Consider the following statements: (i) In the late 1920's emerged two powerful left parties, the Communist Party of India & the Congress Socialist Party. (ii) The Kiti Kisan Party of Hindustan was founded in Chennai (iii) Mahatma Gandhi attended Brussels Congress of the oppressed nationalities and visited Soviet Union", "options": ["(i) & (iii) are correct", "None is correct", "(i) & (ii) are correct", "All the above statements are correct"], "correct_answer": "C", "subject": "History"},
    {"id": 58, "question": "Consider the following statements: (i) Abul Kalam Azad and Abdul Gaffar Khan went to Shimla as a congress delegate (ii) In the Shimla conference, the Muslim League demanded a communal vote by asking for a two third Majority in the proposed council on any decision opposed by the Muslim members. (iii) In Shimla conference, the Muslim League wanted to be the sole spokesman of Indian Muslims,", "options": ["(i) & (ii) are correct", "All the above are correct", "(ii) & (iii) are correct", "None of the above"], "correct_answer": "C", "subject": "History"},
    {"id": 59, "question": "Consider the following 1. Mountbatten supported the congress stand that the princely states must not be given the option of independence. 2. Viceroy Wavell offered a set of proposals to the congress for securing its cooperation the \"August Offer\". 3. Disillusioned with the August offer the congress decided to launch Individual Satyagraha", "options": ["All the above are true", "Only 1 & 3 are true", "Only 2 is true", "None of the above"], "correct_answer": "B", "subject": "History"},
    {"id": 60, "question": "Which of the following right s is are enshrined in Article 21 – \"No person shall be deprived of his life or personal liberty except according to procedure established by law.\" 1. Right to speedy trial. 2. Right against delayed execution.", "options": ["1 only.", "2 only.", "Both.", "None"], "correct_answer": "C", "subject": "Polity"},
    {"id": 61, "question": "Which of the following writs can be issued against administrative authorities?", "options": ["Prohibition, Certiorari & Mandamus.", "Certiorari & Mandamus.", "Prohibition & Mandamus.", "Prohibition & Certiorari."], "correct_answer": "B", "subject": "Polity"},
    {"id": 62, "question": "The directive principles were made non – justiciable and legally non – enforceable because: 1. The country did not possess sufficient financial resources to implement them. 2. There was widespread backwardness in the country that could stand in the way of implementation.", "options": ["1 only.", "2 only.", "Both.", "None"], "correct_answer": "C", "subject": "Polity"},
    {"id": 63, "question": "Which of the following statement/s is/are correct. 1. The directive principles are meant to establish Political Democracy. 2. The directive principles are meant to establish Social Democracy. 3. The directive principles are meant to establish Economic Democracy.", "options": ["1 only.", "2 & 3 only.", "1 & 3 only.", "1, 2 & 3."], "correct_answer": "D", "subject": "Polity"},
    {"id": 64, "question": "Which of the following statement/s is/are correct. 1. Fundamental Rights enjoy legal supremacy over Directive principles. 2. The parliament can amend the Fundamental Rights for implementing the directive principles.", "options": ["1 only.", "2 only.", "Both.", "None."], "correct_answer": "C", "subject": "Polity"},
    {"id": 65, "question": "Which of the following statement/s is/are correct regarding Constitutional Amendment bill. 1. Prior permission of President is required before introducing the constitutional amendment bill in parliament. 2. President must give his assent to the bill if duly passed by both houses.", "options": ["1 only.", "2 only.", "Both.", "None"], "correct_answer": "D", "subject": "Polity"},
    {"id": 66, "question": "The emoluments, allowances, privileges and so on of Governor can be altered by:", "options": ["A Constitutional Amendment Bill passed by simple majority of Parliament.", "A Constitutional Amendment Bill passed by special majority of Parliament.", "A Constitutional Amendment Bill passed by special majority of the Parliament and ratified by half of the state legislatures.", "By a normal legislative process that does not require Constitutional Amendment."], "correct_answer": "D", "subject": "Polity"},
    {"id": 67, "question": "Which of the following is/are federal feature/s of our constitution. 1. Supremacy of the Constitution. 2. Rigid Constitution. 3. Independent Judiciary.", "options": ["1 only.", "2 & 3 only.", "1 & 3 only.", "1, 2 & 3."], "correct_answer": "D", "subject": "Polity"},
    {"id": 68, "question": "Which of the following statements are true about Centre – State relations. 1. In respect to matters enumerated in the concurrent list, the executive power rests with the states. 2. In respect to matters enumerated in the concurrent list, the legislative power rests with the centre.", "options": ["1 only.", "2 only.", "Both.", "None."], "correct_answer": "D", "subject": "Polity"},
    {"id": 69, "question": "Which of the following statements are true about Centre – State relations. 1. During the proclamation of emergency (Article 352) the center can give direction to a state on any matter. 2. During the proclamation of emergency (Article 352) President can modify the constitutional distribution of revenues between the Centre & the states.", "options": ["1 only.", "2 only.", "Both.", "None."], "correct_answer": "A", "subject": "Polity"},
    {"id": 70, "question": "Which of the following statements are correct. 1. The chairman and members of state PSC are appointed by the Governor, but can be removed only by the President. 2. The state Election Commissioner is appointed by the Governor but can be removed only by the President.", "options": ["1 only.", "2 only.", "Both.", "None."], "correct_answer": "D", "subject": "Polity"},
    {"id": 71, "question": "Which of the following statement is correct with regard to Proclamation of Emergency. a. Resolution approving & disapproving the proclamation of emergency is to be passed by either house of parliament by a special majority. b. Resolution approving & disapproving the proclamation of emergency is to be passed by either house of parliament by a simple majority. c. Resolution disapproving the proclamation of emergency is to be passed by either house of parliament by a simple majority. d. None of these.", "options": ["a", "b", "c", "d"], "correct_answer": "B", "subject": "Polity"},
    {"id": 72, "question": "Which of the following situation s will be proper to impose Presidents rule in a state (Article 356). 1. Where after general elections to the assembly, no party secures a majority. 2. Serious maladministration in the state. 3. Stringent financial exigencies of the state.", "options": ["1 only.", "2 & 3 only.", "1 & 3 only.", "1, 2 & 3."], "correct_answer": "A", "subject": "Polity"},
    {"id": 73, "question": "Which of the following situation s are correct with regard to Proclamation of Financial Emergency (Article 360). 1. It can be extended to an indefinite period with an approval of the parliament for every six months. 2. A resolution approving the proclamation of financial emergency is to be passed by either house of parliament by simple majority. 3. The President may issue directions for reduction of salaries and allowances of Supreme Court and High Court Judges.", "options": ["1 only.", "2 & 3 only.", "1 & 3 only.", "1, 2 & 3."], "correct_answer": "D", "subject": "Polity"},
    {"id": 74, "question": "The Electoral College for President's election consist of: 1. Elected members of both the houses of parliament. 2. Elected members of the legislative assemblies. 3. Elected members of all Union Territories.", "options": ["1.", "2 & 3.", "1 & 2.", "1, 2 & 3"], "correct_answer": "C", "subject": "Polity"},
    {"id": 75, "question": "When the offices of both Speaker and Deputy Speaker falls vacant –", "options": ["The members of Lok Sabha immediately elect a Speaker.", "The senior most willing member of Lok Sabha becomes the speaker.", "The President appoints any member of Lok Sabha as speaker.", "The Deputy Chairman of Rajya Sabha presides over till the next speaker is elected."], "correct_answer": "D", "subject": "Polity"},
    {"id": 76, "question": "With Regard to Constitutional Amendment Bill –", "options": ["The President can reject the bill but cannot return the bill.", "The President cannot reject the bill but can return the bill.", "The President can neither reject the bill nor return the bill.", "The President can either reject the bill or return the bill"], "correct_answer": "C", "subject": "Polity"},
    {"id": 77, "question": "The correct statement/s with regard to Ordinance making power of President is are – 1. The President cannot promulgate an ordinance to amend tax laws. 2. The President cannot promulgate an ordinance to amend the constitution.", "options": ["1 only.", "2 only.", "Both.", "None."], "correct_answer": "C", "subject": "Polity"},
    {"id": 78, "question": "The Vice President can be removed from office before completion of his term in which of the following manner?", "options": ["She/he can be impeached in similar manner as President.", "A Resolution of Rajya Sabha passed by special majority and agreed to by the Lok Sabha.", "A Resolution of Rajya Sabha passed by simple majority and agreed to by the Lok Sabha.", "A Resolution of Rajya Sabha passed by an absolute majority and agreed to by the Lok Sabha."], "correct_answer": "B", "subject": "Polity"},
    {"id": 79, "question": "The 'Council of Ministers' does not consist of: 1. Deputy Ministers. 2. Parliamentary Secretaries. 3. Deputy Chairman – Planning Commission.", "options": ["1, 2 & 3.", "2 only.", "3 only.", "None of these"], "correct_answer": "D", "subject": "Polity"},
    {"id": 80, "question": "The Representatives of states & UT in the Rajya Sabha are elected by: 1. The members of the State Legislative Assembly only. 2. The elected members of the State Legislative Assembly only. 3. The system of proportional representation by single transferrable vote. 4. The system of proportional representation by List.", "options": ["1 & 3.", "1 & 4.", "2 & 3.", "2 & 4."], "correct_answer": "C", "subject": "Polity"},
    {"id": 81, "question": "Which of the following criteria is laid down by the constitution for a person to be chosen a member of parliament: 1. If a candidate is to contest a seat reserved for SC / ST, he must be a member of a SC / ST in any state or Union Territory. 2. He/she must not have been punished for preaching and practicing social crimes such as untouchability, dowry & sati. 3. He/she must not have any interest in government contracts, works or services.", "options": ["1 only.", "2 & 3 only.", "1, 2, & 3.", "None of these"], "correct_answer": "D", "subject": "Polity"},
    {"id": 82, "question": "Match the rocks with the type of rocks and select the correct answer by using the code given below: List-I A. Intrusive rocks B. Extrusive rocks C. Igneous rocks D. Sedimentary rock List-II 1. Basalt 2. Granite 3. Coal 4. Pegmatite Code: A. B. C. D.", "options": ["1 2 3 4", "2 1 4 3", "2 3 4 4", "1 3 4 2"], "correct_answer": "D", "subject": "Geography"},
    {"id": 83, "question": "Which of the following is not one of Pattison's four traditions of geography?", "options": ["Man-land tradition", "Area studies tradition", "Spatial tradition", "Cultural diffusion."], "correct_answer": "D", "subject": "Geography"},
    {"id": 84, "question": "Situation identifies a place by its...", "options": ["unique physical characteristics", "mathematical location on Earth's surface", "nominal location", "location relative to other objects"], "correct_answer": "A", "subject": "Geography"},
    {"id": 85, "question": "Which one of the following is not an approach in human geography?", "options": ["Areal differentiation", "Spatial organisation", "Quantitative revolution", "Exploration and description."], "correct_answer": "D", "subject": "Geography"},
    {"id": 86, "question": "Which approach was supported by Vidal de la Blache?", "options": ["Determinism", "Possibilism", "Humanism", "Welfare approach."], "correct_answer": "B", "subject": "Geography"},
    {"id": 87, "question": "Match the descriptions with the correct term List-I A River of molten rock C Pulverised rock and lava fall List-II 1. Pyroclastic flow 3. Lava flow Code: A. B. C. D.", "options": ["1 2 3 4", "2 1 4 3", "3 1 4 2", "4 3 2 1"], "correct_answer": "C", "subject": "Geography"},
    {"id": 88, "question": "Which of the following is NOT a component of the Human Development Index (HDI)", "options": ["Push factor", "Education", "Income", "Life Expectancy"], "correct_answer": "A", "subject": "Geography"},
    {"id": 89, "question": "Identify the proponent climate hypothesis among the following human geographers.", "options": ["Vidal de la Blache", "Peter Haggett", "Ellsworth Huntington", "Frederick Ratzel"], "correct_answer": "C", "subject": "Geography"},
    {"id": 90, "question": "Which is NOT an ethnic group of the people of India?", "options": ["Negrito, Veddas", "Toda", "Dravidian", "Australian aborigine"], "correct_answer": "D", "subject": "Geography"},
    {"id": 91, "question": "_______ is the one of the most important commercial metal after iron.", "options": ["Manganese", "Copper", "Aluminium", "Lead"], "correct_answer": "B", "subject": "Geography"},
    {"id": 92, "question": "Transhumance refers to _________.", "options": ["Seasonal movement of people with their belongings from low Lands and vice-versa", "Mixed farming", "Migration of people from rural to urban", "Dairy farming"], "correct_answer": "A", "subject": "Geography"},
    {"id": 93, "question": "The location of some Japan based industries in Malaysia and Taiwan is due to", "options": ["Technology being locally available", "Availability of shipping facilities", "Availability of cheap labour", "Availability of raw materials"], "correct_answer": "C", "subject": "Geography"},
    {"id": 94, "question": "Jersey is the breed of milch-cow from which one of the following countries?", "options": ["Channel Island", "Scotland", "Netherlands", "Denmark"], "correct_answer": "A", "subject": "Geography"},
    {"id": 95, "question": "Mixed farming means___________.", "options": ["Combining crop production with horticulture", "Growing more than one crop in a year", "Combining crop production with live-stock raising", "Growing more than one crop in the same fields in the same season"], "correct_answer": "C", "subject": "Agriculture"},
    {"id": 96, "question": "The concept of carrying capacity of land in terms of population for measuring agricultural efficiency was first propounded by_______.", "options": ["Dudley Stamp", "J.L. Buck", "Jasbir Singh", "G.Y. Enyedi"], "correct_answer": "A", "subject": "Agriculture"},
    {"id": 97, "question": "'A New approach to the functional classification'. This approach was a pioneer to work of _____________.", "options": ["Doi", "Weaver and Rafiullah", "Weaver", "Rafiullah"], "correct_answer": "D", "subject": "Agriculture"},
    {"id": 98, "question": "Fertilizer Corporation of India was established in which one of the following years?", "options": ["1963", "1961", "1971", "1962"], "correct_answer": "B", "subject": "Agriculture"},
    {"id": 99, "question": "Match the List-I and List-II and select the correct answer by using the code given below- List-I ( Theories) A. Least Cost Theory B. Locational Theory of Demand C. Crop Combination method D. Location of Agricultural Activity Model List-II (Authors) 1. Von Thunen's 2. J.C.Weaver's 3. Losch's 4. Weber's A. B. C. D.", "options": ["4 3 2 1", "3 4 1 2", "1 2 3 4", "2 1 4 3"], "correct_answer": "A", "subject": "Agriculture"},
    {"id": 100, "question": "Who among the following is the author of the book\" Geography of Puranas\"?", "options": ["James Todd", "B.G. Tamaskar", "Alexander Unwin", "S.Muzaffar Ali"], "correct_answer": "D", "subject": "Geography"},
    {"id": 101, "question": "The geographical Pivot of History was presented by one of the following_", "options": ["Ratzel", "Mackinder", "Mackinder and Spykman", "Spykman"], "correct_answer": "B", "subject": "Geography"},
    {"id": 102, "question": "Which of the following statements is not correct?", "options": ["Konkani belongs to Indo-Aryan family", "Indo- Aryan languages are spoken over the North-Indian plain from Punjab", "Maithali belong to the Austrio-Asiatic family", "In certain pockets, Dravidian is still spoken in Baluchistan and Bihar"], "correct_answer": "C", "subject": "Geography"},
    {"id": 103, "question": "Arrange the tribes in ascending order in terms of their total number__. A.Bhil B. Santhal C. Mina D. Oraon", "options": ["b a c d", "d b a c", "a b c d", "a d b c"], "correct_answer": "A", "subject": "Geography"},
    {"id": 104, "question": "Mackinder has divided the world into main divisions for his heartland theory __. 1. Outer crescent 2. Pivot area or heartland 3. Periphery area 4. Inner crescent Which of the following divisions are correct?", "options": ["1,2 and 4", "1,2 and 3", "1 and 2", "1and 3"], "correct_answer": "A", "subject": "Geography"},
    {"id": 105, "question": "India's location at the head of the Indian Ocean gives it a special advantage because__.", "options": ["It can expand its fish industry", "It controls the Indian ocean routes", "It can use the resources of the ocean", "It can make exploration easy to the sea-bed for minerals"], "correct_answer": "B", "subject": "Geography"},
    {"id": 106, "question": "Which of the following is the correct sequence of natural vegetation that one sees while flying from Trivandrum to Calcutta?", "options": ["Tropical evergreen, wet deciduous, deciduous, dry savana", "Wet deciduous, dry savana, deciduous, tropical evergreen", "Deciduous, dry savana, wet deciduous, tropical evergreen", "Tropical evergreen, deciduous, dry savana, wet deciduous"], "correct_answer": "A", "subject": "Geography"},
    {"id": 107, "question": "With reference to INSACOG, consider the following statements: 1. It is jointly initiated by the Union Health Ministry of Health and Indian Council of Medical Research (ICMR) among others. 2. It is a pan-India network to monitor genomic variations in the SARS-CoV-2 3. It is facilitated by the National Centre for Disease Control. Which of the statements given above is/are correct?", "options": ["1 only", "1 and 2 only", "2 and 3 only", "None of the above"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 108, "question": "With reference to Helium, consider the following statements: 1. It is the lightest element on the Earth. 2. It is the only element that cannot be solidified by sufficient cooling at normal atmospheric pressure. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "B", "subject": "Science & Technology"},
    {"id": 109, "question": "\"The Purple Revolution\" is associated with cultivation of?", "options": ["Lavender", "Blueberry", "Mulberry", "Coral Reefs"], "correct_answer": "C", "subject": "Agriculture"},
    {"id": 110, "question": "With reference to Antimicrobial Resistance (AMR), consider the following statements: 1. It occurs when bacteria, viruses, fungi and parasites no longer respond to medicines. 2. Antimicrobial-resistant organisms are found in humans only. 3. WHO has declared that AMR is one of the top 10 global public health threats facing humanity. Which of the statements given above are correct?", "options": ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1,2 and 3"], "correct_answer": "C", "subject": "Science & Technology"},
    {"id": 111, "question": "With reference to NeoCoV, consider the following statements: 1. It is a bat coronavirus that was first identified in 2011. 2. It shares an 85% similarity to MERS-CoV in the genome sequence. 3. Infection with NeoCov could not be cross-neutralised by antibodies targeting SARS-CoV-2 or MERS-CoV. Which of the statements given above is/are correct?", "options": ["1 only", "2 and 3 only", "3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 112, "question": "With reference to Small Satellite Launch Vehicle (SSLV), consider the following statements: 1. NewSpace India Limited (NSIL) under the Department of Space is the sole nodal agency responsible for providing end to end SSLV launch services. 2. It can carry satellites weighing up to 5000 kg to a low earth orbit. 3. It is perfectly suited for launching multiple microsatellites at a time. Which of the statements given above is/are correct?", "options": ["1 only", "1 and 2 only", "2 only", "1 and 3 only"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 113, "question": "Consider the following statements regarding Rare Earth Elements (REE): 1. Both light RE elements (LREE) and heavy RE elements (HREE) are abundantly found in India. 2. India is a part of the USA-led Minerals Security Partnership (MSP). 3. REEs are an essential part required for the manufacturing of batteries used in electric vehicles. Which of the statements given above is/are correct?", "options": ["1 and 2 only", "2 only", "1 and 3 only", "3 only"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 114, "question": "With reference to the Genetic Engineering Appraisal Committee (GEAC), consider the following statements: 1. It is an apex body established under the Ministry of Science and Technology for research and industrial production related to biotechnology. 2. Bt Cotton and Bt Brinjal are the only crops permitted for cultivation in India by the Genetic Engineering Appraisal Committee. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 115, "question": "With reference to Human Eye, consider the following statements: 1. The white part of the eyes is called Iris. 2. Cornea contributes the majority of the eye's total focusing power. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "B", "subject": "Science & Technology"},
    {"id": 116, "question": "Consider the following statements regarding Web 3.0: 1. It combines older-generation web tools with cutting-edge technologies such as AI and blockchain. 2. It establishes a new version of the Internet protocol incorporating token-based economics, transparency, and decentralization. Which of the statements given above is/are not correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 117, "question": "With reference to the Snailfish, consider the following statements: 1. The Snailfish releases biofluorescence, which allows it to glow in the water. 2. Snailfish are the only polar fish reported to have biofluorescence. Which of the given above statements is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 118, "question": "With reference to the James Webb Telescope comparison with other Telescopes, consider the following statements: 1. Kepler was designed to be a wide and shallow survey telescope, while Webb is designed for narrow and deep. 2. Webb is sensitive to wavelengths from visible light to mid-infrared, while Herschel was sensitive to the far-infrared wavelength. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "Science & Technology"},
    {"id": 119, "question": "Artemis I Mission recently seen in the news, it is related to which of the following?", "options": ["Mercury", "Neptune", "Moon", "Jupiter"], "correct_answer": "C", "subject": "Science & Technology"},
    {"id": 120, "question": "Which of the following best describes \"Agnikul\" and \"Skyroot\", which were recently in news?", "options": ["ISRO's in-orbit satellite servicing stations", "Start-ups developing launch vehicles for small payloads", "The controlled anti-satellite weapons", "ISRO's initiative to monitor space debris"], "correct_answer": "B", "subject": "Science & Technology"},
    {"id": 121, "question": "What is the Cas9 protein that is often mentioned in the news?", "options": ["A molecular scissors used in targeted gene editing.", "A biosensor used in the accurate detection of pathogens in patients.", "A gene that makes plants pest-resistant.", "A herbicidal substance synthesised in genetically modified crops"], "correct_answer": "A", "subject": "Science & Technology"},
    {"id": 122, "question": "Consider the following statements: 1. The National Tiger Conservation Authority (NTCA) is a statutory body constituted under enabling provisions of the Wildlife (Protection) Act, 1972. 2. The 'Project Tiger' is a Central Sector Scheme of the Ministry of Environment, Forests and Climate Change. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "C", "subject": "Environment"},
    {"id": 123, "question": "Recently, \"Pangong Tso Lake\" was in the news, with reference to it, consider the following statements: 1. It is an endorheic lake. 2. The lake is identified under the Ramsar Convention as a wetland of international importance. 3. An Inner Line Permit is required to visit the lake. Which of the following statements is correct?", "options": ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1,2 and 3"], "correct_answer": "C", "subject": "Environment"},
    {"id": 124, "question": "Which of the following projects comes under the State Environment Impact Assessment Authority (SEIAA)? 1. Metallurgical industries 2. Highways 3. Cement plants 4. Hydroelectric power projects Select the correct answer using the code given below", "options": ["1, 3 and 4 only", "2 and 3 only", "1 and 4 only", "1, 2, 3 and 4"], "correct_answer": "D", "subject": "Environment"},
    {"id": 125, "question": "The proposal for the creation of the India Environment Service (IES) was recommended by:", "options": ["Gadgil committee", "Kelkar Committee", "T.S.R Subramanian committee", "Ranbir Singh Committee"], "correct_answer": "D", "subject": "Environment"},
    {"id": 126, "question": "Which of the following are the key provisions of the Energy Conservation (Amendment) Bill, 2022? 1. Mandating the use of non-fossil sources. 2. Establishment of Carbon Markets 3. Bringing large residential buildings within the fold of the Energy Conservation regime 4. Increasing the members of the governing council of the Bureau of Energy Efficiency (BEE) Select the correct answer using the code given below:", "options": ["1 and 2 only", "3 and 4 only", "1, 2 and 3 only", "1, 2, 3 and 4"], "correct_answer": "A", "subject": "Environment"},
    {"id": 127, "question": "Consider the following statements regarding India's recently launched Hydrogen Fuel Cell Bus: 1. It is made up of novel downstream process technology. 2. It is a Russian technology imported through India-Russia Joint Technology Assessment and Accelerated Commercialization Programme. 3. Its refueling time is more compared to the Battery-operated Electric Vehicles. Which of the statements given above is are correct?", "options": ["1 only", "2 and 3 only", "1 and 3 only", "3 only"], "correct_answer": "D", "subject": "Environment"},
    {"id": 128, "question": "Consider the following statements: 1. \"Net Zero\" is when a country's emissions are compensated by the absorption and removal of greenhouse gases (GHGs) from the atmosphere. 2. 'Getting India to Net Zero' report was recently released by NITI Aayog. 3. Panchamrit strategy envisages 'Net Zero' targets to be achieved by 2050 in India. Which of the statements given above is are correct?", "options": ["1 only", "1 and 2 only", "2 and 3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "Environment"},
    {"id": 129, "question": "Center for Wildlife Rehabilitation and Conservation (CWRC) is a joint initiative of which of the following ? 1. Wildlife Trust of India (WTI) 2. International Fund for Animal Welfare (IFAW) 3. Arunachal Pradesh State Forest Department Select the correct answer using the code given below", "options": ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "Environment"},
    {"id": 130, "question": "Recently, the Lisbon Declaration was in the news. It aims at?", "options": ["Ocean conservation", "Preserving the Wetlands", "Persistent Organic Pollutants", "Trade in Endangered Species"], "correct_answer": "A", "subject": "Environment"},
    {"id": 131, "question": "With reference to Regional Comprehensive Economic Partnership (RCEP), consider the following statements: (1) The RCEP is expected to eliminate all the tariffs. (2) The group includes India and China both but not the USA. (3) Australia and Japan are members of RCEP and CPTPP both. Which of the following statements is/are correct?", "options": ["1 and 2 only", "2 only", "3 only", "1 and 3 only"], "correct_answer": "D", "subject": "Economics"},
    {"id": 132, "question": "Recently, RBI allowed offline digital payments, consider the following statements in this regard: 1. An offline digital payment means a transaction that does not require internet or telecom connectivity. 2. These transactions require an additional factor of authentication (AFA). 3. There is a lower limit of Rs 2,000 for all transactions. Which of the following statements is are correct?", "options": ["1 only", "2 only", "1 and 3 only", "1, 2 and 3"], "correct_answer": "A", "subject": "Economics"},
    {"id": 133, "question": "With reference to the Index of Industrial Production (IIP), consider the following statements: 1. It is compiled and published monthly by the Office of Economic Adviser. 2. The base year for the index is 2004-2005. Which of the statements given above is are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "A", "subject": "Economics"},
    {"id": 134, "question": "With reference to Pradhan Mantri Jan Arogya Yojana (PM-JAY ), consider the following statements: 1. It provides a cover of Rs. 5 lakhs per family per year for secondary and tertiary care hospitalization in public hospitals only. 2. Under it, there is no restriction on the family size, age or gender. 3. The households included in the yojna are based on the deprivation and occupational criteria of Socio-Economic Caste Census 2011 (SECC 2011) for rural and urban areas respectively. Which of the statements given above are correct?", "options": ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1, 2 and 3"], "correct_answer": "B", "subject": "Economics"},
    {"id": 135, "question": "With reference to Purchasing Managers' Index (PMI), consider the following statements: 1. It provides information about current and future business conditions. 2. It is indicated by a number from 0 to 100. 3. If the previous month PMI is higher than the current month PMI, it represents that the economy is contracting. Which of the statements given above are correct?", "options": ["1 and 2 only", "2 and 3 only", "1 and 3 only", "1,2 and 3"], "correct_answer": "D", "subject": "Economics"},
    {"id": 136, "question": "Which of the following statements is /are correct regarding the Sovereign Gold Bond (SGB) scheme? 1. Gold Bonds are issued by the Scheduled Commercial Banks on behalf of the Union Government. 2. Interest on Gold Bonds are tax exempted under the Income Tax Act, 1961. Select the correct answer using the codes given below:", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "Economics"},
    {"id": 137, "question": "With reference to the Codex Alimentarius Commission, often seen in the news, which of the following statements is/are correct? 1. It is an international food standards body aimed at ensuring fair practices in the food trade. 2. It is established by the World Trade Organization (WTO). 3. Codex Standards issued by the commission is mandatory and binding on the member nations. Select the correct answer using the code given below:", "options": ["1 only", "1 and 2 only", "1 and 3 only", "2 and 3 only"], "correct_answer": "A", "subject": "Economics"},
    {"id": 138, "question": "Which of the following reports were published by the World Economic Forum (WEF)? 1. Global Gender Gap Report. 2. Global Risk Report. 3. Global Financial Stability Report 4. Global Competitiveness Report Select the correct answer using the code given below:", "options": ["1 and 3 only", "3 and 4 only", "1, 2 and 4 only", "1, 2, 3 and 4"], "correct_answer": "C", "subject": "Economics"},
    {"id": 139, "question": "Consider the following statements: 1. Capital expenditure involves any expenditure that does not add to assets or reduce liabilities. 2. Revenue expenditure is incurred with the purpose of increasing assets of a durable nature or of reducing recurring liabilities. Which of the statements given above is/are not correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "C", "subject": "Economics"},
    {"id": 140, "question": "Consider the following statements: 1. Repo Rate is the interest rate at which the Reserve Bank provides liquidity against the collateral of government and other approved securities. 2. Marginal Standing Facility (MSF) Rate is the penal rate at which banks can borrow, on an overnight basis, from the Reserve Bank by dipping into their Statutory Liquidity Ratio (SLR) portfolio up to a predefined limit. Which of the statements given above is/are correct?", "options": ["1 Only", "2 Only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "C", "subject": "Economics"},
    {"id": 141, "question": "With reference to Agriculture Infrastructure Fund (AIF), consider the following statements: 1. It is a pan India Central Sector Scheme launched in the year 2020. 2. It provides a medium - long term debt financing facility for investment in viable projects. 3. All loans under this financing facility will have an interest subvention of 10% per annum up to a limit of Rs. 2 crores. Which of the statements given above is/are correct?", "options": ["1 only", "1 and 2 only", "3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "Economics"},
    {"id": 142, "question": "Recently, the Global Employment Trend for Youth 2022 report was released by which organisation?", "options": ["World Economic Forum", "World Bank", "International Labour Organisation", "International Monetary Fund"], "correct_answer": "C", "subject": "Current Affairs"},
    {"id": 143, "question": "India Council for Research on International Economic Relations (ICRIER) conducts thematic research in which of the following areas? 1. Growth, Employment and Macroeconomics (GEM) 2. Trade, Investment and External Relations (TIER) 3. Agriculture Policy, Sustainability and Innovation (APSI) 4. Climate Change, Urbanisation and Sustainability (CCUS) Select the correct answer using the code given below:", "options": ["1, 2 and 3 only", "1, 2 and 4 only", "1, 3 and 4 only", "1,2, 3 and 4"], "correct_answer": "D", "subject": "Economics"},
    {"id": 144, "question": "Which organisation releases the \"Financial Stability Report\"?", "options": ["Organisation for Economic Co-operation and Development", "World Bank", "United Nations", "Reserve Bank of India"], "correct_answer": "D", "subject": "Economics"},
    {"id": 145, "question": "Consider the following statements regarding Sustainable Development Goals (SDGs): 1. India is behind all south Asian nations except Pakistan in its 2021 SDG ranking. 2. SDG India Index is developed by Oxfam India in collaboration with the United Nations. Which of the statements given above is/are correct?", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "Current Affairs"},
    {"id": 146, "question": "Consider the following statements regarding Foreign portfolio investment (FPI): 1. It is often referred to as Hot money because it is less liquid and less risky than FDI. 2. FPI is part of a country's Current account. 3. It provides the investor with direct ownership of financial assets. Which of the given above statements is/are correct?", "options": ["1 only", "2 only", "3 only", "None of the above"], "correct_answer": "D", "subject": "Economics"},
    {"id": 147, "question": "Microcredit is delivered through which of the institutional channels in India ? 1. Scheduled commercial banks (SCBs) 2. Cooperative banks 3. Non-banking financial companies (NBFCs) Select the correct answer using the code given below:", "options": ["1 only", "1 and 2 only", "3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "Economics"},
    {"id": 148, "question": "Consider the following statements regarding Global Gender Gap Index, 2022: 1. It is published by UN's Inter-Agency Network on Women and Gender Equality (IANWGE). 2. India's score is above the global average in Political Empowerment dimension. 3. India is ranked the last among all the countries in Health and Survival dimension. Select the correct answer using the code given below:", "options": ["1 only", "2 only", "2 and 3 only", "1, 2 and 3"], "correct_answer": "D", "subject": "Current Affairs"},
    {"id": 149, "question": "Which of the following statements are incorrect regarding the Global Minimum Tax deal? 1. It aims to ensure that big companies pay a minimum tax rate of 15% and do not avoid taxation 2. The rate would apply to all the overseas profits of multinational firms irrespective of their global sales. Select the correct answer using the code given below:", "options": ["1 only", "2 only", "Both 1 and 2", "Neither 1 nor 2"], "correct_answer": "D", "subject": "Economics"},
    {"id": 150, "question": "Which of the following are the benefits of the creation of Eco Sensitive Zone (ESZ)? 1. In-situ conservation 2. Reduction in man-animal conflict 3. Mitigating climate change 4. Protection of tribal rights Select the correct answer using the code given below:", "options": ["1 and 2 only", "3 and 4 only", "2, 3 and 4 only", "1, 2, 3 and 4"], "correct_answer": "D", "subject": "Environment"}
]

# Subject-wise analysis categories
SUBJECT_ANALYSIS = {
    "Mathematics": "Quantitative Aptitude & Problem Solving",
    "Geography": "Physical & Human Geography",
    "Environment": "Environment & Ecology",
    "Current Affairs": "Current Events & General Awareness",
    "Science & Technology": "Science & Technology",
    "History": "Ancient, Medieval & Modern History",
    "Polity": "Indian Polity & Governance",
    "Economics": "Indian Economy & Finance",
    "Agriculture": "Agriculture & Rural Development"
}

@app.route('/')
def index():
    # Clear any existing session data when returning to home
    session.clear()
    return render_template('index.html')

@app.route('/start_exam')
def start_exam():
    try:
        # Clear any existing session data first
        session.clear()
        
        # Initialize fresh session data
        session['exam_id'] = str(uuid.uuid4())
        session['start_time'] = datetime.now().isoformat()
        session['answers'] = {}
        session['marked_for_review'] = []
        session['current_question'] = 1
        session['time_remaining'] = 90 * 60  # 90 minutes in seconds
        
        logger.info(f"Started new exam session: {session['exam_id']}")
        # Add 'new' parameter to indicate fresh start
        return redirect(url_for('exam') + '?new=1')
    except Exception as e:
        logger.error(f"Error starting exam: {e}")
        return render_template('error.html'), 500

# Add route to clear session and restart
@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect(url_for('index'))

@app.route('/exam')
def exam():
    try:
        # Debug session state
        logger.info(f"Exam route accessed. Session keys: {list(session.keys())}")
        logger.info(f"Session exam_id: {session.get('exam_id', 'NOT FOUND')}")
        
        # Temporary workaround for session issues in VS Code browser
        if 'exam_id' not in session:
            logger.warning("No exam_id in session, creating temporary session")
            # Create a temporary session for testing
            session['exam_id'] = 'temp-session'
            session['start_time'] = datetime.now().isoformat()
            session['answers'] = {}
            session['marked_for_review'] = []
            session['current_question'] = 1
            session['time_remaining'] = 90 * 60  # 90 minutes in seconds
        
        # Get question number from URL parameter or session
        question_num = request.args.get('q', type=int)
        if question_num and 1 <= question_num <= len(QUESTIONS_DATA):
            session['current_question'] = question_num
        
        current_q = session.get('current_question', 1)
        question = next((q for q in QUESTIONS_DATA if q['id'] == current_q), QUESTIONS_DATA[0])
        
        # Get user's answer for this question
        user_answer = session.get('answers', {}).get(str(current_q))
        
        logger.info(f"Rendering exam page for question {current_q}")
        
        return render_template('exam.html', 
                             question=question,
                             total_questions=len(QUESTIONS_DATA),
                             current_question=current_q,
                             user_answer=user_answer,
                             answers=session.get('answers', {}),
                             marked_for_review=session.get('marked_for_review', []))
    except Exception as e:
        logger.error(f"Error loading exam page: {e}")
        return render_template('error.html'), 500

@app.route('/navigate/<int:question_id>')
def navigate_question(question_id):
    if 'exam_id' not in session:
        return redirect(url_for('index'))
    
    if 1 <= question_id <= len(QUESTIONS_DATA):
        session['current_question'] = question_id
    
    return redirect(url_for('exam'))

@app.route('/save_answer', methods=['POST'])
def save_answer():
    if 'exam_id' not in session:
        return jsonify({'error': 'Session expired'}), 400
    
    data = request.json
    question_id = data.get('question_id')
    answer = data.get('answer')
    
    if 'answers' not in session:
        session['answers'] = {}
    
    session['answers'][str(question_id)] = answer
    session.modified = True
    
    return jsonify({'success': True})

@app.route('/mark_for_review', methods=['POST'])
def mark_for_review():
    if 'exam_id' not in session:
        return jsonify({'error': 'Session expired'}), 400
    
    data = request.json
    question_id = data.get('question_id')
    
    if 'marked_for_review' not in session:
        session['marked_for_review'] = []
    
    if question_id not in session['marked_for_review']:
        session['marked_for_review'].append(question_id)
    else:
        session['marked_for_review'].remove(question_id)
    
    session.modified = True
    
    return jsonify({'success': True})

# Add route to handle form-based answer submission
@app.route('/exam', methods=['POST'])
def submit_answer():
    if 'exam_id' not in session:
        return redirect(url_for('index'))
    
    answer = request.form.get('answer')
    current_q = session.get('current_question', 1)
    
    if answer:
        if 'answers' not in session:
            session['answers'] = {}
        session['answers'][str(current_q)] = answer
        session.modified = True
    
    # Navigate to next question or stay on current
    action = request.form.get('action', 'next')
    if action == 'next' and current_q < len(QUESTIONS_DATA):
        return redirect(url_for('exam', q=current_q + 1))
    elif action == 'previous' and current_q > 1:
        return redirect(url_for('exam', q=current_q - 1))
    else:
        return redirect(url_for('exam', q=current_q))

# Auto-save progress API endpoint
@app.route('/api/save-progress', methods=['POST'])
def api_save_progress():
    if 'exam_id' not in session:
        return jsonify({'error': 'Session expired'}), 400
    
    try:
        data = request.json
        if data.get('answers'):
            session['answers'] = data['answers']
        if data.get('currentQuestion'):
            session['current_question'] = data['currentQuestion']
        if data.get('timeLeft'):
            session['time_remaining'] = data['timeLeft']
        
        session.modified = True
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving progress: {e}")
        return jsonify({'error': 'Failed to save progress'}), 500

@app.route('/get_exam_status')
def get_exam_status():
    if 'exam_id' not in session:
        return jsonify({'error': 'Session expired'}), 400
    
    start_time = datetime.fromisoformat(session['start_time'])
    elapsed_time = (datetime.now() - start_time).total_seconds()
    time_remaining = max(0, (3 * 60 * 60) - elapsed_time)
    
    question_status = []
    for q in QUESTIONS_DATA:
        qid = str(q['id'])
        status = 'not_attempted'
        if qid in session.get('answers', {}):
            status = 'attempted'
        if q['id'] in session.get('marked_for_review', []):
            if status == 'attempted':
                status = 'attempted_marked'
            else:
                status = 'marked_for_review'
        
        question_status.append({
            'id': q['id'],
            'status': status
        })
    
    return jsonify({
        'time_remaining': int(time_remaining),
        'question_status': question_status,
        'current_question': session.get('current_question', 1),
        'attempted': len(session.get('answers', {})),
        'total_questions': len(QUESTIONS_DATA),
        'marked_for_review': len(session.get('marked_for_review', []))
    })

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    try:
        # Clean up old results first
        cleanup_old_results()
        
        # Handle both session-based and JSON-based submissions
        if request.is_json:
            # Handle JSON submission from JavaScript
            data = request.get_json()
            answers = data.get('answers', {})
            marked_for_review = data.get('markedForReview', [])
        else:
            # Handle form submission
            answers = session.get('answers', {})
            marked_for_review = session.get('marked_for_review', [])
        
        # Ensure we have session data
        if not answers and 'exam_id' not in session:
            return jsonify({'error': 'No exam session found'}), 400
        
        # Calculate results
        total_questions = len(QUESTIONS_DATA)
        correct_answers = 0
        subject_wise_score = {}
        
        for question in QUESTIONS_DATA:
            qid = str(question['id'])
            subject = question['subject']
            
            if subject not in subject_wise_score:
                subject_wise_score[subject] = {'correct': 0, 'total': 0}
            
            subject_wise_score[subject]['total'] += 1
            
            if qid in answers and answers[qid] == question['correct_answer']:
                correct_answers += 1
                subject_wise_score[subject]['correct'] += 1
        
        # Calculate score (2 marks per question, no negative marking)
        total_score = correct_answers * 2
        max_score = total_questions * 2
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        
        # Store results in both session and temporary storage
        results_data = {
            'total_questions': total_questions,
            'attempted': len(answers),
            'correct': correct_answers,
            'incorrect': len(answers) - correct_answers,
            'not_attempted': total_questions - len(answers),
            'total_score': total_score,
            'max_score': max_score,
            'percentage': percentage,
            'subject_wise_score': subject_wise_score,
            'answers': answers,
            'marked_for_review': marked_for_review
        }
        
        # Generate a unique results ID
        results_id = str(uuid.uuid4())
        
        # Store in temporary storage with timestamp
        exam_results_storage[results_id] = {
            'data': results_data,
            'timestamp': time.time()
        }
        
        # Also try to store in session as backup
        session['exam_results'] = results_data
        session['results_id'] = results_id
        session.permanent = True
        
        logger.info(f"Exam submitted successfully. Score: {total_score}/{max_score} ({percentage:.1f}%)")
        logger.info(f"Results stored with ID: {results_id}")
        
        if request.is_json:
            # For JSON requests, include the results in the response for immediate display
            # Format subject_wise_results with percentage for immediate use
            subject_wise_results = {}
            for subject, stats in subject_wise_score.items():
                percentage_calc = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
                subject_wise_results[subject] = {
                    'correct': stats['correct'],
                    'total': stats['total'],
                    'percentage': percentage_calc
                }
            
            return jsonify({
                'success': True,
                'results': results_data,
                'subject_wise_results': subject_wise_results,
                'results_id': results_id,
                'redirect_url': f'/results?id={results_id}'
            })
        else:
            return redirect(url_for('results', id=results_id))
            
    except Exception as e:
        logger.error(f"Error submitting exam: {e}")
        if request.is_json:
            return jsonify({'error': 'Failed to submit exam', 'details': str(e)}), 500
        else:
            return render_template('error.html'), 500

@app.route('/results')
def results():
    try:
        results_data = None
        results_id = request.args.get('id')
        
        # Try to get results from URL parameter first
        if results_id and results_id in exam_results_storage:
            results_data = exam_results_storage[results_id]['data']
            logger.info(f"Displaying results from storage ID {results_id}: {results_data['correct']}/{results_data['total_questions']} correct")
        
        # Fallback to session
        elif 'exam_results' in session:
            results_data = session['exam_results']
            logger.info(f"Displaying results from session: {results_data['correct']}/{results_data['total_questions']} correct")
        
        # Fallback to session with results_id
        elif 'results_id' in session and session['results_id'] in exam_results_storage:
            results_id = session['results_id']
            results_data = exam_results_storage[results_id]['data']
            logger.info(f"Displaying results from session results_id {results_id}: {results_data['correct']}/{results_data['total_questions']} correct")
        
        else:
            logger.warning("No exam results found")
            # Check if we have any exam data at all
            if 'exam_id' not in session and not results_id:
                logger.warning("No exam session found, redirecting to index")
                return redirect(url_for('index'))
            else:
                logger.warning("Exam session exists but no results found, creating placeholder")
                # Create empty results as fallback
                results_data = {
                    'total_questions': len(QUESTIONS_DATA),
                    'attempted': 0,
                    'correct': 0,
                    'incorrect': 0,
                    'not_attempted': len(QUESTIONS_DATA),
                    'total_score': 0,
                    'max_score': len(QUESTIONS_DATA) * 2,
                    'percentage': 0,
                    'subject_wise_score': {},
                    'answers': {},
                    'marked_for_review': []
                }
        
        # Generate analysis
        analysis = generate_analysis(results_data)
        
        # Format subject_wise_results with percentage for template
        subject_wise_results = {}
        for subject, stats in results_data['subject_wise_score'].items():
            percentage = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            subject_wise_results[subject] = {
                'correct': stats['correct'],
                'total': stats['total'],
                'percentage': percentage
            }
        
        return render_template('results.html', 
                             results=results_data, 
                             analysis=analysis,
                             percentage=results_data['percentage'],
                             subject_wise_results=subject_wise_results,
                             correct_answers=results_data['correct'],
                             total_questions=results_data['total_questions'],
                             unattempted=results_data['not_attempted'])
    except Exception as e:
        logger.error(f"Error loading results page: {e}")
        return render_template('error.html'), 500

def generate_analysis(results):
    analysis = {
        'strengths': [],
        'areas_for_improvement': [],
        'recommendations': []
    }
    
    subject_wise = results['subject_wise_score']
    
    # Identify strengths (>70% in subject)
    for subject, scores in subject_wise.items():
        if scores['total'] > 0:
            percentage = (scores['correct'] / scores['total']) * 100
            if percentage >= 70:
                analysis['strengths'].append(f"{SUBJECT_ANALYSIS.get(subject, subject)} ({percentage:.1f}%)")
            elif percentage < 50:
                analysis['areas_for_improvement'].append(f"{SUBJECT_ANALYSIS.get(subject, subject)} ({percentage:.1f}%)")
    
    # Generate recommendations based on overall performance
    overall_percentage = results['percentage']
    
    if overall_percentage >= 80:
        analysis['recommendations'].append("Excellent performance! Focus on maintaining consistency and speed.")
        analysis['recommendations'].append("Practice advanced level questions to further enhance your skills.")
    elif overall_percentage >= 60:
        analysis['recommendations'].append("Good performance with room for improvement.")
        analysis['recommendations'].append("Focus on weak areas identified in the subject-wise analysis.")
        analysis['recommendations'].append("Practice more questions in areas where you scored below 60%.")
    else:
        analysis['recommendations'].append("Significant improvement needed across multiple areas.")
        analysis['recommendations'].append("Focus on building strong fundamentals in weak subjects.")
        analysis['recommendations'].append("Consider structured study plan with regular practice tests.")
    
    # Time management analysis
    if results['not_attempted'] > results['total_questions'] * 0.1:
        analysis['recommendations'].append("Work on time management - too many questions left unattempted.")
    
    return analysis

@app.route('/answer_review')
def answer_review():
    try:
        results_data = None
        results_id = request.args.get('id')
        
        # Try to get results from URL parameter first
        if results_id and results_id in exam_results_storage:
            results_data = exam_results_storage[results_id]['data']
            logger.info(f"Displaying answer review for storage ID {results_id}")
        
        # Fallback to session
        elif 'exam_results' in session:
            results_data = session['exam_results']
            logger.info(f"Displaying answer review from session")
        
        # Fallback to session with results_id
        elif 'results_id' in session and session['results_id'] in exam_results_storage:
            results_id = session['results_id']
            results_data = exam_results_storage[results_id]['data']
            logger.info(f"Displaying answer review from session results_id {results_id}")
        
        else:
            logger.warning("No exam results found for answer review")
            return redirect(url_for('index'))
        
        # Validate results_data
        if not results_data:
            logger.error("Results data is None or empty")
            return redirect(url_for('index'))
        
        # Create detailed answer analysis
        detailed_answers = []
        user_answers = results_data.get('answers', {})
        
        for question in QUESTIONS_DATA:
            qid = str(question['id'])
            user_answer = user_answers.get(qid, '')
            is_correct = user_answer == question['correct_answer']
            is_attempted = qid in user_answers
            is_marked = qid in results_data.get('marked_for_review', [])
            
            # Calculate character indices for template styling
            correct_index = ord(question['correct_answer']) - ord('A') if question['correct_answer'] else -1
            user_index = ord(user_answer) - ord('A') if user_answer else -1
            
            detailed_answers.append({
                'question_num': question['id'],
                'question': question['question'],
                'options': question['options'],
                'correct_answer': question['correct_answer'],
                'correct_index': correct_index,
                'user_answer': user_answer,
                'user_index': user_index,
                'is_correct': is_correct,
                'is_attempted': is_attempted,
                'is_marked': is_marked,
                'subject': question['subject'],
                'explanation': f"The correct answer is option {question['correct_answer']}."
            })
        
        logger.info(f"Created {len(detailed_answers)} detailed answers for template")
        
        return render_template('answer_review_basic.html', 
                             answers=detailed_answers,
                             results=results_data,
                             total_questions=len(QUESTIONS_DATA))
                             
    except Exception as e:
        import traceback
        logger.error(f"Error loading answer review page: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return render_template('error.html'), 500

if __name__ == '__main__':
    # Use environment variable for port (Railway will set this)
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
