<h1 align="center">Vinted-Aplikacja</h1>
<H2>Podgląd aplikacji jak wyglada na danym ubraniu</H2>
<hr>
<img width="1188" height="956" alt="obraz" src="https://github.com/user-attachments/assets/2c8d853e-6c8e-4598-8ab9-4b3013b0c71d" />

<tr></tr>
<table>
<tr>
<td align="center">
<img width="350" alt="AI Analysis" src="https://github.com/user-attachments/assets/fd8ca03a-c031-4e73-9a8c-5f8e63e271b3" />
<br />
<strong>AI Analysis</strong>
</td>
<td align="center">
<img width="350" alt="Dashboard" src="https://github.com/user-attachments/assets/f4d90a4a-ff74-4bff-aadc-90082ff225bf" />
<br />
<strong>Dashboard</strong>
</td>
<td align="center">
<img width="350" alt="Offers" src="https://github.com/user-attachments/assets/5418b690-ed9a-4f11-b9f4-a9e4c81c0d0e" />
<br />
<strong>Offers</strong>
</td>

</tr>
</table>
<hr>

## Tech Stack

### Frontend
- React
- TypeScript / TSX
- Axios
- Recharts
- CSS
<hr>
### Backend
- Java
- Spring Boot
- WebClient
- REST API

### AI / Data Service
- Python
- FastAPI
- Playwright
- Pandas
- NumPy
- scikit-learn
- SQLAlchemy

### Database
- PostgreSQL

### AI Integration
- Gemini Vision API

---

## Project Structure

```txt
vinted-pricer-api/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── MarketDashboard.tsx
│   │   ├── App.css
│   │   └── main.tsx
│   └── package.json
│
├── python-ai/
│   ├── main.py
│   ├── dashboard.py
│   ├── brands.py
│   ├── .env
│   └── venv/
│
├── src/
│   └── main/
│       ├── java/
│       │   └── com/arek/vintedpricer/vintedpricerapi/
│       │       ├── controller/
│       │       │   └── ValuationController.java
│       │       ├── dto/
│       │       │   ├── ClothingAnalysisResponse.java
│       │       │   └── SimilarOffer.java
│       │       ├── service/
│       │       │   ├── OpenAiVisionService.java
│       │       │   ├── PythonPricingService.java
│       │       │   └── SimilarOffersSearchService.java
│       │       └── VintedPricerApiApplication.java
│       └── resources/
│
├── build/
├── gradle/
└── README.md
```
<hr>
<h1>Aplikacja od środka - jak wygląda</h1>
