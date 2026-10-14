# 📈 AlphaSage — AI-Powered Investment Intelligence Platform
### Sentiment Analysis + Deep Learning Price Prediction (DL + AI + AWS-ready)

Yeh project ek **simulated trading portfolio dashboard** hai jisme:
- Tumhare (mock) holdings dikhte hain — jaise Zerodha Kite / Groww app
- **Add/Delete stocks** — sidebar se apna portfolio manage karo, permanently save hota hai
- **Price alerts/notifications** — jab koi stock buy price se bahut zyada up/down chala jaye
- Har stock ka **REAL live price** (yfinance se) aur **candlestick chart**
- **News sentiment analysis** (NLP) — company ke baare mein news positive hai ya negative
- **LSTM (Deep Learning) price prediction** — agla price kya ho sakta hai, **pre-trained saved models** ke saath (fast, production-jaisa)
- **Model evaluation + backtesting** — RMSE/MAE metrics, aur "strategy vs buy-and-hold" comparison
- **Explainability (SHAP)** — dikhata hai prediction mein kaunsa feature kitna contribute kar raha hai
- **Multi-stock comparison** — 2+ stocks ka normalized performance ek saath dekho
- Sentiment + Prediction combine karke ek simple **Buy/Hold/Sell signal**
- **Dark/Light theme toggle** — real trading app jaisa professional look
- **Dockerized** — `Dockerfile` + `docker-compose.yml` se kahin bhi deploy ho sakta hai
- **CI/CD pipeline** (GitHub Actions) — har push pe automatic syntax + Docker build check

Broker API (Kite Connect) **paid hai**, isliye yahaan **free yfinance** use kiya hai live
prices ke liye, aur ek **mock portfolio** (`data/mock_portfolio.json`) real holdings ki
jagah use hoti hai. Poora code isi tarah likha gaya hai ki agar kabhi Kite/Angel One
API mil jaye, sirf `src/fetch_prices.py` replace karna hoga — baaki sab (sentiment,
prediction, dashboard) same rahega.

---

## 🗂️ Project Structure

```
stock-ai-dashboard/
├── app.py                    ← Main dashboard (Streamlit) - ISE RUN KARNA HAI
├── requirements.txt          ← Saari libraries ki list
├── .streamlit/
│   └── config.toml           ← Light blue theme settings
├── data/
│   └── mock_portfolio.json   ← Tumhara portfolio (Add/Delete se auto-update hota hai)
├── src/
│   ├── fetch_prices.py       ← yfinance se REAL live + historical prices
│   ├── sentiment.py          ← News sentiment analysis (TextBlob + NewsAPI)
│   ├── predict.py            ← LSTM deep learning price prediction
│   ├── portfolio_manager.py  ← Add/Delete stock logic (JSON file update)
│   └── alerts.py             ← Price alert/notification logic
└── README.md                 ← Yeh file
```

---

## 🚀 Kaise Chalana Hai (Step-by-Step)

### Step 1: Python install check karo
Terminal/CMD mein:
```bash
python --version
```
Python 3.9+ hona chahiye. Agar nahi hai toh [python.org](https://python.org) se install karo.

### Step 2: Zip file extract karo
Zip ko kisi folder mein extract karo, phir terminal mein us folder ke andar jao:
```bash
cd stock-ai-dashboard
```

### Step 3: Virtual environment banao (recommended)
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 4: Libraries install karo
```bash
pip install -r requirements.txt
```
⚠️ Yeh 5-10 minute le sakta hai (tensorflow bada hai). Internet connection chahiye.

### Step 5: Dashboard run karo
```bash
streamlit run app.py
```
Yeh automatically browser mein khul jayega (`http://localhost:8501`). Agar nahi khule
toh terminal mein diya gaya link copy-paste kar do browser mein.

### Step 6: Dekho magic! 🎉
- Portfolio table dikhega
- Kisi bhi stock ko dropdown se select karo
- Uska graph, sentiment, aur prediction dikhega

---

## ➕ Stock Add/Delete Karna (Dashboard se hi)

Left sidebar mein:
- **"➕ Add New Stock"** expander kholo → symbol (e.g. `WIPRO`), quantity, buy price, date bharo → "Add Stock" dabao. Agar stock already portfolio mein hai, quantity aur average price automatically update ho jayegi (jaise real broker karta hai).
- **"🗑️ Remove Stock"** expander kholo → dropdown se stock select karo → "Remove Selected Stock" dabao.

Yeh sab `data/mock_portfolio.json` mein **permanently save** hota hai — dashboard restart karne pe bhi data rahega.

## 🔔 Price Alerts / Notifications

Sidebar mein "Alert Settings" ke sliders se decide karo:
- **Loss alert**: kitna % niche jaane pe warning aaye (default -10%)
- **Gain alert**: kitna % upar jaane pe notification aaye (default +15%)

Jab koi stock threshold cross karta hai, dashboard ke top pe red/green alert box dikhega + ek chhota **toast notification** bhi aayega.

---

---

## Zerodha Kite Connect Se Real Holdings Lena (FREE)

Zerodha ne 2025 mein **Kite Connect "Personal" plan free** kar diya hai — holdings, positions, orders access karna bilkul free hai. (Sirf live market data ke liye paise lagte hain, jo hume nahi chahiye kyunki hum yfinance use kar rahe hain.)

### Setup Steps:

1. **App register karo**: [kite.trade](https://kite.trade) pe jaake apne Zerodha login se sign in karo
2. **"Create new app"** click karo, App type mein **"Personal"** select karo (FREE)
3. Redirect URL mein kuch bhi daal do: `http://127.0.0.1:5000/callback`
4. Tumhe **API Key** aur **API Secret** milega — copy kar lo

5. Project ke root folder mein `.env.example` ko `.env` naam se copy karo:
   ```bash
   copy .env.example .env
   ```
   `.env` file kholo aur apni API key/secret daalo:
   ```
   KITE_API_KEY=your_api_key_here
   KITE_API_SECRET=your_api_secret_here
   ```

6. **Access token generate karo** (yeh roz karna padega — Kite ka token security ke liye sirf 1 din valid hota hai):
   ```bash
   python src/generate_kite_token.py
   ```
   Yeh ek link dega, use browser mein kholo, apne Zerodha credentials se login karo, redirect hone ke baad URL mein se `request_token=XXXX` wala part copy karke terminal mein paste karo. Access token automatically `.env` mein save ho jayega.

7. `streamlit run app.py` chalao — sidebar mein **"Use real Zerodha holdings"** toggle dikhega, ON karo. Ab tumhari **asli holdings** (jo mobile Kite app mein dikhti hain) yahan dikhengi, live prices ke saath.

**Important**: Access token roz expire hota hai, isliye roz dashboard use karne se pehle Step 6 (`generate_kite_token.py`) ek baar chalana padega.

---

## ⚙️ Optional: Real News Sentiment ke liye NewsAPI Key lagao

Bina key ke bhi chalega (demo headlines use hongi), lekin real news ke liye:

1. [newsapi.org](https://newsapi.org/register) pe free account banao (100 requests/day free)
2. API key copy karo
3. `src/sentiment.py` file kholo, yeh line dhundo:
   ```python
   NEWS_API_KEY = "YOUR_NEWSAPI_KEY_HERE"
   ```
4. Apni key paste karo:
   ```python
   NEWS_API_KEY = "abc123yourkey..."
   ```
5. Dashboard restart karo

---

## ✏️ Apna Portfolio Customize Karna

`data/mock_portfolio.json` file kholo aur apne hisaab se stocks add/edit/remove karo:

```json
{"symbol": "WIPRO.NS", "name": "Wipro", "quantity": 12, "avg_buy_price": 480.0, "buy_date": "2025-08-01"}
```

**Important**: NSE stocks ke liye symbol ke aage `.NS` lagana zaroori hai
(e.g., `RELIANCE.NS`, `TCS.NS`). BSE ke liye `.BO` use hota hai.

---

## ☁️ AWS Pe Deploy Kaise Karein (Placement ke liye important)

Abhi yeh locally chal raha hai. Real project ke liye AWS pe deploy karne ka plan:

| Local Component | AWS Equivalent |
|---|---|
| `mock_portfolio.json` | DynamoDB table |
| `fetch_prices.py` (runs locally) | Lambda function (scheduled via EventBridge) |
| `sentiment.py` | Lambda + Comprehend, ya SageMaker endpoint |
| `predict.py` (LSTM training) | SageMaker Training Job |
| Trained model | SageMaker Endpoint (real-time inference) |
| `app.py` (Streamlit) | EC2 instance, ya rewrite as React + host on S3+CloudFront |
| Historical data | S3 bucket |

### Simple deployment path (beginner-friendly):
1. **EC2 instance** launch karo (t2.micro - free tier)
2. Is poore project ko EC2 pe copy karo (git clone ya scp)
3. `pip install -r requirements.txt` EC2 pe bhi chalao
4. `streamlit run app.py --server.port 80` se run karo
5. Security group mein port 80 open karo
6. EC2 public IP se dashboard access ho jayega

### Advanced path (interview mein zyada impress karega):
1. LSTM model ko SageMaker mein train karo (notebook instance use karke)
2. Model ko SageMaker endpoint pe deploy karo
3. Lambda function banao jo har 15 min mein prices/news fetch kare (EventBridge trigger)
4. Results DynamoDB mein store karo
5. API Gateway banao jo DynamoDB se data serve kare
6. Frontend (React) banao jo API Gateway se data le aur dikhaye
7. S3 + CloudFront pe frontend host karo

*(Agar chaho toh main is advanced AWS version ka poora code bhi bana sakti hu - alag se maang lena)*

---

## 🎯 Advanced Features Kaise Use Karein

### Pre-trained Models (fast predictions)
Dashboard by default LSTM ko har baar live train karta hai (thoda slow). Isko fast banane ke liye ek baar models train karke save kar do:
```bash
python src/train_models.py
```
Ye har portfolio stock ke liye model train karke `models/` folder mein save kar dega. Agli baar dashboard khulega toh saved models directly load honge (fast).

### Backtesting + Model Accuracy
Stock Deep Dive section mein "Model Performance & Backtest" expander kholo — wahan RMSE, MAE, aur "Strategy vs Buy & Hold" return comparison dikhega.

### Explainability (SHAP)
Stock Deep Dive mein "Why this prediction?" section mein dikhega ki kaunsa feature (kal ka price, parson ka price, news sentiment) prediction ko sabse zyada influence kar raha hai.

### Multi-Stock Comparison
Dashboard mein "Compare Stocks" section mein 2+ stocks select karo — unka normalized % performance ek hi chart mein dikhega.

### Docker se Run Karna
```bash
docker-compose up --build
```
Isse dashboard ek container mein chalega — `http://localhost:8501` pe access karo. Interview mein bolna: "Maine app ko Dockerize kiya hai taaki kahin bhi consistent environment mein deploy ho sake."

---

## 🎤 Interview Mein Kya Bolna Hai

**Q: Project ke baare mein bataiye**
> "Maine ek AI-powered stock portfolio dashboard banaya jo do ML models combine karta
> hai — ek NLP-based sentiment analysis model jo news headlines analyze karta hai, aur
> ek LSTM-based deep learning model jo historical price data se future price predict
> karta hai. Dono outputs ko combine karke ek trading signal generate hota hai."

**Q: Real broker data use kyun nahi kiya?**
> "Kite Connect API paid hai (₹2000/month), toh maine architecture Kite Connect ke
> data structure ke around design kiya taaki production mein directly plug-and-play
> ho sake, lekin development/testing free yfinance API se ki jo unlimited aur free
> hai."

**Q: LSTM kyun use kiya, simple regression kyun nahi?**
> "Stock prices sequential/time-dependent data hai — LSTM ka strength hi yeh hai ki
> woh long-term dependencies aur temporal patterns capture kar sakta hai jo simple
> regression miss kar deta. Maine dropout layers bhi add kiye overfitting rokne ke
> liye."

**Q: Isko production/scale ke liye kaise design karoge?**
> "SageMaker pe training pipeline banaunga jisse auto-retraining ho sake naye data pe,
> Lambda + EventBridge se scheduled data ingestion, aur DynamoDB se low-latency reads.
> Cost optimize karne ke liye SageMaker endpoint ko auto-scaling pe rakhunga aur idle
> time mein scale-down karunga."

---

## 🐛 Common Issues

| Problem | Solution |
|---|---|
| `yfinance` data empty aa raha hai | Internet check karo, ya market band ho toh purana data aayega (normal hai) |
| TensorFlow install nahi ho raha | `pip install tensorflow-cpu` try karo (lighter version) |
| Streamlit port already in use | `streamlit run app.py --server.port 8502` |
| NLTK download error | Manually run: `python -c "import nltk; nltk.download('vader_lexicon')"` |
| `pandas`/build error, "Meson build system", "vswhere.exe not found" | Yeh hota hai jab Python version bahut naya hai (3.13+) aur package ka pre-built wheel nahi milta, toh pip source se build karne ki koshish karta hai. **Fix**: `python --version` check karo — agar 3.13+ hai, toh Python **3.11 ya 3.12** install karo ([python.org](https://python.org)) aur venv usi se banao: `py -3.11 -m venv venv`. Requirements.txt mein ab version pins hata diye hain, isliye latest wheels khud milengi. |
| `tensorflow` install hi nahi ho raha | TensorFlow abhi bahut naye Python versions (3.13+) support nahi karta. Python 3.11/3.12 use karo, ya `pip install tensorflow-cpu` try karo, ya code chalega LSTM ke bina bhi (moving-average fallback automatically use hoga). |

---

## 📌 Next Steps / Improvements (agar time ho)

- [x] Backtesting module (RMSE/MAE + strategy vs buy-and-hold) — DONE
- [x] SHAP explainability — DONE
- [x] Multi-stock comparison — DONE
- [x] Docker + CI/CD (GitHub Actions) — DONE
- [ ] Real Kite Connect/Angel One API integrate karo (agar access mil jaye)
- [ ] FinBERT model use karo TextBlob ki jagah (zyada accurate, finance-specific)
- [ ] Email/SMS alerts (AWS SNS use karke)
- [ ] SageMaker pe actual deploy karo (abhi architecture SageMaker-compatible hai)

---

Good luck for placements! 🚀
