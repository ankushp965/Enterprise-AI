import json
import os

questions = [
    # 1-15: Happy Path (Single Domain)
    {"question": "How many paid annual leave days do employees get?", "expected_answer": "Employees are entitled to 24 paid leave days annually."},
    {"question": "How many sick leaves do I get?", "expected_answer": "Employees receive 12 sick leave days per year."},
    {"question": "What is the maternity leave policy?", "expected_answer": "26 weeks paid leave."},
    {"question": "What are the standard work hours?", "expected_answer": "Standard work hours are 9 AM to 6 PM IST."},
    {"question": "How much internet reimbursement is allowed?", "expected_answer": "Remote employees may claim up to ₹1500/month."},
    {"question": "Can I claim meal reimbursement?", "expected_answer": "Allowed only for approved overtime work."},
    {"question": "Who needs to approve expense claims?", "expected_answer": "All claims require manager approval."},
    {"question": "How do I reset my password?", "expected_answer": "Use self-service portal first."},
    {"question": "What is the response time for critical incidents?", "expected_answer": "Response time under 30 minutes."},
    {"question": "Can I work from outside India?", "expected_answer": "Working outside India requires VP approval."},
    {"question": "What are the core hours for remote workers?", "expected_answer": "Core collaboration hours are 10 AM to 4 PM IST."},
    {"question": "Is there a budget for home office equipment?", "expected_answer": "One-time allowance of ₹25000 for home office setup."},
    {"question": "How often must I change my password?", "expected_answer": "Passwords must be changed every 90 days."},
    {"question": "Is VPN access required?", "expected_answer": "VPN access is mandatory for external connections."},
    {"question": "How soon must I report a lost device?", "expected_answer": "Lost devices must be reported within 1 hour."},

    # 16-30: Multi-Domain & Complex Routing
    {"question": "How many sick leaves do I get, and what are the core hours for remote work?", "expected_answer": "Employees receive 12 sick leave days per year. Core collaboration hours are 10 AM to 4 PM IST."},
    {"question": "Can interns claim travel reimbursement, and what are the standard work hours?", "expected_answer": "Interns cannot claim travel reimbursement. Standard work hours are 9 AM to 6 PM IST."},
    {"question": "Is VPN mandatory, and how much is the home office allowance?", "expected_answer": "VPN access is mandatory. One-time allowance of ₹25000 for home office setup."},
    {"question": "Do I need manager approval for meal reimbursement and laptop replacement?", "expected_answer": "Yes, meal reimbursement is for approved overtime, and laptop replacement requires manager authorization."},
    {"question": "What is the paternity leave, and how often must I change my password?", "expected_answer": "Paternity leave is 15 days paid leave. Passwords must be changed every 90 days."},
    {"question": "Can interns get internet reimbursement and paid annual leave?", "expected_answer": "Interns are not eligible for internet reimbursement and are not eligible for paid annual leave."},
    {"question": "Are USB devices allowed, and who do I escalate VPN issues to?", "expected_answer": "Unauthorized external USB devices are prohibited. VPN issues should be escalated to the Network Support Team."},
    {"question": "What are the remote work core hours and standard work hours?", "expected_answer": "Standard work hours are 9 AM to 6 PM IST. Core collaboration hours are 10 AM to 4 PM IST."},
    {"question": "Can I work outside India, and is MFA required?", "expected_answer": "Working outside India requires VP approval. Multi-factor authentication is required."},
    {"question": "How many days of annual leave and maternity leave do we get?", "expected_answer": "Employees get 24 paid annual leave days and 26 weeks of paid maternity leave."},
    {"question": "What is the password reset process and the VPN requirement?", "expected_answer": "Use self-service portal first for password reset. VPN access is mandatory for external connections."},
    {"question": "Who approves travel reimbursement and laptop replacement?", "expected_answer": "Both require manager approval/authorization."},
    {"question": "How much is the internet reimbursement and home office allowance?", "expected_answer": "Internet reimbursement up to ₹1500/month. Home office allowance is ₹25000."},
    {"question": "If I work overtime, can I claim meals and what is the attendance check-in?", "expected_answer": "Meals are allowed for approved overtime work. Daily check-in on Slack is required by 9:30 AM."},
    {"question": "What happens to lost devices and what is the critical incident response time?", "expected_answer": "Lost devices must be reported within 1 hour. Critical incident response time is under 30 minutes."},

    # 31-40: Edge Cases & Conflicting Keywords (Contextual Relevancy Focus)
    {"question": "I lost my laptop while on a business travel - what is the reimbursement process?", "expected_answer": "Lost devices must be reported within 1 hour. Travel reimbursement is for approved business travel expenses. Laptop replacement requires manager authorization."},
    {"question": "During maternity leave, do I need to do a daily check-in on Slack?", "expected_answer": "The policy requires daily check-in on Slack by 9:30 AM, but typically leaves exempt you. Context does not explicitly exempt maternity leave."},
    {"question": "If I am sick, can I get meal reimbursement?", "expected_answer": "Meal reimbursement is allowed only for approved overtime work, not for sick leave."},
    {"question": "Can interns use unauthorized USB devices if they get VP approval?", "expected_answer": "Unauthorized external USB devices are prohibited. VP approval is only mentioned for working outside India."},
    {"question": "If I have an incident with my internet, can I escalate to Level 1 support and get ₹1500?", "expected_answer": "For IT issues, contact Level 1 IT support if self-service fails. Remote employees may claim up to ₹1500/month for internet reimbursement."},
    {"question": "What is the response time if I forget my password?", "expected_answer": "Use self-service portal first for password reset. Critical incidents have a response time under 30 minutes (password reset is not explicitly critical)."},
    {"question": "Are interns eligible for paternity leave and travel reimbursement?", "expected_answer": "Interns cannot claim travel reimbursement. The policy does not explicitly deny interns paternity leave, but states they are not eligible for paid annual leave."},
    {"question": "I'm working outside India. Do I still get the home office allowance?", "expected_answer": "Working outside India requires VP approval. There is a one-time allowance of ₹25000 for home office setup."},
    {"question": "Do I need a VPN to check my paid annual leave balance?", "expected_answer": "VPN access is mandatory for external connections. Annual leave is 24 days."},
    {"question": "Can a manager approve working outside India?", "expected_answer": "Working outside India requires VP approval, not manager approval."},

    # 41-50: Negative Constraints & Out-of-Domain (Faithfulness Focus)
    {"question": "What is the policy for dog insurance?", "expected_answer": "I could not find this information in company policy."},
    {"question": "How many days of bereavement leave are allowed?", "expected_answer": "I could not find this information in company policy."},
    {"question": "Can I claim gym membership reimbursement?", "expected_answer": "I could not find this information in company policy."},
    {"question": "What happens if I lose my personal phone?", "expected_answer": "Lost devices must be reported within 1 hour. It does not specify personal vs company phone."},
    {"question": "Are interns eligible for paid annual leave, internet reimbursement, and travel reimbursement?", "expected_answer": "Interns are not eligible for paid annual leave, internet reimbursement, or travel reimbursement."},
    {"question": "Can I expense my coffee if I work from a cafe?", "expected_answer": "Meal reimbursement is allowed only for approved overtime work. Coffee is not explicitly mentioned."},
    {"question": "Who provides support for broken chairs?", "expected_answer": "I could not find this information in company policy."},
    {"question": "Do I get paid overtime if I work past 6 PM?", "expected_answer": "I could not find this information in company policy (only meal reimbursement is mentioned for overtime)."},
    {"question": "Can I use a VPN to bypass the 90-day password change rule?", "expected_answer": "No, passwords must be changed every 90 days. VPN access is mandatory for external connections."},
    {"question": "Is there a bonus for completing 5 years at TechNova?", "expected_answer": "I could not find this information in company policy."}
]

os.makedirs('data', exist_ok=True)
with open('data/comprehensive_eval_questions.json', 'w', encoding='utf-8') as f:
    json.dump(questions, f, indent=2, ensure_ascii=False)

print(f"Generated {len(questions)} test cases.")
