# Finance Categorizer

This command analyzes bank statement CSV files, corrects missing or incorrect categorizations, and generates comprehensive spending reports with visual indicators for high spending areas.

## Instructions

- IMPORTANT: Use inline astral uv python code (with any libraries you need) to calculate the totals and percentages. Use `uv run python --with pandas --with <whatever library you need> -c "import pandas as pd; print(\"whatever you want here\")"` to test your code.
  - Example: `uv run --with rich python -c "from rich.console import Console; Console().print('Hello', style='bold red')"`
- IMPORTANT: Think hard about your calculations ALWAYS double check your work as you go along.
- IMPORTANT: After you generate your report, review your numbers comprehensively with python. Also, make sure you write emojis and not unicode characters.
- In your finance_report.yaml file, do not use yaml anchors or aliases and do not use !!python tags. Write everything out as primitive types even if it means duplicating data.

## Variables

DROPPED_FILE_PATH: [[FILE_PATH]]
DROPPED_FILE_PATH_ARCHIVE: agentic_drop_zone/finance_zone/drop_zone_file_archive/
FINANCE_OUTPUT_DIR: agentic_drop_zone/finance_zone/finance_output/<date_time>/
    - This is the directory where all processed files and reports will be saved
    - The date_time is the current date and time in the format YYYY-MM-DD_HH-MM-SS

### Output File Paths
CATEGORIZED_STATEMENT: FINANCE_OUTPUT_DIR/<date_time>/categorized_statement.csv
    - The cleaned and properly categorized bank statement
FINANCE_REPORT: FINANCE_OUTPUT_DIR/<date_time>/finance_report.yaml
    - The comprehensive financial analysis report in YAML format
SPENDING_PIE_CHART: FINANCE_OUTPUT_DIR/<date_time>/spending_by_category.png
    - Pie chart visualization of spending by category
BALANCE_LINE_CHART: FINANCE_OUTPUT_DIR/<date_time>/balance_over_time.png
    - Line chart showing account balance progression over time

### Spending Thresholds (per category monthly spending)
LOW_SPENDING_THRESHOLD: 500
    - Categories under this amount get 💰 emoji
MODERATE_SPENDING_THRESHOLD: 1000  
    - Categories between LOW and MODERATE get 🔥 emoji
HIGH_SPENDING_THRESHOLD: 2000
    - Categories between MODERATE and HIGH get 🔥🔥 emoji
    - Categories over HIGH get 🔥🔥🔥 emoji

### Individual Transaction Alerts
LARGE_TRANSACTION: 500
    - Single transactions over this get 🚨 flag
UNUSUAL_TRANSACTION: 1000
    - Single transactions over this get ⚠️ flag
MAJOR_PURCHASE: 2500
    - Single transactions over this get 🔴 flag

### Budget Warning Percentages
HOUSING_WARNING_PCT: 30
    - Alert if housing > this % of monthly income
DINING_ENTERTAINMENT_WARNING_PCT: 20
    - Alert if dining/entertainment > this % of total expenses
SHOPPING_WARNING_PCT: 15
    - Alert if shopping > this % of total expenses
TRANSPORTATION_WARNING_PCT: 20
    - Alert if transportation > this % of total expenses
SUBSCRIPTION_WARNING_PCT: 10
    - Alert if subscriptions > this % of total expenses

## Workflow

### Setup Phase
- Create output directory: `mkdir -p FINANCE_OUTPUT_DIR/<date_time>/`
- Copy original file to preserve it: `cp DROPPED_FILE_PATH FINANCE_OUTPUT_DIR/<date_time>/original_statement.csv`
- Create working copy: `cp FINANCE_OUTPUT_DIR/<date_time>/original_statement.csv FINANCE_OUTPUT_DIR/<date_time>/categorized_statement.csv`

### Analysis & Categorization Phase
- Read the working copy: `FINANCE_OUTPUT_DIR/<date_time>/categorized_statement.csv`
- For each transaction row:
  - Check if category is missing or incorrect
  - Apply categorization rules from "How to Categorize" section
  - Track which categories need updating
- Use MultiEdit to update all categories at once in the working copy
- Verify all transactions now have appropriate categories

### Calculation Phase
- Calculate totals:
  - Total income = sum of all deposits
  - Total expenses = sum of all withdrawals
  - Net cash flow = income - expenses
- Group expenses by category and calculate:
  - Total spending per category
  - Number of transactions per category
  - Percentage of total expenses per category
- Identify top 5 spending categories
- Identify top 5 largest individual transactions
- Count transactions exceeding alert thresholds

### Report Generation Phase
- Create report file: `FINANCE_OUTPUT_DIR/<date_time>/finance_report.yaml`
- Generate visualization charts as PNG files (use matplotlib with optional seaborn for styling):
  1. **Spending Pie Chart** (`FINANCE_OUTPUT_DIR/<date_time>/spending_by_category.png`):
     - Use matplotlib or plotly to create a pie chart
     - Show top 10 categories by spending amount
     - Include percentages and dollar amounts on labels
     - Use distinct colors for each category
     - Title: "Monthly Spending by Category - [Month Year]"
     - Figure size: 12x8 inches
     - DPI: 150 for high quality
     - Add legend with category names and amounts
     - Explode the largest spending category slightly for emphasis
     - Example command:
       ```bash
       uv run --with pandas --with matplotlib python -c "
       import pandas as pd
       import matplotlib.pyplot as plt
       # Read categorized data
       df = pd.read_csv('categorized_statement.csv')
       # Group by category and sum withdrawals
       # Create pie chart with top 10 categories
       # plt.figure(figsize=(12, 8))
       # plt.savefig('spending_by_category.png', dpi=150, bbox_inches='tight')
       "
       ```
  
  2. **Account Balance Chart** (`FINANCE_OUTPUT_DIR/<date_time>/balance_over_time.png`):
     - Create a line chart showing balance progression through the month
     - X-axis: dates (formatted as MM/DD)
     - Y-axis: running balance (formatted with $ and commas)
     - Mark major transactions (>$1000) with red dots and annotations
     - Add horizontal dashed line for starting balance
     - Add horizontal dotted line for ending balance
     - Include grid for better readability
     - Title: "Account Balance Over Time - [Month Year]"
     - Figure size: 14x7 inches
     - DPI: 150 for high quality
     - Use gradient fill below the line (green for positive, red for negative if applicable)
     - Add min/max balance annotations
     - Example command:
       ```bash
       uv run --with pandas --with matplotlib python -c "
       import pandas as pd
       import matplotlib.pyplot as plt
       import matplotlib.dates as mdates
       # Read categorized data
       df = pd.read_csv('categorized_statement.csv')
       # Convert date column to datetime
       # plt.figure(figsize=(14, 7))
       # Plot balance over time with styling
       # Annotate major transactions
       # plt.savefig('balance_over_time.png', dpi=150, bbox_inches='tight')
       "
       ```

- Generate YAML report with the following structure:

```yaml
report_date: YYYY-MM-DD HH:MM:SS
month_analyzed: August 2025

financial_summary:
  total_income: 20000.00
  total_expenses: 74567.89
  net_cash_flow: -54567.89
  cash_flow_status: negative  # positive or negative
  transactions_analyzed: 87

top_spending_categories:
  - category: "AI Services"
    amount: 45678.90
    emoji: "🔥🔥🔥"  # Based on thresholds
    percentage: 61.2
    transaction_count: 23
  - category: "Technology - Cloud"
    amount: 12345.67
    emoji: "🔥🔥🔥"
    percentage: 16.5
    transaction_count: 15
  # ... top 5

largest_transactions:
  - date: "2025-08-29"
    description: "ANTHROPIC CLAUDE-OPUS-4-1-API"
    amount: 6789.01
    category: "AI Services"
    alert: "🔴"  # Based on individual thresholds
  - date: "2025-08-22"
    description: "AWS MONTHLY BILLING 866-216-1072"
    amount: 5678.90
    category: "Technology"
    alert: "🔴"
  # ... top 5

all_categories:
  - category: "AI Services"
    amount: 45678.90
    transactions: 23
    percentage: 61.2
  - category: "Amazon"
    amount: 23456.78
    transactions: 18
    percentage: 31.4
  # ... all categories sorted by amount

budget_warnings:
  - type: "Housing"
    actual_percentage: 21.0
    recommended_max: 30
    status: "OK"
  - type: "Shopping"
    actual_percentage: 31.4
    recommended_max: 15
    status: "⚠️ EXCEEDED"
  # ... check all warning categories

transaction_alerts:
  major_purchases:  # Over MAJOR_PURCHASE threshold
    count: 12
    total: 45678.90
  unusual_transactions:  # Over UNUSUAL_TRANSACTION threshold
    count: 28
    total: 67890.12
  large_transactions:  # Over LARGE_TRANSACTION threshold
    count: 45
    total: 89012.34

insights:
  highest_spending_day:
    date: "2025-08-29"
    amount: 9234.56
  most_frequent_merchant:
    name: "AMAZON"
    count: 18
  total_amazon_spending: 23456.78
  subscription_count: 6
  
subscriptions_detected:
  - name: "Netflix"
    amount: 15.99
  - name: "Spotify"
    amount: 9.99
  - name: "AWS"
    amount: 5678.90
  # ... all recurring charges

recommendations:
  - "AI Services spending (61.2%) is extremely high - review API usage and consider optimization"
  - "Shopping exceeds budget by 16.4% - consider reducing Amazon purchases"
  - "Multiple AWS charges detected - consolidate billing or review unused services"

visualizations:
  spending_pie_chart: "spending_by_category.png"
  balance_line_chart: "balance_over_time.png"
```

### Completion Phase
- Save the categorized statement and report
- Display summary in console:
  ```
  ✅ Processing Complete
  - Transactions processed: XX
  - Categories fixed: XX
  - Files created:
    - categorized_statement.csv
    - finance_report.yaml
    - spending_by_category.png
    - balance_over_time.png
  ```
- Open output directory: `open FINANCE_OUTPUT_DIR/<date_time>/`
- Archive the original: `mv DROPPED_FILE_PATH DROPPED_FILE_PATH_ARCHIVE/`

## How to Categorize

Apply these rules in order of priority:

### Priority 1: Merchant-Specific Mappings
- AMAZON (any mention including AMZN but not AWS) → `Amazon`
- AWS (Amazon Web Services) → `Technology - Cloud`
- ANTHROPIC, CLAUDE → `AI Services`
- OPENAI, GPT, DALL-E → `AI Services`
- GOOGLE NANO-BANANA → `AI Services`
- GOOGLE COMPUTE, COMPUTE ENGINE, EC2, VM, INSTANCE → `Compute`
- TARGET → `Retail Shopping`
- WALMART, COSTCO, SAM'S CLUB → `Wholesale Shopping`
- SAFEWAY, KROGER, WHOLE FOODS, TRADER JOE'S → `Groceries`
- UBER (not UBER EATS), LYFT, TAXI → `Transportation - Rideshare`
- SHELL, CHEVRON, EXXON, GAS STATION → `Transportation - Gas`
- TESLA, CAR PAYMENT → `Transportation - Auto`
- NETFLIX, HULU, SPOTIFY, APPLE MUSIC → `Entertainment - Streaming`
- STARBUCKS, COFFEE, CAFE, BLUE BOTTLE, PHILZ → `Dining - Coffee`
- RESTAURANT, BISTRO, SUSHI, PIZZA → `Dining - Restaurant`
- UBER EATS, DOORDASH, GRUBHUB → `Dining - Delivery`
- CHIPOTLE, MCDONALD'S, SUBWAY → `Dining - Fast Food`

### Priority 2: Keyword-Based Rules
- MORTGAGE, RENT → `Housing - Primary`
- ELECTRIC, PG&E, WATER, UTILITY → `Utilities`
- INSURANCE → `Insurance - [Type]` (Auto/Health/Life based on context)
- GYM, FITNESS, EQUINOX, YOGA → `Health - Fitness`
- DOCTOR, DENTIST, MEDICAL, DR → `Health - Medical`
- PHARMACY, CVS, WALGREENS → `Health - Pharmacy`
- PAYROLL, SALARY, DIRECT DEPOSIT, ACH CREDIT → `Income - Salary`
- TAX, IRS, COUNTY TAX → `Taxes`
- INVESTMENT, SCHWAB, FIDELITY, VANGUARD → `Investment`
- PHONE, VERIZON, AT&T, T-MOBILE → `Utilities - Phone`
- INTERNET, XFINITY, COMCAST → `Utilities - Internet`
- PET, VET, PETCO → `Pet Care`
- HOME DEPOT, LOWE'S → `Home Improvement`
- PARKING METER, PARKING → `Transportation - Parking`
- AIRLINE, HOTEL, AIRBNB → `Travel`
- APPLE STORE, BEST BUY → `Shopping - Electronics`
- NORDSTROM, GAP, H&M → `Shopping - Clothing`

### Priority 3: Default Categories
- Deposits without clear source → `Income - Other`
- Withdrawals without clear purpose → `Cash Withdrawal`
- Any Amazon not categorized → `Amazon`
- Food-related uncategorized → `Groceries`
- Service-related uncategorized → `Services`
- Retail uncategorized → `Shopping - General`

## My Categories

- `AI Services`
- `Amazon`
- `Banking Fees`
- `Cash Withdrawal`
- `Cloud Computing`
- `Compute`
- `Dining - Coffee`
- `Dining - Delivery`
- `Dining - Fast Food`
- `Dining - Restaurant`
- `Entertainment - General`
- `Entertainment - Streaming`
- `Groceries`
- `Health - Fitness`
- `Health - Medical`
- `Health - Pharmacy`
- `Home Improvement`
- `Housing - Primary`
- `Income - Other`
- `Income - Salary`
- `Insurance - Auto`
- `Insurance - Health`
- `Insurance - Life`
- `Investment`
- `Miscellaneous`
- `Pet Care`
- `Retail Shopping`
- `Services`
- `Shopping - Clothing`
- `Shopping - Electronics`
- `Shopping - General`
- `Taxes`
- `Technology - Cloud`
- `Technology - Software`
- `Transportation - Auto`
- `Transportation - Gas`
- `Transportation - Parking`
- `Transportation - Rideshare`
- `Travel`
- `Utilities`
- `Utilities - Internet`
- `Utilities - Phone`
- `Wholesale Shopping`