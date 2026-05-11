# SpendSense AI — Personal Expense Tracker

An AI-powered personal finance dashboard built with **Python & Streamlit**, featuring smart data analysis, Groq AI insights, interactive charts, EDA tools, forecasting, and PDF export.

---

## Features

### 📊 Analytics Dashboard
- Time series charts for expense trends
- Category-wise pie/bar breakdown
- Correlation heatmap across numeric columns
- Multi-currency support (PKR, USD, EUR, GBP, AED, SAR)

### 🔍 EDA (Exploratory Data Analysis)
- Full data overview: rows, columns, missing values, duplicates
- Column info table with data types, unique counts & samples
- Missing values heatmap
- Key stats: Mean, Median, Mode, Std, Min, Max
- Outlier detection with IQR boxplot

### ✏️ Data Editing (Live)
- Fill missing values (Mean / Median / Mode / Zero)
- Drop duplicate rows
- Rename columns
- Drop columns
- Change data types (int, float, str, datetime)
- Download edited CSV

### 🤖 AI Insights (Groq API)
- 6 analysis types: Spending Patterns, Budget Recommendations, Saving Tips, Category Analysis, Anomaly Detection, Monthly Summary
- 3 quick insight buttons
- Multi-language support (English / Urdu)
- Powered by Llama, Gemma & Mixtral models

### 💬 AI Chat
- Multi-turn conversational chat about your data
- 3 quick prompt suggestions
- Clear chat history option

### 🎯 Savings Goal Tracker
- Custom savings goal input
- 4 preset goals
- Progress bar with percentage tracking

### 📈 Forecast & PDF
- Linear trend forecasting per column
- AI-powered forecast analysis
- One-click PDF report generation

---

## Tech Stack

| Layer        | Technology                              |
|--------------|-----------------------------------------|
| UI Framework | Streamlit                               |
| Data         | Pandas, NumPy                           |
| Charts       | Plotly Express & Graph Objects          |
| AI           | Groq API (Llama 3.1, Gemma2, Mixtral)   |
| Forecasting  | Statsmodels (Linear Regression)         |
| PDF Export   | fpdf2                                   |
| Language     | Python 3.10+                            |

---

## Project Structure

```
spendsense/
├── app.py              # Main Streamlit UI (tabs, sidebar, layout)
├── utils.py            # Data logic, AI functions, PDF, forecasting
├── theme.py            # Color themes, currencies, CSS injection
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/spendsense.git
cd spendsense
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run app.py
```

### 4. Get a Groq API Key (Free)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up and generate a free API key (`gsk_...`)
3. Paste it in the sidebar under 🔑 **Groq API Key**

---

## CSV Format

Your CSV should have at least a `Date` and one numeric column (e.g. `Amount`).

| Date       | Amount | Category  | Income | Savings | Description |
|------------|--------|-----------|--------|---------|-------------|
| 2024-01-07 | 7770   | Shopping  | 60253  | 10996   | Fuel        |
| 2024-01-14 | 1360   | Health    | 58433  | 4731    | Medicine    |

> Don't have a CSV? Click **Load Sample Data** on the landing page!

---

## Themes & Customization

6 built-in color themes via sidebar:
- Purple (Default)
- Ocean Blue
- Emerald
- Rose
- Amber
- Pink

---

## Supported AI Models

| Model                     | Best For              |
|---------------------------|-----------------------|
| `llama-3.1-8b-instant`    | Fast responses        |
| `llama-3.3-70b-versatile` | Deep analysis         |
| `llama3-8b-8192`          | Long context          |
| `gemma2-9b-it`            | Balanced performance  |
| `mixtral-8x7b-32768`      | Complex reasoning     |

---

## Screenshots

> _Add your screenshots here_

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [yourprofile](https://linkedin.com/in/yourprofile)